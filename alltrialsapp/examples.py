"""
FastAPI app helper functions for interacting with the AACT (Aggregate Analysis of ClinicalTrials.gov) database using psycopg2 and pandas.
"""

from typing import Dict, Union
import psycopg2
import pandas as pd
from psycopg2.extensions import connection

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
