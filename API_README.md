# ProxyBroker REST API Microservice

A Dockerized REST API microservice for ProxyBroker that allows you to find and check public proxies via HTTP API calls.

## Features

- **REST API**: Find and grab proxies via HTTP endpoints
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **Async Operations**: Built on FastAPI for high performance
- **Health Checks**: Built-in health check endpoint
- **Auto Documentation**: Interactive API docs at `/docs`

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and start the service (default port 8008)
docker-compose up -d

# Or specify a custom host port via environment variable
PROXYBROKER_PORT=9000 docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

**Port Configuration:**
- The host port can be configured via the `PROXYBROKER_PORT` environment variable
- Default host port is `8008` (maps to container port `8008`)
- Example: `PROXYBROKER_PORT=9000 docker-compose up -d` will expose the service on host port 9000
- You can also create a `docker-compose.override.yml` file to customize the port mapping

### Using Docker

```bash
# Build the image
docker build -t proxybroker-api .

# Run the container
docker run -d -p 8008:8008 --name proxybroker-api proxybroker-api

# View logs
docker logs -f proxybroker-api

# Stop the container
docker stop proxybroker-api
```

### Manual Installation

```bash
# Install dependencies
pip install -r requirements-api.txt
pip install -e .

# Run the service
uvicorn api_service:app --host 0.0.0.0 --port 8008
```

## API Endpoints

### Base URL
- Local: `http://localhost:8008` (or your configured port)
- Docker: `http://localhost:${PROXYBROKER_PORT:-8008}` (port can be configured via environment variable)

### Endpoints

#### `GET /`
Root endpoint with API information.

**Response:**
```json
{
  "service": "ProxyBroker API",
  "version": "1.0.0",
  "endpoints": {
    "find": "/api/v1/find",
    "grab": "/api/v1/grab",
    "health": "/health",
    "docs": "/docs"
  }
}
```

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "ProxyBroker API"
}
```

#### `POST /api/v1/find`
Find and check proxies with specified parameters.

**Request Body:**
```json
{
  "types": ["HTTP", "HTTPS"],
  "countries": ["US", "GB"],
  "limit": 10,
  "post": false,
  "strict": false,
  "dnsbl": null,
  "timeout": 8
}
```

**Parameters:**
- `types` (required): List of proxy types. Valid values: `HTTP`, `HTTPS`, `SOCKS4`, `SOCKS5`, `CONNECT:80`, `CONNECT:25`
- `countries` (optional): List of ISO country codes (e.g., `["US", "GB"]`)
- `limit` (optional): Maximum number of proxies to find (default: 10, max: 1000)
- `post` (optional): Use POST instead of GET for requests (default: false)
- `strict` (optional): Strict mode for anonymity levels (default: false)
- `dnsbl` (optional): Spam databases for proxy checking
- `timeout` (optional): Timeout in seconds (default: 8, max: 60)

**Response:**
```json
[
  {
    "host": "192.168.1.1",
    "port": 8080,
    "types": ["HTTP", "HTTPS"],
    "geo": {
      "code": "US",
      "name": "United States"
    },
    "is_working": true,
    "avg_resp_time": 1.23,
    "error_rate": 0.05
  }
]
```

#### `POST /api/v1/grab`
Grab proxies from providers without checking them.

**Request Body:**
```json
{
  "countries": ["US"],
  "limit": 20
}
```

**Parameters:**
- `countries` (optional): List of ISO country codes
- `limit` (optional): Maximum number of proxies to grab (default: 10, max: 1000)

**Response:**
Same format as `/api/v1/find`

## Usage Examples

### Using cURL

```bash
# Find 10 HTTP/HTTPS proxies from US
curl -X POST "http://localhost:8008/api/v1/find" \
  -H "Content-Type: application/json" \
  -d '{
    "types": ["HTTP", "HTTPS"],
    "countries": ["US"],
    "limit": 10
  }'

# Grab 20 proxies without checking
curl -X POST "http://localhost:8008/api/v1/grab" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 20
  }'
```

### Using Python

```python
import requests

# Find proxies
response = requests.post(
    "http://localhost:8008/api/v1/find",
    json={
        "types": ["HTTP", "HTTPS"],
        "countries": ["US"],
        "limit": 10
    }
)
proxies = response.json()
print(f"Found {len(proxies)} proxies")

# Grab proxies
response = requests.post(
    "http://localhost:8008/api/v1/grab",
    json={"limit": 20}
)
proxies = response.json()
```

### Using JavaScript/Node.js

```javascript
const axios = require('axios');

// Find proxies
async function findProxies() {
  const response = await axios.post('http://localhost:8008/api/v1/find', {
    types: ['HTTP', 'HTTPS'],
    countries: ['US'],
    limit: 10
  });
  console.log(`Found ${response.data.length} proxies`);
  return response.data;
}

// Grab proxies
async function grabProxies() {
  const response = await axios.post('http://localhost:8008/api/v1/grab', {
    limit: 20
  });
  return response.data;
}
```

## Interactive API Documentation

Once the service is running, visit (replace 8008 with your configured port if different):
- **Swagger UI**: http://localhost:8008/docs
- **ReDoc**: http://localhost:8008/redoc

## Configuration

### Environment Variables

- `PYTHONUNBUFFERED=1`: Ensures Python output is not buffered (useful for Docker logs)

### Port Configuration

The host port (the port on your machine) can be configured in several ways:

1. **Environment Variable (Recommended)**:
   ```bash
   PROXYBROKER_PORT=9000 docker-compose up -d
   ```
   This will expose the service on host port 9000 (container port remains 8008).

2. **docker-compose.override.yml**:
   Create a `docker-compose.override.yml` file to override the port mapping:
   ```yaml
   version: '3.8'
   services:
     proxybroker-api:
       ports:
         - "9000:8008"  # Custom host port
   ```

3. **Direct modification**:
   Edit `docker-compose.yml` and change the port mapping directly:
   ```yaml
   ports:
     - "9000:8008"  # Replace 9000 with your desired host port
   ```

**Note**: The container port (8008) is fixed and should not be changed unless you also modify the Dockerfile and api_service.py.

## Troubleshooting

### Service won't start
- Check Docker logs: `docker-compose logs`
- Ensure port 8008 is not already in use
- Verify all dependencies are installed

### No proxies found
- Try increasing the `limit` parameter
- Remove country filters to search globally
- Check network connectivity (proxies are fetched from external sources)

### Timeout errors
- Increase the `timeout` parameter in the request
- The service has a 60-second timeout for finding proxies

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Building for Production

```bash
# Build optimized image
docker build -t proxybroker-api:latest .

# Tag for registry
docker tag proxybroker-api:latest your-registry/proxybroker-api:latest

# Push to registry
docker push your-registry/proxybroker-api:latest
```

## License

Same as ProxyBroker: Apache License, Version 2.0
