import os
from typing import Optional, Tuple
import httpx
import json

class AudioService:
    def __init__(self):
        print(f"[AudioService] Initializing...")
        
        # Primary: Fish Audio (best quality, no character limit)
        self.fish_api_key = os.getenv("FISH_API_KEY")
        print(f"[AudioService] Fish Audio API Key present: {bool(self.fish_api_key)}")
        
        if self.fish_api_key:
            print(f"[AudioService] Fish Audio API Key found, initializing Fish client...")
            try:
                from fish_audio_sdk import Session
                self.fish_session = Session(self.fish_api_key)
                print(f"[AudioService] Fish Audio client initialized successfully")
            except Exception as e:
                print(f"[AudioService] Failed to initialize Fish Audio: {e}")
                self.fish_session = None
        else:
            print(f"[AudioService] No Fish Audio API key found")
            self.fish_session = None
        
        # Secondary: OpenAI TTS HD
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        print(f"[AudioService] OpenAI API Key present: {bool(self.openai_api_key)}")
        
        if self.openai_api_key:
            print(f"[AudioService] OpenAI API Key found, initializing OpenAI client...")
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            print(f"[AudioService] OpenAI client initialized successfully")
        else:
            print(f"[AudioService] No OpenAI API key found")
            self.openai_client = None
            
        # Tertiary: Kokoro TTS (self-hosted, free)
        self.kokoro_url = os.getenv("KOKORO_URL", "http://localhost:8880")
        self.use_kokoro_fallback = bool(self.kokoro_url)
        print(f"[AudioService] Kokoro URL: {self.kokoro_url}")
        print(f"[AudioService] Kokoro fallback available: {self.use_kokoro_fallback}")
        
    async def generate_audio(self, text: str, voice: str = None, tier: str = "free") -> bytes:
        """
        Generate audio from text using Fish Audio (primary), OpenAI (secondary), or Kokoro (tertiary)
        
        Fish Audio models:
        - Default model used (configurable)
        
        OpenAI voices:
        - alloy, echo, fable, onyx, nova, shimmer
        
        Free tier: default voices
        Premium tier: premium voices
        """
        try:
            # Try Fish Audio first (no character limit, best quality)
            if self.fish_session:
                print(f"[AudioService] Using Fish Audio TTS")
                return await self._generate_with_fish(text, tier)
            
            # Fallback to OpenAI if Fish not available
            elif self.openai_client:
                print(f"[AudioService] Fish Audio not configured, using OpenAI TTS")
                # Choose voice based on tier if not specified
                if not voice:
                    voice = "nova" if tier == "premium" else "alloy"
                print(f"[AudioService] Using OpenAI voice '{voice}' and tier '{tier}'")
                return await self._generate_with_openai(text, voice, tier)
            
            # Final fallback to Kokoro
            elif self.use_kokoro_fallback:
                print(f"[AudioService] WARNING: Fish and OpenAI not configured, falling back to Kokoro TTS")
                kokoro_voice = "af_bella" if tier == "free" else "af_sarah"
                print(f"[AudioService] Using Kokoro voice: {kokoro_voice}")
                return await self._generate_with_kokoro(text, kokoro_voice)
            else:
                print(f"[AudioService] ERROR: No TTS service configured!")
                print(f"[AudioService] Fish session: {self.fish_session}")
                print(f"[AudioService] OpenAI client: {self.openai_client}")
                print(f"[AudioService] Kokoro fallback: {self.use_kokoro_fallback}")
                raise Exception("No TTS service configured. Please set FISH_API_KEY, OPENAI_API_KEY, or KOKORO_URL")
                
        except Exception as e:
            print(f"[AudioService] ERROR generating audio: {str(e)}")
            print(f"[AudioService] Error type: {type(e).__name__}")
            
            # Try cascade of fallbacks
            if self.fish_session and self.openai_client:
                print(f"[AudioService] Fish failed, attempting OpenAI fallback...")
                voice = "nova" if tier == "premium" else "alloy"
                return await self._generate_with_openai(text, voice, tier)
            elif self.openai_client and self.use_kokoro_fallback:
                print(f"[AudioService] OpenAI failed, attempting Kokoro fallback...")
                kokoro_voice = "af_bella" if tier == "free" else "af_sarah"
                return await self._generate_with_kokoro(text, kokoro_voice)
            else:
                print(f"[AudioService] No fallback available, re-raising error")
                raise
    
    async def _generate_with_kokoro(self, text: str, voice: str = "af_bella") -> bytes:
        """
        Generate audio using Kokoro TTS
        """
        url = f"{self.kokoro_url}/v1/audio/speech"
        print(f"[AudioService] Kokoro TTS request to: {url}")
        print(f"[AudioService] Kokoro voice: {voice}")
        print(f"[AudioService] Text length: {len(text)} characters")
        
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
                print(f"[AudioService] Kokoro TTS success! Audio size: {len(response.content)} bytes")
                return response.content
            else:
                error_detail = response.text
                print(f"[AudioService] Kokoro TTS failed with status {response.status_code}")
                print(f"[AudioService] Error details: {error_detail}")
                raise Exception(f"Kokoro API error {response.status_code}: {error_detail}")
    
    async def _generate_with_openai(self, text: str, voice: str = "alloy", tier: str = "free") -> bytes:
        """
        Generate audio using OpenAI TTS HD for better quality
        """
        # Use HD model for premium tier, standard for free
        model = "tts-1-hd" if tier == "premium" else "tts-1"
        print(f"[AudioService] OpenAI TTS request:")
        print(f"[AudioService]   Model: {model}")
        print(f"[AudioService]   Voice: {voice}")
        print(f"[AudioService]   Text length: {len(text)} characters")
        
        try:
            response = self.openai_client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format="mp3",
                speed=1.0  # Can be adjusted from 0.25 to 4.0
            )
            print(f"[AudioService] OpenAI TTS success! Audio generated")
            audio_content = response.content
            print(f"[AudioService] Audio size: {len(audio_content)} bytes")
            return audio_content
        except Exception as e:
            print(f"[AudioService] OpenAI TTS failed: {str(e)}")
            print(f"[AudioService] Error type: {type(e).__name__}")
            raise
    
    async def _generate_with_fish(self, text: str, tier: str = "free") -> bytes:
        """
        Generate audio using Fish Audio TTS (no character limit)
        Using highest quality settings with consistent voice
        """
        print(f"[AudioService] Fish Audio TTS request:")
        print(f"[AudioService]   Text length: {len(text)} characters")
        print(f"[AudioService]   Tier: {tier}")
        
        try:
            from fish_audio_sdk import TTSRequest
            import io
            
            # Get consistent voice model ID from environment or use default
            # You can get model IDs from fish.audio playground or by creating your own
            fish_model_id = os.getenv("FISH_MODEL_ID", None)
            
            if fish_model_id:
                print(f"[AudioService]   Using specific model: {fish_model_id}")
                request = TTSRequest(
                    text=text,
                    reference_id=fish_model_id  # Use consistent voice model
                )
            else:
                print(f"[AudioService]   Using default Fish Audio voice")
                print(f"[AudioService]   Note: Set FISH_MODEL_ID in .env for consistent voice")
                # List available models (optional - for debugging)
                try:
                    models = list(self.fish_session.list_models())
                    if models:
                        print(f"[AudioService]   Available models: {len(models)}")
                        # Optionally print first few model IDs
                        for i, model in enumerate(models[:3]):
                            print(f"[AudioService]     - {model.id}: {model.title}")
                except Exception as e:
                    print(f"[AudioService]   Could not list models: {e}")
                
                request = TTSRequest(
                    text=text
                    # Without reference_id, Fish Audio uses a default voice
                )
            
            # Collect audio chunks
            audio_data = io.BytesIO()
            chunk_count = 0
            
            # Use async iterator
            async for chunk in self.fish_session.tts.awaitable(request):
                audio_data.write(chunk)
                chunk_count += 1
                if chunk_count % 10 == 0:
                    print(f"[AudioService]   Received {chunk_count} chunks...")
            
            audio_bytes = audio_data.getvalue()
            print(f"[AudioService] Fish Audio TTS success! Audio size: {len(audio_bytes)} bytes")
            return audio_bytes
            
        except Exception as e:
            print(f"[AudioService] Fish Audio TTS failed: {str(e)}")
            print(f"[AudioService] Error type: {type(e).__name__}")
            raise
    
    def _map_to_kokoro_voice(self, openai_voice: str) -> str:
        """
        Map OpenAI voice names to Kokoro equivalents
        """
        voice_mapping = {
            "alloy": "af_bella",      # Neutral -> American female
            "echo": "bm_george",       # Articulate -> British male
            "fable": "af_sarah",       # Expressive -> American female
            "onyx": "am_michael",      # Deep -> American male
            "nova": "af_nicole",       # Conversational -> American female
            "shimmer": "bf_emma"       # Warm -> British female
        }
        return voice_mapping.get(openai_voice, "af_bella")
    
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