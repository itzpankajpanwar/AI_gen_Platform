"""Rendering a scene through Remotion instead of through an ffmpeg filter graph.

Remotion renders React in a headless browser, one frame at a time. That is far
slower than ffmpeg, so it is used only for the scenes whose `animation` column
names a Remotion template; everything else keeps the fast path.

Cost is dominated by bundling the project, not by the frames, so a job bundles
once and then renders every animated scene from that bundle. The job's stills
are copied into the bundle's public directory first, because `staticFile()`
resolves against whatever was public at bundle time.

Every clip that comes back is conformed with ffmpeg to the same fps, SAR and
pixel format as the ffmpeg-rendered clips — otherwise the xfade chain that joins
the film fails the moment it meets the first mismatch.
"""

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.services.remotion import TEMPLATES


class RemotionError(RuntimeError):
    pass


@dataclass(frozen=True)
class SceneRender:
    """Everything one Remotion clip needs, already resolved from the CSV."""

    template: str
    text: str
    params: dict[str, str]
    image: str
    seconds: float
    width: int
    height: int
    label: str  # for error messages: which scene failed
    overlay: str = ""

    def props(self, settings: Settings) -> dict:
        frames = max(int(round(self.seconds * settings.video_fps)), 1)
        return {
            "image": self.image,
            "overlay": self.overlay,
            "template": self.template,
            "text": self.text,
            "params": self.params,
            "accent": settings.remotion_accent,
            "ink": settings.remotion_ink,
            "durationInFrames": frames,
            "fps": settings.video_fps,
            "width": self.width,
            "height": self.height,
        }


def project_dir(settings: Settings) -> Path:
    return settings.asset_path(settings.remotion_dir)


def is_available(settings: Settings) -> tuple[bool, str]:
    """Whether a Remotion render could run, and why not if it could not."""
    root = project_dir(settings)
    if not (root / "src" / "index.ts").is_file():
        return False, f"Remotion project not found at {root}"
    if not (root / "node_modules").is_dir():
        return False, f"Remotion dependencies are not installed — run: npm install --prefix {root}"
    if shutil.which(settings.remotion_binary) is None:
        return False, f"'{settings.remotion_binary}' not found on PATH (install Node.js)"
    return True, ""


def _run(command: list[str], cwd: Path, timeout: float, what: str) -> None:
    try:
        completed = subprocess.run(
            command, cwd=str(cwd), capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired as exc:
        raise RemotionError(f"{what} timed out after {timeout:g}s") from exc
    if completed.returncode != 0:
        noise = (completed.stderr or completed.stdout or "").strip().splitlines()
        raise RemotionError(f"{what} failed: " + " | ".join(noise[-8:]))


class RemotionSession:
    """One bundle of the animation project, holding one job's stills.

    Create it, stage the images the animated scenes reference, call `bundle()`,
    then render as many clips as you like. `close()` removes the working copy.
    """

    def __init__(self, settings: Settings, work_dir: Path):
        self.settings = settings
        self.root = project_dir(settings)
        self.work_dir = work_dir
        self.public_dir = work_dir / "public"
        self.bundle_dir = work_dir / "bundle"
        self._bundled = False

    # ------------------------------------------------------------- staging
    def stage_image(self, source: Path, name: str) -> str:
        """Copy a still into the bundle's public dir; return its staticFile path."""
        target = self.public_dir / "scenes" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        return f"scenes/{name}"

    def bundle(self) -> None:
        """Build the project once, with the staged stills inside it."""
        available, reason = is_available(self.settings)
        if not available:
            raise RemotionError(reason)

        # useFont.ts asks for fonts/<original filename>, and assets/fonts is the
        # one place the film's typefaces are configured — ffmpeg reads the same
        # two files. Copying them in keeps the two renderers on one set.
        fonts_dir = self.public_dir / "fonts"
        fonts_dir.mkdir(parents=True, exist_ok=True)
        for configured in (self.settings.font_sans, self.settings.font_serif):
            source = self.settings.asset_path(configured)
            if not source.is_file():
                raise RemotionError(f"font not found: {source}")
            shutil.copyfile(source, fonts_dir / source.name)

        # Templates may also ask for faces beyond the configured pair — the
        # quick-commerce film sets its English data typography in Inter, in
        # several weights. Stage every typeface that sits beside them rather
        # than making each one a setting.
        for extra in sorted(self.settings.asset_path(self.settings.font_sans).parent.glob("*")):
            if extra.suffix.lower() in {".ttf", ".otf", ".woff", ".woff2"}:
                target = fonts_dir / extra.name
                if not target.exists():
                    shutil.copyfile(extra, target)

        _run(
            [
                self.settings.remotion_binary, "remotion", "bundle", "src/index.ts",
                f"--public-dir={self.public_dir}",
                f"--out-dir={self.bundle_dir}",
                "--log=error",
            ],
            cwd=self.root,
            timeout=self.settings.remotion_timeout_seconds,
            what="Remotion bundle",
        )
        if not (self.bundle_dir / "index.html").is_file():
            raise RemotionError(f"Remotion bundle produced nothing at {self.bundle_dir}")
        self._bundled = True

    # ----------------------------------------------------------- rendering
    def render(self, scene: SceneRender, target: Path) -> None:
        if not self._bundled:
            raise RemotionError("render() called before bundle()")
        if scene.template not in TEMPLATES:
            raise RemotionError(f"unknown Remotion template '{scene.template}'")

        props_file = self.work_dir / f"props_{target.stem}.json"
        props_file.write_text(
            json.dumps(scene.props(self.settings), ensure_ascii=False), encoding="utf-8"
        )

        command = [
            self.settings.remotion_binary, "remotion", "render",
            str(self.bundle_dir), "Scene", str(target),
            f"--props={props_file}",
            "--codec=h264",
            f"--crf={self.settings.remotion_crf}",
            "--pixel-format=yuv420p",
            "--muted",
            "--overwrite",
            "--log=error",
        ]
        if self.settings.remotion_concurrency > 0:
            command.append(f"--concurrency={self.settings.remotion_concurrency}")
        if self.settings.remotion_browser_executable:
            command.append(f"--browser-executable={self.settings.remotion_browser_executable}")

        try:
            _run(
                command,
                cwd=self.root,
                timeout=self.settings.remotion_timeout_seconds,
                what=f"Remotion render of {scene.label} ({scene.template})",
            )
        finally:
            props_file.unlink(missing_ok=True)

        if not target.is_file():
            raise RemotionError(f"Remotion produced no file for {scene.label}")

    def close(self) -> None:
        shutil.rmtree(self.work_dir, ignore_errors=True)
