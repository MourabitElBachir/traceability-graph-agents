"""Prompt-injection signals and a check that prose stays inside known ids."""

from __future__ import annotations

import re

_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", "ignore_instructions"),
    (r"\bsystem\s+prompt\b", "system_prompt"),
    (r"\byou\s+are\s+now\b", "role_override"),
    (r"\b(drop|delete)\s+(the\s+)?(database|graph|constraint)", "destructive_instruction"),
    (r"\bdo\s+not\s+cite\b", "citation_bypass"),
    (r"reveal\s+(your\s+)?(hidden|system)", "exfiltration"),
)
_ID = re.compile(r"\b(?:BLE|FAR|BIS|CERT|OIL|DOC|CHK|AUD|SHIP|SITE|ACT|PRD|ING|P)-[A-Z0-9-]+\b")
_LOT = re.compile(r"\b(?:BLE|FAR|BIS|OIL)-[A-Z0-9-]+\b")
_CERT = re.compile(r"\bCERT-\d+\b")


def injection_flags(question: str) -> list[str]:
    return [name for pattern, name in _PATTERNS if re.search(pattern, question, re.IGNORECASE)]


def extract_lot_ids(question: str) -> list[str]:
    return list(dict.fromkeys(_LOT.findall(question)))


def extract_certificate_ids(question: str) -> list[str]:
    return list(dict.fromkeys(_CERT.findall(question)))


def mentioned_ids(text: str) -> list[str]:
    return list(dict.fromkeys(_ID.findall(text)))


def ungrounded_ids(text: str, allowed: set[str]) -> list[str]:
    return [token for token in mentioned_ids(text) if token not in allowed]
