# Django Blog Platform

A blogging platform built with **Django** and **Django REST Framework**.

## 🚀 Features

- User registration and login
- Create, edit, delete and list posts
- View post details with comments and likes
- Add, edit, and delete comments + reply to other users
- Like or unlike posts
- View personal profile
- Clean template views
- API support for all major actions

## ⚙️ Tech Stack

- **Backend:** Django, Django REST Framework
- **Database:** PostgreSQL
- **Authentication:** JWT (Simplejwt)
- **Environment Variables:** Managed using `python-decouple`
- **Frontend (templates):** HTML, Bootstrap
- **Version Control:** Git & GitHub

## 🧰 Setup Instructions

1. Clone this repository 
    ```bash
    git clone https://github.com/Fatima-NW/Blogging-Platform.git
    ```
2. Create and activate virtual environment
    ```bash
    python -m venv venv
    source venv/bin/activate    # macOS/Linux
    venv\Scripts\activate       # Windows
    ```
3. Install dependencies
    ```bash
    pip install django psycopg2-binary
    pip install djangorestframework
    pip install djangorestframework-simplejwt 
    pip install python-decouple
    ```
4. Create .env file
    ```env
    DB_NAME=your-database-name
    DB_USER=postgres
    DB_PASSWORD=pyour-database-password
    DB_HOST=localhost
    DB_PORT=port-number
    SECRET_KEY=your-secret-key
    DEBUG=True
    ```
5. Apply migrations and run server
    ```bash
    python manage.py migrate
    python manage.py runserver
    ```



