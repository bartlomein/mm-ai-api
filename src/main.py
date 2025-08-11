from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Debug: Check which TTS service is configured
print("[Main] Environment check:")
print(f"[Main] FISH_API_KEY present: {bool(os.getenv('FISH_API_KEY'))}")
print(f"[Main] OPENAI_API_KEY present: {bool(os.getenv('OPENAI_API_KEY'))}")
print(f"[Main] KOKORO_URL: {os.getenv('KOKORO_URL', 'Not set')}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up Market Brief API...")
    print(f"[Main] Using OpenAI: {bool(os.getenv('OPENAI_API_KEY'))}")
    print(f"[Main] Kokoro fallback available: {bool(os.getenv('KOKORO_URL'))}")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="Market Brief API",
    description="AI-powered financial news audio briefings",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for React Native
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "name": "Market Brief API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/api/health")
async def health_check():
    # Determine primary TTS service
    if os.getenv("FISH_API_KEY"):
        primary_service = "Fish Audio"
    elif os.getenv("OPENAI_API_KEY"):
        primary_service = "OpenAI"
    elif os.getenv("KOKORO_URL"):
        primary_service = "Kokoro"
    else:
        primary_service = "None configured"
    
    return {
        "status": "healthy",
        "environment": os.getenv("APP_ENV", "development"),
        "tts_config": {
            "fish_configured": bool(os.getenv("FISH_API_KEY")),
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "kokoro_configured": bool(os.getenv("KOKORO_URL")),
            "primary_service": primary_service
        }
    }

from fastapi import BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Optional
from pydantic import BaseModel
import os

# Import our services
from src.services.pipeline_service import PipelineService

# Initialize pipeline
pipeline_service = PipelineService()

# Request models
class GenerateBriefingRequest(BaseModel):
    tickers: Optional[List[str]] = None
    voice: Optional[str] = None  # OpenAI voice: alloy, echo, fable, onyx, nova, shimmer

# Test endpoints for pipeline
@app.post("/api/test/generate")
async def test_generate(voice: Optional[str] = None):
    """Test endpoint to generate a general market briefing"""
    result = await pipeline_service.generate_general_briefing(voice=voice)
    return result

@app.post("/api/test/generate-personalized")
async def test_generate_personalized(request: GenerateBriefingRequest):
    """Test endpoint to generate a personalized briefing"""
    tickers = request.tickers or ["AAPL", "GOOGL", "TSLA"]
    result = await pipeline_service.generate_personalized_briefing(tickers, voice=request.voice)
    return result

@app.get("/api/test/audio/{file_id}")
async def get_test_audio(file_id: str):
    """Serve audio files from temp directory (for testing)"""
    file_path = f"/tmp/audio_briefings/{file_id}.mp3"
    
    if os.path.exists(file_path):
        return FileResponse(
            file_path,
            media_type="audio/mpeg",
            filename=f"{file_id}.mp3"
        )
    else:
        raise HTTPException(status_code=404, detail="Audio file not found")