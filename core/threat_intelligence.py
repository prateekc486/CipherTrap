"""
Threat Intelligence Module for CipherTrap.

Detects known ransomware signatures and attack patterns by analyzing:
- File encryption patterns (entropy, extension changes)
- File deletion/mass modification patterns
- Specific malware behavioral signatures (LockBit, Ryuk, WannaCry, etc.)

This module helps identify the TYPE of ransomware attacking, not just that
an attack is happening.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
import re


@dataclass
class MalwareSignature:
    """Represents a known ransomware's behavioral signature."""
    name: str  # e.g., "LockBit 3.0"
    extensions: list[str]  # File extensions this malware adds
    patterns: list[str]  # Regex patterns in filenames/behavior
    confidence: float  # 0.0 to 1.0
    description: str


# Known Ransomware Signatures (Real malware families)
KNOWN_SIGNATURES = [
    MalwareSignature(
        name="LockBit 3.0",
        extensions=[".lockbit", ".abcd", ".encrypted"],
        patterns=[r"\.lockbit$", r"LOCKBIT.*README", r"restore_files_info\.txt"],
        confidence=0.95,
        description="Mass file encryption + double extortion threats"
    ),
    MalwareSignature(
        name="Ryuk",
        extensions=[".RYK", ".RYUK"],
        patterns=[r"\.RYK$", r"RyukReadMe\.txt"],
        confidence=0.90,
        description="Targeted ransomware with high ransom demands"
    ),
    MalwareSignature(
        name="WannaCry",
        extensions=[".WNCRY", ".wcry"],
        patterns=[r"\.WNCRY$", r"WANNACRY"],
        confidence=0.85,
        description="Mass encryption with self-propagation"
    ),
    MalwareSignature(
        name="Conti",
        extensions=[".conti", ".encrypted"],
        patterns=[r"NOTE\.txt$", r"\.conti$"],
        confidence=0.88,
        description="Sophisticated ransomware targeting enterprises"
    ),
    MalwareSignature(
        name="BlackMatter",
        extensions=[".blackmatter"],
        patterns=[r"\.blackmatter$", r"INSTRUCTIONS\.txt"],
        confidence=0.87,
        description="Advanced ransomware with data exfiltration"
    ),
    MalwareSignature(
        name="DarkSide",
        extensions=[".darkside"],
        patterns=[r"\.darkside$", r"README\.txt$"],
        confidence=0.86,
        description="Ransomware-as-a-Service (RaaS) platform"
    ),
    MalwareSignature(
        name="Cerber",
        extensions=[".cerber"],
        patterns=[r"cerber"],
        confidence=0.80,
        description="Ransomware targeting file servers"
    ),
    MalwareSignature(
        name="NotPetya",
        extensions=[".PETA"],
        patterns=[r"\.PETA$"],
        confidence=0.82,
        description="Destructive malware disguised as ransomware"
    ),
]


@dataclass
class ThreatDetection:
    """Result of threat analysis."""
    detected_malware: list[str]  # Names of detected malware signatures
    confidence_scores: dict[str, float]  # Malware -> confidence (0.0-1.0)
    attack_patterns: list[str]  # Descriptions of detected behaviors
    severity: float  # Overall severity 0.0 to 1.0


def detect_malware_signature(
    modified_files: list[Path],
    deleted_files: list[Path],
    encrypted_files: list[Path],
) -> ThreatDetection:
    """
    Analyze recent file modifications and detect known malware signatures.
    
    Args:
        modified_files: Recently modified file paths
        deleted_files: Recently deleted file paths
        encrypted_files: Files that appear encrypted (high entropy)
    
    Returns:
        ThreatDetection with matched signatures and confidence scores
    """
    detected_malware = []
    confidence_scores = {}
    attack_patterns = []
    
    # Analyze file extensions
    all_files = modified_files + encrypted_files
    file_extensions = defaultdict(int)
    for f in all_files:
        ext = f.suffix.lower()
        if ext:
            file_extensions[ext] += 1
    
    # Match against known signatures
    for sig in KNOWN_SIGNATURES:
        matches = 0
        total_checks = len(sig.extensions) + len(sig.patterns)
        
        # Check extension matches
        for ext in sig.extensions:
            if file_extensions.get(ext.lower(), 0) > 0:
                matches += 1
        
        # Check pattern matches in filenames
        for pattern in sig.patterns:
            for f in all_files:
                if re.search(pattern, f.name):
                    matches += 1
                    break
        
        # Calculate confidence
        if matches > 0:
            confidence = sig.confidence * (matches / total_checks)
            if confidence >= 0.6:  # Only report if >60% confidence
                detected_malware.append(sig.name)
                confidence_scores[sig.name] = confidence
    
    # Analyze attack behavior patterns
    if deleted_files and len(deleted_files) > 5:
        attack_patterns.append(f"Mass file deletion detected ({len(deleted_files)} files)")
    
    if encrypted_files and len(encrypted_files) > 3:
        attack_patterns.append(f"High-entropy file modifications ({len(encrypted_files)} files) - consistent with encryption")
    
    if file_extensions and len(file_extensions) > 5:
        ext_str = ", ".join(list(file_extensions.keys())[:3])
        attack_patterns.append(f"Multiple file extension modifications: {ext_str}...")
    
    # Calculate overall severity
    severity = 0.0
    if detected_malware:
        severity = max(confidence_scores.values())
    elif attack_patterns:
        severity = min(0.7, len(attack_patterns) * 0.2)
    
    return ThreatDetection(
        detected_malware=detected_malware,
        confidence_scores=confidence_scores,
        attack_patterns=attack_patterns,
        severity=severity
    )


def get_malware_description(malware_name: str) -> str:
    """Get detailed description of a known malware."""
    for sig in KNOWN_SIGNATURES:
        if sig.name == malware_name:
            return sig.description
    return "Unknown malware"


def analyze_file_entropy(data: bytes) -> float:
    """
    Calculate Shannon entropy of file content.
    High entropy (close to 1.0) suggests encryption.
    Low entropy suggests plaintext.
    """
    if len(data) == 0:
        return 0.0
    
    entropy = 0.0
    for i in range(256):
        freq = data.count(bytes([i])) / len(data)
        if freq > 0:
            import math
            entropy -= freq * math.log2(freq)
    
    return entropy / 8.0  # Normalize to 0-1


def is_likely_encrypted(file_path: Path, sample_size: int = 4096) -> bool:
    """Check if a file appears to be encrypted based on entropy."""
    try:
        data = file_path.read_bytes()[:sample_size]
        entropy = analyze_file_entropy(data)
        return entropy > 0.7  # Encrypted files have high entropy
    except Exception:
        return False
