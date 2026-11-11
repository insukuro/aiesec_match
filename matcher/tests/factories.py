from app.domain.models import Opportunity
from app.domain.profile import Profile


def make_opp(oid: int, kind: str = "talent", **kw) -> Opportunity:
    return Opportunity(opportunity_id=oid, programme_kind=kind, **kw)


def make_profile(**kw) -> Profile:
    base = dict(programmes=["talent"], background_ids=set(), skill_ids=set(),
                language_ids=set(), english_level="B2", study_level_ids=set(),
                nationality_id=None, min_weeks=None, max_weeks=None,
                max_budget_eur=None, willing_to_pay=None, preferred_lc_ids=set())
    base.update(kw)
    return Profile(**base)


class ListReader:
    def __init__(self, opps):
        self.opps = opps

    def list_open(self, kind):
        return [o for o in self.opps if o.programme_kind == kind]


class BrokenReader:
    def list_open(self, kind):
        raise RuntimeError("db down")