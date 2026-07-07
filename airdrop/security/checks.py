from __future__ import annotations

import os

from airdrop.models import AirdropCandidate
from airdrop.security.domain_verifier import DomainVerifier
from airdrop.security.goplus_checker import GoPlusChecker


def run_security_checks(candidate: AirdropCandidate) -> tuple[int, list[str], list[str]]:
    blacklist = [d.strip() for d in os.getenv("AIRDROP_DOMAIN_BLACKLIST", "").split(",") if d.strip()]
    domain_score, domain_warnings = DomainVerifier(blacklist=blacklist).verify_url(candidate.official_url)
    goplus_points, goplus_warnings, goplus_flags = GoPlusChecker().check_contracts(candidate.contracts)
    score = max(0, min(20, domain_score + goplus_points))
    return score, domain_warnings + goplus_warnings, goplus_flags
