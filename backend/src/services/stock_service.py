"""Stock name lookup service using stock_names_kr.json."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from src.core.logging import logger


class StockService:
    """Service for stock code validation and name lookup."""

    _instance: Optional[StockService] = None
    _stock_names: dict[str, str] = {}

    def __new__(cls) -> StockService:
        """Singleton pattern for stock service."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_stock_names()
        return cls._instance

    def _load_stock_names(self) -> None:
        """Load stock names from JSON file."""
        # Try multiple paths
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "data" / "stock_names_kr.json",
            Path("data/stock_names_kr.json"),
            Path("/Users/kalee/workspace/bollinger-band-trade/trading_wizard_web/data/stock_names_kr.json"),
        ]

        for path in possible_paths:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self._stock_names = json.load(f)
                logger.info(f"Loaded {len(self._stock_names)} stock names from {path}")
                return

        logger.warning("stock_names_kr.json not found, using empty stock names")
        self._stock_names = {}

    @staticmethod
    def validate_stock_code(stock_code: str) -> bool:
        """Validate stock code format (6-digit number)."""
        return bool(re.match(r"^[0-9]{6}$", stock_code))

    def get_stock_name(self, stock_code: str) -> Optional[str]:
        """Get stock name by code.

        Args:
            stock_code: 6-digit stock code

        Returns:
            Stock name or None if not found
        """
        return self._stock_names.get(stock_code)

    def get_stock_name_or_default(self, stock_code: str, default: str = "Unknown") -> str:
        """Get stock name by code with default fallback."""
        return self._stock_names.get(stock_code, default)

    def search_stocks(self, query: str, limit: int = 10) -> list[dict]:
        """Search stocks by code or name.

        Args:
            query: Search query (code prefix or name substring)
            limit: Maximum number of results

        Returns:
            List of matching stocks with code and name
        """
        query = query.strip()
        if not query:
            return []

        results = []

        # Search by code prefix first
        for code, name in self._stock_names.items():
            if code.startswith(query):
                results.append({"code": code, "name": name})
                if len(results) >= limit:
                    return results

        # Then search by name
        query_lower = query.lower()
        for code, name in self._stock_names.items():
            if query_lower in name.lower():
                # Avoid duplicates
                if not any(r["code"] == code for r in results):
                    results.append({"code": code, "name": name})
                    if len(results) >= limit:
                        return results

        return results

    def stock_exists(self, stock_code: str) -> bool:
        """Check if a stock code exists in the database."""
        return stock_code in self._stock_names

    def get_all_stock_names(self) -> dict[str, str]:
        """Get all stock names as a dictionary.

        Returns:
            Dictionary mapping stock code to stock name
        """
        return self._stock_names.copy()

    @property
    def total_stocks(self) -> int:
        """Total number of stocks in the database."""
        return len(self._stock_names)


# Singleton instance
stock_service = StockService()
