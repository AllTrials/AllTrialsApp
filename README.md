# All Trails APP

To run locally:

1. Clone the repo
2. Run `python3 -m pip install -r requirements.txt`
3. Run `uvicorn all_trials_api.main:app --reload`
4. Open `http://127.0.0.1:8000/` in your browser

To see auto generated docs, go to `http://127.0.0.1:8000/docs` or `http://127.0.0.1:8000/redoc`.
This API documentation is generated automatically from the code and will update as we modify and add endpoints and query parameters. Neat, eh?

For information about FastAPI, see the [FastAPI documentation](https://fastapi.tiangolo.com/).
For information about uvicorn, see the [uvicorn documentation](https://www.uvicorn.org/).


## Example usage of a quick table access lookup:

### View studies table
> http://127.0.0.1:8000/studies/ 

This url would by default fetch the first 100 records from studies table from ctgov schema

### View a different table
You can change the table by changing the url:

> http://127.0.0.1:8000/studies/?aact_table=conditions. 

This would fetch the first 100 records from conditions table

### Change default display parameters
You can change the default parameters by changing the url as follows:

> http://127.0.0.1:8000/studies/?aact_table=conditions&n_rows_limit=1000&aact_schema=ctgov. 

This would fetch the first 100 records from conditions table ensuring the ctgov schema

## Text query and download button
> http://127.0.0.1:8000/textbox

Under this url you can try our free text search. 

It is our first attempt to incorporate chatGPT like features via the openai python package. 

Upon hitting the "search" button the app will perform up to 10 attempts to generate a valid query to the database and it if finds a valid query it will return a downloadable dataframe

Good luck, have fun.