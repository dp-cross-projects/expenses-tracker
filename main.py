from fastapi import FastAPI, HTTPException, Request, Form, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from pydantic import BaseModel
from typing import Literal, Annotated
from uuid import UUID

## Init firestore database
cred = credentials.Certificate(".\\db_account.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

## Init FastAPI
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Pydantic

class Transaction(BaseModel):
    amount: float
    category: str
    date: str
    type: Literal["income","expense"]

## Collection names
ACCOUNT_COLLECTION = db.collection("accounts")
TRANSFER_COLLECTION = db.collection("transfers")
TRANSACTION_COLLECTION = db.collection("transactions")
CATEGORY_COLLECTION = db.collection("category")


## Routes
## HOME
@app.get("/", response_class=HTMLResponse)
async def execute_root(request: Request):
    categories = get_categories()
    accounts = get_accounts()
    # incomes = 
    return templates.TemplateResponse(
        request=request, name="index.html", context={
            "categories":categories,
            "accounts": accounts["accounts"]
        }
    )

@app.post("/transaction")
def create_new_transaction(
    request: Request,
    account: Annotated[str, Form()],
    amount: Annotated[float, Form()],
    category: Annotated[str, Form()],
    date: Annotated[str, Form()],
    type: Annotated[str, Form()] 
    ):
    document = ACCOUNT_COLLECTION.document(account).collection(type)
    transaction = {
        "amount":amount,
        "category":category,
        "date":date
    }
    document.add(transaction)

    redirect_url = request.url_for("execute_root")
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
#### END HOME ######

## CATEGORY
@app.get("/category", response_class=HTMLResponse)
async def render_category(request: Request):
    # documents = CATEGORY_COLLECTION.get()
    # collections = []
    # for doc in documents:
    #     collections.append(doc.id)
    collections = get_categories()

    return templates.TemplateResponse(
        request=request, name="category.html", context={"categories": collections}
    )

@app.post("/category")
def add_new_category(
    request: Request,
    category: Annotated[str, Form()],
    type: Annotated[str, Form()]
):
    category_name = category.capitalize()
    document = CATEGORY_COLLECTION.document(category_name)
    doc = document.get()
    error = ""
    if doc.exists:
        error = "Category already exists"
    else:
        new_category = {"type": type}
        document.create(new_category)
    
    redirect_url = request.url_for("render_category")
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    
#### END CATEGORY ######

## ACCOUNT

@app.get("/account", response_class=HTMLResponse)
async def render_account(request: Request):
    # documents = ACCOUNT_COLLECTION.get()
    # collections = []
    # total_balance = 0

    # for doc in documents:
    #     collections.append({"id": doc.id, "balance":doc.to_dict()["balance"]})
    #     total_balance += doc.to_dict()["balance"]
    accounts = get_accounts()
    
    return templates.TemplateResponse(
        request=request, name="accounts.html", context={"accounts": accounts["accounts"], "balance": accounts["balance"]}
    )

@app.get("/account/{account_id}", response_class=HTMLResponse)
async def render_account_details(request: Request, account_id):
    documents = ACCOUNT_COLLECTION.document(account_id)
    balance = documents.get().to_dict()["balance"]

    income = get_transactions(documents, "income")
    expenses = get_transactions(documents, "expense")
    
    # collections = []
    # total_balance = 0

    # for doc in documents:
    #     collections.append({"id": doc.id, "balance":doc.to_dict()["balance"]})
    #     total_balance += doc.to_dict()["balance"]
    # accounts = get_accounts()
    
    return templates.TemplateResponse(
        request=request,
        name="account_details.html",
        context={
            "account": account_id,
            "balance": balance,
            "income": income,
            "expenses": expenses
        }
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

def get_transactions(account, type):
    data = account.collection(type).get()
    transactions = []

    for t in data:
        details = t.to_dict()
        transactions.append({
            "id": t.id,
            "amount": details["amount"],
            "category": details["category"],
            "date": details["date"]
        })
    return transactions

def get_categories(type="expense"):
    documents = CATEGORY_COLLECTION.where(filter=FieldFilter("type","==",type)).stream()#get()
    collections = []
    for doc in documents:
        collections.append(doc.id)
    return collections

def get_accounts():
    documents = ACCOUNT_COLLECTION.get()
    collections = []
    total_balance = 0

    for doc in documents:
        collections.append({"id": doc.id, "balance":doc.to_dict()["balance"]})
        total_balance += doc.to_dict()["balance"]

    return {"accounts": collections, "balance": total_balance}

