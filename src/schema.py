"""
Stage 4 (part 2) — the shape of a finished record, enforced.

BookRecord is the schema described in the assignment: which fields are
required, what type each one is, description optional. Every record is
validated against this before it is allowed anywhere near books.json.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

from pydantic import BaseModel, Field, field_validator


class BookRecord(BaseModel):
    title: str = Field(min_length=1)
    product_url: str  # this is the record's canonical identity (Stage 4 rule)
    price_text: str
    price_gbp: float = Field(gt=0)
    availability_text: str
    availability_count: Optional[int] = Field(default=None, ge=0)
    in_stock: bool
    rating_text: Optional[str] = None
    rating_stars: Optional[int] = Field(default=None, ge=0, le=5)
    description: Optional[str] = None
    source_page: str
    fetched_at: str

    @field_validator("product_url", "source_page")
    @classmethod
    def must_be_absolute_https(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError(f"expected an absolute https:// URL, got: {value!r}")
        return value

    @field_validator("fetched_at")
    @classmethod
    def must_be_iso_timestamp(cls, value: str) -> str:
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"fetched_at is not a valid ISO timestamp: {value!r}") from exc
        return value


def validate_record(clean: dict) -> Tuple[Optional[BookRecord], Optional[str]]:
    """
    Returns (record, None) on success or (None, reason) on failure.
    A record that fails never sneaks into books.json — it goes to
    errors.json together with this reason (Stage 4 rule).
    """
    try:
        return BookRecord(**clean), None
    except Exception as exc:  # pydantic.ValidationError, but keep this import-light
        return None, str(exc).replace("\n", " ")
