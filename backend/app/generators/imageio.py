import io

from PIL import Image

from app.generators.base import GenerationError, GenerationRequest


def snap(value: int, multiple: int) -> int:
    """Nearest multiple of `multiple`, never below it."""
    if multiple <= 1:
        return value
    return max(multiple, int(round(value / multiple)) * multiple)


def save_image_bytes(data: bytes, request: GenerationRequest) -> None:
    """Write raw image bytes to the request's output path at the exact requested size.

    Hosted backends often only accept certain dimension steps (Runware wants
    multiples of 64), so the returned image may not match the project's
    resolution. Resizing here keeps that a backend detail rather than
    something the ZIP or the UI has to know about.
    """
    if not data:
        raise GenerationError("Backend returned an empty image")

    target_format = request.image_format.upper()
    if target_format == "JPG":
        target_format = "JPEG"

    try:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            if image.size != (request.width, request.height):
                image = image.resize((request.width, request.height), Image.LANCZOS)
            if target_format == "JPEG" and image.mode != "RGB":
                image = image.convert("RGB")
            elif image.mode not in {"RGB", "RGBA", "L"}:
                image = image.convert("RGB")

            request.output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(request.output_path, format=target_format)
    except OSError as exc:
        raise GenerationError(f"Backend returned an unreadable image: {exc}") from exc
