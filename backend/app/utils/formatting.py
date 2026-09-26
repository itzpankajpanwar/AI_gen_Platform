def human_bytes(size: float | None) -> str:
    if not size:
        return "0 B"
    units = ("B", "KB", "MB", "GB", "TB")
    index = 0
    value = float(size)
    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1
    precision = 0 if index == 0 else 1
    return f"{value:.{precision}f} {units[index]}"


def human_duration(seconds: float | None) -> str:
    if seconds is None or seconds < 0:
        return "--"
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}h {minutes:02d}m"
    if minutes:
        return f"{minutes:02d}m {secs:02d}s"
    return f"{secs}s"
