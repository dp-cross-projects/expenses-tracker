# Overview

This is the "Expense Tracker" project. The main objective is to improve my Python skills by learning and programing with FastAPI and a non-SQL database Firebase.
The software is an expense tracker where you can track your income and expenses by creating accounts and categories. You can read, add, update and delete transactions and get your total balance.

How to connect to database:
- Signup or Signin on Firebase using your Google Account
- Create a new project
- Go to Firestore and create a new database
- Go to service account and generate a new private key
- Save the .json downloaded into the root folder of this project as "db_account.json"

To start the server:

`fastapi run`

To access the application:
_http://127.0.0.1:8000_

No credentials are needed.


[Software Demo Video](https://www.youtube.com/watch?v=4Fs-zzI6DmY)

# Cloud Database

[Google Firestore](https://firebase.google.com/products/firestore): A non-SQL database service from Google.

**Database Structure**

- accounts
    - {account name}
        - expense
            - [id]
                - amount (float)
                - category (string)
                - date (string)
        - income
            - [id]
                - amount (float)
                - category (string)
                - date (string)
        - balance (float)
- category
    - {category name}
        - type (string)

# Development Environment
- Language: Python
- Framework: FastAPI
- Templates: HTML
- Styles: Bootstrap
- Database: Firestore

# Useful Websites

- [Fast API Documentation](https://fastapi.tiangolo.com/)
- [Firestore Documentation](https://firebase.google.com/docs/firestore)

# Future Work

- Authentication: It will work better for multi-user tracking tool by adding authentication.
- Transfers: Adding a "transfer between accounts" feature will help for a lot of cases on cashflow.
- Styles Improve: The site focus on functionality, but it would look better by adding better styles and effects.