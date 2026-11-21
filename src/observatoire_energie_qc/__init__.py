"""Observatoire énergétique du Québec."""

from .models import EnergyReading
from .collector import collect_records
from .analysis import daily_summary

__all__ = ["EnergyReading", "collect_records", "daily_summary"]
