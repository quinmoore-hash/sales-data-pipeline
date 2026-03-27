"""CSV processing module — replaces ``process_csv.sh``.

Filters sales data by region and generates a summary report.  Uses the
stdlib :mod:`csv` module instead of ``awk``, which correctly handles quoted
commas inside fields.
"""

from __future__ import annotations

import csv
import logging
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Optional

from sales_data_pipeline.config import PipelineConfig

logger = logging.getLogger("sales_data_pipeline")


def process_csv(config: PipelineConfig, input_file: Path) -> Optional[Path]:
    """Filter *input_file* by region and write filtered CSV + summary.

    Returns the path to the filtered CSV, or ``None`` if zero rows matched.
    """
    today = date.today().isoformat()
    filtered_path = config.processed_dir / f"sales_{config.region}_{today}.csv"
    summary_path = config.processed_dir / f"summary_{config.region}_{today}.txt"

    if not input_file.is_file():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    logger.info("Processing CSV file: %s", input_file.name)

    # Read all rows via DictReader (handles quoted commas correctly)
    with open(input_file, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames
        if fieldnames is None:
            raise ValueError(f"CSV file has no header row: {input_file}")
        all_rows = list(reader)

    total_rows = len(all_rows)

    # Identify the column names by position for resilience.
    # Spec says: region=col 1, product=col 2, revenue=col 4 (0-indexed).
    # But we use DictReader column names from the header.
    region_col = fieldnames[1]
    product_col = fieldnames[2]
    revenue_col = fieldnames[4]

    # Filter by region
    matched_rows = [
        row for row in all_rows
        if row[region_col] == config.region
    ]

    logger.info(
        "Filtered %d rows, %d matched region=%s",
        total_rows, len(matched_rows), config.region,
    )

    if not matched_rows:
        logger.warning("No data found for region: %s", config.region)
        filtered_path.unlink(missing_ok=True)
        return None

    # Write filtered CSV
    with open(filtered_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matched_rows)

    # Calculate totals
    total_revenue = sum(float(row[revenue_col]) for row in matched_rows)
    logger.info("Summary — Total revenue for %s: $%.2f", config.region, total_revenue)

    # Per-product breakdown
    product_revenue: dict[str, float] = defaultdict(float)
    product_count: dict[str, int] = defaultdict(int)
    for row in matched_rows:
        product = row[product_col]
        product_revenue[product] += float(row[revenue_col])
        product_count[product] += 1

    # Write summary file (same format as process_csv.sh lines 53-64)
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("=== Sales Summary ===\n")
        fh.write(f"Region: {config.region}\n")
        fh.write(f"Date: {today}\n")
        fh.write(f"Records: {len(matched_rows)}\n")
        fh.write(f"Total Revenue: ${total_revenue:.2f}\n")
        fh.write("\n")
        fh.write("Revenue by Product:\n")
        for product in product_revenue:
            fh.write(
                f"  {product:<12s} {product_count[product]} units  "
                f"${product_revenue[product]:.2f}\n"
            )

    logger.info("Summary written to %s", summary_path)
    return filtered_path
