from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.generators import ImageGenerator, build_generator
from app.services.storage import JobStorage

_generator: ImageGenerator | None = None


def get_storage(settings: Annotated[Settings, Depends(get_settings)]) -> JobStorage:
    return JobStorage(settings)


def get_generator(settings: Annotated[Settings, Depends(get_settings)]) -> ImageGenerator:
    """A process-wide generator handle used for health/status reporting."""
    global _generator
    if _generator is None:
        _generator = build_generator(settings)
    return _generator


def reset_generator() -> None:
    global _generator
    _generator = None


SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[Session, Depends(get_db)]
StorageDep = Annotated[JobStorage, Depends(get_storage)]
GeneratorDep = Annotated[ImageGenerator, Depends(get_generator)]
