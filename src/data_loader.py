"""DataLoader: loads transactions from CSV/JSON sample datasets."""

import csv
import json
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd

from src.models import REQUIRED_FIELDS, VALID_CATEGORIES, VALID_CHANNELS, Transaction

logger = logging.getLogger(__name__)


class DataLoader:
    """Load and validate transactions from CSV or JSON files."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_from_csv(self, file_path: str) -> List[Transaction]:
        """Load transactions from a CSV file.

        Args:
            file_path: Path to the CSV file.

        Returns:
            List of valid Transaction objects.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is empty or contains no valid records.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        try:
            df = pd.read_csv(path)
        except Exception as exc:
            raise ValueError(f"Invalid CSV format: {exc}") from exc

        records = df.to_dict(orient="records")
        return self._process_records(records, file_path)

    def load_from_json(self, file_path: str) -> List[Transaction]:
        """Load transactions from a JSON file.

        Args:
            file_path: Path to the JSON file.

        Returns:
            List of valid Transaction objects.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is empty or contains no valid records.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        try:
            with open(path, "r", encoding="utf-8") as fh:
                records = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON format: {exc}") from exc

        if not isinstance(records, list):
            raise ValueError("JSON file must contain a top-level array of transactions")

        return self._process_records(records, file_path)

    def load(self, file_path: str) -> List[Transaction]:
        """Auto-detect format and load transactions.

        Args:
            file_path: Path to CSV or JSON file.

        Returns:
            List of valid Transaction objects.
        """
        ext = Path(file_path).suffix.lower()
        if ext == ".csv":
            return self.load_from_csv(file_path)
        elif ext == ".json":
            return self.load_from_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Use .csv or .json")

    def validate_transaction(self, data: Dict) -> bool:
        """Validate that a transaction dict has all required fields with correct types.

        Args:
            data: Dictionary of raw transaction fields.

        Returns:
            True if valid, False otherwise.
        """
        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in data or self._is_empty(data[field]):
                logger.warning("Missing required field '%s' in record %s", field, data.get("txn_id", "UNKNOWN"))
                return False

        # Amount validation
        try:
            amount = float(data["amount"])
            if math.isnan(amount) or math.isinf(amount):
                raise ValueError("NaN or Inf")
            if amount <= 0 or amount > 1_000_000:
                logger.warning("Invalid amount %s in record %s", data["amount"], data["txn_id"])
                return False
        except (ValueError, TypeError):
            logger.warning("Non-numeric amount in record %s", data.get("txn_id", "UNKNOWN"))
            return False

        # Budget validation
        try:
            budget = float(data["monthly_budget_remaining"])
            if math.isnan(budget) or math.isinf(budget):
                raise ValueError("NaN or Inf")
        except (ValueError, TypeError):
            logger.warning("Non-numeric budget in record %s", data.get("txn_id", "UNKNOWN"))
            return False

        # Timestamp validation
        try:
            self._parse_timestamp(data["timestamp"])
        except (ValueError, TypeError):
            logger.warning("Invalid timestamp in record %s", data.get("txn_id", "UNKNOWN"))
            return False

        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_records(self, records: List[Dict], source: str) -> List[Transaction]:
        """Convert raw dicts to Transaction objects, skipping invalid ones."""
        transactions: List[Transaction] = []
        skipped = 0

        # Auto-fill missing fields with defaults
        records = [self._fill_defaults(r, idx) for idx, r in enumerate(records)]

        for record in records:
            if not self.validate_transaction(record):
                skipped += 1
                continue
            try:
                txn = Transaction(
                    txn_id=str(record["txn_id"]),
                    user_id=str(record["user_id"]),
                    timestamp=self._parse_timestamp(record["timestamp"]),
                    amount=float(record["amount"]),
                    category=str(record["category"]),
                    recipient_status=str(record["recipient_status"]),
                    monthly_budget_remaining=float(record["monthly_budget_remaining"]),
                    device_id=str(record["device_id"]),
                    location=str(record["location"]),
                    channel=str(record["channel"]),
                )
                transactions.append(txn)
            except Exception as exc:
                skipped += 1
                logger.warning("Failed to create Transaction from record %s: %s", record.get("txn_id"), exc)

        if not transactions:
            sample = records[0] if records else {}
            present = list(sample.keys())
            raise ValueError(
                f"No valid transactions found in {source}. "
                f"Skipped {skipped}/{len(records)} records. "
                f"Columns found: {present}. "
                f"Check that 'timestamp', 'amount', and 'category' have valid values."
            )

        if skipped:
            logger.warning("Skipped %d invalid records out of %d total in %s", skipped, len(records), source)
        logger.info("Loaded %d valid transactions from %s", len(transactions), source)
        return transactions

    @staticmethod
    def _fill_defaults(record: Dict, index: int = 0) -> Dict:
        """Fill missing fields with sensible defaults so minimal CSVs work.

        At minimum the CSV needs: timestamp, amount, category.
        Everything else is auto-generated.
        """
        import uuid
        import random

        filled = dict(record)  # shallow copy

        if "txn_id" not in filled or DataLoader._is_empty(filled.get("txn_id")):
            filled["txn_id"] = f"TXN_{index + 1:05d}"

        if "user_id" not in filled or DataLoader._is_empty(filled.get("user_id")):
            filled["user_id"] = "USR_DEFAULT"

        if "recipient_status" not in filled or DataLoader._is_empty(filled.get("recipient_status")):
            # If the CSV has an 'is_impulsive' column, use it as a proxy
            if "is_impulsive" in filled:
                is_imp = str(filled.get("is_impulsive", "")).strip().lower()
                filled["recipient_status"] = "new" if is_imp in ("1", "true", "yes") else "existing"
            else:
                filled["recipient_status"] = "existing"

        if "monthly_budget_remaining" not in filled or DataLoader._is_empty(filled.get("monthly_budget_remaining")):
            # Default: 5x the transaction amount so it stays under the 50% flag threshold
            try:
                filled["monthly_budget_remaining"] = max(2000.0, float(filled.get("amount", 0)) * 5)
            except (ValueError, TypeError):
                filled["monthly_budget_remaining"] = 2000.0

        if "device_id" not in filled or DataLoader._is_empty(filled.get("device_id")):
            filled["device_id"] = "DEV_DEFAULT"

        if "location" not in filled or DataLoader._is_empty(filled.get("location")):
            filled["location"] = "Unknown"

        if "channel" not in filled or DataLoader._is_empty(filled.get("channel")):
            filled["channel"] = "web"

        return filled

    @staticmethod
    def _is_empty(value) -> bool:
        """Check if a value is empty, None, or NaN."""
        if value is None:
            return True
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return True
        try:
            if pd.isna(value):
                return True
        except (ValueError, TypeError):
            pass
        if str(value).strip() == "":
            return True
        return False

    @staticmethod
    def _parse_timestamp(value) -> datetime:
        """Parse a timestamp string into a datetime object."""
        if isinstance(value, datetime):
            return value
        ts_str = str(value).strip()
        # Try ISO format first
        try:
            return datetime.fromisoformat(ts_str)
        except ValueError:
            pass
        # Try common formats
        for fmt in ("%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%d-%m-%Y %H:%M:%S",
                     "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(ts_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Cannot parse timestamp: {ts_str}")
