# Quickstart: 
After installing thwe app localy, enter the followin url to your browser:

    http://127.0.0.1:8000/textbox

# Install Locally
Using your favourit terminal:

1. Clone the repo:
    
        git clone https://github.com/AllTrials/AllTrialsApp.git

2. Install required python packages:

        python -m pip install -r requirements.txt

3. Register your personal openai api key following the instruction in the link below: 
- Yes, you need to pay for it.
- No, it's not expensive. 1$ will let you explore all app features
https://platform.openai.com/docs/quickstart?context=python

4. After registering your api-key don't forget to source your .rc file that you have edited with the new api key. 
Settings vary, but in most cases in termina run:
- For mac users: 

        source ~/.zshrc

- For linux users: 
    
        source ~/.bashrc

- For windows users: Good luck.

5. Start the app server: 

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


## Example usage of a quick table access lookup:

This feature uses chatGPT features and medprompt to conduct sql queries for you.
**To use the textbox feature you will have to setup an openAI API KEY**
Follow the instruction below to get the API KEY working
> https://platform.openai.com/docs/quickstart?context=python

Under this url you can try our free text search. 

It is our first attempt to incorporate chatGPT like features via the openai python package. 

Upon hitting the "search" button the app will perform up to 10 attempts to generate a valid query to the database and it if finds a valid query it will return a downloadable dataframe.

This is still very much imperfect and requires better prompt engineering. Current baseline prompt looks as follows:


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
    
It then is improved with the medprompt approach as listed here:
    
    https://www.microsoft.com/en-us/research/blog/steering-at-the-frontier-extending-the-power-of-prompting/

, if you have any idea how to improve it, feel free to add your statements:

Good luck, have fun.

