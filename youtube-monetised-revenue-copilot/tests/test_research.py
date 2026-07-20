from ytcopilot import channel_profile as profile
from ytcopilot.research import rollout_plan


def test_rollout_plan_covers_every_niche_exactly_once():
    plan = rollout_plan(months=3)
    all_niches = [n for c in profile.NICHE_CLUSTERS.values() for n in c["niches"]]
    plan_niches = [item["niche"] for item in plan]
    assert sorted(plan_niches) == sorted(all_niches)


def test_rollout_plan_weeks_are_within_requested_window():
    months = 3
    plan = rollout_plan(months=months)
    assert all(1 <= item["week"] <= months * 4 for item in plan)


def test_rollout_plan_heavy_niches_front_loaded():
    plan = rollout_plan(months=3)
    heavy_weeks = [item["week"] for item in plan if item["weight"] == "heavy"]
    light_weeks = [item["week"] for item in plan if item["weight"] == "light"]
    assert sum(heavy_weeks) / len(heavy_weeks) <= sum(light_weeks) / len(light_weeks)
