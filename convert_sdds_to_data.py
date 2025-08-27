#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
convert_sdds_to_data.py
-----------------------
Scan a folder for .sdds files and convert each to .data (parentheses format),
saving next to the source file.

Requires: bpm_data_comparer.py (providing BPMDataSDDS with .to_data()).
Dependencies: numpy, pandas

Usage examples:
  python convert_sdds_to_data.py /path/to/folder
  python convert_sdds_to_data.py /path/to/folder -r           # recursive
  python convert_sdds_to_data.py . --pattern "*.SDDS"          # custom glob
  python convert_sdds_to_data.py . --suffix "_conv"            # add suffix
  python convert_sdds_to_data.py . --fmt "{:.7f}" --wrap 16    # fixed decimals + wrap lines
  python convert_sdds_to_data.py . --dry-run                   # just show what would happen
"""

from __future__ import annotations
import argparse
from pathlib import Path
import sys
from typing import List, Tuple

# Import the class we wrote earlier
try:
    from bpm_data_comparer import BPMDataSDDS
except ImportError as e:
    print("ERROR: Could not import 'BPMDataSDDS' from bpm_data_comparer.py.\n"
          "Make sure bpm_data_comparer.py is in the same folder or on PYTHONPATH.", file=sys.stderr)
    raise

# Function to find all matching files
def find_files(root: Path, pattern: str, recursive: bool) -> List[Path]:
    if recursive:
        return sorted(root.rglob(pattern))
    return sorted(root.glob(pattern))

# Function to convert one .sdds file to .data
def convert_one(
    sdds_path: Path,
    include_z: bool,
    fmt: str,
    wrap: int | None,
    suffix: str | None,
    overwrite: bool,
    dry_run: bool,
    scale: float, 
) -> Tuple[Path, Path | None, str]:
    """
    Convert one .sdds file to .data.

    Returns (src, dst, status):
      status in {"ok", "skipped_exists", "error", "dry_run"}
    """
    if not sdds_path.is_file():
        return (sdds_path, None, "error")

    # Determine output path (same folder)
    if suffix:
        dst = sdds_path.with_name(f"{sdds_path.stem}{suffix}.data")
    else:
        dst = sdds_path.with_suffix(".data")

    if dst.exists() and not overwrite and not dry_run:
        return (sdds_path, dst, "skipped_exists")

    try:
        if dry_run:
            return (sdds_path, dst, "dry_run")

        bpm = BPMDataSDDS.from_file(str(sdds_path))
        bpm.to_data(str(dst), include_z=include_z, fmt=fmt, scale=scale,
                    header_lines='"06/17/2024 17:50:17",3927635417,"2024-06-17_17:32:32.919_Tune",3927635412')  # No header lines in this case
        return (sdds_path, dst, "ok")
    except Exception as ex:  # noqa: BLE001 - report any conversion error
        return (sdds_path, dst, f"error: {ex}")


# Main function to parse arguments and run conversion
def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Convert .sdds files to .data (parentheses format) in place.")
    p.add_argument("folder", type=Path, help="Folder to scan for .sdds files.")
    p.add_argument("--pattern", default="*.sdds", help="Glob pattern to match (default: *.sdds).")
    p.add_argument("-r", "--recursive", action="store_true", help="Recurse into subfolders.")
    p.add_argument("--include-z", action="store_true", default=True,
                   help="Include z array in output (SDDS has only x,y; z will be zeros). Default: True.")
    p.add_argument("--no-include-z", dest="include_z", action="store_false",
                   help="Disable including z (it will still write a z-block of zeros for compatibility).")
    p.add_argument("--fmt", default="{:.7g}", help='Number format, e.g. "{:.7g}" or "{:.7f}".')
    p.add_argument("--wrap", type=int, default=None,
                   help="If set (e.g., 16), insert backslash-newline after every N values per array.")
    p.add_argument("--suffix", default=None,
                   help='Optional suffix for output base name (e.g., "_conv" -> file_conv.data).')
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing .data files.")
    p.add_argument("--dry-run", action="store_true", help="Show what would be converted, without writing files.")
    p.add_argument("--scale", type=float, default=1e0,
                   help="Scale factor for the data values (default: 1.0).")
    args = p.parse_args(argv)

    root = args.folder
    if not root.exists() or not root.is_dir():
        print(f"ERROR: {root} is not a folder.", file=sys.stderr)
        return 2

    files = find_files(root, args.pattern, args.recursive)
    if not files:
        print("No files matched.")
        return 0

    print(f"Found {len(files)} file(s). Converting...")
    ok = 0
    skipped = 0
    errors = 0
    dry = 0

    for src in files:
        src, dst, status = convert_one(
            src,
            include_z=args.include_z,
            fmt=args.fmt,
            wrap=args.wrap,
            suffix=args.suffix,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
            scale=args.scale
        )
        if status == "ok":
            ok += 1
            print(f"[OK] {src.name} -> {dst.name}")
        elif status == "skipped_exists":
            skipped += 1
            print(f"[SKIP] {src.name} -> {dst.name} (exists; use --overwrite or --suffix)")
        elif status == "dry_run":
            dry += 1
            print(f"[DRY] {src.name} -> {dst.name}")
        else:
            errors += 1
            print(f"[ERR] {src.name}: {status}")

    print("\nSummary:")
    print(f"  OK     : {ok}")
    print(f"  Skipped: {skipped}")
    print(f"  DryRun : {dry}")
    print(f"  Errors : {errors}")

    return 0 if errors == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
