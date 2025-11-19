# Blogging Platform

The Blogging Platform is a modern, full-featured web application built with **Django** and **Django REST Framework**. It delivers a seamless blogging experience where users can share their stories, engage with others through comments and likes, and enjoy a clean, responsive interface. Behind the scenes, the platform handles background tasks, automated notifications, and data management with efficiency and reliability. Powered by Docker for effortless setup and deployment, it combines functionality and performance to provide a smooth, end-to-end blogging environment.


## 🚀 Features

- Secure user authentication with JWT-based login and registration.
- Create, edit, delete, and download blog posts as PDFs.
- Interactive post pages with likes, threaded comments, and replies.
- Add, edit, delete and reply to other comments.
- Dynamic post filtering for easy content discovery.
- Automated email alerts for new comments and delayed downloads.
- Complete API support for all major functionalities.
- Fully containerized with Docker for quick setup and deployment.

## ⚙️ Tech Stack

- **Backend:** Django, Django REST Framework
- **Database:** PostgreSQL
- **Authentication:** JWT (SimpleJWT)
- **Frontend (templates):** HTML, Bootstrap
- **Task Queue:** Celery + Redis
- **Version Control:** Git, GitHub
- **Containerization:** Docker, Docker Compose
- **Testing:** Pytest 


## 🧰 Setup Instructions

You can run this project in two ways:
- **Option A:** Locally, using a Python virtual environment
- **Option B:** Using Docker containers for a fully isolated setup

>**Note:** All commands below should be run inside the **project root directory** — the main folder that contains your project files.

### 1. Clone the repository
Create a new folder (e.g., `yourfolder`) anywhere on your system, open a terminal inside that folder, and run:

```bash
git clone https://github.com/Fatima-NW/Blogging-Platform.git .
```

## Option A: Manual Setup

### 2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
pip install -e ./logger_pkg          # Logger package 
```

### 4. Create .env file
Create a file named `.env` in the project root and copy the following content into it:

>**Note:** Replace the values according to your own specific configurations.
```env
DB_NAME=your-database-name
DB_USER=postgres
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=port-number
SECRET_KEY=your-secret-key
DEBUG=False
PAGINATE_BY=posts-per-page
EMAIL_USER=sender-email-address
EMAIL_PASS=sender-app-password
CELERY_BROKER="redis://localhost:6379/0"  
CELERY_RESULT="redis://localhost:6379/0" 
```

### 5. Apply database migrations
```bash
python manage.py migrate
```

### 6. Collect static files (only needed if DEBUG=False)
```bash
python manage.py collectstatic
```

### 7. Run the project
- **Start the server**
    ```bash
    python manage.py runserver
    ```

- **Start Celery and Celery beat**
    ```bash
    celery -A myproject worker -l info
    celery -A myproject beat -l info
    ```

- **Access the app**                          
    Once running, open your browser and go to: http://localhost:8000

- **Run tests** (Optional)
    ```bash
    pytest                                       # All tests
    pytest path/to/test_file.py                  # Specific test file
    pytest path/to/test_file.py::test_func       # Specific test function
    ```

## Option B: Docker Setup

### 2. Create `.env` file
Create a file named `.env` in the project root and copy the following content into it:

>**Note:** Only replace the values where it is mentioned. Keep all other values as they are.

```.env
DB_NAME=myprojectdb
DB_USER=postgres
DB_PASSWORD=postgres123
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your-secret-key              # Replace with your secret key
DEBUG=False                             # True=dev, False=prod
PAGINATE_BY=5                           # Adjustable (posts per page)
EMAIL_USER=your-email@example.com       # Replace with sender email
EMAIL_PASS=your-app-password            # Replace with sender app password
CELERY_BROKER="redis://redis:6379/0"  
CELERY_RESULT="redis://redis:6379/0" 
```

### 3. Build the Docker images
```bash
sudo docker compose up --build -d
```

### 4. Apply database migrations
```bash
sudo docker compose exec web python manage.py migrate
```

### 5. Run the project

- **Start all containers**
    ```bash
    # Run in detached mode (background)
    sudo docker compose up -d

    # Or run in foreground (shows logs)
    sudo docker compose up
    ```

- **Access the app**             
    Once running, open your browser and go to: http://localhost:8000

>**Note:** If your main folder has a different name, replace `yourfolder` in the commands below with your actual folder name.

- **Run tests** (Optional)    
    ```bash
    sudo docker exec -it yourfolder-web-1 bash   # Open shell in Django container

    pytest                                       # All tests
    pytest path/to/test_file.py                  # Specific test file
    pytest path/to/test_file.py::test_func       # Specific test function
    ```

- **Check logs** (Optional)
    ```bash
    sudo docker compose logs -f                    # All services
    sudo docker logs -f yourfolder-web-1           # Django only
    sudo docker logs -f yourfolder-celery-1        # Celery worker only
    sudo docker logs -f yourfolder-celery-beat-1   # Celery beat only
    ```

- **Stop containers**
    ```bash
    sudo docker compose down
    ```

### 💡 Services Used
This setup automatically starts the following services under Docker:
- Django app
- PostgreSQL
- Redis
- Celery
- Celery Beat


## 📂 Project Structure
```
yourfolder/
│
├── myproject/                # Core configuration (settings, URLs, Celery setup)
│
├── posts/                    # Blog posts app (models, views, urls, APIs, tests, etc.)
│ ├── api/                    
│ ├── tests/                    
│
├── users/                    # User management app (models, views, urls, APIs, tests, etc.)
│ ├── api/                                
│ ├── tests/                                     
│
├── templates/                # HTML templates
├── static/                   # Static assets
│
├── logger_pkg/               # Custom logger package (mylogger module)
│
├── .env                      # Environment variables
├── Dockerfile                # Docker configuration
├── docker-compose.yml        # Multi-service setup
├── pytest.ini                # Testing configuration
├── requirements.txt          # Project dependencies
└── manage.py                 # Django management script
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
- POST   `/api/posts/<post_id>/like/`         → Toggle like/unlike
