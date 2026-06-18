"""
Hourly SKU data integration demo for a Windows server.

This script is designed for a local Windows Task Scheduler job or a long-running
demo process. It checks supplier files and a catalog API source, refreshes the
integrated SKU dataset when inputs change, and writes an anonymized output CSV.

Real client connection details are intentionally omitted. Configure paths and
API credentials with environment variables, or run the script as-is in demo mode.

Recommended production pattern on Windows:
    python hourly_sku_data_update_demo.py --run-once

Schedule that command hourly with Windows Task Scheduler. The optional
--loop-hourly mode is included for demos, but Task Scheduler is easier to
monitor and recover in production.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

try:
    import chardet
except ImportError:  # pragma: no cover - demo fallback for minimal installs
    chardet = None


APP_NAME = "hourly_sku_data_update_demo"


def env_path(name: str, default: str) -> Path:
    """Return a configurable filesystem path from an environment variable.

    Windows server deployments normally differ by environment: development,
    staging, and production often use different mounted drives or folders. This
    helper keeps those paths outside the code while still providing safe demo
    defaults.
    """
    return Path(os.getenv(name, default)).expanduser()


class Settings:
    """Runtime configuration for the hourly SKU sync process.

    The values are read at process start from environment variables. This keeps
    credentials and server-specific paths out of the script, which is important
    when the same file is used for portfolio review, local testing, and a real
    Windows Task Scheduler deployment.
    """

    # Base folders are separated by purpose so operations teams can archive logs,
    # inspect raw inputs, and consume outputs without mixing transient state.
    base_dir = env_path("SKU_SYNC_BASE_DIR", r"C:\sku_sync_demo")
    raw_dir = env_path("SKU_SYNC_RAW_DIR", str(base_dir / "raw"))
    output_dir = env_path("SKU_SYNC_OUTPUT_DIR", str(base_dir / "output"))
    state_dir = env_path("SKU_SYNC_STATE_DIR", str(base_dir / "state"))
    log_dir = env_path("SKU_SYNC_LOG_DIR", str(base_dir / "logs"))

    # File-feed inputs. In production these can point to SFTP landing folders,
    # mounted network shares, or any local path populated by upstream jobs.
    source_a_path = env_path(
        "SKU_SOURCE_A_PATH",
        str(raw_dir / "source_a_inventory.csv"),
    )
    source_b_path = env_path(
        "SKU_SOURCE_B_PATH",
        str(raw_dir / "source_b_inventory.txt"),
    )

    # API input. The demo deliberately uses a generic bearer-token pattern
    # without hard-coded endpoint or credential details.
    catalog_api_url = os.getenv("SKU_CATALOG_API_URL", "")
    catalog_api_token = os.getenv("SKU_CATALOG_API_TOKEN", "")
    api_timeout_seconds = int(os.getenv("SKU_API_TIMEOUT_SECONDS", "30"))
    api_retries = int(os.getenv("SKU_API_RETRIES", "3"))
    demo_mode = os.getenv("SKU_DEMO_MODE", "1") == "1"

    # State files allow the hourly job to skip work when no source changed.
    state_path = state_dir / "last_successful_run.json"
    output_path = output_dir / "sku_inventory_latest.csv"
    api_snapshot_path = raw_dir / "catalog_api_last_response.json"


def configure_logging(settings: Settings) -> logging.Logger:
    """Configure console and rotating-file logging.

    On a Windows server this log is the first place to check after a scheduled
    run. Rotating logs prevent the task from filling disk over time while still
    keeping recent execution history available for support and audit review.
    """
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = RotatingFileHandler(
        settings.log_dir / f"{APP_NAME}.log",
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


def ensure_demo_inputs(settings: Settings, logger: logging.Logger) -> None:
    """Create local anonymized input files when running without real feeds.

    The demo files mirror the same structural issues as the original feeds:
    headerless CSV data, European decimal commas, pipe-delimited supplier data,
    missing EAN values, and mismatched product coverage.
    """
    settings.raw_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.state_dir.mkdir(parents=True, exist_ok=True)

    # In production mode, source files are expected to be delivered by upstream
    # systems. The script should not generate demo data in that case.
    if not settings.demo_mode:
        return

    if not settings.source_a_path.exists():
        logger.info("Creating demo Source A file: %s", settings.source_a_path)
        rows = [
            [
                "12345678",
                "Hydrating Gel 50ml",
                "Supplier Alpha",
                "12,50",
                "8000000000012",
                "9,10",
                "",
                "",
                24,
                "",
                "",
                "",
                "",
                "",
                22,
                "SKU-A-001",
            ],
            [
                "23456789",
                "Vitamin C Tablets",
                "Supplier Alpha",
                "18,90",
                "8000000000029",
                "13,75",
                "",
                "",
                8,
                "",
                "",
                "",
                "",
                "",
                10,
                "SKU-A-002",
            ],
            [
                "34567890",
                "Digital Thermometer",
                "Supplier Alpha",
                "21,00",
                "8000000000036",
                "16,40",
                "",
                "",
                0,
                "",
                "",
                "",
                "",
                "",
                22,
                "SKU-A-003",
            ],
        ]
        pd.DataFrame(rows).to_csv(
            settings.source_a_path,
            sep=";",
            header=False,
            index=False,
            encoding="utf-8",
        )

    if not settings.source_b_path.exists():
        logger.info("Creating demo Source B file: %s", settings.source_b_path)
        lines = [
            "AIC000001|8000000000012|012345678|Supplier Beta|Hydrating Gel 50ml|19|9.40|22|12.50|SKU-B-001|Y|",
            "AIC000002|8000000000029|023456789|Supplier Beta|Vitamin C Tablets|10|13.10|10|18.90|SKU-B-002|Y|",
            "AIC000003|             |034567890|Supplier Beta|Digital Thermometer|4|16.90|22|21.00|SKU-B-003|Y|",
        ]
        settings.source_b_path.write_text("\n".join(lines), encoding="utf-8")


def detect_encoding(path: Path, sample_size: int = 100_000) -> str:
    """Detect a text file's encoding before reading it with pandas.

    Supplier feeds often arrive from different systems and may not all use
    UTF-8. Detecting encoding reduces avoidable failures and mojibake in product
    descriptions. If chardet is not installed, UTF-8 is used as a practical
    default for the demo.
    """
    if chardet is None:
        return "utf-8"
    raw = path.read_bytes()[:sample_size]
    result = chardet.detect(raw)
    return result.get("encoding") or "utf-8"


def normalize_product_id(series: pd.Series, width: int = 9) -> pd.Series:
    """Normalize product IDs to zero-padded strings for reliable joins.

    Product identifiers are business keys. Treating them as numbers can strip
    leading zeros and cause false non-matches, so every source is converted to a
    fixed-width text representation before merging.
    """
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.strip().str.zfill(width)


def parse_decimal(series: pd.Series) -> pd.Series:
    """Parse decimal values from feeds that may use comma separators."""
    return pd.to_numeric(series.astype(str).str.replace(",", ".", regex=False), errors="coerce")


def clean_text(series: pd.Series) -> pd.Series:
    """Trim text fields and convert empty strings into missing values."""
    return series.astype(str).str.strip().replace({"": np.nan, "nan": np.nan})


def file_fingerprint(path: Path) -> dict[str, Any]:
    """Return a stable fingerprint for a local input file.

    The hourly process uses this metadata to decide whether a file changed since
    the previous successful run. The SHA-256 hash is more reliable than modified
    timestamps alone when files are copied or re-saved by external systems.
    """
    if not path.exists():
        return {"exists": False, "path": str(path)}

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    stat = path.stat()
    return {
        "exists": True,
        "path": str(path),
        "size": stat.st_size,
        "modified_utc": int(stat.st_mtime),
        "sha256": digest.hexdigest(),
    }


def stable_payload_hash(payload: Any) -> str:
    """Hash an API payload after deterministic JSON serialization."""
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_state(path: Path) -> dict[str, Any]:
    """Load the previous successful run state, if one exists."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict[str, Any]) -> None:
    """Persist successful-run metadata for the next hourly check."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def fetch_catalog_api(settings: Settings, logger: logging.Logger) -> list[dict[str, Any]]:
    """
    Fetch catalog records from an API source.

    Expected real API response shape for this demo:
        {
          "products": [
            {
              "product_id": "012345678",
              "aic": "AIC000001",
              "ean": "8000000000012",
              "description": "Product name",
              "supplier": "Catalog Brand",
              "catalog_qty": 21,
              "catalog_unit_price": 9.25
            }
          ]
        }

    If SKU_CATALOG_API_URL is not set, demo records are returned instead.
    """
    # Portfolio/demo mode: show the API contract without exposing a real endpoint.
    if not settings.catalog_api_url:
        logger.info("SKU_CATALOG_API_URL not set; using anonymized demo API payload")
        return [
            {
                "product_id": "012345678",
                "aic": "AIC000001",
                "ean": "8000000000012",
                "description": "Hydrating Gel 50ml",
                "supplier": "Catalog Brand A",
                "catalog_qty": 21,
                "catalog_unit_price": 9.25,
            },
            {
                "product_id": "023456789",
                "aic": "AIC000002",
                "ean": "8000000000029",
                "description": "Vitamin C Tablets",
                "supplier": "Catalog Brand B",
                "catalog_qty": 7,
                "catalog_unit_price": 13.55,
            },
            {
                "product_id": "099999999",
                "aic": "AIC000999",
                "ean": "8000000000999",
                "description": "Catalog Only Product",
                "supplier": "Catalog Brand Z",
                "catalog_qty": 3,
                "catalog_unit_price": 8.90,
            },
        ]

    headers = {"Accept": "application/json"}
    if settings.catalog_api_token:
        headers["Authorization"] = f"Bearer {settings.catalog_api_token}"

    # API calls are retried because scheduled jobs should tolerate temporary
    # network or upstream-service issues. Persistent failures are raised so the
    # scheduler/log monitor can surface them.
    last_error: Exception | None = None
    for attempt in range(1, settings.api_retries + 1):
        try:
            logger.info("Calling catalog API, attempt %s/%s", attempt, settings.api_retries)
            request = Request(settings.catalog_api_url, headers=headers, method="GET")
            with urlopen(request, timeout=settings.api_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            products = payload.get("products", payload)
            if not isinstance(products, list):
                raise ValueError("Catalog API response must be a list or contain a 'products' list")
            settings.api_snapshot_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            return products
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            logger.warning("Catalog API attempt failed: %s", exc)
            time.sleep(min(2**attempt, 30))

    raise RuntimeError(f"Catalog API failed after {settings.api_retries} attempts") from last_error


def read_source_a(path: Path) -> pd.DataFrame:
    """Read and normalize the semicolon-delimited supplier CSV feed.

    Source A is modeled as a headerless export with more columns than the
    integration needs. The function assigns a schema, selects relevant columns,
    normalizes identifiers, and converts commercial values into numeric fields.
    """
    columns = [
        "product_id",
        "description",
        "supplier",
        "list_price",
        "ean",
        "unit_price",
        "unused_1",
        "unused_2",
        "qty",
        "unused_3",
        "unused_4",
        "unused_5",
        "unused_6",
        "unused_7",
        "vat_rate",
        "sku",
    ]
    df = pd.read_csv(
        path,
        sep=";",
        header=None,
        names=columns,
        usecols=[
            "product_id",
            "description",
            "supplier",
            "list_price",
            "ean",
            "unit_price",
            "qty",
            "vat_rate",
            "sku",
        ],
        encoding=detect_encoding(path),
        dtype={"product_id": "string", "ean": "string", "sku": "string"},
    )

    # Normalize immediately after ingestion so later business rules can assume a
    # consistent schema regardless of source-specific quirks.
    df["product_id"] = normalize_product_id(df["product_id"])
    df["description"] = clean_text(df["description"])
    df["supplier"] = clean_text(df["supplier"])
    df["ean"] = clean_text(df["ean"]).fillna("UNKNOWN")
    df["list_price"] = parse_decimal(df["list_price"])
    df["unit_price"] = parse_decimal(df["unit_price"])
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0).astype(int)
    df["vat_rate"] = pd.to_numeric(df["vat_rate"], errors="coerce")
    return df


def read_source_b(path: Path) -> pd.DataFrame:
    """Read and normalize the pipe-delimited secondary supplier feed.

    Source B carries the AIC/SKU identifiers used in the supplier-to-catalog
    reconciliation. Missing EAN values are retained as UNKNOWN rather than
    dropping the row, because the product ID is the primary join key.
    """
    columns = [
        "aic",
        "ean",
        "product_id",
        "supplier",
        "description",
        "qty",
        "unit_price",
        "vat_rate",
        "list_price",
        "sku",
        "feed_flag",
        "unused",
    ]
    df = pd.read_csv(
        path,
        sep="|",
        header=None,
        names=columns,
        encoding=detect_encoding(path),
        dtype="string",
    ).drop(columns="unused")

    # Source B arrives in a fixed field order, so the primary control is parsing
    # every field into the intended type before reconciliation.
    df["product_id"] = normalize_product_id(df["product_id"])
    df["description"] = clean_text(df["description"])
    df["supplier"] = clean_text(df["supplier"])
    df["ean"] = clean_text(df["ean"]).replace({"             ": np.nan}).fillna("UNKNOWN")
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0).astype(int)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["list_price"] = pd.to_numeric(df["list_price"], errors="coerce")
    df["vat_rate"] = pd.to_numeric(df["vat_rate"], errors="coerce")
    return df


def read_catalog_api(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Convert catalog API records into the standard catalog DataFrame.

    The validation here intentionally checks the API contract before the merge.
    If a field is missing, the run fails with a clear message rather than
    producing a partial or misleading availability file.
    """
    df = pd.DataFrame(records)
    required = [
        "product_id",
        "aic",
        "ean",
        "description",
        "supplier",
        "catalog_qty",
        "catalog_unit_price",
    ]
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"Catalog API records missing required fields: {missing}")

    # Keep only the fields required by the reconciliation layer. This shields the
    # downstream model from unrelated API attributes that may change over time.
    df = df[required].copy()
    df["product_id"] = normalize_product_id(df["product_id"])
    df["description"] = clean_text(df["description"])
    df["supplier"] = clean_text(df["supplier"])
    df["ean"] = clean_text(df["ean"])
    df["catalog_qty"] = pd.to_numeric(df["catalog_qty"], errors="coerce").fillna(0).astype(int)
    df["catalog_unit_price"] = pd.to_numeric(df["catalog_unit_price"], errors="coerce")
    return df


def validate_inputs(source_a: pd.DataFrame, source_b: pd.DataFrame, catalog: pd.DataFrame) -> None:
    """Run pre-merge data quality checks.

    Duplicate product IDs would create many-to-many joins and inflated row
    counts. Negative prices or quantities are treated as impossible operational
    values for this workflow and stop the update before export.
    """
    # The product ID is the shared business key across all three sources.
    for source_name, df in [
        ("Source A", source_a),
        ("Source B", source_b),
        ("Catalog API", catalog),
    ]:
        duplicates = df.duplicated("product_id").sum()
        if duplicates:
            raise ValueError(f"{source_name} has {duplicates} duplicate product_id values")

    # Quantity and price checks are deliberately strict. If a source sends
    # corrections as negative values, that should be modeled explicitly rather
    # than accepted into the ecommerce availability layer.
    for source_name, df, qty_col, price_col in [
        ("Source A", source_a, "qty", "unit_price"),
        ("Source B", source_b, "qty", "unit_price"),
        ("Catalog API", catalog, "catalog_qty", "catalog_unit_price"),
    ]:
        if (df[qty_col] < 0).any():
            raise ValueError(f"{source_name} contains negative quantity values")
        if (df[price_col] < 0).any():
            raise ValueError(f"{source_name} contains negative price values")


def build_integrated_dataset(
    source_a: pd.DataFrame,
    source_b: pd.DataFrame,
    catalog: pd.DataFrame,
) -> pd.DataFrame:
    """Build the final SKU-level availability and review dataset.

    The integration happens in two stages:
    1. Reconcile supplier feeds using conservative price and stock rules.
    2. Outer-join the supplier view to the catalog to expose coverage gaps.

    The returned DataFrame is designed for reporting, ecommerce availability
    checks, and operational triage.
    """
    # First reconcile supplier feeds on the standardized business key. The
    # validate option makes unexpected duplicate-key behavior fail loudly.
    supplier_merge = pd.merge(
        source_b,
        source_a,
        on="product_id",
        how="inner",
        suffixes=("_b", "_a"),
        validate="one_to_one",
    )

    # Business rule: select the higher unit price and lower quantity. This is a
    # conservative ecommerce stance when suppliers disagree.
    supplier_merge["selected_unit_price"] = supplier_merge[["unit_price_b", "unit_price_a"]].max(axis=1)
    supplier_merge["sellable_qty"] = supplier_merge[["qty_b", "qty_a"]].min(axis=1)
    supplier_merge["selected_price_source"] = np.where(
        supplier_merge["unit_price_b"] >= supplier_merge["unit_price_a"],
        "Source B",
        "Source A",
    )
    supplier_merge["stock_constraint_source"] = np.where(
        supplier_merge["qty_b"] <= supplier_merge["qty_a"],
        "Source B",
        "Source A",
    )
    supplier_merge["price_gap"] = (supplier_merge["unit_price_b"] - supplier_merge["unit_price_a"]).round(2)

    # Difference metrics explain why a SKU may need commercial or operational
    # review even when it successfully matched across supplier feeds.
    supplier_merge["price_gap_pct"] = np.where(
        supplier_merge[["unit_price_b", "unit_price_a"]].min(axis=1) > 0,
        supplier_merge["price_gap"].abs()
        / supplier_merge[["unit_price_b", "unit_price_a"]].min(axis=1),
        np.nan,
    ).round(4)
    supplier_merge["stock_gap"] = supplier_merge["qty_b"] - supplier_merge["qty_a"]

    # Reduce the supplier merge to the canonical operational view before joining
    # it to catalog metadata.
    supplier_view = supplier_merge[
        [
            "product_id",
            "aic",
            "ean_b",
            "sku_b",
            "description_b",
            "supplier_b",
            "selected_unit_price",
            "sellable_qty",
            "selected_price_source",
            "stock_constraint_source",
            "price_gap",
            "price_gap_pct",
            "stock_gap",
        ]
    ].rename(
        columns={
            "ean_b": "ean",
            "sku_b": "sku",
            "description_b": "description",
            "supplier_b": "supplier",
        }
    )

    # The outer join is intentional: a client needs to see missing mappings, not
    # just the products that matched cleanly.
    merged = pd.merge(
        supplier_view,
        catalog,
        on="product_id",
        how="outer",
        suffixes=("_supplier", "_catalog"),
        indicator=True,
        validate="one_to_one",
    )
    merged["aic"] = merged["aic_supplier"].combine_first(merged["aic_catalog"])
    merged["ean"] = merged["ean_supplier"].combine_first(merged["ean_catalog"])
    merged["sku"] = merged["sku"].fillna("CATALOG_ONLY")
    merged["description"] = merged["description_supplier"].combine_first(merged["description_catalog"])
    merged["supplier"] = merged["supplier_supplier"].combine_first(merged["supplier_catalog"])
    merged["selected_unit_price"] = merged["selected_unit_price"].combine_first(merged["catalog_unit_price"])
    merged["sellable_qty"] = merged["sellable_qty"].combine_first(merged["catalog_qty"]).fillna(0).astype(int)

    # Translate pandas merge labels into business-facing source coverage states.
    merged["source_coverage"] = merged["_merge"].map(
        {
            "both": "supplier_and_catalog",
            "left_only": "supplier_only",
            "right_only": "catalog_only",
        }
    )

    # Keep the exported model compact and focused on fields a business user can
    # interpret or act on.
    analytics = merged[
        [
            "product_id",
            "aic",
            "ean",
            "sku",
            "description",
            "supplier",
            "selected_unit_price",
            "sellable_qty",
            "source_coverage",
            "selected_price_source",
            "stock_constraint_source",
            "price_gap",
            "price_gap_pct",
            "stock_gap",
        ]
    ].sort_values("product_id").reset_index(drop=True)

    # Availability, catalog alignment, and review priority are lightweight
    # business rules that convert raw reconciliation results into action queues.
    analytics["availability_status"] = np.select(
        [
            analytics["sellable_qty"].eq(0),
            analytics["sellable_qty"].between(1, 5),
            analytics["sellable_qty"].gt(5),
        ],
        ["out_of_stock", "low_stock", "in_stock"],
        default="unknown",
    )
    analytics["catalog_alignment_status"] = analytics["source_coverage"].map(
        {
            "supplier_and_catalog": "matched",
            "supplier_only": "missing_from_catalog",
            "catalog_only": "missing_from_supplier_feeds",
        }
    )
    analytics["sellable_inventory_value"] = (
        analytics["selected_unit_price"] * analytics["sellable_qty"]
    ).round(2)
    analytics["price_gap_flag"] = analytics["price_gap_pct"].fillna(0).gt(0.05)
    analytics["stock_gap_flag"] = analytics["stock_gap"].fillna(0).abs().gt(5)
    analytics["catalog_gap_flag"] = analytics["source_coverage"].ne("supplier_and_catalog")
    analytics["review_priority"] = np.select(
        [
            analytics["catalog_gap_flag"],
            analytics["availability_status"].eq("out_of_stock"),
            analytics["price_gap_flag"] | analytics["stock_gap_flag"],
        ],
        ["catalog_mapping", "stock_replenishment", "commercial_review"],
        default="no_action",
    )
    return analytics


def source_snapshot(settings: Settings, catalog_records: list[dict[str, Any]]) -> dict[str, Any]:
    """Collect fingerprints for all inputs used in a run.

    Local files are fingerprinted by metadata and SHA-256 content hash. The API
    input is hashed from the normalized JSON payload. Together, these values
    represent the source state that produced the current output.
    """
    return {
        "source_a": file_fingerprint(settings.source_a_path),
        "source_b": file_fingerprint(settings.source_b_path),
        "catalog_api_hash": stable_payload_hash(catalog_records),
    }


def should_refresh(state: dict[str, Any], snapshot: dict[str, Any], output_path: Path) -> bool:
    """Return True when the output should be rebuilt.

    A rebuild is required if there is no output yet or if the current input
    snapshot differs from the last successful snapshot.
    """
    if not output_path.exists():
        return True
    return state.get("last_snapshot") != snapshot


def run_once(settings: Settings, logger: logging.Logger, force: bool = False) -> bool:
    """Execute a single source-check and update cycle.

    This is the function a Windows Task Scheduler job should run hourly. It
    prepares demo inputs if needed, checks whether sources changed, validates
    inputs, rebuilds the integrated dataset, and persists state for the next run.

    Returns:
        True if the output CSV was rebuilt; False if no source changes were
        detected and the existing output was reused.
    """
    ensure_demo_inputs(settings, logger)

    logger.info("Checking configured SKU sources")
    catalog_records = fetch_catalog_api(settings, logger)
    snapshot = source_snapshot(settings, catalog_records)
    state = load_state(settings.state_path)

    # Avoid unnecessary work and downstream file churn when the hourly run sees
    # exactly the same supplier files and API payload as the previous success.
    if not force and not should_refresh(state, snapshot, settings.output_path):
        logger.info("No source changes detected; output is already current")
        return False

    # Read and validate all sources before writing anything. This prevents a bad
    # feed from replacing the last known-good output.
    logger.info("Reading and validating inputs")
    source_a = read_source_a(settings.source_a_path)
    source_b = read_source_b(settings.source_b_path)
    catalog = read_catalog_api(catalog_records)
    validate_inputs(source_a, source_b, catalog)

    logger.info("Building integrated SKU dataset")
    analytics = build_integrated_dataset(source_a, source_b, catalog)

    # Only after a successful integration do we overwrite the public output and
    # update the state file.
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    analytics.to_csv(settings.output_path, index=False)

    save_state(
        settings.state_path,
        {
            "last_success_epoch": int(time.time()),
            "last_snapshot": snapshot,
            "last_output_path": str(settings.output_path),
            "last_row_count": int(len(analytics)),
        },
    )

    logger.info(
        "SKU dataset updated: rows=%s output=%s",
        len(analytics),
        settings.output_path,
    )
    return True


def parse_args() -> argparse.Namespace:
    """Parse command-line options for scheduled or demo execution."""
    parser = argparse.ArgumentParser(description="Hourly SKU data integration demo")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--run-once",
        action="store_true",
        help="Run one check/update cycle. Recommended for Windows Task Scheduler.",
    )
    mode.add_argument(
        "--loop-hourly",
        action="store_true",
        help="Run continuously and check sources every hour.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild the output even if source fingerprints have not changed.",
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=3600,
        help="Loop interval for --loop-hourly. Defaults to 3600 seconds.",
    )
    return parser.parse_args()


def main() -> int:
    """Program entry point.

    By default the script performs one update cycle. The --loop-hourly option is
    useful for demonstrations, while --run-once is the recommended production
    mode for Windows Task Scheduler.
    """
    args = parse_args()
    settings = Settings()
    logger = configure_logging(settings)

    if args.loop_hourly:
        # Long-running mode is included for local demos. For production, an
        # external scheduler gives better visibility, restart behavior, and
        # operational control.
        logger.info("Starting hourly loop with interval_seconds=%s", args.interval_seconds)
        while True:
            try:
                run_once(settings, logger, force=args.force)
            except Exception:
                logger.exception("SKU update cycle failed")
            time.sleep(args.interval_seconds)

    try:
        updated = run_once(settings, logger, force=args.force)
        logger.info("Completed run_once; updated=%s", updated)
        return 0
    except Exception:
        logger.exception("SKU update failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
