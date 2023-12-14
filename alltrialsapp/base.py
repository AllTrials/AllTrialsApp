"""
FastAPI app helper functions for interacting with the AACT (Aggregate Analysis of ClinicalTrials.gov) database using psycopg2 and pandas.
"""

from typing import Dict, Union
import psycopg2
import pandas as pd
from psycopg2.extensions import connection
import os
from openai import OpenAI
from datetime import datetime as dt
from tqdm import tqdm
"""
Database connection parameters.
TODO:  Hardcoded for now, but should be moved to a config file.
"""
DB_PARAMS: Dict[str, Union[str, int]] = {
    'dbname': 'aact',
    'user': 'wesserg',
    'password': 'h5p1le4sq',
    'host': 'aact-db.ctti-clinicaltrials.org',
    'port': 5432  # Default PostgreSQL port
}
USER_TRIGGER = "User provided text: \n"
EXAMPLE_ALS = f"""{USER_TRIGGER}
    I want to check out all clinical trials that are related to ALS that have reached at least phase 3\n_rows_limit

    Correct sample answer:\n
    SELECT *
    FROM ctgov.studies
    WHERE (brief_title ILIKE '% ALS %' OR brief_title ILIKE 'ALS %' OR brief_title ILIKE '% ALS' OR brief_title = 'ALS')
        AND (brief_title ILIKE '%amyotrophic lateral sclerosis%' OR brief_title ILIKE 'amyotrophic lateral sclerosis%' OR brief_title ILIKE '%amyotrophic lateral sclerosis' OR brief_title = 'amyotrophic lateral sclerosis')
        AND (phase ILIKE '%Phase 3%' OR phase ILIKE '%Phase 4%)
    LIMIT 100;
    """
USEFUL_TABLES = ['studies','brief_summaries', 'calculated_values', 'eligibilities', 'participant_flows', 'designs', 'detailed_descriptions']

USEFUL_COLUMNS = [
    'completion_date_type', 'completion_date', 'primary_completion_month_year',
    'primary_completion_date_type', 'primary_completion_date', 'target_duration',
    'study_type', 'acronym', 'baseline_population', 'brief_title', 'official_title',
    'overall_status', 'last_known_status', 'phase', 'enrollment', 'enrollment_type',
    'source', 'limitations_and_caveats', 'number_of_arms', 'number_of_groups',
    'why_stopped', 'has_expanded_access', 'expanded_access_type_individual',
    'expanded_access_type_intermediate', 'expanded_access_type_treatment',
    'has_dmc', 'is_fda_regulated_drug', 'is_fda_regulated_device',
    'is_unapproved_device', 'is_ppsd', 'is_us_export', 'biospec_retention',
    'biospec_description', 'ipd_time_frame', 'ipd_access_criteria', 'ipd_url',
    'plan_to_share_ipd', 'plan_to_share_ipd_description', 'created_at', 'updated_at',
    'source_class'
]

BASELINE_PROMPT = f"""
    Here is the context for the tasks to follow.
    
    Context:
    You are an sql query assistant.
    You have deep knowledge of the AACT clinical trials database, tables and schemas.
    
    You are responding to a user data request on a web app.
    User intends to query the AACT database but has limited knowledge of the database schemas, tables and sql language.
    
    Your job is to convert the text provided by the user to a valid sql query to the aact postgres database.
    
    It is critical that the query you propose uses the correctly named tables and corresponding columns in the aact ctgov database.
    It is critical that the query is case sensitive to acronyms and abbreviations.
    It is critical that you only return the sql query and not the context.
    
    At your disposal are the following tables from the aact database: 
    {USEFUL_TABLES}
    Unless directed differently use ctgov schema, return all columns and limit the number of rows returned to 100.
    """

PROMPTS_DICT = {
    "default":  f"{BASELINE_PROMPT}{USER_TRIGGER}",
    "medprompt": f"""{BASELINE_PROMPT} \n
    To achieve the sound response I want you to conduct the following steps as you complete the task:
    1. In Context learning: Look at the example of simple plausible solution below:
    {EXAMPLE_ALS} \n
    2. Chain of thought: Look at the user provided text and try to understand what the user wants to achieve.
    a) What are the key terms user asks about, what are the key disease or drug terms?
    b) Do the terms contain acronyms that should be exapnded or are there synonyms that should be also included?
    c) Which tables in aact database are relevant to the user request and which columns in those tables could be relevant?

    3. Ensambling: Construct 5 possible solutions to the user request in the form of sql queries.

    4. Aggregation: Comapre the 5 proposed solutions and select the one that is most common and most likely to be correct.

    5. Report only the final solution in the form of the sql query.

    {USER_TRIGGER}\n
    """
}

def remove_limit_from_sql(sql_query: str) -> str:
    # Find the position of the LIMIT clause
    limit_index = sql_query.upper().rfind('LIMIT')

    # If LIMIT clause exists, remove it from the query
    if limit_index != -1:
        # Find the position of the end of the LIMIT clause
        limit_end = sql_query.find(';', limit_index)

        # If LIMIT clause is at the end, remove it along with the preceding space
        if limit_end == -1:
            return sql_query[:limit_index].rstrip()

        # Remove the LIMIT clause along with the preceding space and trailing space or semicolon
        return sql_query[:limit_index].rstrip() + sql_query[limit_end:]

    # If LIMIT clause doesn't exist, return the original query
    return sql_query


def check_aact_query(aact_query: str) -> bool:
    """
    This function checks if the aact_query is a valid sql query
    to the aact database.
    """
    print(f"Checking query: \n{aact_query}")
    
    try:
        conn = get_aact_connection()
        cursor = conn.cursor()
        cursor.execute(aact_query)
        result = cursor.fetchall()
        conn.close()
        print("Success \n")
        if len(result) > 0:
            return True
        else:
            assert False
    
    except:
        print("Failed to get data: Trying a different approach... \n")
        return False
    

def get_query_completion(aact_query: str, n_tries :int = 10) -> str:
    """ 
    This function used a text input and openain text completion to convert
    the text input into a query that can be used to query the aact database.
    """    
    prompt_prefix = PROMPTS_DICT["medprompt"]
    ##It is also important that the query is flexible enough to synonims and abbreviations for the searched phrase.
    prompt = f"{prompt_prefix}{aact_query}"
    print(prompt)
    aact_query_msg_content = None
    for n in tqdm(range(n_tries)):
        client = OpenAI(
            # This is the default and can be omitted
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

        aact_query_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.9,
            model="gpt-3.5-turbo",
        )
        # test if the aact_query is a valid query:
        aact_query_msg_content = aact_query_completion.choices[0].message.content
        if check_aact_query(aact_query_msg_content):
            break
    if n == n_tries:
        print("Could not convert the text to a valid sql query.")
        return False
    else:    
        return aact_query_msg_content


def get_aact_connection(db_params: Dict[str, Union[str, int]] = DB_PARAMS) -> connection:
    """
    Establishes a connection to the AACT database.

    Args:
    - db_params (dict): Dictionary containing database connection parameters.

    Returns:
    - connection: Psycopg2 database connection object.
    """
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        print("Connected to the database!")
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error:", error)


def get_user_data(aact_query: str, only_useful_cols: bool = True) -> pd.DataFrame:
    """
    Retrieves data from the AACT database for a specified table and schema.

    Args:
    - aact_table (str): The table name in the AACT database.
    - aact_schema (str): The schema name in the AACT database.
    - n_rows_limit (int): Maximum number of rows to fetch.

    Returns:
    - pd.DataFrame: DataFrame containing the queried data.
    """
    conn = get_aact_connection()
    cursor = conn.cursor()

    cursor.execute(aact_query)
    
    result = cursor.fetchall()
    conn.close()
    
    # Get column names
    column_names = [desc[0] for desc in cursor.description]

    # Convert the result to a DataFrame with column names
    df = pd.DataFrame(result, columns=column_names)
    # Additional data handling steps (commented out)
    # if len(df) > 0 and "nct_id" in df.columns and df["nct_id"].nunique() == len(df):
    #    df.set_index('nct_id', inplace=True)
    # if "id" in df.columns:
    #    df.drop('id', axis=1, inplace=True)
    #extend the USEFUL_COLUMNS list with the columns that start with the table names
    use_columns = USEFUL_COLUMNS.copy()
    for table_name in USEFUL_TABLES:
        use_columns.extend([col for col in df.columns if col.startswith(table_name)])

    if only_useful_cols:
        df = df[use_columns]
    return df


def get_studies(aact_table: str = 'studies', aact_schema: str = 'ctgov', n_rows_limit: int = 10000, only_useful_cols: bool = True) -> pd.DataFrame:
    """
    Retrieves data from the AACT database for a specified table and schema.

    Args:
    - aact_table (str): The table name in the AACT database.
    - aact_schema (str): The schema name in the AACT database.
    - n_rows_limit (int): Maximum number of rows to fetch.

    Returns:
    - pd.DataFrame: DataFrame containing the queried data.
    """
    conn = get_aact_connection()
    cursor = conn.cursor()
    aact_query = f"""
    SELECT * FROM {aact_schema}.{aact_table}
    LIMIT {n_rows_limit};
    """

    cursor.execute(aact_query)
    
    result = cursor.fetchall()
    conn.close()
    
    # Get column names
    column_names = [desc[0] for desc in cursor.description]

    # Convert the result to a DataFrame with column names
    df = pd.DataFrame(result, columns=column_names)
    # Additional data handling steps (commented out)
    # if len(df) > 0 and "nct_id" in df.columns and df["nct_id"].nunique() == len(df):
    #    df.set_index('nct_id', inplace=True)
    # if "id" in df.columns:
    #    df.drop('id', axis=1, inplace=True)
    if only_useful_cols:
        df = df[USEFUL_COLUMNS]
    return df


# This is a function that fetched and prints brief summaries from the table in aact database
def get_brief_summaries(aact_table: str = 'brief_summaries', aact_schema: str = 'ctgov', n_rows_limit: int = 10000) -> pd.DataFrame:
    """
    Retrieves data from the AACT database for a specified table and schema.

    Args:
    - aact_table (str): The table name in the AACT database.
    - aact_schema (str): The schema name in the AACT database.
    - n_rows_limit (int): Maximum number of rows to fetch.

    Returns:
    - pd.DataFrame: DataFrame containing the queried data.
    """
    conn = get_aact_connection()
    cursor = conn.cursor()
    aact_query = f"""
    SELECT * FROM {aact_schema}.{aact_table}
    LIMIT {n_rows_limit};
    """

    cursor.execute(aact_query)
    
    result = cursor.fetchall()
    conn.close()
    
    # Get column names
    column_names = [desc[0] for desc in cursor.description]

    # Convert the result to a DataFrame with column names
    df = pd.DataFrame(result, columns=column_names)
    # Additional data handling steps (commented out)
    # if len(df) > 0 and "nct_id" in df.columns and df["nct_id"].nunique() == len(df):
    #    df.set_index('nct_id', inplace=True)
    # if "id" in df.columns:
    #    df.drop('id', axis=1, inplace=True)
    
    return df