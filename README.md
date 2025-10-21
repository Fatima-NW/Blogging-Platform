# Django Blog Platform

A blogging platform built with **Django** and **Django REST Framework**.

## 🚀 Features

- User registration and login
- Create, view, edit, delete, and download posts
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

### 1. Clone this repository 
    ```bash
    git clone https://github.com/Fatima-NW/Blogging-Platform.git
    ```
### 2. Create and activate virtual environment
    ```bash
    python -m venv venv
    source venv/bin/activate    # macOS/Linux
    venv\Scripts\activate       # Windows
    ```
### 3. Install dependencies
    ```bash
    pip install django psycopg2-binary         # Django framework + PostgreSQLconnector
    pip install python-decouple                # For .env
    pip install djangorestframework            # Django REST Framework for building APIs
    pip install djangorestframework-simplejwt  # JWT authentication support for DRF
    pip install pytest pytest-django           # For testing
    pip install celery redis                   # For background tasks
    pip install weasyprint                     # For downloading PDFs
    ```
### 4. Create .env file
    ```env
    DB_NAME=your-database-name
    DB_USER=postgres
    DB_PASSWORD=your-database-password
    DB_HOST=localhost
    DB_PORT=port-number
    SECRET_KEY=your-secret-key
    DEBUG=True
    PAGINATE_BY=number-of-posts-on-one-page
    EMAIL_USER=sender-email-address
    EMAIL_PASS=sender-app-password
    ```
### 5. Run the project
- Apply database migrations:
    ```bash
    python manage.py migrate
    ```
- Start the development server:
    ```bash
    python manage.py runserver
    ```
- (Optional) Start Celery worker for background tasks:
    ```bash
    celery -A myproject worker -l info

    # Start Celery with 4 workers (replace 4 with your desired number)
    celery -A myproject worker -l info -c 4
    ```
- (Optional) Run tests:
    ```bash
    pytest

    # Run a specific test file (replace with your desired path)
    pytest posts/tests/test_templates.py

    # Run a specific test function
    pytest posts/tests/test_templates.py::test_post_create_view
    ```

## 📂 Project Structure
```
yourFolder/
│
├── myproject/
│ ├── __init__.py            
│ ├── settings.py             # Main configuration file
│ ├── urls.py                 # Root URL routing
│ ├── celery.py               # Celery configuration
│
├── posts/
│ ├── models.py               # Post, Comment, Like models
│ ├── views.py                # Template-based views
│ ├── forms.py                # Forms for posts and comments
│ ├── urls.py                 # Template-based view routes
│ ├── tasks.py                # Asynchronous tasks for the posts
│ ├── filters.py              # Filters for posts
│ ├── serializers.py          # Serializers for APIs
│ ├── utils.py                # Utility helpers
│ ├── api/                    
│ │ ├── views.py               # API logic
│ │ ├── urls.py                # API endpoints
│ ├── tests/                    
│ │ ├── test_api.py             # Tests for API views
│ │ ├── test_templates.py       # Tests for template views
│ │ ├── test_models.py          # Tests for models
│
├── users/
│ ├── models.py               # CustomUser model
│ ├── views.py                # Template-based views
│ ├── forms.py                # CustomUserCreationForm
│ ├── backends.py             # Custom authentication backend
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
├── PDFs/                     # Autocreated on post download
├── venv/                     # Virtual environment folder
├── .env                      # Environment variables
├── .gitignore 
├── pytest.ini                # For testing
├── README.md 
└── manage.py
```

## 📡 API Endpoints

**Authentication (JWT)**
- POST   `/api/token/`                        → Obtain JWT token (username/password)
- POST   `/api/token/refresh/`                → Refresh JWT token

**Users**
- POST   `/api/users/register/`              → Register a new user
- GET    `/api/users/profile/`               → Retrieve authenticated user profile
- GET    `/api/users/search/?q=<query>`      → Search users by username (autocomplete dropdown)

**Posts**
- GET    `/api/posts/`                        → List all posts
- GET    `/api/posts/<post_id>/`              → Retrieve a single post
- POST   `/api/posts/create/`                 → Create a new post
- PUT    `/api/posts/<post_id>/update/`       → Update a post (author only)
- DELETE `/api/posts/<post_id>/delete/`       → Delete a post (author only)
- GET    `/api/posts/<post_id>/generate-pdf/` → Generate/download PDF of a post

**Comments**
- POST   `/api/posts/<post_id>/comment/`      → Add a comment or reply
- PUT    `/api/comments/<comment_id>/update/` → Update a comment (author only)
- DELETE `/api/comments/<comment_id>/delete/` → Delete a comment (author only)

**Likes**
- POST   `/api/posts/<post_id>/like/`       → Toggle like/unlike


