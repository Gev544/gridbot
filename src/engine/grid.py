from dataclasses import dataclass

@dataclass
class GridSide:
    entries: list
    tps: list

@dataclass
class BothSidesGrid:
    longs: GridSide
    shorts: GridSide

def build_both_sides(mid: float, levels: int, step_pct: float, tp_pct: float):
    step = step_pct / 100.0
    tp = tp_pct / 100.0
    downs = [mid * (1 - i * step) for i in range(1, levels+1)]
    downs_tp = [p * (1 + tp) for p in downs]
    ups = [mid * (1 + i * step) for i in range(1, levels+1)]
    ups_tp = [p * (1 - tp) for p in ups]
    return BothSidesGrid(longs=GridSide(entries=downs, tps=downs_tp),
                         shorts=GridSide(entries=ups, tps=ups_tp))
