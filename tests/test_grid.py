from src.engine.grid import build_grid


def test_build_grid_splits_levels_and_computes_step():
    grid = build_grid(min_price=100, max_price=110, levels=6, mid=105)
    assert grid.buy_levels == [104.0, 102.0, 100.0]
    assert grid.sell_levels == [106.0, 108.0, 110.0]
    assert grid.step == 2.0
