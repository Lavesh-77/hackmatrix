"""Build a verified, flat ZIP for the Applied ML evaluation platform.

Example from the repository root::

    python tools/package_submission.py --output /tmp/opencode/candidate.zip

Only the three required inference files are packaged. Development data, tests,
training code, caches, and enclosing directories are never included.
"""

import argparse
import hashlib
import json
import stat
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "submission"
REQUIRED_FILES = {"solution.py", "features.py", "starter_model.json"}
OPTIONAL_FILES = {"README.md"}
ALLOWED_SUFFIXES = {".py", ".json", ".txt", ".md"}
MAX_FILES = 100
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 16 * 1024 * 1024
MAX_ARCHIVE_BYTES = 32 * 1024 * 1024


def collect_submission_files(source_dir):
    """Return the allowlisted top-level files after checking format/size rules."""
    if not source_dir.is_dir():
        raise ValueError(f"Submission source directory does not exist: {source_dir}")

    files = {}
    for path in sorted(source_dir.iterdir(), key=lambda item: item.name):
        if path.is_symlink():
            raise ValueError(f"Submission files cannot be symlinks: {path.name}")
        if not path.is_file():
            # Directory contents (including __pycache__) are never followed or zipped.
            continue
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            raise ValueError(f"Unsupported submission file extension: {path.name}")
        if path.name not in REQUIRED_FILES | OPTIONAL_FILES:
            raise ValueError(f"Unexpected submission file; review before packaging: {path.name}")
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError(f"Submission file exceeds 2 MiB: {path.name}")
        files[path.name] = path

    missing = REQUIRED_FILES - files.keys()
    if missing:
        raise ValueError(f"Missing required submission files: {', '.join(sorted(missing))}")
    if len(files) > MAX_FILES:
        raise ValueError("Submission exceeds the 100-file limit")
    total_bytes = sum(path.stat().st_size for path in files.values())
    if total_bytes > MAX_TOTAL_BYTES:
        raise ValueError("Submission exceeds the 16 MiB uncompressed limit")
    return files, total_bytes


def build_archive(source_dir, output_path):
    """Write and verify a flat archive; return its manifest."""
    source_dir = source_dir.resolve()
    output_path = output_path.resolve()
    if output_path == source_dir or source_dir in output_path.parents:
        raise ValueError("Write the archive outside the submission source directory")
    if output_path.exists():
        raise ValueError(f"Refusing to overwrite an existing archive: {output_path}")

    files, total_bytes = collect_submission_files(source_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(
        output_path, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name, path in files.items():
            archive.write(path, arcname=name)

    if output_path.stat().st_size > MAX_ARCHIVE_BYTES:
        output_path.unlink()
        raise ValueError("Compressed ZIP exceeds the 32 MiB upload limit")

    with zipfile.ZipFile(output_path, mode="r") as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if set(names) != set(files) or len(names) != len(files):
            raise ValueError("ZIP contents do not match the selected flat submission files")
        if any("/" in name or "\\" in name for name in names):
            raise ValueError("ZIP entries must be at the archive root; subfolders are forbidden")
        for entry in entries:
            mode = entry.external_attr >> 16
            if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
                raise ValueError(f"ZIP entry is not a regular file: {entry.filename}")
            if Path(entry.filename).suffix.lower() not in ALLOWED_SUFFIXES:
                raise ValueError(f"ZIP contains an unsupported file: {entry.filename}")
            if entry.file_size > MAX_FILE_BYTES:
                raise ValueError(f"ZIP entry exceeds 2 MiB: {entry.filename}")
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC verification failed")

    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    return {
        "archive": str(output_path),
        "archive_bytes": output_path.stat().st_size,
        "uncompressed_bytes": total_bytes,
        "files": sorted(files),
        "sha256": digest,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        manifest = build_archive(args.source, args.output)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
