"""Management command to load caption files from the captions directory."""

from pathlib import Path

import djclick as click

from transcripts.models import Transcript


@click.command()
@click.option(
    "--captions-dir",
    default="captions",
    help="Path to the captions directory (default: captions)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be loaded without actually saving to the database",
)
def command(captions_dir, dry_run):
    """Load caption files from the captions directory and store them as Transcript objects."""
    captions_dir = Path(captions_dir)

    if not captions_dir.exists():
        click.secho(f"Captions directory not found: {captions_dir}", fg="red")
        return

    # Get all SRT and TXT files
    srt_files = list(captions_dir.glob("*.srt"))
    txt_files = list(captions_dir.glob("*.txt"))

    # Group files by YouTube ID (filename without extension)
    youtube_ids = {}
    for srt_file in srt_files:
        youtube_id = srt_file.stem
        if youtube_id not in youtube_ids:
            youtube_ids[youtube_id] = {}
        youtube_ids[youtube_id]["srt"] = srt_file

    for txt_file in txt_files:
        youtube_id = txt_file.stem
        if youtube_id not in youtube_ids:
            youtube_ids[youtube_id] = {}
        youtube_ids[youtube_id]["txt"] = txt_file

    created_count = 0
    updated_count = 0
    skipped_count = 0

    click.echo(f"Found {len(youtube_ids)} unique YouTube IDs")

    for youtube_id, files in sorted(youtube_ids.items()):
        srt_content = ""
        text_content = ""

        # Read SRT file if exists
        if "srt" in files:
            try:
                srt_content = files["srt"].read_text(encoding="utf-8")
            except Exception as e:
                click.secho(f"Error reading SRT file for {youtube_id}: {e}", fg="yellow")

        # Read TXT file if exists
        if "txt" in files:
            try:
                text_content = files["txt"].read_text(encoding="utf-8")
            except Exception as e:
                click.secho(f"Error reading TXT file for {youtube_id}: {e}", fg="yellow")

        # Skip if both files are empty or missing
        if not srt_content and not text_content:
            click.secho(f"Skipping {youtube_id}: no content found", fg="yellow")
            skipped_count += 1
            continue

        if dry_run:
            click.echo(
                f"[DRY RUN] Would process {youtube_id}: "
                f"SRT={len(srt_content)} chars, TXT={len(text_content)} chars"
            )
            continue

        # Create or update the transcript
        transcript, created = Transcript.objects.update_or_create(
            youtube_id=youtube_id,
            defaults={
                "srt_content": srt_content,
                "text_content": text_content,
            },
        )

        if created:
            created_count += 1
            click.secho(
                f"Created transcript for {youtube_id}: "
                f"SRT={len(srt_content)} chars, TXT={len(text_content)} chars",
                fg="green",
            )
        else:
            updated_count += 1
            click.secho(
                f"Updated transcript for {youtube_id}: "
                f"SRT={len(srt_content)} chars, TXT={len(text_content)} chars",
                fg="green",
            )

    # Summary
    click.echo("\n" + "=" * 70)
    if dry_run:
        click.secho("[DRY RUN] No changes were made", fg="yellow")
    click.secho(f"Created: {created_count}", fg="green")
    click.secho(f"Updated: {updated_count}", fg="green")
    if skipped_count:
        click.secho(f"Skipped: {skipped_count}", fg="yellow")
    click.echo("=" * 70)
