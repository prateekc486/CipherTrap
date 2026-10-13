"""
Risk scoring engine for CipherTrap.

Consumes:
- RawEventStats from FolderMonitor (raw, never-debounced counts) so rapid
  repeated writes to a single file are NOT hidden by UI-level debouncing.
- Honeyfile integrity checks.
- A simple entropy estimate on file content (high entropy can indicate
  the file has been encrypted by ransomware).

IMPORTANT: this is a rule-based heuristic, not a guarantee. It detects
ransomware-LIKE destructive behavior in the monitored folder -- legitimate
tools (backup software, compressors, updaters) can also trigger elevated
scores. Always pair automated scoring with a human decision before taking
destructive action (like auto-restoring files).
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from core.honeyfiles import Honeyfile, check_honeyfile_integrity
from core.monitor import RawEventStats

# --- Scoring weights (sum to 100 at max) ---
WEIGHT_RAPID_MODIFICATIONS = 30
WEIGHT_EXTENSION_CHANGES = 25
WEIGHT_HIGH_ENTROPY = 20
WEIGHT_HONEYFILE_TOUCHED = 25

# --- Thresholds ---
RAPID_MOD_EVENT_THRESHOLD = 15      # raw events on ONE file within the window
MANY_FILES_THRESHOLD = 10           # distinct files with extension changes
HIGH_ENTROPY_THRESHOLD = 7.5        # bits/byte; random/encrypted data approaches 8.0

RISK_LEVELS = [
    (0, 29, "Normal"),
    (30, 59, "Suspicious"),
    (60, 79, "High-risk"),
    (80, 100, "Likely destructive activity"),
]


@dataclass
class RiskAssessment:
    score: int
    level: str
    reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {"score": self.score, "level": self.level, "reasons": self.reasons}


def _risk_level_for_score(score: int) -> str:
    for low, high, label in RISK_LEVELS:
        if low <= score <= high:
            return label
    return "Unknown"


def shannon_entropy(data: bytes) -> float:
    """
    Compute Shannon entropy (bits per byte) of the given data.
    Plaintext (English text, code, etc.) is typically 3-5 bits/byte.
    Compressed or encrypted data is typically 7.5-8.0 bits/byte.
    """
    if not data:
        return 0.0
    counts = Counter(data)
    length = len(data)
    entropy = 0.0
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy


def score_activity(
    *,
    raw_stats: Iterable[RawEventStats],
    honeyfiles: list[Honeyfile],
    changed_extensions: set[str] | None = None,
    sampled_file_bytes: list[bytes] | None = None,
) -> RiskAssessment:
    """
    Compute a 0-100 risk score from the current window of activity.

    Parameters:
        raw_stats: RawEventStats objects from FolderMonitor.all_raw_stats().
                   Directory-level stats must NOT be passed in here -- the
                   caller is responsible for filtering to file paths only
                   (FolderMonitor's raw stats are keyed by path, not by
                   event, so filter using is_directory info from the
                   FileEvent stream before calling this function).
        honeyfiles: currently deployed honeyfiles to check for tampering.
        changed_extensions: set of file extensions seen changing in this
                             window (e.g. {".txt.locked", ".docx.enc"}).
        sampled_file_bytes: a small sample of recently-modified file
                             contents, used to estimate entropy.

    Returns:
        RiskAssessment with a 0-100 score, a human-readable level, and a
        list of reasons contributing to the score.
    """
    score = 0
    reasons: list[str] = []

    # --- 1. Rapid modifications to a single file ---
    max_events_on_one_file = max((s.event_count for s in raw_stats), default=0)
    if max_events_on_one_file >= RAPID_MOD_EVENT_THRESHOLD:
        score += WEIGHT_RAPID_MODIFICATIONS
        reasons.append(
            f"One file received {max_events_on_one_file} raw modification events "
            f"(threshold: {RAPID_MOD_EVENT_THRESHOLD})"
        )

    # --- 2. Many distinct file extensions changing ---
    if changed_extensions and len(changed_extensions) >= MANY_FILES_THRESHOLD:
        score += WEIGHT_EXTENSION_CHANGES
        reasons.append(
            f"{len(changed_extensions)} distinct file extensions changed in this window "
            f"(threshold: {MANY_FILES_THRESHOLD})"
        )

    # --- 3. High entropy content (possible in-place encryption) ---
    if sampled_file_bytes:
        entropies = [shannon_entropy(b) for b in sampled_file_bytes if b]
        if entropies:
            avg_entropy = sum(entropies) / len(entropies)
            if avg_entropy >= HIGH_ENTROPY_THRESHOLD:
                score += WEIGHT_HIGH_ENTROPY
                reasons.append(
                    f"Sampled file content has high entropy ({avg_entropy:.2f} bits/byte, "
                    f"threshold: {HIGH_ENTROPY_THRESHOLD}) -- consistent with encrypted data"
                )

    # --- 4. Honeyfile tampering ---
    tampered = [h for h in honeyfiles if not check_honeyfile_integrity(h)]
    if tampered:
        score += WEIGHT_HONEYFILE_TOUCHED
        names = ", ".join(h.path.name for h in tampered)
        reasons.append(f"{len(tampered)} honeyfile(s) modified or deleted: {names}")

    score = min(score, 100)
    return RiskAssessment(score=score, level=_risk_level_for_score(score), reasons=reasons)


def filter_file_only_stats(
    raw_stats: Iterable[RawEventStats], directory_paths: set[Path],
) -> list[RawEventStats]:
    """
    Remove RawEventStats entries whose path is a known directory, so
    directory-level filesystem noise never inflates the risk score.

    `directory_paths` should be collected by the caller from FileEvent
    objects where `is_directory=True` (RawEventStats itself doesn't store
    is_directory since the same path could theoretically be seen with
    mixed event types; callers should track directory paths separately).
    """
    return [s for s in raw_stats if s.path not in directory_paths]
