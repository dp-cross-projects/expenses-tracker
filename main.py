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
from typing import Annotated
from operator import itemgetter

## Init Firestore database client
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

"""
    Method: GET
    Route: /

    This function renders the home page
    using the expense form.
"""
@app.get("/", response_class=HTMLResponse)
async def execute_root_expense(request: Request):

    # Get categories with expense type from
    # category collection
    categories = get_categories("expense")

    # Get accounts from account collection
    accounts = get_accounts()

    # Renders the home using the categories,
    # accounts and "expense" as parameters
    return templates.TemplateResponse(
        request=request, name="index.html", context={
            "categories": categories,
            "accounts": accounts["accounts"],
            "transaction_type": "expense"
        }
    )

"""
    Method: GET
    Route: /add-income

    This function renders the home page
    using the income form.
"""
@app.get("/add-income", response_class=HTMLResponse)
async def execute_root_income(request: Request):
    
    # Get categories with expense type from
    # category collection
    categories = get_categories("income")

    # Get accounts from account collection
    accounts = get_accounts()

    # Renders the home using the categories,
    # accounts and "income" as parameters
    return templates.TemplateResponse(
        request=request, name="index.html", context={
            "categories":categories,
            "accounts": accounts["accounts"],
            "transaction_type": "income"
        }
    )


## TRANSACTION ROUTES

"""
    Method: GET
    Route: /transaction/{account_id}/{transaction_type}/{transaction_id}

    This function renders the transaction details according to the
    account_id, transaction_type and transaction_id.
"""
@app.get("/transaction/{account_id}/{transaction_type}/{transaction_id}", response_class=HTMLResponse)
async def render_transaction_details(request: Request, account_id, transaction_type, transaction_id):
    # Get the transaction document from database
    doc = ACCOUNT_COLLECTION.document(account_id).collection(transaction_type).document(transaction_id)

    # Converts the document into dictionary
    transaction = doc.get().to_dict()

    # Get categories according to transaction_type from params
    categories = get_categories(transaction_type)

    # Renders the template using the transaction dictionary,
    # categories, account_id, transaction_type and transaction_id
    return templates.TemplateResponse(
        request=request, name="transaction_details.html", context={
            "transaction":transaction,
            "categories":categories,
            "account":account_id,
            "transaction_type":transaction_type,
            "transaction_id":transaction_id
        }
    )

"""
    Method: POST
    Route: /transaction

    This function receives data from form and creates
    a new transaction.
"""
@app.post("/transaction")
def create_new_transaction(
    request: Request,
    account: Annotated[str, Form()],
    amount: Annotated[float, Form()],
    category: Annotated[str, Form()],
    date: Annotated[str, Form()],
    type: Annotated[str, Form()] 
    ):
    # Get the transaction type collection
    document = ACCOUNT_COLLECTION.document(account).collection(type)

    # Create a transaction document
    transaction = {
        "amount":amount,
        "category":category,
        "date":date
    }

    # Insert the document into the transaction collection
    document.add(transaction)

    # Get the account balance
    balance = ACCOUNT_COLLECTION.document(account).get().to_dict()["balance"]

    # If transaction type is "income" it will be added to account balance,
    # if not, it will be substracted from balance
    if type == "income":
        new_balance = balance + amount
        ACCOUNT_COLLECTION.document(account).set({"balance": new_balance})
    else:
        new_balance = balance - amount
        ACCOUNT_COLLECTION.document(account).set({"balance": new_balance})

    # Save the home function for redirect
    redirect_url = request.url_for("execute_root_expense")

    # Redirect browser to Home
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)

"""
    Method: POST
    Route: /transaction/update/{account_id}/{transaction_type}/{transaction_id}

    This function updates a transaction details according to params and
    form data.
"""
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

    # Get transaction document
    doc = ACCOUNT_COLLECTION.document(account_id).collection(transaction_type).document(transaction_id)

    # Get the amount from transaction
    old_amount = doc.get().to_dict()["amount"]

    # Update the document with new details from form data
    doc.set({
        "amount":amount,
        "category":category,
        "date":date
    })

    # Get the actual account balance
    balance = ACCOUNT_COLLECTION.document(account_id).get().to_dict()["balance"]

    # If the transaction type is income, then the old amount will be substracted,
    # then the new amount will be added.
    # If not, the old amount will be added,
    # then the new amount will be substracted.
    if transaction_type == "income":
        new_balance = balance - old_amount + amount
        ACCOUNT_COLLECTION.document(account_id).set({"balance": new_balance})
    else:
        new_balance = balance + old_amount - amount
        ACCOUNT_COLLECTION.document(account_id).set({"balance": new_balance})

    # Set the account details as redirect route
    redirect_url = f"/account/{account_id}"

    # Redirect the browser to the account details route
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


"""
    Method: POST
    Route: /transaction/remove/{account_id}/{transaction_type}/{transaction_id}

    This function delete a transaction according to params and form data.
"""
@app.post("/transaction/remove/{account_id}/{transaction_type}/{transaction_id}")
def delete_transaction(request: Request, account_id,transaction_type,transaction_id):

    # Get the transaction document
    doc = ACCOUNT_COLLECTION.document(account_id).collection(transaction_type).document(transaction_id)
    
    # Get the account balance
    balance = ACCOUNT_COLLECTION.document(account_id).get().to_dict()["balance"]

    # Get the transaction amount
    doc_balance = doc.get().to_dict()["amount"]

    # If the transaction type is income, the transaction
    # amount will be substracted.
    # If not, the transaction amount will be added.
    if transaction_type == "income":
        new_balance = balance - doc_balance
        ACCOUNT_COLLECTION.document(account_id).set({"balance": new_balance})
    else:
        new_balance = balance + doc_balance
        ACCOUNT_COLLECTION.document(account_id).set({"balance": new_balance})

    # Delete the transaction document
    doc.delete()

    # Set the account details as redirect route
    redirect_url = f"/account/{account_id}"

    # Redirect the browser to the account details route
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

## CATEGORY ROUTES

"""
    Method: GET
    Route: /category

    This function renders the categories available from database
"""
@app.get("/category", response_class=HTMLResponse)
async def render_category(request: Request):

    # Get income categories
    income_categories = get_categories("income")

    # Get expense categories
    expense_categories = get_categories("expense")

    # Render the template using the income and
    # expense categories
    return templates.TemplateResponse(
        request=request,
        name="category.html",
        context={
            "income_categories": income_categories,
            "expense_categories": expense_categories
        }
    )

"""
    Method: POST
    Route: /category

    This function add a category according to form data.
"""
@app.post("/category")
def add_new_category(
    request: Request,
    category: Annotated[str, Form()],
    type: Annotated[str, Form()]
):
    # Standarize the category name by capitalizing
    category_name = category.capitalize()

    # Set category document 
    document = CATEGORY_COLLECTION.document(category_name)

    # Query category document, if the document already exists
    # return an error message.
    # If document don't exists, create a new one.
    doc = document.get()
    error = ""
    if doc.exists:
        error = "Category already exists"
    else:
        new_category = {"type": type}
        document.create(new_category)
    
    # Set the render category function as redirect page
    redirect_url = request.url_for("render_category")

    # Redirect to category page
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    
## ACCOUNT ROUTES

"""
    Method: GET
    Route: /account

    This function renders the accounts available from database
"""
@app.get("/account", response_class=HTMLResponse)
async def render_account(request: Request):

    # Get accounts from database
    accounts = get_accounts()
    
    # Render template with accounts data
    return templates.TemplateResponse(
        request=request,
        name="accounts.html",
        context={
            "accounts": accounts["accounts"],
            "balance": accounts["balance"]
        }
    )

"""
    Method: GET
    Route: /account

    This function renders the accounts details according
    to params
"""
@app.get("/account/{account_id}", response_class=HTMLResponse)
async def render_account_details(request: Request, account_id):

    # Get the account document from param
    documents = ACCOUNT_COLLECTION.document(account_id)

    # Get the account balance
    balance = documents.get().to_dict()["balance"]

    # Get and order by date the transactions
    # (income and expense) from account
    income = sorted(get_transactions(documents, "income"), key=itemgetter("date"), reverse=True)
    expenses = sorted(get_transactions(documents, "expense"), key=itemgetter("date"), reverse=True)
    
    # Render the template using the account_id,
    # balance, income and expenses.
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

"""
    Method: POST
    Route: /account

    This function add a new account according to form data.
"""
@app.post("/account")
def add_new_account(request: Request, account: Annotated[str, Form()]):

    # Standarize the account name by capitalizing
    account_name = account.capitalize()

    # Set account document 
    document = ACCOUNT_COLLECTION.document(account_name)

    # Query account document, if the document already exists
    # return an error message.
    # If document don't exists, create a new one.
    doc = document.get()
    error = ""
    if doc.exists:
        error = "Account already exists"
    else:
        balance = {"balance": 0.0}
        document.create(balance)
        
    # Set the render account function as redirect page
    redirect_url = request.url_for("render_account")

    # Redirect to account page
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    

##### Utilities #####

"""
    This function return a one type transactions
    from account collection
    INPUT:
        account - account_id from collection
        type - type_id from collection
    
    OUTPUT:
        array
"""
def get_transactions(account, type):
    # Get the transaction documents
    data = account.collection(type).get()

    # Init array for transaction
    transactions = []

    # Iterates the documents and save id,
    # amount, category and date as dictionary
    # into array
    for t in data:
        details = t.to_dict()
        transactions.append({
            "id": t.id,
            "amount": details["amount"],
            "category": details["category"],
            "date": details["date"]
        })

    # Return the array
    return transactions

"""
    This function return a one type categories
    from category collection
    INPUT:
        type [default = "expense"] - type_id from collection
        
    OUTPUT:
        array
"""
def get_categories(type="expense"):
    # Query the categories where type equals to argument
    documents = CATEGORY_COLLECTION.where(filter=FieldFilter("type","==",type)).stream()

    # Init array for categories
    collections = []

    # Iterates the collection and save the
    # document into array 
    for doc in documents:
        collections.append(doc.id)

    # Return the array
    return collections

"""
    This function return all the accounts available and the
    balance from account collection
    INPUT:
        None
    OUTPUT:
        dictionary
"""
def get_accounts():
    # Get the account collection
    documents = ACCOUNT_COLLECTION.get()

    # Init array for accounts
    collections = []

    # Init the balance 
    total_balance = 0

    # Iterate the accounts from collection
    for doc in documents:
        # Add the account to array with id and balance
        collections.append({"id": doc.id, "balance":doc.to_dict()["balance"]})

        # Adds the balance from account to total_balance
        total_balance += doc.to_dict()["balance"]

    # Return the array of accounts and total balance calculated
    return {"accounts": collections, "balance": total_balance}

