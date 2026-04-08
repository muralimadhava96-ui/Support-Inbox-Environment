from graders import grade, grade_with_breakdown


def test_grade_is_strictly_open_interval_for_empty_state():
    score = grade({})
    assert 0.0 < score < 1.0


def test_grade_is_strictly_open_interval_for_perfect_state():
    state = {
        "classified_correctly": True,
        "used_kb": True,
        "responded": True,
        "resolved_correctly": True,
    }
    score = grade(state)
    assert 0.0 < score < 1.0
    assert score == 0.999


def test_grade_with_breakdown_total_is_strictly_open_interval():
    state = {
        "classified_correctly": True,
        "used_kb": True,
        "responded": False,
        "resolved_correctly": False,
    }
    payload = grade_with_breakdown(state)
    assert 0.0 < payload["total"] < 1.0
    assert set(payload["breakdown"].keys()) == {"classification", "kb_usage", "response", "resolution"}
