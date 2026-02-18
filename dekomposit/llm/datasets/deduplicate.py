#!/usr/bin/env python3
"""Remove duplicate source sentences from translation datasets.

Keeps the first occurrence of each unique source sentence,
removes all subsequent duplicates.
"""

import sys
from pathlib import Path
from collections import OrderedDict


def deduplicate_tsv(filepath: Path, dry_run: bool = False) -> dict:
    """Remove duplicates from a TSV file.

    Args:
        filepath: Path to TSV file
        dry_run: If True, don't write changes, just report

    Returns:
        Dict with statistics
    """
    print(f"\n{'='*70}")
    print(f"Processing: {filepath.name}")
    print(f"{'='*70}")

    # Read file
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        print("⚠️  Empty file, skipping")
        return {"original": 0, "unique": 0, "removed": 0}

    # Extract header
    header = lines[0]
    data_lines = lines[1:]

    original_count = len(data_lines)
    print(f"Original pairs: {original_count}")

    # Deduplicate using OrderedDict (preserves first occurrence)
    seen_sources = OrderedDict()

    for line in data_lines:
        if '\t' not in line:
            continue

        parts = line.strip().split('\t')
        if len(parts) < 2:
            continue

        source = parts[0]

        # Keep first occurrence only
        if source not in seen_sources:
            seen_sources[source] = line

    unique_count = len(seen_sources)
    removed_count = original_count - unique_count

    print(f"Unique pairs:   {unique_count}")
    print(f"Duplicates:     {removed_count} ({removed_count/original_count*100:.1f}%)")

    # Show top duplicates
    if removed_count > 0:
        from collections import Counter
        sources = [line.split('\t')[0] for line in data_lines if '\t' in line]
        source_counts = Counter(sources)
        duplicates = {src: count for src, count in source_counts.items() if count > 1}

        if duplicates:
            print(f"\nTop duplicates removed:")
            for src, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {count-1}x: {src[:60]}...")

    # Write deduplicated file
    if not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(header)
            for line in seen_sources.values():
                f.write(line)
        print(f"\n✅ Saved deduplicated file")
    else:
        print(f"\n🔍 DRY RUN - No changes written")

    return {
        "original": original_count,
        "unique": unique_count,
        "removed": removed_count,
    }


def main():
    """Deduplicate all TSV files in automl directory."""

    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║              TRANSLATION DATASET DEDUPLICATOR                    ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    # Check for flags
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    force = "--force" in sys.argv or "-f" in sys.argv

    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be modified\n")
    else:
        print("\n⚠️  LIVE MODE - Files will be modified\n")
        if not force:
            response = input("Continue? [y/N]: ").strip().lower()
            if response != 'y':
                print("Cancelled.")
                return
        else:
            print("🔥 FORCE MODE - Proceeding without confirmation\n")

    # Find automl directory
    script_dir = Path(__file__).parent
    automl_dir = script_dir / "automl"

    if not automl_dir.exists():
        print(f"❌ Error: {automl_dir} not found")
        return

    # Process all TSV files
    tsv_files = sorted(automl_dir.glob("*.tsv"))

    if not tsv_files:
        print(f"❌ No TSV files found in {automl_dir}")
        return

    print(f"Found {len(tsv_files)} TSV files\n")

    # Process each file
    total_stats = {
        "original": 0,
        "unique": 0,
        "removed": 0,
    }

    for filepath in tsv_files:
        stats = deduplicate_tsv(filepath, dry_run)
        total_stats["original"] += stats["original"]
        total_stats["unique"] += stats["unique"]
        total_stats["removed"] += stats["removed"]

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total original pairs: {total_stats['original']}")
    print(f"Total unique pairs:   {total_stats['unique']}")
    print(f"Total duplicates:     {total_stats['removed']} "
          f"({total_stats['removed']/total_stats['original']*100:.1f}%)")

    if not dry_run:
        print(f"\n✅ All files deduplicated successfully!")
    else:
        print(f"\n🔍 Dry run complete. Run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
