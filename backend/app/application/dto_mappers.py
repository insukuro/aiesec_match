from __future__ import annotations

from typing import Any

from ..infrastructure.models import OpportunityRequirementV1, OpportunityV1


def requirement_dto(r: OpportunityRequirementV1) -> dict[str, Any]:
    return {
        "kind": r.kind,
        "constant_id": r.constant_id,
        "name": r.constant_name,
        "parent_name": r.parent_name,
        "option": r.option,
    }


def card_dto(
    c: OpportunityV1,
    reqs: list[OpportunityRequirementV1],
) -> dict[str, Any]:
    return {
        "opportunity_id": c.opportunity_id,
        "title": c.title,
        "family_key": c.family_key,
        "programme": {
            "id": c.programme_id,
            "kind": c.programme_kind,
            "name": c.programme_kind,
        },
        "place": {
            "country_code": c.country_code,
            "country_name": c.country_name,
            "lc_id": c.lc_id,
            "lc_name": c.lc_name,
            "location": c.location,
        },
        "organisation_name": c.organisation_name,
        "capacity": {
            "openings": c.openings or 0,
            "available_openings": c.available_openings or 0,
            "applicants_count": c.applicants_count or 0,
            "accepted_count": c.accepted_count or 0,
        },
        "duration_weeks": c.duration_weeks,
        "cost": (
            {"amount": float(c.cost_total), "currency": c.cost_currency}
            if c.cost_total is not None else None
        ),
        "requirements": [requirement_dto(r) for r in reqs],
        "date_opened": c.date_opened,
        "applications_close_date": c.applications_close_date,
        "is_open": c.is_open,
        "updated_at": c.updated_at,
    }