# Transcription App

> A Django-powered transcription service using MLX Whisper for fast, local audio/video transcription on Apple Silicon

This application transcribes audio and video files (including YouTube videos) using MLX Whisper, stores transcripts in a PostgreSQL database with full-text search capabilities, and outputs both SRT (subtitle) and plain text formats.

## About This Project

This project was built during livestream collaborations between Jay Miller and Jeff Triplett:

### Livestreams & Related Content

- **Part 1**: [EITR Project: Django-Transcripts - more search types and looking at the DB](https://www.youtube.com/watch?v=ycjNznwGVn0)
- **Part 2**: [Django Transcription App Development Continued](https://www.youtube.com/watch?v=wBUm3126BwE)
- **Aiven**: [Elephant in the Room, Episode 1: Working with Long Form Text in PostgreSQL and Django](https://www.youtube.com/watch?v=-GCASa5xWxw)

## Features

- **Fast Local Transcription**: Uses [MLX Whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) optimized for Apple Silicon
- **Multiple Model Support**: Choose between turbo, large, or parakeet models based on your needs
- **Dual Format Output**: Generates both SRT subtitle files and plain text transcripts
- **Database Storage**: Store and search transcripts with PostgreSQL full-text search
- **Django Admin**: Manage transcripts through Django's admin interface
- **Standalone Script**: Use `transcribe.py` for quick transcriptions without Django

## Tech Stack

- **Django 5.2** with Python 3.13
- **MLX Whisper** for transcription
- **PostgreSQL** with full-text search and auto-upgrade
- **Docker Compose** for containerization
- **uv** for dependency management
- **just** for task automation

## Prerequisites

- Apple Silicon Mac (M1/M2/M3/M4) for MLX Whisper
- Docker (OrbStack recommended)
- Python 3.13+
- [just](https://github.com/casey/just) command runner

## Quick Start

### Initial Setup

```shell
# Clone the repository
git clone <your-repo-url>
cd transcription-git

# Bootstrap the project (creates .env, installs dependencies, builds containers)
`just bootstrap`

# Run database migrations
`just manage migrate`

# Create a Django superuser (optional, for admin access)
just manage createsuperuser

# Start the development server
just up
```

## Usage

### Transcribing Audio/Video Files

#### Using Standalone Script

> **Note**: The transcription script runs outside of Docker due to MLX Whisper's Apple Silicon requirements, which can cause issues when running inside Docker containers.

```shell
# Transcribe a single file (outputs to captions/ directory)
uv run scripts/transcribe.py path/to/audio.mp3

# Transcribe multiple files
uv run scripts/transcribe.py path/to/audio1.mp3 path/to/video.mp4

# Use a different model (turbo, large, or parakeet)
uv run scripts/transcribe.py audio.mp3 --model large

# Include word-level timestamps
uv run scripts/transcribe.py audio.mp3 --word-timestamps

# Overwrite existing transcriptions
uv run scripts/transcribe.py audio.mp3 --overwrite
```

### Loading Transcripts into Database

After transcribing files, load them into the database for searching and management:

```shell
# Load all caption files from captions/ directory
just manage load_captions

# Load from a custom directory
just manage load_captions --captions-dir my-captions

# Preview what would be loaded without saving
just manage load_captions --dry-run
```

### Searching Transcripts

Access the Django admin interface at `http://localhost:8000/admin/` to search and manage transcripts using PostgreSQL full-text search.

### Common Commands

```shell
# Start the development server (foreground)
just up

# Start in background mode
just start

# Stop all containers
just down

# View logs
just logs

# Follow logs in real-time
just tail

# Open a bash console
just console

# Run tests
just test

# Lint code
just lint

# Database backup
just pg_dump

# Database restore
just pg_restore
```

## Available Whisper Models

Choose the model based on your needs for speed vs. accuracy:

| Model | HuggingFace Repository | Best For |
|-------|----------------------|----------|
| **turbo** (default) | mlx-community/whisper-turbo | Balanced speed and accuracy |
| **large** | mlx-community/whisper-large-v3-turbo | Highest accuracy, slower |
| **parakeet** | mlx-community/parakeet-tdt_ctc-1.1b | Experimental alternative model |

Example: `just manage transcribe video.mp4 --model large`

## Project Structure

```
transcription-git/
├── captions/              # Default output directory for transcriptions
├── config/                # Django settings and configuration
├── scripts/
│   └── transcribe.py      # Standalone transcription script (runs outside Docker)
├── transcripts/           # Django app for managing transcripts
│   ├── models.py         # Transcript model with full-text search
│   ├── admin.py          # Django admin configuration
│   └── management/
│       └── commands/
│           └── load_captions.py  # Import captions to database
├── docker-compose.yml     # Container orchestration
├── justfile              # Command shortcuts
└── pyproject.toml        # Python dependencies
```

## All Available Commands

Run `just --list` to see all available commands:

```
Available recipes:
    bootstrap *ARGS           # Initialize project with dependencies and environment
    build *ARGS               # Build Docker containers with optional args
    console                   # Open interactive bash console in utility container
    down *ARGS                # Stop and remove containers, networks
    lint *ARGS                # Run pre-commit hooks on all files
    lint-autoupdate *ARGS     # Update pre-commit hooks to latest versions
    lock *ARGS                # Lock dependencies with uv
    logs *ARGS                # Show logs from containers
    manage *ARGS              # Run Django management commands
    pg_dump file='db.dump'    # Dump database to file
    pg_restore file='db.dump' # Restore database dump from file
    restart *ARGS             # Restart containers
    run *ARGS                 # Run command in utility container
    start *ARGS="--detach"    # Start services in detached mode by default
    stop *ARGS                # Stop services (alias for down)
    tail                      # Show and follow logs
    test *ARGS                # Run pytest with arguments
    up *ARGS                  # Start containers
    upgrade                   # Upgrade dependencies and lock
```

## Configuration

### Database Setup

This demo is configured to work with **any PostgreSQL database**, including:
- **Aiven PostgreSQL** (recommended for cloud deployments)
- Local PostgreSQL (via Docker Compose)
- Any other PostgreSQL-compatible database

To use a PostgreSQL database, set the `DATABASE_URL` environment variable with your connection string:

```
DATABASE_URL=postgresql://username:password@hostname:port/database_name
```

**Aiven Example:**
```
DATABASE_URL=postgresql://avnadmin:your-password@pg-xxxxx.aivencloud.com:12345/defaultdb
```

**Local Docker Database:**
The default Docker Compose setup automatically creates a PostgreSQL container. The `DATABASE_URL` is automatically configured in `.env` during `just bootstrap`.

### Environment Variables

Environment variables can be set in `.env` (created by `just bootstrap`):

- `DATABASE_URL` - PostgreSQL connection string (Aiven, local Docker, or any PostgreSQL database)
- `DJANGO_DEBUG` - Enable debug mode (default: false in production)
- `SECRET_KEY` - Django secret key (auto-generated)
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `ADMIN_URL` - Custom admin URL path (default: "admin/")

## Development

### Code Quality

This project uses pre-commit hooks via [prek](https://github.com/pre-commit/pre-commit):

```shell
# Run linting
just lint

# Update hooks to latest versions
just lint-autoupdate
```

Configured tools:
- **ruff** - Fast Python linter and formatter
- **pyupgrade** - Modernize Python syntax (3.13+)
- **django-upgrade** - Upgrade Django patterns (5.0+)
- **djhtml** - Django template formatter

### Testing

```shell
# Run all tests
just test

# Run specific test file
just test path/to/test.py
```

## Troubleshooting

### MLX Whisper Issues

MLX Whisper requires Apple Silicon. If you're running on a different platform, you may need to use a different transcription backend.

### Container Issues

```shell
# Rebuild containers
just build

# View container logs
just logs

# Restart containers
just restart
```

## License

This project is built from the [django-startproject](https://github.com/jefftriplett/django-startproject) template.

## Author

**Jeff Triplett**
- Website: [jefftriplett.com](https://jefftriplett.com)
- GitHub: [@jefftriplett](https://github.com/jefftriplett)
