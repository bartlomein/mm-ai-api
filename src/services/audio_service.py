import os
from typing import Optional, Tuple
import httpx
import json

class AudioService:
    def __init__(self):
        # Use Kokoro TTS (self-hosted, free)
        self.kokoro_url = os.getenv("KOKORO_URL", "http://localhost:8880")
        # Fallback to OpenAI if needed
        self.use_openai_fallback = os.getenv("OPENAI_API_KEY") is not None
        if self.use_openai_fallback:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    async def generate_audio(self, text: str, voice: str = "af_bella", tier: str = "free") -> bytes:
        """
        Generate audio from text using Kokoro TTS
        
        Kokoro voices available:
        - af_bella, af_sarah, af_nicole (American female)
        - am_adam, am_michael (American male)  
        - bf_emma, bf_isabella (British female)
        - bm_george, bm_lewis (British male)
        
        Free tier: af_bella (default)
        Premium tier: af_sarah or bf_emma (variety)
        """
        try:
            # Choose voice based on tier
            if tier == "premium":
                voice = "af_sarah"  # Different voice for premium
            else:
                voice = "af_bella"  # Default voice for free
            
            # Generate audio using Kokoro
            return await self._generate_with_kokoro(text, voice)
            
        except Exception as e:
            print(f"Error generating audio with Kokoro: {str(e)}")
            
            # Fallback to OpenAI if available
            if self.use_openai_fallback:
                print("Falling back to OpenAI TTS...")
                return await self._generate_with_openai(text, tier)
            else:
                raise
    
    async def _generate_with_kokoro(self, text: str, voice: str = "af_bella") -> bytes:
        """
        Generate audio using Kokoro TTS
        """
        url = f"{self.kokoro_url}/v1/audio/speech"
        
        payload = {
            "model": "kokoro",
            "input": text,
            "voice": voice,
            "response_format": "mp3",
            "speed": 1.0
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.content
            else:
                error_detail = response.text
                raise Exception(f"Kokoro API error {response.status_code}: {error_detail}")
    
    async def _generate_with_openai(self, text: str, tier: str) -> bytes:
        """
        Fallback to OpenAI TTS
        """
        voice = "nova" if tier == "premium" else "alloy"
        
        response = self.openai_client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            response_format="mp3"
        )
        
        return response.content
    
    def estimate_duration(self, text: str) -> int:
        """
        Estimate audio duration in seconds
        Assuming ~150 words per minute speaking rate
        """
        word_count = len(text.split())
        duration_minutes = word_count / 150
        return int(duration_minutes * 60)
    
    async def generate_with_elevenlabs(self, text: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM") -> bytes:
        """
        Alternative: Generate audio using ElevenLabs
        (Better quality but more expensive)
        """
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("ElevenLabs API key not configured")
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                return response.content
            else:
                raise Exception(f"ElevenLabs API error: {response.status_code}")
    
    async def generate_with_cartesia(self, text: str, voice_id: str = "a0e99841-438c-4a64-b679-ae501e7d6091") -> bytes:
        """
        Alternative: Generate audio using Cartesia
        (Good balance of quality and price)
        """
        api_key = os.getenv("CARTESIA_API_KEY")
        if not api_key:
            raise ValueError("Cartesia API key not configured")
        
        url = "https://api.cartesia.ai/tts/bytes"
        
        headers = {
            "X-API-Key": api_key,
            "Cartesia-Version": "2024-06-10",
            "Content-Type": "application/json"
        }
        
        data = {
            "model_id": "sonic-english",
            "transcript": text,
            "voice": {
                "mode": "id",
                "id": voice_id
            },
            "output_format": {
                "container": "mp3",
                "encoding": "mp3",
                "sample_rate": 44100
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                return response.content
            else:
                raise Exception(f"Cartesia API error: {response.status_code}")