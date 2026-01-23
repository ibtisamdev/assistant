# Configuration Guide

## Quick Start

### First-Time Setup

Run the setup wizard:

```bash
pday setup
```

This will:
1. Prompt for your OpenAI API key
2. Create configuration directories
3. Save your API key securely

### Manual Setup

If you prefer manual setup:

1. Create the config directory:
   ```bash
   mkdir -p ~/.config/planmyday
   ```

2. Create a `.env` file:
   ```bash
   echo "OPENAI_API_KEY=sk-your-key-here" > ~/.config/planmyday/.env
   chmod 600 ~/.config/planmyday/.env
   ```

3. Run the application:
   ```bash
   pday start
   ```

## Configuration Locations

### Global Mode (Default)

| Type | Location |
|------|----------|
| Config directory | `~/.config/planmyday/` |
| API key | `~/.config/planmyday/.env` |
| Sessions | `~/.local/share/planmyday/sessions/` |
| Profiles | `~/.local/share/planmyday/profiles/` |
| Templates | `~/.local/share/planmyday/templates/` |
| Exports | `~/.local/share/planmyday/exports/` |

### Local Mode (Development)

Use `--local` flag to store everything in the current directory:

```bash
pday --local start
```

This stores data in:
- `./sessions/`
- `./profiles/`
- `./data/templates/`
- `./data/plans/`
- `./data/summaries/`

## Configuration Priority

The application loads configuration in this order (highest to lowest priority):

1. **Environment variables** - Set in your shell or CI/CD platform
2. **Local `.env` file** - In current directory (if exists)
3. **Global `.env` file** - `~/.config/planmyday/.env`
4. **YAML config** - `~/.config/planmyday/config.yaml` (optional)
5. **Code defaults** - Hardcoded fallbacks

## View Configuration

```bash
# Show config file locations
pday config --path

# Show current configuration (if loaded)
pday config --show

# Update API key
pday config --set-key
```

## Troubleshooting

### Error: "planmyday is not configured yet"

**Cause:** First-time setup hasn't been run.

**Solution:**
```bash
pday setup
```

### Error: "OPENAI_API_KEY is required but not found"

**Cause:** Setup was run but the API key is missing or invalid.

**Solution:**
1. Check if config exists: `ls -la ~/.config/planmyday/`
2. Verify API key is set: `cat ~/.config/planmyday/.env`
3. Re-run setup: `pday setup`

### Error: "Invalid API key format"

**Cause:** The API key doesn't match expected format.

**Solution:**
- Get a valid key from https://platform.openai.com/api-keys
- OpenAI keys start with `sk-` and are ~50 characters
- Ensure you copied the entire key without extra spaces

### Debug Mode

Enable debug logging to see configuration loading details:

```bash
pday --debug start
```

You should see messages like:
```
Loading global environment from: ~/.config/planmyday/.env
Configuration loaded successfully
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | None | Your OpenAI API key |
| `ENVIRONMENT` | No | `development` | Runtime environment |
| `DEBUG` | No | `false` | Enable debug logging |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |

## API Key Storage Security

planmyday stores your API key with restricted permissions:

```bash
# Permissions set to 600 (owner read/write only)
-rw------- 1 user user 64 Jan 23 10:00 ~/.config/planmyday/.env
```

**Security best practices:**
- Never commit `.env` files to version control
- Don't share your API key
- Rotate your key periodically at https://platform.openai.com/api-keys

## Advanced: YAML Configuration

Create `~/.config/planmyday/config.yaml` for additional settings:

```yaml
# Optional: Override LLM settings
llm:
  model: gpt-4o-mini
  temperature: 0.7
  timeout: 60.0

# Optional: Override storage paths
storage:
  backend: json
  # sessions_dir: ~/custom/sessions

# Feature flags
enable_export: true
```

## Production Deployment

For production, **do not use `.env` files**. Instead, set environment variables directly:

### Docker

```bash
docker run -e OPENAI_API_KEY=sk-... planmyday
```

### Docker Compose

```yaml
services:
  planmyday:
    image: planmyday
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
  name: planmyday
spec:
  containers:
  - name: planmyday
    image: planmyday
    env:
    - name: OPENAI_API_KEY
      valueFrom:
        secretKeyRef:
          name: api-keys
          key: OPENAI_API_KEY
```

## See Also

- [12-Factor App Methodology](https://12factor.net/config)
- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)
