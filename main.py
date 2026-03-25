# FastAPI Imports
from fastapi import FastAPI, Request, Form, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse

# Firebase Imports
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# Other Imports
from typing import Literal, Annotated
from operator import itemgetter

## Init Firestore database
cred = credentials.Certificate(".\\db_account.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

## Init FastAPI
app = FastAPI()

# Mount Static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# Init Jinja 2 Templates
templates = Jinja2Templates(directory="templates")


## Collections
ACCOUNT_COLLECTION = db.collection("accounts")
CATEGORY_COLLECTION = db.collection("category")


##### Routes #####

## HOME ROUTES
@app.get("/", response_class=HTMLResponse)
async def execute_root_expense(request: Request):
    categories = get_categories("expense")
    accounts = get_accounts()
    return templates.TemplateResponse(
        request=request, name="index.html", context={
            "categories":categories,
            "accounts": accounts["accounts"],
            "transaction_type": "expense"
        }
    )

@app.get("/add-income", response_class=HTMLResponse)
async def execute_root_income(request: Request):
    categories = get_categories("income")
    accounts = get_accounts()
    return templates.TemplateResponse(
        request=request, name="index.html", context={
            "categories":categories,
            "accounts": accounts["accounts"],
            "transaction_type": "income"
        }
    )


## TRANSACTION ROUTES
@app.get("/transaction/{account_id}/{transaction_type}/{transaction_id}", response_class=HTMLResponse)
async def render_transaction_details(request: Request, account_id, transaction_type, transaction_id):
    doc = ACCOUNT_COLLECTION.document(account_id).collection(transaction_type).document(transaction_id)
    transaction = doc.get().to_dict()
    categories = get_categories(transaction_type)
    return templates.TemplateResponse(
        request=request, name="transaction_details.html", context={
            "transaction":transaction,
            "categories":categories,
            "account":account_id,
            "transaction_type":transaction_type,
            "transaction_id":transaction_id
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

    balance = ACCOUNT_COLLECTION.document(account).get().to_dict()["balance"]
    if type == "income":
        
        new_balance = balance + amount
        ACCOUNT_COLLECTION.document(account).set({"balance": new_balance})
    else:
        new_balance = balance - amount
        ACCOUNT_COLLECTION.document(account).set({"balance": new_balance})

    redirect_url = request.url_for("execute_root_expense")
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)

@app.post("/transaction/update/{account_id}/{transaction_type}/{transaction_id}")
def update_transaction(
        request: Request,
        account_id,
        transaction_type,
        transaction_id,
        amount: Annotated[float, Form()],
        category: Annotated[str, Form()],
        date: Annotated[str, Form()]
    ):
    doc = ACCOUNT_COLLECTION.document(account_id).collection(transaction_type).document(transaction_id)
    old_amount = doc.get().to_dict()["amount"]

    doc.set({
        "amount":amount,
        "category":category,
        "date":date
    })

    balance = ACCOUNT_COLLECTION.document(account_id).get().to_dict()["balance"]
    if transaction_type == "income":
        
        new_balance = balance - old_amount + amount
        ACCOUNT_COLLECTION.document(account_id).set({"balance": new_balance})
    else:
        new_balance = balance + old_amount - amount
        ACCOUNT_COLLECTION.document(account_id).set({"balance": new_balance})

    redirect_url = f"/account/{account_id}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

@app.post("/transaction/remove/{account_id}/{transaction_type}/{transaction_id}")
def delete_transaction(request: Request, account_id,transaction_type,transaction_id):
    doc = ACCOUNT_COLLECTION.document(account_id).collection(transaction_type).document(transaction_id)
    
    balance = ACCOUNT_COLLECTION.document(account_id).get().to_dict()["balance"]
    doc_balance = doc.get().to_dict()["amount"]

    if transaction_type == "income":
        
        new_balance = balance - doc_balance
        ACCOUNT_COLLECTION.document(account_id).set({"balance": new_balance})
    else:
        new_balance = balance + doc_balance
        ACCOUNT_COLLECTION.document(account_id).set({"balance": new_balance})

    doc.delete()
    redirect_url = f"/account/{account_id}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

## CATEGORY ROUTES
@app.get("/category", response_class=HTMLResponse)
async def render_category(request: Request):
    income_categories = get_categories("income")
    expense_categories = get_categories("expense")

    return templates.TemplateResponse(
        request=request, name="category.html", context={"income_categories": income_categories, "expense_categories": expense_categories}
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
    
## ACCOUNT ROUTES

@app.get("/account", response_class=HTMLResponse)
async def render_account(request: Request):
    accounts = get_accounts()
    
    return templates.TemplateResponse(
        request=request, name="accounts.html", context={"accounts": accounts["accounts"], "balance": accounts["balance"]}
    )

@app.get("/account/{account_id}", response_class=HTMLResponse)
async def render_account_details(request: Request, account_id):
    documents = ACCOUNT_COLLECTION.document(account_id)
    balance = documents.get().to_dict()["balance"]

    income = sorted(get_transactions(documents, "income"), key=itemgetter("date"), reverse=True)
    expenses = sorted(get_transactions(documents, "expense"), key=itemgetter("date"), reverse=True)
    
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
    


##### Utilities #####

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
    documents = CATEGORY_COLLECTION.where(filter=FieldFilter("type","==",type)).stream()
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

