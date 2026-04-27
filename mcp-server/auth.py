import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import Header, HTTPException

load_dotenv()

MCP_API_KEY = os.getenv("MCP_API_KEY")


def require_auth(authorization: Optional[str] = Header(default=None)) -> bool:
    if not MCP_API_KEY:
        raise HTTPException(status_code=500, detail="MCP_API_KEY is not configured")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.replace("Bearer ", "").strip()
    if token != MCP_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return True
