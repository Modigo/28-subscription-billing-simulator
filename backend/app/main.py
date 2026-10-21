from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Subscription Billing Simulator API is running!"}