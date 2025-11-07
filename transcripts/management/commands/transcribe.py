"""Management command to transcribe audio/video files using MLX Whisper."""

from pathlib import Path

import djclick as click
import mlx_whisper
from mlx_whisper.writers import get_writer


@click.command()
@click.argument("input_paths", nargs=-1, required=True, type=click.Path(exists=True))
@click.option(
    "--model",
    type=click.Choice(["large", "turbo", "parakeet"], case_sensitive=False),
    default="turbo",
    help="Model to use for transcription (default: turbo)",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing transcription files",
)
@click.option(
    "--word-timestamps",
    is_flag=True,
    help="Include word-level timestamps in transcription",
)
@click.option(
    "--output-dir",
    type=click.Path(),
    default="captions",
    help="Output directory for transcription files (default: captions)",
)
def command(input_paths, model, overwrite, word_timestamps, output_dir):
    """Transcribe audio/video files using MLX Whisper.

    This command transcribes one or more audio or video files and saves the results
    in both SRT (subtitle) and TXT (plain text) formats.

    Example usage:
        python manage.py transcribe audio.mp3
        python manage.py transcribe audio1.mp3 audio2.wav --model large
        python manage.py transcribe *.mp4 --overwrite
    """
    # Model mapping
    model_map = {
        "large": "mlx-community/whisper-large-v3-turbo",
        "turbo": "mlx-community/whisper-turbo",
        "parakeet": "mlx-community/parakeet-tdt_ctc-1.1b",
    }

    model_path = model_map[model]
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    click.echo(f"Using model: {model} ({model_path})")
    click.echo(f"Output directory: {output_dir}")
    click.echo("")

    for input_path in input_paths:
        filename_stem = Path(input_path).stem

        # Define output paths for both formats
        srt_filename = f"{filename_stem}.srt"
        txt_filename = f"{filename_stem}.txt"
        srt_path = output_dir.joinpath(srt_filename)
        txt_path = output_dir.joinpath(txt_filename)

        # Check if files already exist
        if (not srt_path.exists() and not txt_path.exists()) or overwrite:
            click.echo(f"Transcribing: {Path(input_path).name}")
            result = mlx_whisper.transcribe(
                input_path,
                path_or_hf_repo=model_path,
                word_timestamps=word_timestamps,
            )

            # Write SRT file
            srt_writer = get_writer("srt", str(output_dir))
            srt_writer(result, srt_filename, {})
            click.secho(f"  ✓ {srt_path.name}", fg="green")

            # Write plain text file
            txt_writer = get_writer("txt", str(output_dir))
            txt_writer(result, txt_filename, {})
            click.secho(f"  ✓ {txt_path.name}", fg="green")
        else:
            click.secho(f"Skipping (already exists): {filename_stem}", fg="yellow")
