
# Description

This application utilizes ChatGPT features and MedPrompt to execute SQL queries on the AACT clinical trials database. It accepts free-form text input that can include task descriptions and optional code. The app is designed to be user-friendly and does not require prior knowledge of the database or SQL language.

Upon clicking the "Search" button, the app will make up to 10 attempts to generate a valid query based on the provided text. If a valid query is found, it will return a downloadable dataframe.

## Limitations
This app is a work in progress and requires further refinement in prompt engineering. Like most tools using Language Models (LLMs), there may be a degree of uncertainty in the results. If the initial outcome does not meet expectations, consider repeating the search. To save a particular search outcome for future use, you can:
- Download the full dataframe as a CSV file
- Copy the generated SQL query

## Current Baseline Prompt
The initial prompt used by the app is:

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
    

This prompt has been enhanced using the MedPrompt approach. [Learn more about it here](https://www.microsoft.com/en-us/research/blog/steering-at-the-frontier-extending-the-power-of-prompting/).

If you have any ideas on how to improve it, feel free to contribute your suggestions.

Good luck and have fun!

# Quickstart

After installing the app locally, access it by entering the following URL in your browser:

        http://127.0.0.1:8000/textbox
    
# Install Locally
Using your favorite terminal:

1. Clone the repo:
    
        git clone https://github.com/AllTrials/AllTrialsApp.git

2. Install required python packages:

        python -m pip install -r requirements.txt

3. Register your personal openai api key following the instruction in the link below: 
- Yes, you need to pay for it.
- No, it's not expensive. 1$ will let you explore all app features
https://platform.openai.com/docs/quickstart?context=python

4. After registering your api-key don't forget to source your .rc file that you have edited with the new api key. 
Settings vary, but in majority of cases the following will do:
- For mac users: 

        source ~/.zshrc

- For linux users: 
    
        source ~/.bashrc

- For windows users: Good luck.

5. Start the app server using uvicorn: 

        uvicorn all_trials_api.main:app --reload

6. Open the main app component in a browser under the following url: 
http://127.0.0.1:8000/textbox

# Prerequisits
- Python 3.8+
- pip
- git

# Additional resources
To see auto generated docs, go to `http://127.0.0.1:8000/docs` or `http://127.0.0.1:8000/redoc`.
This API documentation is generated automatically from the code and will update as we modify and add endpoints and query parameters. Neat, eh?

For information about FastAPI, see the [FastAPI documentation](https://fastapi.tiangolo.com/).
For information about uvicorn, see the [uvicorn documentation](https://www.uvicorn.org/).

