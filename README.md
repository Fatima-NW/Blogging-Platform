# Django Blog Platform

A blogging platform built with **Django** and **Django REST Framework**.


## 🚀 Features

- User registration and login
- Create, view, edit, delete, and download posts
- View post details with comments and likes
- Add, edit, and delete comments + reply to other users
- Like or unlike posts
- Clean template views
- Filtering blog posts
- Automated email notifications for new comments or delayed PDF downloads
- API support for all major actions
- Dockerized setup for easy deployment

## ⚙️ Tech Stack

- **Backend:** Django, Django REST Framework
- **Database:** PostgreSQL
- **Authentication:** JWT (Simplejwt)
- **Environment Variables:** Managed using `python-decouple`
- **Frontend (templates):** HTML, Bootstrap
- **Task Queue:** Celery + Redis
- **Version Control:** Git & GitHub
- **Containerization:** Docker, Docker Compose


## 🧰 Setup Instructions

You have two options:

## Option 1: Manual Python Setup (Classic)

### 1. Clone this repository 
```bash
git clone https://github.com/Fatima-NW/Blogging-Platform.git
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate    # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt            # All requirements
pip install -e /full/path/to/mylogger      # For logger package        

or

pip install django psycopg2-binary         # Django framework + PostgreSQLconnector
pip install python-decouple                # For .env
pip install djangorestframework            # Django REST Framework for building APIs
pip install djangorestframework-simplejwt  # JWT authentication support for DRF
pip install pytest pytest-django           # For testing
pip install celery redis                   # For background tasks
pip install weasyprint                     # For downloading PDFs
pip install -e /full/path/to/mylogger      # For logger package
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

## Option 2: Docker Setup

### 1. Clone the repository
```bash
git clone https://github.com/Fatima-NW/Blogging-Platform.git
```

### 2. Create .env file
```.env
DB_NAME=myprojectdb
DB_USER=postgres
DB_PASSWORD=postgres123
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your-secret-key
DEBUG=True
PAGINATE_BY=5
EMAIL_USER=your-email@example.com
EMAIL_PASS=your-app-password
```

### 3. Build and start containers
```bash
sudo docker compose up --build

#After the first build, you can start containers normally without rebuilding:
sudo docker compose up
```

### 4. Check logs
- All services
    ```bash
    sudo docker compose logs -f
    ```
- Django only
    ```bash
    sudo docker logs -f project1-web-1
    ```
- Celery worker only
    ```bash
    sudo docker logs -f project1-celery-1
    ```
- Celery beat only
    ```bash
    sudo docker logs -f project1-celery-beat-1
    ```

### 5. Run tests
```bash
sudo docker exec -it project1-web-1 bash     # Open python shell in Django container
pytest                                       # Run all tests or specific ones
```

### 6. Stop containers
```bash
sudo docker compose down
```

### 7. Services
Services included: 
- Django app
- PostgreSQL
- Redis
- Celery
- Cerlery Beat


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
│ ├── tests/                                     
│
├── templates/
│ ├── base.html 
│ ├── home.html     
│ ├── users/                  # User specific templates 
│ ├── posts/                  # Post specific templates 
│
├── logger_pkg/               # Custom logger package
│ ├── mylogger/               # Python module  
│ │ ├── __init__.py           
│ │ ├── logger.py             # Main Logger class      
│ │ ├── utils.py              
│ ├── setup.py                
│ ├── pyproject.toml          
│ ├── example_usage.py        
│ ├── README.md
│
├── static/                   # Static files
├── PDFs/                     # Autocreated on post download
├── venv/                     # Virtual environment folder
├── .env                      # Environment variables
├── .gitignore 
├── Dockerfile                # Docker
├── docker-compose.yml  
├── pytest.ini                # For testing
├── requirements.txt
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


