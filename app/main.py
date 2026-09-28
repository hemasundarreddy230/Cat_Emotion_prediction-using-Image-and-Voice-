from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.routers import auth, prediction

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Cat Emotion Recognition API",
    description="A complete FastAPI backend with JWT authentication and ML-powered cat emotion prediction from audio and images",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(prediction.router)

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Welcome to Cat Emotion Recognition API",
        "version": "2.0.0",
        "features": [
            "JWT Authentication",
            "Audio-based Cat Emotion Prediction",
            "Image-based Cat Emotion Prediction",
            "User Management"
        ],
        "frontend": "/static/index.html",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Cat Emotion Recognition API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)