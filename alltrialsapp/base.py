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

USEFUL_COLUMNS = [
    'nct_id', 'completion_date_type', 'completion_date', 'primary_completion_month_year',
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

USEFUL_TABLES = ['studies','brief_summaries', 'calculated_values', 'eligibilities', 'participant_flows', 'designs', 'detailed_descriptions']

USER_TRIGGER = "User provided text:\n"

EXAMPLE_ALS_AND_FTD = f"""{USER_TRIGGER}
I want to check out all clinical trials related to ALS and FTD that have reached at least phase 3.

Correct sample answer:

SELECT *
FROM ctgov.studies
WHERE (brief_title ILIKE '% ALS %' OR brief_title ILIKE 'ALS %' OR brief_title ILIKE '% ALS' OR brief_title = 'ALS'
    OR brief_title ILIKE '%amyotrophic lateral sclerosis%' OR brief_title ILIKE 'amyotrophic lateral sclerosis%' OR brief_title ILIKE '%amyotrophic lateral sclerosis' OR brief_title = 'amyotrophic lateral sclerosis')
    AND (brief_title ILIKE '% FTD %' OR brief_title ILIKE 'FTD %' OR brief_title ILIKE '% FTD' OR brief_title = 'FTD' 
    OR brief_title ILIKE '%frontotemporal dementia%' OR brief_title ILIKE 'frontotemporal dementia%' OR brief_title ILIKE '%frontotemporal dementia' OR brief_title = 'frontotemporal dementia')
    AND (phase ILIKE '%Phase 3%' OR phase ILIKE '%Phase 4%')
LIMIT 100;
"""

EXAMPLE_NEGATIVE = f"""{USER_TRIGGER}
I'd like to see all trials that are currently enrolling patients with ALS and FTD

Correct sample answer:

SELECT *
FROM ctgov.studies
WHERE (brief_title ILIKE '% ALS %' OR brief_title ILIKE 'ALS %' OR brief_title ILIKE '% ALS' OR brief_title = 'ALS'
    OR brief_title ILIKE '%amyotrophic lateral sclerosis%' OR brief_title ILIKE 'amyotrophic lateral sclerosis%' OR brief_title ILIKE '%amyotrophic lateral sclerosis' OR brief_title = 'amyotrophic lateral sclerosis')
    AND (brief_title ILIKE '% FTD %' OR brief_title ILIKE 'FTD %' OR brief_title ILIKE '% FTD' OR brief_title = 'FTD' 
    OR brief_title ILIKE '%frontotemporal dementia%' OR brief_title ILIKE 'frontotemporal dementia%' OR brief_title ILIKE '%frontotemporal dementia' OR brief_title = 'frontotemporal dementia')
    AND (overall_status = 'Recruiting' and overall_status NOT ILIKE '%Not%')
LIMIT 100;
"""

EXAMPLE_ALS_OR_FTD = f"""{USER_TRIGGER}
I want to check out all clinical trials related to ALS and FTD that have reached at least phase 3.

Correct sample answer:

SELECT *
FROM ctgov.studies
WHERE (brief_title ILIKE '% ALS %' OR brief_title ILIKE 'ALS %' OR brief_title ILIKE '% ALS' OR brief_title = 'ALS'
    OR brief_title ILIKE '%amyotrophic lateral sclerosis%' OR brief_title ILIKE 'amyotrophic lateral sclerosis%' OR brief_title ILIKE '%amyotrophic lateral sclerosis' OR brief_title = 'amyotrophic lateral sclerosis')
    OR (brief_title ILIKE '% FTD %' OR brief_title ILIKE 'FTD %' OR brief_title ILIKE '% FTD' OR brief_title = 'FTD' 
    OR brief_title ILIKE '%frontotemporal dementia%' OR brief_title ILIKE 'frontotemporal dementia%' OR brief_title ILIKE '%frontotemporal dementia' OR brief_title = 'frontotemporal dementia')
    AND (phase ILIKE '%Phase 3%' OR phase ILIKE '%Phase 4%')
LIMIT 100;
"""


BASELINE_PROMPT = f"""
Here is the context for the tasks to follow:

You are an SQL query assistant with deep knowledge of the AACT clinical trials database, tables, and schemas.
You are responding to a user data request on a web app. The user intends to query the AACT database but has limited knowledge of the database schemas, tables, and SQL language.
Your job is to convert the text provided by the user to a valid SQL query for the AACT PostgreSQL database.

Key requirements:
- the query you propose uses the correctly named tables and corresponding columns in the AACT CTGOV database.
- you only return the SQL query and not the context.
- the resulting sql query uses same the logic terms as in user statement.

Resources at your disposal:
- The primary resource at your disposal is the 'studies' table, which has the following columns: {USEFUL_COLUMNS}.
- In addition to 'studies' table, you can use the following tables: {USEFUL_TABLES}.
- When looking for text patterns, in addition on "brief_title" column from studies table, check the following tables their columns:

    "detaield_descriptions": ['description'],
    "eligibilities":['criteria'],
    "participant_flows":['recruitment_details', 'pre_assignment_details'],
    "brief_summaries":['description'],

Unless directed differently, use the CTGOV schema, and limit the number of rows returned to 100.
"""

PROMPTS_DICT = {
    "default": f"{BASELINE_PROMPT}{USER_TRIGGER}",
    "medprompt": f"""{BASELINE_PROMPT}\n
To achieve a sound response, conduct the following steps as you complete the task:
1. In-Context Learning: Examine this example of a simple plausible solution:
- {EXAMPLE_ALS_AND_FTD}\n
- {EXAMPLE_ALS_OR_FTD}\n
- {EXAMPLE_NEGATIVE}\n

2. Chain of Thought: Review the user-provided text and comprehend the user's intent.
    a) What are the key terms user asks about, what are the key disease or drug terms?
    b) Do the terms contain acronyms? If yes, expand acronyms to full terms and include both in the search.
    c) Are there common synonyms for the terms? If yes, include them in the search too.
    d) Which tables and columns in aact database are relevant to the determined set of terms and user request?
    e) What logical operators should be used to combine the terms and columns to best match user input?
    f) Are there any negation statements in the user input? What is the best way to handle them in SQL?
3. Assemble: Develop 10 potential solutions to the user request in SQL query format.

4. Aggregation: Compare the 10 proposed solutions and select the one based on the following criteria:
a) Is common among solutions
b) Is most likely correct answer is user query
c) is least restrictive or has the potential to show the most data.

5. Report only the final solution in the form of an SQL query.

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
    print(f"Checking query:")
    print("------------------------------------------") 
    print(f"{aact_query}\n")
    print("------------------------------------------") 
    
    try:
        conn = get_aact_connection()
        cursor = conn.cursor()
        cursor.execute(aact_query)
        result = cursor.fetchall()
        conn.close()
        
        if len(result) > 0:
            print(f"\n {dt.now()}:  SUCCESS: data found \n")
            return True
        else:
            assert False
    
    except:
        print(f"Failed to get data: Trying a different approach... \n")
        return False
    

def get_query_completion(aact_query: str, n_tries :int = 10) -> str:
    """ 
    This function used a text input and openain text completion to convert
    the text input into a query that can be used to query the aact database.
    """    
    prompt_prefix = PROMPTS_DICT["medprompt"]
    ##It is also important that the query is flexible enough to synonims and abbreviations for the searched phrase.
    prompt = f"{prompt_prefix}{aact_query}"
    print(f"{dt.now()}: Generating daat query using medPrompt: \n")
    print("############################")
    print(f"{prompt}")
    print("############################")
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
        print(f"{dt.now()}: Could not convert the text to a valid sql query, returning empty query")
        return "SELECT * FROM ctgov.studies LIMIT 0;"
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
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database Connection Error:", error)


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
    if only_useful_cols and aact_table == 'studies':
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