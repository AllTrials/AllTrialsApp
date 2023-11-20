import psycopg2
import pandas as pd


DB_PARAMS = {
    'dbname': 'aact',
    'user': 'wesserg',
    'password': 'h5p1le4sq',
    'host': 'aact-db.ctti-clinicaltrials.org',
    'port': 5432  # Default PostgreSQL port
}


def get_aact_connection(db_params: dict = DB_PARAMS)-> psycopg2.extensions.connection:
    """Connect to AACT database"""

    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        print("Connected to the database!")
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error:", error)


# %%
# Get a list of tables in the ctgov schema
def get_studies(aact_table: str = 'studies', aact_schema: str = 'ctgov', n_rows_limit: int = 10000):
    conn = get_aact_connection()
    cursor = conn.cursor()
    aact_query = f"""
    SELECT * FROM {aact_schema}.{aact_table}
    LIMIT {n_rows_limit};
    """

    cursor.execute(aact_query)
    
    result = cursor.fetchall()
    conn.close()
    # get colnames
    column_names = [desc[0] for desc in cursor.description]

    # Convert the result to a DataFrame with column names
    df = pd.DataFrame(result, columns=column_names)
    #if len(df) > 0 and "nct_id" in df.columns and df["nct_id"].nunique() == len(df):
    #    df.set_index('nct_id', inplace=True)
    #if "id" in df.columns:
    #    df.drop('id', axis=1, inplace=True)
    
    return df
    