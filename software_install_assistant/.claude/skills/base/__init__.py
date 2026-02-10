"""
Base package initialization
"""

from .base_adapter import BaseAdapter, HealthResult, Issue, IssueType, FixResult

__all__ = ["BaseAdapter", "HealthResult", "Issue", "IssueType", "FixResult"]
