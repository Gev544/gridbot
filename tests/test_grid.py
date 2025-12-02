from src.engine.grid import build_grid, auto_range_from_series


def test_build_grid_splits_levels_and_computes_step():
    grid = build_grid(min_price=100, max_price=110, levels=6, mid=105)
    assert grid.buy_levels == [104.0, 102.0, 100.0]
    assert grid.sell_levels == [106.0, 108.0, 110.0]
    assert grid.step == 2.0


def test_auto_range_from_series_uses_percentiles_and_expands_if_flat():
    series = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
    low, high = auto_range_from_series(series, 0.1, 0.9)
    assert low == 101.0
    assert high == 109.0

    low, high = auto_range_from_series([100, 100, 100], 0.1, 0.9)
    assert low == 100.0
    assert high > low
