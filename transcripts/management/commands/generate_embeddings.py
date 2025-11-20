"""Management command to generate vector embeddings for transcript segments."""

import djclick as click

from transcripts.models import SRTSegment
from transcripts.search import get_embedding


@click.command()
@click.option(
    "--batch-size",
    default=10,
    type=int,
    help="Number of segments to process in each batch (default: 10)",
)
def command(batch_size):
    """Generate vector embeddings for all transcript segments without embeddings."""
    # Get segments that don't have embeddings yet
    segments_without_embeddings = SRTSegment.objects.filter(embedding__isnull=True).order_by(
        "transcript", "segment_index"
    )

    total_count = segments_without_embeddings.count()

    if total_count == 0:
        click.secho("All segments already have embeddings!", fg="green")
        return

    click.echo(f"Found {total_count} segments without embeddings")
    click.echo(f"Processing in batches of {batch_size}...")

    processed = 0
    failed = 0

    for i, segment in enumerate(segments_without_embeddings, 1):
        try:
            # Generate embedding for this segment's text
            embedding = get_embedding(segment.text)

            # Update the segment with embedding and model name
            segment.embedding = embedding
            segment.embedding_model = "all-MiniLM-L6-v2"
            segment.save(update_fields=["embedding", "embedding_model"])

            processed += 1

            # Progress update every batch_size items
            if i % batch_size == 0:
                click.secho(f"Progress: {i}/{total_count} segments processed", fg="blue")
        except Exception as e:
            failed += 1
            click.secho(f"Error processing segment {segment.id}: {e}", fg="red")
            continue

    # Summary
    click.echo("\n" + "=" * 70)
    click.secho(f"Successfully generated embeddings: {processed}", fg="green")
    if failed > 0:
        click.secho(f"Failed: {failed}", fg="red")
    click.secho(f"Total: {processed + failed}/{total_count}", fg="blue")
    click.echo("=" * 70)
