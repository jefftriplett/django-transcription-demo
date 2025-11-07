# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = [
#     "mlx-whisper",
#     "rich",
#     "typer",
# ]
# ///
from enum import Enum
from pathlib import Path

import mlx_whisper
import typer
from mlx_whisper.writers import get_writer
from rich import print


class ModelChoices(str, Enum):
    large = "mlx-community/whisper-large-v3-turbo"
    turbo = "mlx-community/whisper-turbo"
    parakeet = "mlx-community/parakeet-tdt_ctc-1.1b"


def main(
    input_paths: list[str],
    model: ModelChoices = ModelChoices.turbo,
    overwrite: bool = False,
    word_timestamps: bool = False,
):
    output_dir = Path("captions")
    output_dir.mkdir(parents=True, exist_ok=True)

    for input_path in input_paths:
        filename_stem = Path(input_path).stem

        # Define output paths for both formats
        srt_filename = f"{filename_stem}.srt"
        txt_filename = f"{filename_stem}.txt"
        srt_path = output_dir.joinpath(srt_filename)
        txt_path = output_dir.joinpath(txt_filename)

        # Check if files already exist
        if (not srt_path.exists() or not txt_path.exists()) or overwrite:
            print(f"Transcribing: {Path(input_path).name}")
            result = mlx_whisper.transcribe(
                input_path,
                path_or_hf_repo=model.value,
                word_timestamps=word_timestamps,
            )

            # Write SRT file
            srt_writer = get_writer("srt", str(output_dir))
            srt_writer(result, srt_filename, {})
            print(f"  ✓ {srt_path.name}")

            # Write plain text file
            txt_writer = get_writer("txt", str(output_dir))
            txt_writer(result, txt_filename, {})
            print(f"  ✓ {txt_path.name}")
        else:
            print(f"Skipping (already exists): {filename_stem}")


if __name__ == "__main__":
    typer.run(main)
