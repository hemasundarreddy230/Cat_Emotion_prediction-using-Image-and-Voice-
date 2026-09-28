# FastAPI Authentication System

A complete FastAPI backend project with JWT-based authentication, user registration, login, and protected routes.

## Features

- ✅ User Registration and Login
- ✅ JWT Token Authentication
- ✅ Password Hashing with bcrypt
- ✅ Protected Routes
- ✅ SQLAlchemy ORM with SQLite
- ✅ Pydantic Schemas for Data Validation
- ✅ Clean, Modular Project Structure
- ✅ Comprehensive API Documentation
- ✅ CORS Support

## Project Structure 
```
fastapi-auth/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database configuration and session
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # Authentication utilities
│   └── routers/
│       ├── __init__.py
│       └── auth.py          # Authentication routes
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
└── README.md               # Project documentation
```

## Setup Instructions

### 1. Clone or Create Project Directory

```bash
mkdir fastapi-auth
cd fastapi-auth
```

### 2. Create Virtual Environment

#### Windows (cmd)
```cmd
python -m venv venv
venv\Scripts\activate
```

#### Windows (PowerShell)
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

#### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Update the `.env` file with your configuration:

```env
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30clear
DATABASE_URL=sqlite:///./app.db
```

**Important**: Generate a secure secret key for production:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5. Run the Application

```bash
uvicorn app.main:app --reload
```

The application will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | Login user | No |
| POST | `/auth/logout` | Logout user | Yes |
| GET | `/auth/me` | Get current user info | Yes |
| GET | `/auth/protected` | Protected route example | Yes |

### General Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/` | Root endpoint | No |
| GET | `/health` | Health check | No |

## Postman Testing Guide

### 1. Register User

**URL**: `POST http://localhost:8000/auth/register`

**Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123"
}
```

**Expected Response** (201 Created):
```json
{
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00.000Z"
}
```

### 2. Login User

**URL**: `POST http://localhost:8000/auth/login`

**Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
    "username": "testuser",
    "password": "testpassword123"
}
```

**Expected Response** (200 OK):
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

**Important**: Save the `access_token` for authenticated requests.

### 3. Get Current User Info

**URL**: `GET http://localhost:8000/auth/me`

**Headers**:
```
Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
```

**Expected Response** (200 OK):
```json
{
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00.000Z"
}
```

### 4. Access Protected Route

**URL**: `GET http://localhost:8000/auth/protected`

**Headers**:
```
Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
```

**Expected Response** (200 OK):
```json
{
    "message": "Hello testuser, this is a protected route!"
}
```

### 5. Logout User

**URL**: `POST http://localhost:8000/auth/logout`

**Headers**:
```
Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
```

**Expected Response** (200 OK):
```json
{
    "message": "Successfully logged out. Please remove the token from client storage."
}
```

## Error Responses

### 400 Bad Request
```json
{
    "detail": "Username already registered"
}
```

### 401 Unauthorized
```json
{
    "detail": "Could not validate credentials"
}
```

### 422 Validation Error
```json
{
    "detail": [
        {
            "loc": ["body", "email"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]
}
```

## Development Tips

### Database Management

The SQLite database (`app.db`) is created automatically when you first run the application. To reset the database:

1. Stop the application
2. Delete `app.db` file
3. Restart the application

### Adding New Protected Routes

```python
from app.auth import get_current_active_user

@router.get("/my-protected-route")
def my_protected_route(current_user: User = Depends(get_current_active_user)):
    return {"message": f"Hello {current_user.username}!"}
```

### Environment Variables

For production deployment, set these environment variables:

- `SECRET_KEY`: A secure random string
- `DATABASE_URL`: Your production database URL
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time

## Production Deployment

### Security Considerations

1. **Secret Key**: Use a cryptographically secure secret key
2. **HTTPS**: Always use HTTPS in production
3. **CORS**: Configure CORS origins appropriately
4. **Database**: Use PostgreSQL or MySQL for production
5. **Environment Variables**: Use proper environment variable management

### Example Production Settings

```env
SECRET_KEY=your-production-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/dbname
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## Testing

Run the application and visit http://localhost:8000/docs to test all endpoints interactively using FastAPI's built-in Swagger UI.

## License

This project is open source and available under the MIT License.