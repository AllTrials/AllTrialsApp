from fastapi import FastAPI, Response, Form
from fastapi.responses import HTMLResponse  # Import HTMLResponse
import urllib.parse
import html
from alltrialsapp.base import get_studies, get_user_data, get_query_completion
app = FastAPI()


# This is the root path
@app.get("/")
async def root():
    return {"message": "Hello World"}

EXAMPLE_TEXT = """
Please show me all studies related to ALS that have reached second phase.
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


@app.get("/textbox", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>FastAPI Text Input</title>
        <link rel="stylesheet" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css">
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
        <style>
            /* Optional CSS for styling the textarea */
            #text_form textarea {
                width: 400px; /* Set the initial width to your desired size */
                min-height: 100px; /* Set the minimum height to allow expansion */
                padding: 8px; /* Adjust padding for better appearance */
                font-size: 16px; /* Adjust font size if needed */
            }
        </style>
        <script>
            $(document).ready(function() {
                $('#text_form').submit(function(event) {
                    event.preventDefault();
                    $.ajax({
                        type: 'POST',
                        url: '/process_text',
                        data: $('#text_form').serialize(),
                        success: function(response) {
                            $('#result').html(response);
                            $('#result_data').DataTable(); // Enable DataTable on the result
                        }
                    });
                });
                // Prevent form submission on Enter key press within textarea
                $('#text_form textarea').keypress(function(e) {
                    if (e.which === 13 && !e.shiftKey) {
                        e.preventDefault();
                    }
                });
            });
        </script>
    </head>
    <body>
        <h3>Tell us what you want to search for in the clinical trials world?</h3>
        <form id="text_form">
            <textarea name="input_text" style="width: 400px; min-height: 100px;"></textarea> <!-- Adjust width and height -->
            <button type="submit">Search</button>
        </form>
        <div id="result"></div>
    </body>
    </html>
    """


@app.post("/process_text", response_class=HTMLResponse)
async def process_text(input_text: str = Form(...)):
    # Perform actions with the input text to get DataFrame (For demonstration purposes, assuming df is obtained)
    print(input_text)
    aact_query = get_query_completion(input_text)
    print(aact_query)  # Perform actions with the input text
    df = get_user_data(aact_query=aact_query)

    df_html = df.to_html(classes="compact-table")
    encoded_aact_query = urllib.parse.quote_plus(aact_query)
    csv_route = f"/download_csv?aact_query={encoded_aact_query}"  # Route to download CSV

    # Function to escape special HTML characters in the query
    escaped_query = html.escape(aact_query)

    html_content = f"""
    <h4>RESULTING QUERY:</h4>
    <pre><code style="background-color: #f0f0f0">{escaped_query}</code></pre>
    <button onclick="copyToClipboard()">Copy to Clipboard</button>
    <div>
        <a href="{csv_route}" download="result.csv"><button>Download search results as CSV</button></a>
    </div>
    <div id="result_data">{df_html}</div>
        <script>
        $(document).ready(function() {{
            $('#result_data table').DataTable(); // Enable DataTable on the table inside result_data div
        }});

        function copyToClipboard() {{
            const queryText = document.querySelector('pre code').textContent;
            const el = document.createElement('textarea');
            el.value = queryText;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);
            alert('Copied to clipboard: ' + queryText);
        }}
    </script>
    """

    # Return the DataFrame HTML content as the response
    return HTMLResponse(content=html_content)


    # Return the DataFrame HTML content as the response
    return HTMLResponse(content=html_content)



@app.get("/download_csv", response_class=Response)
async def download_csv(aact_query: str):
    # Perform actions with the input text to get DataFrame (For demonstration purposes, assuming df is obtained)
    df = get_user_data(aact_query=aact_query)

    # Convert DataFrame to CSV content
    csv_content = df.to_csv(index=False)

    # Return CSV as a downloadable file
    return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=result.csv"})


