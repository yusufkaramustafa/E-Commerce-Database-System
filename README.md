# E-Commerce-Database-System

This repository contains an E-Commerce Database System designed in Flask with JWT Tokens, Swagger UI/Documentation using MySQL.

# Installation

## Prerequisites
- **MySQL** (Ensure MySQL is running)

## Installation Steps

### 1. Clone the Repository  
```sh
git clone https://github.com/yusufkaramustafa/E-Commerce-Database-System.git
```

### 2. Navigate to the Project Directory  
```sh
cd E-Commerce-Database-System
```

### 3. Install Dependencies  
```sh
pip install -r requirements.txt
```

### 4. Set Up the Database  
Create the database:
```sh
mysql -u <username> -p -e "CREATE DATABASE ecommerce;"
```
Import the schema:
```sh
mysql -u <username> -p ecommerce < ecommerce_db.sql
```
If using Flask-Migrate, apply migrations:
```sh
flask db upgrade
```

### 5. Set Environment Variables (If Needed)  
#### macOS/Linux
```sh
export FLASK_APP=app.py
```
#### Windows
```sh
set FLASK_APP=app.py
```

### 6. Run the Flask Application  
```sh
flask run
```
or
```sh
python app.py 
```

