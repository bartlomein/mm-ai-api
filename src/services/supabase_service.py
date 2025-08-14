"""
Supabase service for managing briefing storage and user access
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseService:
    """Service for managing Supabase storage and database operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        url = os.getenv("SUPABASE_URL")
        # Try service key first for admin operations, fall back to anon key
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")
        
        self.client: Client = create_client(url, key)
        self.url = url
        self.is_service_role = bool(os.getenv("SUPABASE_SERVICE_KEY"))
        logger.info(f"✅ Supabase client initialized (service role: {self.is_service_role})")
    
    async def upload_briefing_audio(
        self,
        file_content: bytes,
        filename: str,
        briefing_type: str,
        date: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload briefing audio file to Supabase storage
        
        Args:
            file_content: Audio file content in bytes
            filename: Name of the file
            briefing_type: Type of briefing (morning, afternoon, evening)
            date: Date of the briefing
            metadata: Additional metadata
        
        Returns:
            Dict with upload details and public URL
        """
        try:
            # Create folder structure: YYYY/MM/DD/type/filename
            folder_path = f"{date.year}/{date.month:02d}/{date.day:02d}/{briefing_type}"
            full_path = f"{folder_path}/{filename}"
            
            # Upload to storage bucket (create bucket if doesn't exist)
            bucket_name = "briefings"
            
            # Check if bucket exists, create if not
            try:
                self.client.storage.get_bucket(bucket_name)
            except:
                # Create bucket with private access
                self.client.storage.create_bucket(
                    bucket_name,
                    options={
                        "public": False,  # Only authenticated users can access
                        "fileSizeLimit": 104857600,  # 100MB limit
                        "allowedMimeTypes": ["audio/mpeg", "audio/mp3", "audio/wav"]
                    }
                )
                logger.info(f"✅ Created storage bucket: {bucket_name}")
            
            # Upload file
            response = self.client.storage.from_(bucket_name).upload(
                path=full_path,
                file=file_content,
                file_options={
                    "content-type": "audio/mpeg",
                    "cache-control": "3600",
                    "upsert": "true"  # Must be string, not boolean
                }
            )
            
            # Get signed URL (valid for 7 days for paid users)
            signed_url = self.client.storage.from_(bucket_name).create_signed_url(
                path=full_path,
                expires_in=604800  # 7 days in seconds
            )
            
            logger.info(f"✅ Uploaded audio file to: {full_path}")
            
            return {
                "success": True,
                "path": full_path,
                "bucket": bucket_name,
                "signed_url": signed_url["signedURL"] if signed_url else None,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Error uploading audio: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def save_briefing_metadata(
        self,
        title: str,
        briefing_type: str,
        briefing_date: datetime,
        text_content: str,
        audio_file_path: str,
        word_count: int,
        duration_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tier: str = "premium"
    ) -> Dict[str, Any]:
        """
        Save briefing metadata to database
        
        Args:
            title: Title of the briefing
            briefing_type: Type (morning, afternoon, evening, custom)
            briefing_date: Date of the briefing
            text_content: Text content of the briefing
            audio_file_path: Path to audio file in storage
            word_count: Number of words in briefing
            duration_seconds: Duration of audio in seconds
            metadata: Additional metadata
        
        Returns:
            Dict with insertion result
        """
        try:
            data = {
                "title": title,
                "briefing_type": briefing_type,
                "briefing_date": briefing_date.date().isoformat(),
                "text_content": text_content,
                "audio_file_path": audio_file_path,
                "word_count": word_count,
                "duration_seconds": duration_seconds,
                "metadata": metadata or {},
                "tier": tier,
                "is_public": False  # Default to private
            }
            
            result = self.client.table("briefings").insert(data).execute()
            
            logger.info(f"✅ Saved briefing metadata: {title}")
            return {
                "success": True,
                "briefing_id": result.data[0]["id"] if result.data else None,
                "data": result.data[0] if result.data else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error saving briefing metadata: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_user_access(self, user_id: str) -> Dict[str, Any]:
        """
        Check if user has access to briefings
        
        Args:
            user_id: User ID from auth
        
        Returns:
            Dict with access information
        """
        try:
            result = self.client.table("user_profiles").select("*").eq("id", user_id).execute()
            
            if result.data:
                profile = result.data[0]
                has_access = profile.get("is_paid_subscriber", False)
                
                # Check if subscription is still valid
                if has_access and profile.get("subscription_expires_at"):
                    expires_at = datetime.fromisoformat(profile["subscription_expires_at"].replace("Z", "+00:00"))
                    has_access = expires_at > datetime.now()
                
                return {
                    "success": True,
                    "has_access": has_access,
                    "subscription_tier": profile.get("subscription_tier", "free"),
                    "expires_at": profile.get("subscription_expires_at")
                }
            
            return {
                "success": True,
                "has_access": False,
                "subscription_tier": "free"
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking user access: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_briefing_url(self, briefing_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get signed URL for briefing audio (checks user access based on tier)
        
        Args:
            briefing_id: ID of the briefing
            user_id: User ID requesting access
        
        Returns:
            Dict with signed URL or error
        """
        try:
            # Get briefing metadata
            result = self.client.table("briefings").select("*").eq("id", briefing_id).execute()
            
            if not result.data:
                return {
                    "success": False,
                    "error": "Briefing not found"
                }
            
            briefing = result.data[0]
            tier = briefing.get("tier", "premium")
            
            # Check access based on tier
            if briefing.get("is_public", False):
                # Public briefings are always accessible
                pass
            elif tier == "free":
                # Free tier briefings require authentication only
                if not user_id:
                    return {
                        "success": False,
                        "error": "Please sign in to access free briefings"
                    }
            else:
                # Premium briefings require paid subscription
                if not user_id:
                    return {
                        "success": False,
                        "error": "Authentication required for premium content"
                    }
                
                access_check = await self.check_user_access(user_id)
                if not access_check.get("has_access", False):
                    return {
                        "success": False,
                        "error": "Premium subscription required to access full briefings",
                        "suggestion": "Try our free 3-minute briefings or upgrade for full access"
                    }
            
            # Generate signed URL
            audio_path = briefing.get("audio_file_path")
            if audio_path:
                # Shorter expiry for free tier
                expires_in = 1800 if tier == "free" else 3600  # 30 min for free, 1 hour for premium
                
                signed_url = self.client.storage.from_("briefings").create_signed_url(
                    path=audio_path,
                    expires_in=expires_in
                )
                
                return {
                    "success": True,
                    "url": signed_url["signedURL"] if signed_url else None,
                    "briefing": briefing,
                    "tier": tier,
                    "expires_in": expires_in
                }
            
            return {
                "success": False,
                "error": "Audio file not found"
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting briefing URL: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_briefings(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        briefing_type: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        List available briefings with filters
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            briefing_type: Type filter (morning, afternoon, evening)
            limit: Maximum number of results
        
        Returns:
            Dict with list of briefings
        """
        try:
            query = self.client.table("briefings").select("*")
            
            if start_date:
                query = query.gte("briefing_date", start_date.date().isoformat())
            
            if end_date:
                query = query.lte("briefing_date", end_date.date().isoformat())
            
            if briefing_type:
                query = query.eq("briefing_type", briefing_type)
            
            result = query.order("briefing_date", desc=True).limit(limit).execute()
            
            return {
                "success": True,
                "briefings": result.data,
                "count": len(result.data)
            }
            
        except Exception as e:
            logger.error(f"❌ Error listing briefings: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Singleton instance
_supabase_service = None

def get_supabase_service() -> SupabaseService:
    """Get or create Supabase service instance"""
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
    return _supabase_service