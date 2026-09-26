import shutil
from dataclasses import dataclass

from app.config import Settings

BYTES_PER_MB = 1024 * 1024
BYTES_PER_GB = 1024 * 1024 * 1024


@dataclass(frozen=True)
class DiskCheck:
    ok: bool
    prompt_count: int
    required_bytes: int
    available_bytes: int
    total_bytes: int
    reserve_bytes: int
    message: str

    @property
    def required_gb(self) -> float:
        return round(self.required_bytes / BYTES_PER_GB, 2)

    @property
    def available_gb(self) -> float:
        return round(self.available_bytes / BYTES_PER_GB, 2)

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "prompt_count": self.prompt_count,
            "required_bytes": self.required_bytes,
            "available_bytes": self.available_bytes,
            "total_bytes": self.total_bytes,
            "required_gb": self.required_gb,
            "available_gb": self.available_gb,
            "message": self.message,
        }


def estimate_required_bytes(prompt_count: int, settings: Settings) -> int:
    """Images plus the ZIP copy, with a safety factor for size variance."""
    per_image = settings.estimated_image_mb * BYTES_PER_MB
    return int(prompt_count * per_image * settings.disk_safety_factor)


def check_disk(prompt_count: int, settings: Settings) -> DiskCheck:
    settings.ensure_directories()
    usage = shutil.disk_usage(settings.data_dir)
    required = estimate_required_bytes(prompt_count, settings)
    reserve = int(settings.disk_min_free_mb * BYTES_PER_MB)
    ok = usage.free >= required + reserve

    if ok:
        message = "Sufficient disk space available"
    else:
        message = (
            f"Not enough disk space to start this batch. "
            f"Required space: {required / BYTES_PER_GB:.2f} GB "
            f"(plus {reserve / BYTES_PER_GB:.2f} GB reserve), "
            f"Available space: {usage.free / BYTES_PER_GB:.2f} GB"
        )

    return DiskCheck(
        ok=ok,
        prompt_count=prompt_count,
        required_bytes=required,
        available_bytes=usage.free,
        total_bytes=usage.total,
        reserve_bytes=reserve,
        message=message,
    )
