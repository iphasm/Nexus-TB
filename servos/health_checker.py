"""
Health Checker Service for Railway
Provides HTTP endpoints for health monitoring
"""

import os
import time
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Create FastAPI app
app = FastAPI(title="Nexus Trading Bot Health Check", version="1.0.0")

# Health check data
health_data = {
    "service": "Nexus Trading Bot",
    "status": "starting",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "uptime_seconds": 0,
    "version": "1.0.0",
    "components": {
        "telegram_bot": {"status": "unknown", "last_check": None},
        "database": {"status": "unknown", "last_check": None},
        "exchanges": {"status": "unknown", "last_check": None},
        "nexus_core": {"status": "unknown", "last_check": None}
    }
}

# Store start time for uptime calculation
start_time = time.time()

class HealthStatus(BaseModel):
    service: str
    status: str
    timestamp: str
    uptime_seconds: float
    version: str
    components: Dict[str, Any]

def update_health_status(component: str, status: str, details: Dict[str, Any] = None):
    """Update health status for a specific component"""
    health_data["components"][component]["status"] = status
    health_data["components"][component]["last_check"] = datetime.now(timezone.utc).isoformat()

    if details:
        health_data["components"][component].update(details)

    # Update overall status
    all_components = health_data["components"]
    if all(c["status"] == "healthy" for c in all_components.values()):
        health_data["status"] = "healthy"
    elif any(c["status"] == "unhealthy" for c in all_components.values()):
        health_data["status"] = "degraded"
    else:
        health_data["status"] = "starting"

    health_data["timestamp"] = datetime.now(timezone.utc).isoformat()
    health_data["uptime_seconds"] = time.time() - start_time

@app.get("/")
async def root():
    """Root endpoint - basic service info"""
    return {
        "service": health_data["service"],
        "status": health_data["status"],
        "version": health_data["version"],
        "uptime": f"{health_data['uptime_seconds']:.1f}s"
    }

@app.get("/health")
async def health_check():
    """Railway health check endpoint"""
    # Update uptime
    health_data["uptime_seconds"] = time.time() - start_time
    health_data["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Return 200 OK for healthy OR starting status (Railway needs 200 to pass healthcheck)
    # Only return 503 for truly unhealthy/degraded states
    if health_data["status"] in ("healthy", "starting"):
        return JSONResponse(
            status_code=200,
            content=health_data
        )
    else:
        return JSONResponse(
            status_code=503,
            content=health_data
        )

@app.get("/health/detailed")
async def detailed_health():
    """Detailed health check with all component statuses"""
    health_data["uptime_seconds"] = time.time() - start_time
    health_data["timestamp"] = datetime.now(timezone.utc).isoformat()

    return JSONResponse(content=health_data)

@app.get("/health/{component}")
async def component_health(component: str):
    """Check health of specific component"""
    if component not in health_data["components"]:
        raise HTTPException(status_code=404, detail=f"Component '{component}' not found")

    comp_data = health_data["components"][component]
    comp_data["timestamp"] = datetime.now(timezone.utc).isoformat()

    return JSONResponse(content=comp_data)

@app.post("/health/update/{component}")
async def update_component_health(component: str, status: str, details: Dict[str, Any] = None):
    """Update health status of a component (internal API)"""
    if component not in health_data["components"]:
        raise HTTPException(status_code=404, detail=f"Component '{component}' not found")

    update_health_status(component, status, details)
    return {"message": f"Component '{component}' status updated to '{status}'"}

def mark_service_healthy():
    """Mark the entire service as healthy"""
    health_data["status"] = "healthy"

def mark_service_starting():
    """Mark the service as starting up"""
    health_data["status"] = "starting"

def mark_service_unhealthy():
    """Mark the service as unhealthy"""
    health_data["status"] = "unhealthy"

# Export the app for use in main application
__all__ = ['app', 'update_health_status', 'mark_service_healthy', 'mark_service_starting', 'mark_service_unhealthy']
