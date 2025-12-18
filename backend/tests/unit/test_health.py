"""Health check endpoint tests"""

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """TEST 1: Health check returns 200"""
    response = await client.get("/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_readiness_probe(client: AsyncClient):
    """TEST 2: Readiness probe returns ready"""
    response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["ready"] == True

@pytest.mark.asyncio
async def test_liveness_probe(client: AsyncClient):
    """TEST 3: Liveness probe returns alive"""
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["alive"] == True
