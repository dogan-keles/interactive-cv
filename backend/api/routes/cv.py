"""
CV download API endpoints.
"""

import os
import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.infrastructure.database import SessionLocal
from backend.data_access.knowledge_base.cv_downloads import CVDownloadRequest

router = APIRouter(prefix="/api/cv", tags=["cv"])


class CVDownloadRequestModel(BaseModel):
    """Model for CV download request."""
    name: str
    email: EmailStr
    company: Optional[str] = None
    profile_id: int = 1


class CVDownloadResponse(BaseModel):
    """Response model for CV download request."""
    success: bool
    message: str
    download_token: str
    download_url: str


@router.post("/request-download", response_model=CVDownloadResponse)
async def request_cv_download(
    data: CVDownloadRequestModel,
    request: Request,
):
    """
    Request CV download - saves user info and generates download token.
    
    Args:
        data: User information (name, email, company)
        request: FastAPI request object (for IP, user agent)
        
    Returns:
        Download token and URL
    """
    db = SessionLocal()
    
    try:
        # Generate unique download token
        download_token = secrets.token_urlsafe(32)
        
        # Get IP address and user agent
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Create download request record
        cv_request = CVDownloadRequest(
            profile_id=data.profile_id,
            user_name=data.name,
            user_email=data.email,
            user_company=data.company,
            download_token=download_token,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        db.add(cv_request)
        db.commit()
        db.refresh(cv_request)
        
        # Generate download URL
        base_url = str(request.base_url).rstrip('/')
        download_url = f"{base_url}/api/cv/download/{download_token}"
        
        return CVDownloadResponse(
            success=True,
            message="CV download link generated successfully",
            download_token=download_token,
            download_url=download_url,
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        db.close()


@router.get("/download/{token}")
async def download_cv(token: str):
    """
    Download CV using token.
    
    Args:
        token: Unique download token
        
    Returns:
        CV file
    """
    db = SessionLocal()
    
    try:
        # Find download request
        cv_request = db.query(CVDownloadRequest).filter(
            CVDownloadRequest.download_token == token
        ).first()
        
        if not cv_request:
            raise HTTPException(status_code=404, detail="Invalid download token")
        
        # Mark as downloaded
        if not cv_request.downloaded:
            cv_request.downloaded = True
            cv_request.downloaded_at = datetime.utcnow()
            db.commit()
        
        # Get CV file path
        cv_path = os.path.join("backend", "storage", "cvs", "dogan_keles_cv.pdf")
        
        if not os.path.exists(cv_path):
            raise HTTPException(status_code=404, detail="CV file not found")
        
        # Return file
        return FileResponse(
            path=cv_path,
            media_type="application/pdf",
            filename="Dogan_Keles_CV.pdf",
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        db.close()


@router.get("/downloads")
async def get_download_stats(profile_id: int = 1):
    """
    Get CV download statistics.
    
    Args:
        profile_id: Profile ID
        
    Returns:
        Download statistics
    """
    db = SessionLocal()
    
    try:
        # Get all downloads
        downloads = db.query(CVDownloadRequest).filter(
            CVDownloadRequest.profile_id == profile_id
        ).order_by(CVDownloadRequest.created_at.desc()).all()
        
        # Calculate stats
        total_requests = len(downloads)
        total_downloaded = sum(1 for d in downloads if d.downloaded)
        
        # Recent downloads
        recent = [
            {
                "id": d.id,
                "name": d.user_name,
                "email": d.user_email,
                "company": d.user_company,
                "downloaded": d.downloaded,
                "created_at": d.created_at.isoformat(),
                "downloaded_at": d.downloaded_at.isoformat() if d.downloaded_at else None,
            }
            for d in downloads[:10]  # Last 10
        ]
        
        return {
            "total_requests": total_requests,
            "total_downloaded": total_downloaded,
            "conversion_rate": (total_downloaded / total_requests * 100) if total_requests > 0 else 0,
            "recent_downloads": recent,
        }
    
    finally:
        db.close()