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
        return True
    
    except:
        print("Failed to get data: Trying a different approach... \n")
        return False
    

def get_query_completion(aact_query: str, n_tries :int = 10) -> str:
    """ 
    This function used a text input and openain text completion to convert
    the text input into a query that can be used to query the aact database.
    """    
    prompt_prefix = """
    Set model temperature to 0.8
    Here is the context for the tasks to follow.
    
    Context:
    You are an sql query assistant. 
    You have deep knowledge of the AACT clinical trials database, tables and schemas.
    
    You are responding to a user data request on a web app.
    User intends to query the AACT database but has limited knowledge of the database schemas, tables and sql language. 
    
    Your job is to convert the text provided by the user to a valid sql query to the aact postgres database.
    
    It is critical that the query you propose uses the correctly named tables and corresponding columns in the aact ctgov database.
    It is critical that the query is case sensitive to acronyms and abbreviations.
    It is crtical that you only return the sql query and not the context.
    
    At your disposal are the following tables from the aact database: 
    [studies, brief_summaries, calculated_values, eligibilities, participant_flows, designs, detailed_descriptions]
    Unless directed differently use ctgov schema, return all columns and limit the number of rows returned to 1000.
    
    User provided text:
    
    """
    ##It is also important that the query is flexible enough to synonims and abbreviations for the searched phrase.
    
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
                    "content": f"{prompt_prefix}{aact_query}",
                }
            ],
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


def get_user_data(aact_query: str) -> pd.DataFrame:
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
    
    return df


def get_studies(aact_table: str = 'studies', aact_schema: str = 'ctgov', n_rows_limit: int = 10000) -> pd.DataFrame:
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