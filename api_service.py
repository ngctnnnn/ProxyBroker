"""
ProxyBroker REST API Microservice

A FastAPI-based REST API wrapper for ProxyBroker functionality.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from proxybroker import Broker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global broker instance
broker_instance: Optional[Broker] = None
proxies_queue: Optional[asyncio.Queue] = None
loop: Optional[asyncio.AbstractEventLoop] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI startup/shutdown."""
    global broker_instance, proxies_queue, loop
    
    # Startup
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()
    
    proxies_queue = asyncio.Queue()
    broker_instance = Broker(
        queue=proxies_queue,
        max_conn=200,
        max_tries=3,
        timeout=8,
        loop=loop
    )
    logger.info("ProxyBroker API service started")
    
    yield
    
    # Shutdown
    if broker_instance:
        broker_instance.stop()
    logger.info("ProxyBroker API service stopped")


app = FastAPI(
    title="ProxyBroker API",
    description="REST API for finding and checking public proxies",
    version="1.0.0",
    lifespan=lifespan
)


# Pydantic models for request/response
class FindProxiesRequest(BaseModel):
    types: List[str] = Field(
        ..., 
        description="Proxy types to find (HTTP, HTTPS, SOCKS4, SOCKS5, CONNECT:80, CONNECT:25)"
    )
    countries: Optional[List[str]] = Field(
        None, 
        description="ISO country codes filter (e.g., ['US', 'GB'])"
    )
    limit: int = Field(
        10, 
        ge=1, 
        le=1000, 
        description="Maximum number of proxies to find"
    )
    post: bool = Field(
        False, 
        description="Use POST instead of GET for requests when checking proxies"
    )
    strict: bool = Field(
        False, 
        description="Strict mode: anonymity levels must match exactly"
    )
    dnsbl: Optional[List[str]] = Field(
        None, 
        description="Spam databases for proxy checking"
    )
    timeout: Optional[int] = Field(
        None, 
        ge=1, 
        le=60, 
        description="Timeout in seconds (overrides default)"
    )


class GrabProxiesRequest(BaseModel):
    countries: Optional[List[str]] = Field(
        None, 
        description="ISO country codes filter"
    )
    limit: int = Field(
        10, 
        ge=1, 
        le=1000, 
        description="Maximum number of proxies to grab"
    )


class ProxyResponse(BaseModel):
    host: str
    port: int
    types: List[str]
    geo: dict
    is_working: Optional[bool] = None
    avg_resp_time: Optional[float] = None
    error_rate: Optional[float] = None


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "ProxyBroker API",
        "version": "1.0.0",
        "endpoints": {
            "find": "/api/v1/find",
            "grab": "/api/v1/grab",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ProxyBroker API"
    }


async def collect_proxies(limit: int) -> List[dict]:
    """Collect proxies from the queue."""
    proxies = []
    count = 0
    
    while count < limit:
        try:
            # Wait for proxy with timeout
            proxy = await asyncio.wait_for(proxies_queue.get(), timeout=30.0)
            if proxy is None:
                break
            
            # Use the proxy's as_json method for consistent serialization
            proxy_dict = proxy.as_json()
            
            # Add is_working field if available
            if hasattr(proxy, 'is_working'):
                proxy_dict["is_working"] = proxy.is_working
            
            # Flatten types list for simpler response
            if 'types' in proxy_dict and isinstance(proxy_dict['types'], list):
                # Convert from [{'type': 'HTTP', 'level': 'High'}, ...] to ['HTTP', ...]
                proxy_dict['types'] = [t.get('type', '') for t in proxy_dict['types'] if t.get('type')]
            
            proxies.append(proxy_dict)
            count += 1
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for proxies. Found {count} so far.")
            break
        except Exception as e:
            logger.error(f"Error collecting proxy: {e}")
            break
    
    return proxies


@app.post("/api/v1/find", response_model=List[ProxyResponse])
async def find_proxies(request: FindProxiesRequest):
    """
    Find and check proxies with specified parameters.
    
    This endpoint finds proxies from multiple sources and checks them
    for functionality based on the specified criteria.
    """
    if not broker_instance:
        raise HTTPException(status_code=503, detail="Broker not initialized")
    
    # Validate types
    valid_types = {'HTTP', 'HTTPS', 'SOCKS4', 'SOCKS5', 'CONNECT:80', 'CONNECT:25'}
    types_upper = [t.upper() for t in request.types]
    invalid_types = [t for t in types_upper if t not in valid_types]
    if invalid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid proxy types: {invalid_types}. Valid types: {list(valid_types)}"
        )
    
    try:
        # Clear the queue
        while not proxies_queue.empty():
            try:
                proxies_queue.get_nowait()
            except:
                pass
        
        # Configure broker timeout if provided
        if request.timeout:
            broker_instance._timeout = request.timeout
        
        # Start finding proxies
        find_task = asyncio.create_task(
            broker_instance.find(
                types=types_upper,
                countries=request.countries,
                post=request.post,
                strict=request.strict,
                dnsbl=request.dnsbl,
                limit=request.limit
            )
        )
        
        # Collect proxies
        proxies = await collect_proxies(request.limit)
        
        # Wait for find task to complete (or timeout)
        try:
            await asyncio.wait_for(find_task, timeout=60.0)
        except asyncio.TimeoutError:
            logger.warning("Find task timed out, but returning collected proxies")
        except Exception as e:
            logger.error(f"Error in find task: {e}")
        
        if not proxies:
            raise HTTPException(
                status_code=404,
                detail="No proxies found matching the criteria"
            )
        
        return proxies
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding proxies: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v1/grab", response_model=List[ProxyResponse])
async def grab_proxies(request: GrabProxiesRequest):
    """
    Grab proxies from providers without checking them.
    
    This endpoint quickly collects proxies from sources without
    verifying their functionality.
    """
    if not broker_instance:
        raise HTTPException(status_code=503, detail="Broker not initialized")
    
    try:
        # Clear the queue
        while not proxies_queue.empty():
            try:
                proxies_queue.get_nowait()
            except:
                pass
        
        # Start grabbing proxies
        grab_task = asyncio.create_task(
            broker_instance.grab(
                countries=request.countries,
                limit=request.limit
            )
        )
        
        # Collect proxies
        proxies = await collect_proxies(request.limit)
        
        # Wait for grab task to complete
        try:
            await asyncio.wait_for(grab_task, timeout=60.0)
        except asyncio.TimeoutError:
            logger.warning("Grab task timed out, but returning collected proxies")
        except Exception as e:
            logger.error(f"Error in grab task: {e}")
        
        if not proxies:
            raise HTTPException(
                status_code=404,
                detail="No proxies found matching the criteria"
            )
        
        return proxies
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error grabbing proxies: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
