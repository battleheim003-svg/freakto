from __future__ import annotations

import os
from typing import Any

import requests

from airdrop.models import ContractRef


class GoPlusChecker:
    """Optional GoPlus malicious address checker.

    It only runs when contract addresses are provided. If the API is not
    available, scoring continues with a warning instead of failing the radar.
    """

    BASE_URL = "https://api.gopluslabs.io/api/v1/address_security/{address}"

    def __init__(self, token: str | None = None, timeout: int = 15):
        self.token = token or os.getenv("GOPLUS_API_TOKEN", "")
        self.timeout = timeout

    def check_contracts(self, contracts: list[ContractRef]) -> tuple[int, list[str], list[str]]:
        if not contracts:
            return 0, [], []

        positive_points = 0
        warnings: list[str] = []
        flags: list[str] = []

        for contract in contracts[:5]:
            if not contract.address:
                continue
            try:
                headers = {"accept": "application/json"}
                if self.token:
                    headers["Authorization"] = f"Bearer {self.token}"
                params: dict[str, Any] = {}
                if contract.chain_id:
                    params["chain_id"] = contract.chain_id
                response = requests.get(
                    self.BASE_URL.format(address=contract.address),
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )
                if response.status_code in {401, 403}:
                    warnings.append("GoPlus برای این درخواست مجوز نداد؛ بررسی امنیت قرارداد دستی انجام شود.")
                    continue
                response.raise_for_status()
                payload = response.json()
                result = payload.get("result") or {}
                risky_keys = [k for k, v in result.items() if str(v).lower() in {"1", "true", "yes"} and any(term in k.lower() for term in ["malicious", "phishing", "black", "honeypot", "fake"])]
                if risky_keys:
                    flags.extend([f"GoPlus risk: {key}" for key in risky_keys[:5]])
                    warnings.append(f"GoPlus روی آدرس {contract.address[:10]}... ریسک گزارش کرد.")
                else:
                    positive_points += 2
            except Exception as exc:
                warnings.append(f"بررسی GoPlus کامل نشد: {exc}")
                break

        return min(5, positive_points), warnings, flags
