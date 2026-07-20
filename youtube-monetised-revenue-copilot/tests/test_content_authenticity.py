from ytcopilot.content_authenticity import assess_authenticity_risk


def _safe_defaults(**overrides):
    base = dict(
        uploads_per_day=1,
        ai_script_percent=90,
        human_edit_pass=True,
        disclosure_on=True,
        template_rotation_count=3,
        new_niches_this_month=1,
        human_pov_stated=True,
    )
    base.update(overrides)
    return assess_authenticity_risk(**base)


def test_all_safe_inputs_produce_no_high_flags():
    flags = _safe_defaults()
    assert not any(f.severity == "high" for f in flags)


def test_farm_threshold_upload_frequency_flags_high():
    flags = _safe_defaults(uploads_per_day=10)
    freq = next(f for f in flags if f.marker == "Upload frequency")
    assert freq.severity == "high"


def test_moderate_upload_frequency_is_caution():
    flags = _safe_defaults(uploads_per_day=4)
    freq = next(f for f in flags if f.marker == "Upload frequency")
    assert freq.severity == "caution"


def test_high_ai_percent_without_human_pass_flags_high():
    flags = _safe_defaults(ai_script_percent=95, human_edit_pass=False)
    ai_flag = next(f for f in flags if f.marker == "AI-generated script share")
    assert ai_flag.severity == "high"


def test_high_ai_percent_with_human_pass_is_only_caution():
    flags = _safe_defaults(ai_script_percent=95, human_edit_pass=True)
    ai_flag = next(f for f in flags if f.marker == "AI-generated script share")
    assert ai_flag.severity == "caution"


def test_disclosure_off_flags_high():
    flags = _safe_defaults(disclosure_on=False)
    d = next(f for f in flags if f.marker == "Altered/synthetic content disclosure")
    assert d.severity == "high"


def test_single_template_flags_high():
    flags = _safe_defaults(template_rotation_count=1)
    t = next(f for f in flags if f.marker == "Template sameness")
    assert t.severity == "high"


def test_many_new_niches_this_month_flags_high():
    flags = _safe_defaults(new_niches_this_month=6)
    p = next(f for f in flags if f.marker == "Topic pivot speed")
    assert p.severity == "high"


def test_no_stated_pov_is_caution_not_high():
    flags = _safe_defaults(human_pov_stated=False)
    pov = next(f for f in flags if f.marker == "Stated human point of view")
    assert pov.severity == "caution"
