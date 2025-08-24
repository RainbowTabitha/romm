from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseModel(PydanticBaseModel):
    """Ensures all datetime fields include UTC timezone"""

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda dt: (
                dt.isoformat()
                if dt.tzinfo
                else dt.replace(tzinfo=timezone.utc).isoformat()
            )
        }
    )


class MessageResponse(BaseModel):
    """Standard message response for API endpoints"""
    
    message: str
    data: Optional[Any] = None
