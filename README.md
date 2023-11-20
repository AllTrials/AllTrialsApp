# All Trails APP

To run locally:

1. Clone the repo
2. Run `py -m pip install -r requirements.txt`
3. Run `uvicorn all_trials_api.main:app --reload`
4. Open `http://127.0.0.1:8000/` in your browser

To see auto generated docs, go to `http://127.0.0.1:8000/docs` or `http://127.0.0.1:8000/redoc`.
This API documentation is generated automatically from the code and will update as we modify and add endpoints and query parameters. Neat, eh?

For information about FastAPI, see the [FastAPI documentation](https://fastapi.tiangolo.com/).
For information about uvicorn, see the [uvicorn documentation](https://www.uvicorn.org/).


## Example usage of a quick table access lookup:

http://127.0.0.1:8000/studies/ would by default fetch the first 100 records from studies table from ctgov schema

You can change the table by changing the url:
http://127.0.0.1:8000/studies/?aact_table=conditions. This would fetch the first 100 records from conditions table

You can change the default parameters by changing the url as follows:
http://127.0.0.1:8000/studies/?aact_table=conditions&n_rows_limit=1000&aact_schema==ctgov. This would fetch the first 100 records from conditions table

Good luck, have fun.
