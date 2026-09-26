import re
import shutil
from pathlib import Path

from app.config import Settings

JOB_ID_PATTERN = re.compile(r"^JOB-\d{3,}$")


class JobStorage:
    """Owns every path a job writes to, so cleanup can be exact."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @staticmethod
    def _validate(job_id: str) -> str:
        if not JOB_ID_PATTERN.match(job_id):
            raise ValueError(f"Invalid job id: {job_id!r}")
        return job_id

    def job_dir(self, job_id: str) -> Path:
        return self.settings.jobs_dir / self._validate(job_id)

    def images_dir(self, job_id: str) -> Path:
        return self.job_dir(job_id) / "images"

    def audio_dir(self, job_id: str) -> Path:
        return self.job_dir(job_id) / "audio"

    def audio_path(self, job_id: str, order_index: int) -> Path:
        return self.audio_dir(job_id) / f"{order_index:03d}.m4a"

    def video_path(self, job_id: str) -> Path:
        return self.job_dir(job_id) / f"{self._validate(job_id)}.mp4"

    def image_filename(self, order_index: int, image_format: str = "png") -> str:
        return f"{order_index:03d}.{image_format.lower()}"

    def image_path(self, job_id: str, order_index: int, image_format: str = "png") -> Path:
        return self.images_dir(job_id) / self.image_filename(order_index, image_format)

    def prepare(self, job_id: str) -> Path:
        images = self.images_dir(job_id)
        images.mkdir(parents=True, exist_ok=True)
        return images

    def usage_bytes(self, job_id: str) -> int:
        root = self.job_dir(job_id)
        if not root.exists():
            return 0
        return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())

    def delete(self, job_id: str) -> bool:
        root = self.job_dir(job_id)
        if not root.exists():
            return False
        shutil.rmtree(root, ignore_errors=True)
        return True
