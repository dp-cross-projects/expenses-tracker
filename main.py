from fastapi import FastAPI, HTTPException, Request, Form, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from pydantic import BaseModel
from typing import Literal, Annotated


## Init firestore database
cred = credentials.Certificate(".\\db_account.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

## Init FastAPI
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


## Collection names
ACCOUNT_COLLECTION = db.collection("accounts")
TRANSFER_COLLECTION = db.collection("transfers")
TRANSACTION_COLLECTION = db.collection("transactions")
CATEGORY_COLLECTION = db.collection("category")


## Routes
## HOME
@app.get("/", response_class=HTMLResponse)
async def execute_root(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html"
    )
#### END HOME ######

## CATEGORY
@app.get("/category", response_class=HTMLResponse)
async def render_category(request: Request):
    documents = CATEGORY_COLLECTION.get()
    collections = []
    for doc in documents:
        collections.append(doc.id)

    return templates.TemplateResponse(
        request=request, name="category.html", context={"categories": collections}
    )

@app.post("/category")
def add_new_category(request: Request, category: Annotated[str, Form()]):
    category_name = category.capitalize()
    document = CATEGORY_COLLECTION.document(category_name)
    doc = document.get()
    error = ""
    if doc.exists:
        error = "Category already exists"
    else:
        new_category = {"balance": 0.0}
        document.create(new_category)
    
    redirect_url = request.url_for("render_category")
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    
#### END CATEGORY ######

## ACCOUNT
@app.get("/account", response_class=HTMLResponse)
async def render_account(request: Request):
    documents = ACCOUNT_COLLECTION.get()
    collections = []
    total_balance = 0

    for doc in documents:
        collections.append({"id": doc.id, "balance":doc.to_dict()["balance"]})
        total_balance += doc.to_dict()["balance"]
    
    return templates.TemplateResponse(
        request=request, name="accounts.html", context={"accounts": collections, "balance": total_balance}
    )

@app.post("/account")
def add_new_account(request: Request, account: Annotated[str, Form()]):
    account_name = account.capitalize()
    document = ACCOUNT_COLLECTION.document(account_name)
    doc = document.get()
    error = ""
    if doc.exists:
        error = "Account already exists"
    else:
        balance = {"balance": 0.0}
        document.create(balance)
        
    redirect_url = request.url_for("render_account")
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    
#### END ACCOUNT ######

