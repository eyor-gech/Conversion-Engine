from __future__ import annotations

from agent.core.state import ScoredCompany


class FeatureStore:
    def __init__(self) -> None:
        self._rows: dict[str, ScoredCompany] = {}

    def upsert(self, scored: ScoredCompany) -> None:
        self._rows[scored.company.company_id] = scored

    def get(self, company_id: str) -> ScoredCompany | None:
        return self._rows.get(company_id)

    def all(self) -> list[ScoredCompany]:
        return list(self._rows.values())
