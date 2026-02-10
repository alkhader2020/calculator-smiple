def fmt_number(x: float) -> str:
    if abs(x - int(x)) < 1e-12:
        return str(int(x))
    return str(x)
