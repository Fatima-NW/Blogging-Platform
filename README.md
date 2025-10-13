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
    pip install python-decouple                 # for .env
    pip install djangorestframework
    pip install djangorestframework-simplejwt 
    pip install pytest pytest-django            # for testing
    ```
4. Create .env file
    ```env
    DB_NAME=your-database-name
    DB_USER=postgres
    DB_PASSWORD=your-database-password
    DB_HOST=localhost
    DB_PORT=port-number
    SECRET_KEY=your-secret-key
    DEBUG=True
    PAGINATE_BY=number-of-posts-on-one-page
    ```
5. Apply migrations and run server
    ```bash
    python manage.py migrate
    python manage.py runserver
    ```

## 📂 Project Structure
YourFolder/
│
├── myproject/
│ ├── settings.py             # Main configuration file
│ ├── urls.py                 # Root URL routing
│
├── posts/
│ ├── models.py               # Post, Comment, Like models
│ ├── views.py                # Template-based views
│ ├── forms.py                # Forms for posts and comments
│ ├── urls.py                 # Template-based view routes
│ ├── serializers.py          # Serializers for APIs
│ ├── api/                    
│ │ ├── views.py               # API logic
│ │ ├── urls.py                # API endpoints
│ ├── tests/                    
│ │ ├── test_api.py             # Tests for API views
│ │ ├── test_templates.py       # Tests for template views
│ │ ├── test_models.py          # Tests for API views
│
├── users/
│ ├── models.py               # CustomUser model
│ ├── views.py                # Template-based views
│ ├── forms.py                # CustomUserCreationForm
│ ├── backends.py             
│ ├── urls.py                 # Template-based view routes
│ ├── serializers.py          # Serializers for APIs
│ ├── api/                    
│ │ ├── views.py             
│ │ ├── urls.py              
│ ├── tests/                    
│ │ ├── test_api.py            
│ │ ├── test_templates.py      
│ │ ├── test_models.py                  
│
├── templates/
│ ├── base.html 
│ ├── home.html     
│ ├── users/                  # User specific templates 
│ ├── posts/                  # Post specific templates 
│
├── venv/                     # Virtual environment folder
├── .env                      # Environment variables
├── .gitignore 
├── pytest.ini                # For testing
├── README.md 
└── manage.py