# Configuration Guide

## Quick Start

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Add your OpenAI API key:
   ```env
   OPENAI_API_KEY=sk-proj-your-key-here
   ```

3. Run the application:
   ```bash
   plan start
   ```

## Configuration Priority

The application loads configuration in this order (highest to lowest priority):

1. **Environment variables** - Set in your shell or CI/CD platform
2. **`.env` file** - For local development (gitignored)
3. **YAML config** - Default settings in `config/default.yaml`
4. **Code defaults** - Hardcoded fallbacks

## Troubleshooting

### Error: "OpenAI API key is required"

**Cause:** The `OPENAI_API_KEY` environment variable is not set.

**Solution:**
1. Check if `.env` file exists: `ls -la .env`
2. Verify API key is set: `cat .env | grep OPENAI_API_KEY`
3. Ensure no extra spaces or quotes around the key
4. Verify the key starts with `sk-`

### Error: "Invalid OpenAI API key format"

**Cause:** The API key doesn't start with `sk-`

**Solution:**
- Get a valid key from https://platform.openai.com/api-keys
- Ensure you copied the entire key

### Debug Mode

Enable debug logging to see configuration loading details:

```bash
plan start --debug
```

You should see messages like:
```
Loading environment from: /path/to/.env
Loading YAML config from: /path/to/config/default.yaml
Configuration loaded successfully
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | None | Your OpenAI API key |
| `ENVIRONMENT` | No | `development` | Runtime environment |
| `DEBUG` | No | `false` | Enable debug logging |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |

## Production Deployment

For production, **do not use `.env` files**. Instead, set environment variables directly:

### Docker

```bash
docker run -e OPENAI_API_KEY=sk-... personal-assistant
```

### Docker Compose

```yaml
services:
  assistant:
    image: personal-assistant
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

### Kubernetes

```bash
kubectl create secret generic api-keys --from-literal=OPENAI_API_KEY=sk-...
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: assistant
spec:
  containers:
  - name: assistant
    image: personal-assistant
    env:
    - name: OPENAI_API_KEY
      valueFrom:
        secretKeyRef:
          name: api-keys
          key: OPENAI_API_KEY
```

### Heroku

```bash
heroku config:set OPENAI_API_KEY=sk-...
```

### AWS/GCP/Azure

Use their respective secret management services:
- AWS: Systems Manager Parameter Store or Secrets Manager
- GCP: Secret Manager
- Azure: Key Vault

## Configuration Architecture

The application uses a **hybrid configuration approach** following production best practices:

### How It Works

1. **Load `.env` file** - `python-dotenv` loads `.env` into `os.environ`
2. **Load YAML config** - Default settings from YAML files
3. **Pydantic validation** - Type checking and validation
4. **Merge with priority** - Environment variables override YAML

### Example

```python
from src.application.config import AppConfig

# Automatically loads .env and validates
config = AppConfig.load()

# Access configuration
api_key = config.llm.api_key
model = config.llm.model
```

## Best Practices

1. **Never commit `.env` files** - They contain secrets
2. **Use `.env.example`** - Document required variables
3. **Validate early** - Fail fast with clear error messages
4. **Use environment variables in production** - Not `.env` files
5. **Override selectively** - Only override what you need

## See Also

- [12-Factor App Methodology](https://12factor.net/config)
- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [python-dotenv Documentation](https://pypi.org/project/python-dotenv/)
