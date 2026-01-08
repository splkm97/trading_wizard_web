"""Wizard module for trading recommendations."""

from src.wizard.signal_scanner import SignalScanner, StockSignal
from src.wizard.recommendation import (
    RecommendationEngine,
    BuyRecommendation,
    SellRecommendation,
)

__all__ = [
    "SignalScanner",
    "StockSignal",
    "RecommendationEngine",
    "BuyRecommendation",
    "SellRecommendation",
]
