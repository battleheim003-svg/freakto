from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

SUSPICIOUS_TERMS = {
    "walletconnect-claim",
    "metamask-claim",
    "airdrop-claim",
    "free-claim",
    "bonus-claim",
    "verify-wallet",
    "seed",
    "privatekey",
    "private-key",
}


class DomainVerifier:
    def __init__(self, blacklist: list[str] | None = None):
        self.blacklist = {d.lower().strip() for d in (blacklist or []) if d.strip()}

    def verify_url(self, url: str) -> tuple[int, list[str]]:
        """Return security points out of 15 and warnings."""
        warnings: list[str] = []
        if not url:
            return 6, ["لینک رسمی پروژه موجود نیست؛ قبل از اقدام باید دستی بررسی شود."]

        parsed = urlparse(url if "://" in url else "https://" + url)
        hostname = (parsed.hostname or "").lower()
        score = 15

        if parsed.scheme != "https":
            score -= 6
            warnings.append("لینک HTTPS نیست.")

        if not hostname or "." not in hostname:
            score -= 8
            warnings.append("دامنه لینک رسمی معتبر به نظر نمی‌رسد.")

        if hostname in self.blacklist or any(hostname.endswith("." + d) for d in self.blacklist):
            score = 0
            warnings.append("دامنه در blacklist داخلی ربات قرار دارد.")

        if hostname.startswith("xn--") or ".xn--" in hostname:
            score -= 5
            warnings.append("دامنه punycode است؛ احتمال جعل/فیشینگ را دستی بررسی کن.")

        try:
            ipaddress.ip_address(hostname)
            score -= 7
            warnings.append("لینک رسمی به IP مستقیم اشاره می‌کند، نه دامنه برند.")
        except ValueError:
            pass

        compact = hostname + parsed.path.lower()
        for term in SUSPICIOUS_TERMS:
            if term in compact:
                score -= 5
                warnings.append(f"عبارت مشکوک در URL دیده شد: {term}")
                break

        return max(0, min(15, score)), warnings
