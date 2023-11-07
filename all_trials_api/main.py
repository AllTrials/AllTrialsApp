from fastapi import FastAPI

app = FastAPI()


# This is the root path
@app.get("/")
async def root():
    return {"message": "Hello World"}


# This is an example of a path parameter and query parameters
# Try hitting http://127.0.0.1:8000/condition/?name=als&return_data=column1,column2&limit=50
@app.get("/condition/")
async def condition(
    name: str = "Foo",
    return_data: str | None = None,
    limit: int = 10,
):
    return {"name": name, "return_data": return_data, "limit": limit}
