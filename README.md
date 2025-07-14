# FastAPI Template

A production-ready FastAPI template with modern Python tooling, async database operations, authentication system, and Docker support.

## 🚀 Features

- **FastAPI Framework**: High-performance async web framework
- **SQLModel Integration**: Type-safe async database operations with SQLAlchemy 2.0
- **Authentication System**: Complete session-based authentication with role-based permissions
- **Async Database Operations**: Full async support with AsyncSession
- **Alembic Migrations**: Database schema versioning and migrations
- **Email Services**: SMTP email sending with HTML template support
- **Docker Support**: Multi-stage Dockerfile with Docker Compose
- **Rich Logging**: Colorized console logging with file output
- **CORS Middleware**: Cross-origin resource sharing configuration
- **Environment Configuration**: Flexible environment variable management
- **Code Quality**: Ruff formatting and linting configuration
- **Security Framework**: Role-based permissions and security utilities
- **Modern Python**: Python 3.13+ with UV package manager

## 📁 Project Structure

```
fastapi-template/
├── app/                          # Main application package
│   ├── api/                      # API layer
│   │   └── routes/
│   │       └── v1/               # API version 1
│   │           ├── controllers/  # Route handlers (auth.py, hello_world.py)
│   │           ├── dto/          # Data Transfer Objects (request/response models)
│   │           ├── providers/    # Business logic providers
│   │           └── router.py     # Main API router
│   ├── core/                     # Core application logic
│   │   ├── config/
│   │   │   └── env.py           # Environment configuration
│   │   ├── db/
│   │   │   ├── models.py        # SQLModel database models
│   │   │   ├── setup.py         # Async database setup and connection
│   │   │   ├── utils.py         # Database utilities
│   │   │   └── builders/        # Model builders (role.py, permission.py)
│   │   ├── logging/
│   │   │   └── log.py           # Rich logging utilities
│   │   ├── security/            # Security framework
│   │   │   ├── checkers.py      # Security validation functions
│   │   │   └── permissions.py   # Permission constants and utilities
│   │   └── services/
│   │       ├── email.py         # Email service
│   │       └── templating.py    # Jinja2 template rendering
│   ├── utils/                   # Utility functions
│   │   ├── crypto.py            # Cryptographic utilities
│   │   └── date.py              # Date utilities
│   └── app.py                   # FastAPI application factory
├── migrations/                  # Alembic migration files
│   ├── env.py                  # Alembic environment configuration
│   └── versions/               # Migration versions
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Multi-stage Docker build
├── main.py                     # Application entry point
├── pyproject.toml             # Project configuration and dependencies
├── ruff.toml                  # Code formatting and linting rules
├── alembic.ini                # Alembic configuration
└── .env.example               # Environment variables template
```

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.13+
- PostgreSQL (for production)
- UV package manager (recommended)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/Frusadev/fastapi-template.git
   cd fastapi-template
   ```

2. **Set up environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your configuration
   nano .env
   ```

3. **Install dependencies**
   ```bash
   # Using UV (recommended)
   uv sync
   
   # Or using pip
   pip install -e .
   ```

4. **Set up database**
   ```bash
   # Initialize Alembic (if needed)
   alembic init migrations
   
   # Create migration
   alembic revision --autogenerate -m "Initial migration"
   
   # Apply migrations
   alembic upgrade head
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

### Docker Development

1. **Using Docker Compose**
   ```bash
   # Start all services (app + PostgreSQL)
   docker-compose up --build
   
   # Run in background
   docker-compose up -d --build
   ```

2. **Using Docker only**
   ```bash
   # Build image
   docker build -t fastapi-template .
   
   # Run container
   docker run -p 8000:8000 --env-file .env fastapi-template
   ```

## ⚙️ Configuration

### Environment Variables

Configure your application using the `.env` file:

```bash
# Database Configuration
DB_STRING="postgresql+asyncpg://username:password@db:5432/yourdb"
ALEMBIC_DB_URL="postgresql+psycopg2://username:password@db:5432/yourdb"

# Application Configuration
DEBUG=True
PORT=8000

# Email Configuration
EMAIL_APP_PASSWORD="your-app-password"
APP_EMAIL_ADDRESS="your-email@domain.com"
EMAIL_TEMPLATES_PATH="assets/templates/email/"
```

### Database Configuration

The template supports multiple database backends through SQLModel:

- **PostgreSQL** (recommended for production)
- **SQLite** (for development/testing)

Update the `DB_STRING` in your `.env` file according to your database choice.

## 📊 Database Operations

### Async Database Sessions

The template uses **AsyncSession** for all database operations, providing better performance and scalability:

```python
from typing import Annotated
from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.db.setup import create_db_session

@router.get("/users")
async def get_users(
    db_session: Annotated[AsyncSession, Depends(create_db_session)],
):
    # Execute async query
    result = await db_session.exec(select(User))
    users = result.all()
    return {"users": users}

@router.post("/users")
async def create_user(
    user_data: UserCreateDTO,
    db_session: Annotated[AsyncSession, Depends(create_db_session)],
):
    user = User(**user_data.model_dump())
    db_session.add(user)
    await db_session.commit()  # Async commit
    await db_session.refresh(user)  # Async refresh
    return user
```

### Working with AsyncSession

**Key patterns for async database operations:**

```python
# 1. Querying data
async def get_user_by_email(db_session: AsyncSession, email: str) -> User | None:
    result = await db_session.exec(select(User).where(User.email == email))
    return result.first()

# 2. Creating records
async def create_user(db_session: AsyncSession, user_data: dict) -> User:
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

# 3. Complex queries with relationships
async def get_user_with_roles(db_session: AsyncSession, user_id: str) -> User | None:
    result = await db_session.exec(
        select(User)
        .options(selectinload(User.roles))  # Eager load relationships
        .where(User.id == user_id)
    )
    return result.first()

# 4. Transactions
async def transfer_operation(db_session: AsyncSession):
    try:
        # Multiple operations in transaction
        db_session.add(record1)
        db_session.add(record2)
        await db_session.commit()
    except Exception:
        await db_session.rollback()
        raise
```

### Creating Models

Define your database models in `app/core/db/models.py` using SQLModel:

```python
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: gen_id(10), primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    name: str
    hashed_password: str
    
    # Relationships (async compatible)
    login_sessions: list["LoginSession"] = Relationship(back_populates="user")
    roles: list["Role"] = Relationship(back_populates="users", link_model=RoleUserLink)

class LoginSession(SQLModel, table=True):
    id: str = Field(default_factory=lambda: gen_id(30), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=60))
    expired: bool = False
    
    # Async relationship
    user: User = Relationship(back_populates="login_sessions")
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback to previous migration
alembic downgrade -1

# View migration history
alembic history
```

## 📧 Email Service

The template includes a comprehensive email service with template support:

### Basic Email

```python
from app.core.services.email import send_email

send_email(
    email="user@example.com",
    subject="Welcome!",
    message="Welcome to our service!",
    html=False
)
```

### Templated Email

```python
from app.core.services.email import send_templated_email

send_templated_email(
    email="user@example.com",
    subject="Welcome!",
    template_name="welcome",
    context={"name": "John Doe", "app_name": "MyApp"},
    fallback_message="Welcome to our service!"
)
```

### Email Templates

Create HTML templates in your configured templates directory:

```html
<!-- assets/templates/email/welcome.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Welcome to {{ app_name }}</title>
</head>
<body>
    <h1>Welcome, {{ name }}!</h1>
    <p>Thank you for joining {{ app_name }}.</p>
</body>
</html>
```

## 🔍 Logging

The template includes a rich logging system with colored console output and file logging:

```python
from app.core.logging.log import log_info, log_warning, log_error, log_success

log_info("Application started")
log_warning("This is a warning")
log_error("An error occurred")
log_success("Operation completed successfully")
```

## � Authentication System

The template includes a complete session-based authentication system with role-based permissions.

### Authentication Flow

1. **User Registration**: Create account with email, username, password
2. **Login**: Authenticate and create session cookie
3. **Session Management**: HTTP-only cookies for security
4. **Role-based Access**: Automatic role and permission assignment
5. **Logout**: Clear session and invalidate cookies

### API Endpoints

The authentication system provides these endpoints:

```http
POST /api/v1/auth/register     # Register new user
POST /api/v1/auth/login        # Login user
GET  /api/v1/auth/me          # Get current user info
POST /api/v1/auth/logout      # Logout user
```

### Using Authentication in Your Routes

```python
from typing import Annotated
from fastapi import Depends
from app.api.routes.v1.providers.auth import get_current_user
from app.core.db.models import User

@router.get("/protected-route")
async def protected_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
):
    # User is automatically authenticated via session cookie
    return {"message": f"Hello {current_user.name}!"}

# For WebSocket authentication
from app.api.routes.v1.providers.auth import ws_get_current_user

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    current_user: User = Depends(ws_get_current_user)
):
    # WebSocket with authentication
    await websocket.accept()
    # ... websocket logic
```

### Customizing Authentication

**1. Modify User Model** (`app/core/db/models.py`):
```python
class User(SQLModel, table=True):
    # Add custom fields
    profile_image: str | None = None
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Add custom relationships
    posts: list["Post"] = Relationship(back_populates="author")
```

**2. Extend Registration** (`app/api/routes/v1/providers/auth.py`):
```python
async def register(
    db_session: AsyncSession,
    username: str,
    email: EmailStr,
    password: str,
    password_confirm: str,
    name: str,
    # Add custom fields
    profile_image: str | None = None,
):
    # Your custom validation logic
    check_custom_validation(email)
    
    # Create user with custom fields
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        name=name,
        profile_image=profile_image,
    )
    
    # Custom role assignment logic
    role = create_custom_role(user)
    # ... rest of logic
```

**3. Custom DTOs** (`app/api/routes/v1/dto/auth.py`):
```python
class RegisterRequestDTO(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(min_length=8)  # Add validation
    password_confirm: str
    name: str
    profile_image: str | None = None  # Add custom fields

class UserResponseDTO(BaseModel):
    id: str
    username: str
    email: str
    name: str
    is_verified: bool
    created_at: datetime
    # Add any custom fields you want to expose
```

### Permission System

The template includes a flexible role-based permission system:

```python
# Check permissions in your routes
from app.core.security.permissions import ACTION_READWRITE, USER_RESOURCE

async def check_user_permission(current_user: User, resource_id: str):
    # Permission checking logic (implement as needed)
    for role in current_user.roles:
        for permission in role.permissions:
            if (permission.name == ACTION_READWRITE and 
                permission.resource_name == USER_RESOURCE):
                return True
    return False
```

### Session Configuration

Customize session behavior in the auth provider:

```python
# In login function - customize session duration
login_session = LoginSession(
    user_id=user.id,
    expires_at=datetime.now(timezone.utc) + timedelta(days=30)  # Custom duration
)

# Cookie settings
response.set_cookie(
    key="user_session_id",
    value=login_session.id,
    httponly=True,
    secure=True,  # HTTPS only in production
    samesite="strict",  # CSRF protection
    expires=login_session.expires_at.astimezone(timezone.utc),
)
```

### Cryptographic Utilities

The template includes secure utilities for generating IDs and one-time passwords:

```python
from app.utils.crypto import gen_id, gen_otp

# Generate secure URL-safe ID
user_id = gen_id(32)  # Returns 32-character URL-safe string

# Generate numeric OTP
otp_code = gen_otp(6)  # Returns 6-digit numeric string
```

## 🚀 API Development

The template follows a clean architecture pattern with separation of concerns:

### Project Architecture

```
Controllers (Routes) → Providers (Business Logic) → Models (Database)
                ↓
              DTOs (Data Transfer)
```

### Creating New Features

**1. Create DTOs** (`app/api/routes/v1/dto/`):
```python
# app/api/routes/v1/dto/todo.py
from pydantic import BaseModel
from datetime import datetime

class TodoCreateDTO(BaseModel):
    title: str
    description: str | None = None
    priority: int = 1

class TodoResponseDTO(BaseModel):
    id: str
    title: str
    description: str | None
    completed: bool
    created_at: datetime
    user_id: str

    class Config:
        from_attributes = True
```

**2. Create Provider** (`app/api/routes/v1/providers/`):
```python
# app/api/routes/v1/providers/todo.py
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.core.db.models import User, Todo

async def create_todo(
    db_session: AsyncSession,
    current_user: User,
    title: str,
    description: str | None = None,
    priority: int = 1,
) -> Todo:
    todo = Todo(
        title=title,
        description=description,
        priority=priority,
        user_id=current_user.id,
    )
    db_session.add(todo)
    await db_session.commit()
    await db_session.refresh(todo)
    return todo

async def get_user_todos(
    db_session: AsyncSession,
    current_user: User,
) -> list[Todo]:
    result = await db_session.exec(
        select(Todo).where(Todo.user_id == current_user.id)
    )
    return result.all()
```

**3. Create Controller** (`app/api/routes/v1/controllers/`):
```python
# app/api/routes/v1/controllers/todo.py
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.routes.v1.dto.todo import TodoCreateDTO, TodoResponseDTO
from app.api.routes.v1.providers.auth import get_current_user
from app.api.routes.v1.providers.todo import create_todo, get_user_todos
from app.core.db.models import User
from app.core.db.setup import create_db_session

router = APIRouter(prefix="/todos", tags=["Todos"])

@router.post("/", response_model=TodoResponseDTO)
async def create_user_todo(
    request: TodoCreateDTO,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(create_db_session)],
):
    """Create a new todo for the authenticated user."""
    todo = await create_todo(
        db_session=db_session,
        current_user=current_user,
        title=request.title,
        description=request.description,
        priority=request.priority,
    )
    return todo

@router.get("/", response_model=list[TodoResponseDTO])
async def get_my_todos(
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(create_db_session)],
):
    """Get all todos for the authenticated user."""
    todos = await get_user_todos(db_session, current_user)
    return todos
```

**4. Register Router** (`app/api/routes/v1/router.py`):
```python
from app.api.routes.v1.controllers.todo import router as todo_router

router.include_router(todo_router)
```

### Available Endpoints

After setup, your API will have these endpoints:

```http
# Authentication
POST /api/v1/auth/register     # Register new user
POST /api/v1/auth/login        # Login user  
GET  /api/v1/auth/me          # Get current user
POST /api/v1/auth/logout      # Logout user

# Hello World Examples
GET  /api/v1/hello/           # Simple greeting
GET  /api/v1/hello/greeting   # Time-based greeting
GET  /api/v1/hello/user-greeting  # Authenticated user greeting
GET  /api/v1/hello/info       # API information
GET  /api/v1/hello/stats      # User statistics

# Your custom endpoints...
GET  /api/v1/todos/           # Get user todos
POST /api/v1/todos/           # Create todo
```

### API Documentation

FastAPI automatically generates interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### Error Handling

The template includes comprehensive error handling through security checkers:

```python
from app.core.security.checkers import (
    check_existence,
    check_conditions,
    check_equality,
    check_non_existence,
)

# Usage in providers
async def get_todo_by_id(db_session: AsyncSession, todo_id: str, user_id: str):
    todo = check_existence(
        await db_session.get(Todo, todo_id),
        detail="Todo not found"
    )
    
    check_conditions(
        [todo.user_id == user_id],
        detail="Access denied"
    )
    
    return todo
```

## 🧪 Testing

The template is ready for testing with pytest:

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## 🔧 Development Tools

### Code Formatting and Linting

The project uses Ruff for code formatting and linting:

```bash
# Format code
ruff format

# Check for linting issues
ruff check

# Fix auto-fixable issues
ruff check --fix
```

### UV Package Manager

The template is optimized for UV, a fast Python package manager:

```bash
# Add new dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Update dependencies
uv sync --upgrade
```

## 📦 Dependencies

### Core Dependencies

- **FastAPI[standard]**: Web framework with all standard features
- **SQLModel**: Database ORM with type safety
- **Alembic**: Database migration tool
- **AsyncPG**: Async PostgreSQL driver
- **Psycopg2-binary**: PostgreSQL adapter
- **Uvloop**: High-performance event loop
- **Rich**: Rich console output
- **SlowAPI**: Rate limiting
- **Passlib[bcrypt]**: Password hashing
- **Piccolo**: Additional database tools
- **WebSockets**: WebSocket support
- **Python-dotenv**: Environment variable loading
- **Jinja2**: Template engine (for email templates)

## 🐳 Docker Setup

The template includes a complete Docker setup with multi-stage builds and database integration.

### Quick Start with Docker Compose

```bash
# 1. Clone and navigate to the project
git clone https://github.com/yourusername/fastapi-template.git
cd fastapi-template

# 2. Copy environment file
cp .env.example .env

# 3. Start the entire stack
docker-compose up --build

# The API will be available at http://localhost:8000
# PostgreSQL will be available at localhost:5432
```

### Docker Compose Services

**docker-compose.yml** includes:

```yaml
services:
  # FastAPI Application
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_STRING=postgresql+asyncpg://postgres:password@db:5432/fastapi_db
    depends_on:
      - db
    volumes:
      - ./app:/app/app  # Hot reload in development

  # PostgreSQL Database
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: fastapi_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### Multi-stage Dockerfile

The Dockerfile is optimized for production with multiple stages:

```dockerfile
# Builder stage - Install dependencies
FROM python:3.13-slim as builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

# Production stage - Minimal runtime
FROM python:3.13-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .
EXPOSE 8000
CMD ["/app/.venv/bin/python", "main.py"]
```

### Development vs Production

**Development** (with hot reload):
```bash
# Start with development overrides
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or use volume mounts for hot reload
docker-compose up --build
```

**Production deployment**:
```bash
# Build production image
docker build -t fastapi-template:prod .

# Run with production settings
docker run -d \
  --name fastapi-app \
  -p 8000:8000 \
  --env-file .env.prod \
  fastapi-template:prod
```

### Database Migrations in Docker

Run migrations in the container:

```bash
# Run migrations
docker-compose exec app alembic upgrade head

# Create new migration
docker-compose exec app alembic revision --autogenerate -m "Add new table"

# Check migration status
docker-compose exec app alembic current
```

### Environment Variables for Docker

Create `.env` file for Docker Compose:

```bash
# Database (matches docker-compose.yml)
DB_STRING=postgresql+asyncpg://postgres:password@db:5432/fastapi_db
ALEMBIC_DB_URL=postgresql+psycopg2://postgres:password@db:5432/fastapi_db

# Application
DEBUG=True
PORT=8000

# Email (configure with your SMTP)
EMAIL_APP_PASSWORD=your-app-password
APP_EMAIL_ADDRESS=noreply@yourdomain.com
```

### Docker Best Practices Used

1. **Multi-stage builds** - Smaller production images
2. **Non-root user** - Security best practices
3. **Layer caching** - Faster rebuilds
4. **Volume persistence** - Database data survives container restarts
5. **Health checks** - Container health monitoring
6. **Minimal base images** - Reduced attack surface

## 📝 Environment Configuration

The `env.py` module provides type-safe environment variable access:

```python
from app.core.config.env import get_env

# Get environment variable with default
db_url = get_env("DB_STRING", "sqlite:///./test.db")

# Type-safe environment keys
debug = get_env("DEBUG", "False") == "True"
```

## 🎯 Quick Start Guide

### 1. Setup Your Project

```bash
# Clone the template
git clone https://github.com/yourusername/fastapi-template.git my-project
cd my-project

# Set up environment
cp .env.example .env
# Edit .env with your database and email settings

# Install dependencies
uv sync

# Run database migrations
alembic upgrade head

# Start the development server
python main.py
```

### 2. Test the Authentication

```bash
# Register a new user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com", 
    "password": "password123",
    "password_confirm": "password123",
    "name": "Test User"
  }'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Access protected endpoint (after login)
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  --cookie-jar cookies.txt --cookie cookies.txt
```

### 3. Customize for Your Needs

**Modify User Model** for your requirements:
```python
# In app/core/db/models.py
class User(SQLModel, table=True):
    # Keep existing fields...
    
    # Add your custom fields
    phone: str | None = None
    company: str | None = None
    avatar_url: str | None = None
    is_premium: bool = False
    subscription_ends: datetime | None = None
```

**Create Your Business Logic**:
1. Add new models in `app/core/db/models.py`
2. Create DTOs in `app/api/routes/v1/dto/`
3. Write providers in `app/api/routes/v1/providers/`
4. Build controllers in `app/api/routes/v1/controllers/`
5. Register routes in `app/api/routes/v1/router.py`

## 🔧 Customization Guide

### Adding New Models

```python
# In app/core/db/models.py
class Product(SQLModel, table=True):
    id: str = Field(default_factory=lambda: gen_id(12), primary_key=True)
    name: str = Field(index=True)
    description: str | None = None
    price: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Foreign key relationship
    user_id: str = Field(foreign_key="user.id")
    user: User = Relationship()
```

### Email Templates

Create custom email templates in your templates directory:

```html
<!-- templates/welcome.html -->
<!DOCTYPE html>
<html>
<head>
    <style>
        .container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
        .header { background: #007bff; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to {{ app_name }}!</h1>
        </div>
        <div class="content">
            <p>Hi {{ name }},</p>
            <p>Thank you for joining {{ app_name }}. We're excited to have you!</p>
            <p>Your account details:</p>
            <ul>
                <li>Email: {{ email }}</li>
                <li>Username: {{ username }}</li>
            </ul>
        </div>
    </div>
</body>
</html>
```

### Custom Permissions

Extend the permission system:

```python
# In app/core/security/permissions.py
# Add your custom permissions
PRODUCT_RESOURCE = "product"
ORDER_RESOURCE = "order"

ACTION_CREATE = "create"
ACTION_UPDATE = "update" 
ACTION_DELETE = "delete"

# In your providers
def check_product_permission(user: User, action: str, product_id: str):
    # Your permission logic
    pass
```

### Environment Configuration

Add custom environment variables:

```python
# In app/core/config/env.py or create your own config module
STRIPE_SECRET_KEY = get_env("STRIPE_SECRET_KEY")
REDIS_URL = get_env("REDIS_URL", "redis://localhost:6379")
AWS_BUCKET_NAME = get_env("AWS_BUCKET_NAME")
```

## 🚀 Production Deployment

### Using Docker in Production

```bash
# Build production image
docker build -t my-app:latest .

# Run with production settings
docker run -d \
  --name my-app \
  -p 8000:8000 \
  --env-file .env.production \
  --restart unless-stopped \
  my-app:latest
```

### Environment Variables for Production

```bash
# .env.production
DEBUG=False
DB_STRING=postgresql+asyncpg://user:pass@prod-db:5432/myapp
EMAIL_APP_PASSWORD=your-production-email-password
APP_EMAIL_ADDRESS=noreply@yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Health Checks

The template is ready for health check endpoints:

```python
# Add to your router
@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}
```

## 📄 License

This template is provided as-is for educational and development purposes.

## 🔗 Useful Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [UV Documentation](https://docs.astral.sh/uv/)
