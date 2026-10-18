from api.v2.depth_words import depth_from_words, words_for
from api.v2.level import Obs, estimate, freshness


def test_words_become_depth_ranges():
    assert depth_from_words("น้ำท่วมถึงเข่าแล้ว")[:2] == (0.4, 0.6)
    assert depth_from_words("water is up to my waist")[:2] == (0.9, 1.1)
    lo, hi, _ = depth_from_words("น้ำต่ำกว่าลูกบิดนิดหน่อย")
    assert lo < 0.9 and hi < 1.1
    assert depth_from_words("water about 1.5 m now")[:2] == (1.3, 1.7)
    assert depth_from_words("น้ำสูง 80 ซม.")[:2] == (0.7, 0.9)
    assert depth_from_words("everyone is fine") is None


def test_words_for_round_trip():
    for d in (0.1, 0.5, 1.0, 1.3, 2.0):
        lo, hi, _ = depth_from_words(words_for(d))
        assert lo - 0.15 <= d <= hi + 0.35


def test_level_is_the_shared_water_surface_and_flags_the_outlier():
    # five houses at different ground heights all see water at about 10.0 m; one says chest-deep on high ground
    obs = [Obs(f"r{i}", 1.0, g, d - 0.1, d + 0.1) for i, (g, d) in enumerate([(9.0, 1.0), (9.5, 0.5), (8.8, 1.2), (9.2, 0.8), (9.6, 0.4)])]
    obs.append(Obs("bad", 1.0, 11.0, 1.2, 1.4))
    lvl = estimate(obs, now_h=1.0)
    assert abs(lvl.wse_m - 10.0) <= 0.1
    assert lvl.doubtful == ["bad"]
    assert lvl.depth_at(9.0)[0] == 1.0
    assert lvl.depth_at(10.5)[0] == 0.0


def test_old_reports_count_less_and_trend_shows_rising_water():
    assert freshness(3.0) == 0.5
    obs = [Obs(f"r{h}", float(h), 9.0, 0.1 * h, 0.1 * h + 0.2) for h in range(6)]
    lvl = estimate(obs, now_h=5.0)
    assert lvl.trend_cm_h is not None and 8 <= lvl.trend_cm_h <= 12
    assert lvl.wse_m >= 9.4  # recent, deeper reports dominate


def test_nothing_reported_means_unknown_not_dry():
    lvl = estimate([], now_h=4.0)
    assert lvl.wse_m is None and lvl.certainty == 0.0
