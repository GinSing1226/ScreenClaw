# ScreenClaw Configuration

## Service Endpoint

| Config | Default Value | Description |
|--------|---------------|-------------|
| Base URL | `http://localhost:12261` | ScreenClaw service address |
| Port | `12261` | HTTP service port (auto-increments if occupied) |
| API Docs | `http://localhost:12261/docs` | Swagger UI documentation |

## Authentication

All API requests require authentication header:

```
Authorization: Bearer {token}
Content-Type: application/json
```

### Token Configuration

The token is configured in ScreenClaw's `config.json`:

```json
{
  "server": {
    "token": "your-secret-token-here"
  }
}
```

**Default token during development**: (empty string - no auth required)

**Production**: Set a strong token in config.json before deployment.

## Request Headers

```http
Authorization: Bearer your-token
Content-Type: application/json
```

## Session ID

Each AI application session should use a unique `session_id`:
- Format: `{ai_app_type}-{timestamp}-{random}`
- Example: `claude_code-20260326-a7f2b3`
- Purpose: Isolates screenshots and logs per session

## Network Access

ScreenClaw binds to `0.0.0.0` by default, accessible from:
- Local machine: `http://localhost:12261`
- LAN devices: `http://{local-ip}:12261`

To find your local IP:
- Windows: `ipconfig` → look for IPv4 address
- The service also returns local IP in health check response

## CORS

ScreenClaw allows all origins (CORS enabled) for development.
Configure `allowed_origins` in config.json for production.

## Configuration File Reference

`config.json` structure:

```json
{
  "server": {
    "port": 12261,
    "host": "0.0.0.0",
    "token": "",
    "local_ip": "",
    "auto_start": true,
    "service_enabled": true
  },
  "screenshot": {
    "max_width": 1920,
    "quality": 85,
    "default_grid": {
      "density": 5.0,
      "opacity": 50,
      "color": "#00FF00"
    },
    "default_coordinate": {
      "number_density": 2,
      "number_decimal": 0,
      "number_size": 8,
      "number_color": "#00FF00",
      "number_opacity": 100
    }
  },
  "storage": {
    "data_dir": "./data",
    "max_storage_mb": 500
  }
}
```

## Environment Variables

ScreenClaw also supports environment variable overrides:

| Variable | Description |
|----------|-------------|
| `SCREENCLAW_PORT` | Override default port |
| `SCREENCLAW_TOKEN` | Override auth token |
| `SCREENCLAW_DATA_DIR` | Override data directory |

## Health Check Response

`GET /api/health` returns service info:

```json
{
  "success": true,
  "message": "服务正常",
  "data": {
    "version": "1.0.0",
    "uptime_seconds": 3600,
    "local_ip": "192.168.1.100"
  }
}
```
