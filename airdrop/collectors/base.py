from __future__ import annotations

from abc import ABC, abstractmethod
from airdrop.models import AirdropCandidate


class BaseCollector(ABC):
    name = "base"

    @abstractmethod
    def collect(self) -> list[AirdropCandidate]:
        raise NotImplementedError
