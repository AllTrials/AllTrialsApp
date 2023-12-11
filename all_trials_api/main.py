import pandas as pd
from fastapi import FastAPI, Response
from alltrialsapp.examples import get_studies, get_user_data, get_query_completion
app = FastAPI()


# This is the root path
@app.get("/")
async def root():
    return {"message": "Hello World"}

EXAMPLE_TEXT = """
Please show me all studies that mention the ALS condition in brief summaries or study titles.
"""

# This is an example of a path parameter and query parameters
# Try hitting http://127.0.0.1:8000/condition/?name=als&return_data=column1,column2&limit=50
@app.get("/condition/")
async def condition(
    name: str = "Foo",
    return_data: str = None,
    limit: int = 10,
):
    return {"name": name, "return_data": return_data, "limit": limit}


@app.get("/studies/")
async def studies(
    aact_table: str = "studies",
    aact_schema: str = "ctgov",
    n_rows_limit: int = 100,
):
    df = get_studies(aact_table, aact_schema, n_rows_limit)
    print(df)
    df_html = df.to_html(classes="table table-striped table-bordered")
    html_content = f"""
    <html>
        <head>
            <link rel="stylesheet" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css">
            <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
            <script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
        </head>
        <body>
            <script>
                $(document).ready(function() {{
                    $('#myTable').DataTable();
                }});
            </script>
            {df_html}
            
        </body>
    </html>
    """
    # Return HTML content as response
    return Response(content=html_content, media_type="text/html")


@app.get("/example/")
async def example():
    print(EXAMPLE_TEXT)
    aact_query = get_query_completion(EXAMPLE_TEXT)
    print(aact_query)
    df = get_user_data(aact_query=aact_query)
    print(df)
    df_html = df.to_html(classes="table table-striped table-bordered")
    html_content = f"""
    <html>
        <head>
            <link rel="stylesheet" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css">
            <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
            <script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
        </head>
        <body>
            <script>
                $(document).ready(function() {{
                    $('#myTable').DataTable();
                }});
            </script>
            {df_html}
            
        </body>
    </html>
    """
    # Return HTML content as response
    return Response(content=html_content, media_type="text/html")
