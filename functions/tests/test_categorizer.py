"""Tests for categorizer Lambda function."""

from __future__ import annotations

from categorizer import _categorize


def test_convenience_store():
    assert _categorize("セブンイレブン") == "food"


def test_transport():
    assert _categorize("JR東日本") == "transport"


def test_daily():
    assert _categorize("マツキヨ") == "daily"


def test_entertainment():
    assert _categorize("TOHOシネマ") == "entertainment"


def test_utility():
    assert _categorize("東京電力") == "utility"


def test_telecom():
    assert _categorize("ドコモ") == "telecom"


def test_medical():
    assert _categorize("内科クリニック") == "medical"


def test_clothing():
    assert _categorize("ユニクロ") == "clothing"


def test_unknown_store():
    assert _categorize("謎のお店") == "other"
