# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django 5.2 project for transcription services, built from the django-startproject template. It uses Python 3.13, Docker Compose for containerization, uv for dependency management, and just for task automation.

## Architecture

- **Config package** (`config/`): Django settings, URLs, and WSGI configuration
- **Settings**: Uses environs for environment-based configuration with sensible defaults
- **Database**: PostgreSQL with pgautoupgrade (auto-updates to latest Postgres version)
- **Static files**: Managed by WhiteNoise middleware
- **Production server**: Configured with django-prodserver using Gunicorn (2 workers, bound to 0.0.0.0:8000)

## Development Workflow

All commands are run through `just` (a command runner). Docker Compose orchestrates three services:
- `db`: PostgreSQL database with auto-upgrade capability
- `web`: Django development server (runs on http://localhost:8000)
- `utility`: For running management commands, tests, and one-off tasks

### Essential Commands

```bash
# Initial setup
just bootstrap              # Sets up .env, locks dependencies, builds containers

# Running the application
just up                      # Start Django dev server (foreground)
just start                   # Start Django dev server (background/detached)
just down                    # Stop all containers

# Database operations
just manage migrate          # Run migrations
just manage makemigrations   # Create new migrations
just manage createsuperuser  # Create Django superuser
just pg_dump                 # Dump database to db.dump
just pg_restore              # Restore from db.dump

# Development tasks
just test                    # Run pytest test suite
just test path/to/test.py    # Run specific test file
just lint                    # Run pre-commit hooks (ruff, pyupgrade, django-upgrade, djhtml, djade)
just console                 # Open bash shell in utility container
just manage <command>        # Run any Django management command

# Dependency management
just lock                    # Lock dependencies with uv
just upgrade                 # Upgrade and lock all dependencies

# Logs
just logs                    # Show container logs
just tail                    # Follow container logs
```

### Running Management Commands

Django management commands run inside the `utility` container:
```bash
just manage <command> [args]
```

Examples:
```bash
just manage shell
just manage dbshell
just manage createsuperuser
just manage collectstatic
```

### Testing

- Uses pytest with django-test-plus, model-bakery
- Configured to skip migrations and reuse database for speed
- Test configuration in pyproject.toml

## Configuration

Environment variables (set in `.env`):
- `DATABASE_URL`: Postgres connection string
- `DJANGO_DEBUG`: Debug mode (default: false)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `CSRF_TRUSTED_ORIGINS`: Comma-separated list for CSRF
- `SECRET_KEY`: Django secret key
- `ADMIN_URL`: Custom admin URL path (default: "admin/")
- `CACHE_URL`: Cache backend URL
- `EMAIL_URL`: Email backend configuration

## Code Quality

Pre-commit hooks (run via `uv tool run prek`):
- **ruff**: Linting and formatting (line length: 120)
- **pyupgrade**: Ensures Python 3.13+ syntax
- **django-upgrade**: Ensures Django 5.0+ patterns
- **djhtml**: Formats Django templates (4-space tabs)
- **djade**: Django 5.2 template compatibility checks
- **blacken-docs**: Formats code blocks in documentation

## Docker Context

The web service runs `uv run -m manage devserver --skip-checks 0.0.0.0:8000` via compose-entrypoint.sh. All containers mount the project at `/src` with cache consistency. The utility container is used for running tests and management commands with `--no-deps` and `--rm` flags.

## Transcription Workflow

This project includes MLX Whisper for audio/video transcription:

- **Standalone script**: `uv run scripts/transcribe.py` runs outside Docker (MLX requires Apple Silicon)
- **Output directory**: Transcriptions are saved to `captions/` by default
- **Loading to database**: Use `just manage load_captions` to import transcripts into PostgreSQL
- **Models**: Supports turbo (default), large, and parakeet models

## Important Rules

**Database Migrations:**
- Never run `makemigrations` by hand unless explicitly requested
- Always use `just manage migrate` for running migrations

**Files to Ignore:**
- Ignore all files in the `captions/` folder (transcription output directory)