"""The animation layer.

When a row sets `animation`, that preset takes over the scene's motion and its
on-screen text — `ken_burns` and `text_type` are ignored. `grade` and `grain`
still apply, so an animated scene keeps the film's overall look.

Each preset returns two filter lists:

* **motion**  — how the picture is framed and moves. Runs first.
* **overlay** — bars, boxes, markers and text drawn on top. Runs after the
  grade and grain so the graphics stay clean and ungraded.

Every preset accepts an optional `:value` for intensity, so `map_zoom:2.5`
pushes harder than `map_zoom`.
"""

from collections.abc import Callable
from dataclasses import dataclass

ACCENT = "0xE0A65C"
INK = "0x0B0D10"


@dataclass(frozen=True)
class AnimationContext:
    width: int
    height: int
    seconds: float
    fps: int
    text: str
    font: str
    value: float | None = None

    def scaled(self, ratio: float) -> int:
        return max(int(self.height * ratio), 10)


def _fit(ctx: AnimationContext) -> str:
    """Fill the frame, cropping overflow — animations assume a full bleed."""
    return (
        f"scale={ctx.width}:{ctx.height}:force_original_aspect_ratio=increase,"
        f"crop={ctx.width}:{ctx.height}"
    )


def _escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'").replace("%", r"\%")
    )


def _text(ctx: AnimationContext, *, size: float, x: str, y: str, colour: str, alpha: str) -> str:
    return (
        f"drawtext=fontfile='{ctx.font}':text='{_escape(ctx.text)}':"
        # x/y/alpha are quoted: they contain commas (max(), if()) which the
        # filter parser would otherwise read as filter separators.
        f"fontsize={ctx.scaled(size)}:fontcolor={colour}:x='{x}':y='{y}':alpha='{alpha}'"
    )


def _fade_alpha(start: float, hold: float, seconds: float) -> str:
    """Fade up over `start`, hold, then fade out over the same time."""
    out = max(seconds - hold, start + 0.01)
    return (
        f"if(lt(t,{start:.2f}),t/{start:.2f},"
        f"if(lt(t,{out:.2f}),1,max(0,({seconds:.2f}-t)/{hold:.2f})))"
    )


# ------------------------------------------------------------------ Vox family


def vox_title(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """A solid accent bar wipes in from the left, then bold text lands on it."""
    bar_h = ctx.scaled(0.16)
    bar_y = int(ctx.height * 0.60)
    grow = "min(1,t/0.45)"
    return (
        [_fit(ctx), "eq=brightness=-0.06"],
        [
            f"drawbox=x=0:y={bar_y}:w='max(1,iw*{grow})':h={bar_h}:color={ACCENT}@0.95:t=fill",
            _text(
                ctx,
                size=0.075,
                x=f"{int(ctx.width * 0.06)}",
                y=f"{bar_y + int(bar_h * 0.18)}",
                colour=INK,
                alpha="max(0,min(1,(t-0.35)/0.35))",
            ),
        ],
    )


def vox_lower_bar(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """Full-width bottom bar that wipes in carrying a caption."""
    bar_h = ctx.scaled(0.11)
    bar_y = ctx.height - bar_h - int(ctx.height * 0.06)
    return (
        [_fit(ctx)],
        [
            f"drawbox=x=0:y={bar_y}:w='max(1,iw*min(1,t/0.4))':h={bar_h}:color={INK}@0.82:t=fill",
            f"drawbox=x=0:y={bar_y}:w='max(1,iw*min(1,t/0.4))':h={max(bar_h // 14, 3)}:"
            f"color={ACCENT}@0.95:t=fill",
            _text(
                ctx,
                size=0.048,
                x=f"{int(ctx.width * 0.05)}",
                y=f"{bar_y + int(bar_h * 0.30)}",
                colour="white",
                alpha="max(0,min(1,(t-0.3)/0.3))",
            ),
        ],
    )


def vox_highlight(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """An outline box draws itself around the centre to point at something."""
    scale = ctx.value or 0.45
    box_w = int(ctx.width * scale)
    box_h = int(ctx.height * scale)
    x = (ctx.width - box_w) // 2
    y = (ctx.height - box_h) // 2
    thickness = max(ctx.scaled(0.008), 3)
    return (
        [_fit(ctx), "eq=brightness=-0.04"],
        [
            f"drawbox=x={x}:y={y}:w='max(1,{box_w}*min(1,t/0.5))':h={box_h}:"
            f"color={ACCENT}@0.9:t={thickness}",
            _text(
                ctx,
                size=0.040,
                x=f"{x}",
                y=f"{max(y - ctx.scaled(0.060), 8)}",
                colour=ACCENT,
                alpha="max(0,min(1,(t-0.5)/0.3))",
            ),
        ],
    )


def vox_stat(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """A single large figure rises into a dimmed frame — for numbers and claims."""
    rise = ctx.scaled(0.05)
    return (
        [_fit(ctx), "eq=brightness=-0.22:saturation=0.7"],
        [
            _text(
                ctx,
                size=0.16,
                x="(w-text_w)/2",
                y=f"(h-text_h)/2+{rise}*max(0,1-t/0.6)",
                colour="white",
                alpha=_fade_alpha(0.45, 0.5, ctx.seconds),
            )
        ],
    )


# ------------------------------------------------------------------ Map family


def map_zoom(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """Accelerating push into the centre, the way a map dives to a location."""
    target = ctx.value or 1.8
    frames = max(int(round(ctx.seconds * ctx.fps)), 1)
    zoom = f"1+pow(on/{frames},2)*{target - 1:.4f}"
    return (
        [
            f"scale={ctx.width * 2}:{ctx.height * 2}:force_original_aspect_ratio=increase,"
            f"crop={ctx.width * 2}:{ctx.height * 2}",
            f"zoompan=z='min({zoom},{target:.4f})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={ctx.width}x{ctx.height}:fps={ctx.fps}",
        ],
        [
            _text(
                ctx,
                size=0.045,
                x="(w-text_w)/2",
                y=f"h*0.82",
                colour="white",
                alpha="max(0,min(1,(t-0.6)/0.4))",
            )
        ]
        if ctx.text
        else [],
    )


def map_pin(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """A marker drops onto the centre and settles, then names the place."""
    size = max(ctx.scaled(0.030), 8)
    x = (ctx.width - size) // 2
    settle = ctx.height // 2
    # Ease-out drop: fast at first, easing into place by 0.6s.
    drop = f"{settle}-({settle})*pow(max(0,1-t/0.6),2)"
    stem_h = ctx.scaled(0.055)
    return (
        [_fit(ctx), "eq=brightness=-0.05"],
        [
            f"drawbox=x={x + size // 2 - 1}:y='{drop}':w=3:h={stem_h}:color={ACCENT}@0.95:t=fill",
            f"drawbox=x={x}:y='{drop}-{size}':w={size}:h={size}:color={ACCENT}@0.95:t=fill",
            _text(
                ctx,
                size=0.042,
                x="(w-text_w)/2",
                y=f"{settle + stem_h + ctx.scaled(0.02)}",
                colour="white",
                alpha="max(0,min(1,(t-0.7)/0.35))",
            ),
        ],
    )


def map_reveal(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """The frame lifts out of darkness while a frame-line opens outward."""
    inset = int(min(ctx.width, ctx.height) * 0.08)
    thickness = max(ctx.scaled(0.006), 2)
    return (
        [_fit(ctx), "eq=brightness='-0.35+0.35*min(1,t/1.2)':eval=frame"],
        [
            f"drawbox=x='{ctx.width // 2}-({ctx.width // 2 - inset})*min(1,t/0.9)':"
            f"y='{ctx.height // 2}-({ctx.height // 2 - inset})*min(1,t/0.9)':"
            f"w='max(2,2*({ctx.width // 2 - inset})*min(1,t/0.9))':"
            f"h='max(2,2*({ctx.height // 2 - inset})*min(1,t/0.9))':"
            f"color={ACCENT}@0.55:t={thickness}",
            _text(
                ctx,
                size=0.042,
                x=f"{inset + ctx.scaled(0.02)}",
                y=f"{inset + ctx.scaled(0.02)}",
                colour="white",
                alpha="max(0,min(1,(t-0.9)/0.4))",
            ),
        ]
        if ctx.text
        else [],
    )


# ---------------------------------------------------------- Documentary family


def doc_archival(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """Vignette, heavy grain and a slow gate weave — old footage on a projector."""
    weave = ctx.value or 4.0
    pad = int(weave * 2)
    return (
        [
            f"scale={ctx.width + pad * 2}:{ctx.height + pad * 2}:"
            f"force_original_aspect_ratio=increase",
            f"crop={ctx.width}:{ctx.height}:"
            f"'{pad}+{weave:.1f}*sin(t*2.1)':'{pad}+{weave:.1f}*cos(t*1.7)'",
            "eq=saturation=0.72:contrast=1.12",
            "noise=alls=26:allf=t+u",
            "vignette=angle=PI/4.4",
        ],
        [
            _text(
                ctx,
                size=0.038,
                x=f"{int(ctx.width * 0.05)}",
                y=f"h-h*0.12",
                colour="0xe8d9bd",
                alpha=_fade_alpha(0.5, 0.5, ctx.seconds),
            )
        ]
        if ctx.text
        else [],
    )


def doc_photo(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """A bordered print on a dark table, pushed into slowly."""
    frames = max(int(round(ctx.seconds * ctx.fps)), 1)
    inner_w = int(ctx.width * 0.78) // 2 * 2
    inner_h = int(ctx.height * 0.78) // 2 * 2
    border = max(ctx.scaled(0.022), 6)
    return (
        [
            f"scale={inner_w}:{inner_h}:force_original_aspect_ratio=increase,"
            f"crop={inner_w}:{inner_h}",
            f"pad={inner_w + border * 2}:{inner_h + border * 2}:{border}:{border}:color=0xF2EEE4",
            f"pad={ctx.width}:{ctx.height}:(ow-iw)/2:(oh-ih)/2:color=0x141414",
            f"zoompan=z='min(1+(on/{frames})*0.10,1.10)':x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':d={frames}:s={ctx.width}x{ctx.height}:fps={ctx.fps}",
        ],
        [
            _text(
                ctx,
                size=0.036,
                x="(w-text_w)/2",
                y=f"h*0.90",
                colour="0xcfc6b4",
                alpha=_fade_alpha(0.5, 0.5, ctx.seconds),
            )
        ]
        if ctx.text
        else [],
    )


def doc_title_card(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """The picture recedes almost to black so a statement can carry the beat."""
    return (
        [_fit(ctx), "eq=brightness=-0.55:saturation=0.35"],
        [
            _text(
                ctx,
                size=0.070,
                x="(w-text_w)/2",
                y="(h-text_h)/2",
                colour="white",
                alpha=_fade_alpha(0.7, 0.7, ctx.seconds),
            )
        ],
    )


def doc_timeline(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """A progress rule creeps along the foot of the frame under a year label."""
    bar_y = int(ctx.height * 0.90)
    track_h = max(ctx.scaled(0.006), 2)
    margin = int(ctx.width * 0.08)
    span = ctx.width - margin * 2
    return (
        [_fit(ctx), "eq=brightness=-0.08"],
        [
            f"drawbox=x={margin}:y={bar_y}:w={span}:h={track_h}:color=white@0.28:t=fill",
            f"drawbox=x={margin}:y={bar_y}:"
            f"w='max(1,{span}*min(1,t/{max(ctx.seconds - 0.3, 0.5):.2f}))':"
            f"h={track_h}:color={ACCENT}@0.95:t=fill",
            _text(
                ctx,
                size=0.040,
                x=f"{margin}",
                y=f"{bar_y - ctx.scaled(0.065)}",
                colour="white",
                alpha="max(0,min(1,t/0.4))",
            ),
        ],
    )




# ------------------------------------------------------------ Cinematic family


def cine_letterbox(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """Scope bars slide in and the frame eases forward — the widescreen beat."""
    ratio = ctx.value or 2.39
    bar = max(int((ctx.height - ctx.width / ratio) / 2), 4)
    frames = max(int(round(ctx.seconds * ctx.fps)), 1)
    return (
        [
            f"scale={ctx.width * 2}:{ctx.height * 2}:force_original_aspect_ratio=increase,"
            f"crop={ctx.width * 2}:{ctx.height * 2}",
            f"zoompan=z='min(1+(on/{frames})*0.06,1.06)':x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':d={frames}:s={ctx.width}x{ctx.height}:fps={ctx.fps}",
        ],
        [
            # A box of zero height is invalid, so the bars never fully retract.
            f"drawbox=x=0:y=0:w=iw:h='max(1,{bar}*min(1,t/0.7))':color=black:t=fill",
            f"drawbox=x=0:y='ih-max(1,{bar}*min(1,t/0.7))':w=iw:"
            f"h='max(1,{bar}*min(1,t/0.7))':color=black:t=fill",
        ]
        + (
            [
                _text(
                    ctx,
                    size=0.045,
                    x="(w-text_w)/2",
                    # drawtext exposes the frame as w/h; ih is a drawbox variable.
                    y=f"h-{bar}+{ctx.scaled(0.02)}",
                    colour="white",
                    alpha="max(0,min(1,(t-0.8)/0.4))",
                )
            ]
            if ctx.text
            else []
        ),
    )


def cine_handheld(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """Continuous micro-drift, as if held rather than locked off."""
    amp = ctx.value or 6.0
    pad = int(amp * 2)
    return (
        [
            f"scale={ctx.width + pad * 2}:{ctx.height + pad * 2}:"
            f"force_original_aspect_ratio=increase",
            f"crop={ctx.width}:{ctx.height}:"
            f"'{pad}+{amp:.1f}*sin(t*0.9)+{amp * 0.4:.1f}*sin(t*2.7)':"
            f"'{pad}+{amp:.1f}*cos(t*0.7)+{amp * 0.4:.1f}*cos(t*3.1)'",
        ],
        [],
    )


def cine_dolly(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """An eased lateral track — accelerates in, decelerates out, unlike a linear pan."""
    frames = max(int(round(ctx.seconds * ctx.fps)), 1)
    zoom = ctx.value or 1.18
    # smoothstep keeps the move from starting and stopping abruptly.
    progress = f"(pow(on/{frames},2)*(3-2*(on/{frames})))"
    return (
        [
            f"scale={ctx.width * 2}:{ctx.height * 2}:force_original_aspect_ratio=increase,"
            f"crop={ctx.width * 2}:{ctx.height * 2}",
            f"zoompan=z='{zoom:.4f}':x='(iw-iw/zoom)*{progress}':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={ctx.width}x{ctx.height}:fps={ctx.fps}",
        ],
        [],
    )


def cine_punch(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """A fast snap in that settles almost immediately — for a hard beat."""
    frames = max(int(round(ctx.seconds * ctx.fps)), 1)
    target = ctx.value or 1.22
    snap = max(int(frames * 0.12), 2)
    zoom = f"if(lt(on,{snap}),1+(on/{snap})*{target - 1:.4f},{target:.4f})"
    return (
        [
            f"scale={ctx.width * 2}:{ctx.height * 2}:force_original_aspect_ratio=increase,"
            f"crop={ctx.width * 2}:{ctx.height * 2}",
            f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={ctx.width}x{ctx.height}:fps={ctx.fps}",
        ],
        [],
    )


# --------------------------------------------------------------- Reveal family


def reveal_wipe(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """A black edge travels across, uncovering the picture behind it."""
    speed = ctx.value or 0.9
    return (
        [_fit(ctx)],
        [
            f"drawbox=x='iw*min(1,t/{speed:.2f})':y=0:w=iw:h=ih:color=black:t=fill",
            f"drawbox=x='iw*min(1,t/{speed:.2f})':y=0:w={max(ctx.scaled(0.006), 2)}:h=ih:"
            f"color={ACCENT}@0.9:t=fill",
        ],
    )


def reveal_bars(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """Horizontal shutters retract to expose the frame."""
    count = int(ctx.value or 5)
    band = ctx.height / count
    overlay = []
    for index in range(count):
        top = int(index * band)
        # Alternate bars leave from opposite edges.
        if index % 2 == 0:
            x = f"'-iw*min(1,t/0.8)'"
        else:
            x = f"'iw*min(1,t/0.8)'"
        overlay.append(
            f"drawbox=x={x}:y={top}:w=iw:h={int(band) + 2}:color=black:t=fill"
        )
    return ([_fit(ctx), "eq=brightness=-0.02"], overlay)


def reveal_iris(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """A rectangular iris opens from the centre outward."""
    speed = ctx.value or 0.9
    half_h = ctx.height // 2
    half_w = ctx.width // 2
    grow = f"min(1,t/{speed:.2f})"
    # The covers shrink toward the edges but never reach zero: a drawbox with a
    # zero dimension falls back to the full frame, and one with a negative origin
    # is dropped entirely. A 1px residue at each edge is invisible.
    return (
        [_fit(ctx)],
        [
            f"drawbox=x=0:y=0:w=iw:h='max(1,{half_h}*(1-{grow}))':color=black:t=fill",
            f"drawbox=x=0:y='{ctx.height}-max(1,{half_h}*(1-{grow}))':w=iw:"
            f"h='max(1,{half_h}*(1-{grow}))':color=black:t=fill",
            f"drawbox=x=0:y=0:w='max(1,{half_w}*(1-{grow}))':h=ih:color=black:t=fill",
            f"drawbox=x='{ctx.width}-max(1,{half_w}*(1-{grow}))':y=0:"
            f"w='max(1,{half_w}*(1-{grow}))':h=ih:color=black:t=fill",
        ],
    )


def reveal_fade_up(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """Lifts out of black with a slow settle — a gentle way into a chapter."""
    frames = max(int(round(ctx.seconds * ctx.fps)), 1)
    hold = ctx.value or 1.4
    return (
        [
            f"scale={ctx.width * 2}:{ctx.height * 2}:force_original_aspect_ratio=increase,"
            f"crop={ctx.width * 2}:{ctx.height * 2}",
            f"zoompan=z='max(1.10-(on/{frames})*0.10,1.0)':x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':d={frames}:s={ctx.width}x{ctx.height}:fps={ctx.fps}",
            f"eq=brightness='-0.6+0.6*min(1,t/{hold:.2f})':eval=frame",
        ],
        [],
    )


# ----------------------------------------------------------- Typography family


def type_quote(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """A pulled quotation on a dimmed frame, under a short accent rule."""
    rule_w = int(ctx.width * 0.10)
    rule_x = (ctx.width - rule_w) // 2
    rule_y = int(ctx.height * 0.33)
    return (
        [_fit(ctx), "eq=brightness=-0.35:saturation=0.6"],
        [
            f"drawbox=x={rule_x}:y={rule_y}:w='max(1,{rule_w}*min(1,t/0.5))':"
            f"h={max(ctx.scaled(0.008), 3)}:color={ACCENT}@0.95:t=fill",
            _text(
                ctx,
                size=0.062,
                x="(w-text_w)/2",
                y="(h-text_h)/2",
                colour="white",
                alpha=_fade_alpha(0.6, 0.6, ctx.seconds),
            ),
        ],
    )


def type_stack(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """Lines appear one after another. Separate them with | in text_value."""
    lines = [part.strip() for part in ctx.text.split("|") if part.strip()][:4]
    if not lines:
        lines = [ctx.text]
    size = 0.058 if len(lines) <= 2 else 0.046
    line_h = ctx.scaled(size * 1.55)
    block_top = (ctx.height - line_h * len(lines)) // 2
    overlay = []
    for index, line in enumerate(lines):
        start = 0.25 + index * 0.45
        overlay.append(
            f"drawtext=fontfile='{ctx.font}':text='{_escape(line)}':"
            f"fontsize={ctx.scaled(size)}:fontcolor=white:"
            f"x='{int(ctx.width * 0.10)}':y='{block_top + index * line_h}':"
            f"alpha='max(0,min(1,(t-{start:.2f})/0.4))'"
        )
    return ([_fit(ctx), "eq=brightness=-0.30:saturation=0.7"], overlay)


def type_underline(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """A term with a rule drawing itself underneath — for defining something."""
    y = int(ctx.height * 0.46)
    rule_y = y + ctx.scaled(0.085)
    margin = int(ctx.width * 0.12)
    return (
        [_fit(ctx), "eq=brightness=-0.25"],
        [
            _text(
                ctx,
                size=0.065,
                x="(w-text_w)/2",
                y=f"{y}",
                colour="white",
                alpha="max(0,min(1,t/0.4))",
            ),
            f"drawbox=x={margin}:y={rule_y}:"
            f"w='max(1,{ctx.width - margin * 2}*max(0,min(1,(t-0.4)/0.6)))':"
            f"h={max(ctx.scaled(0.007), 3)}:color={ACCENT}@0.95:t=fill",
        ],
    )


def type_counter(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """A figure counts up to its value — years, totals, populations."""
    try:
        target = int(float(ctx.text.replace(",", "").strip()))
    except ValueError:
        target = 0
    climb = max(min(ctx.value or ctx.seconds * 0.6, ctx.seconds), 0.3)
    # %{eif} evaluates per frame; the colons inside must be escaped for the parser.
    counting = f"%{{eif\\:floor(min(t/{climb:.2f},1)*{target})\\:d}}"
    return (
        [_fit(ctx), "eq=brightness=-0.28:saturation=0.65"],
        [
            f"drawtext=fontfile='{ctx.font}':text='{counting}':"
            f"fontsize={ctx.scaled(0.17)}:fontcolor=white:"
            f"x='(w-text_w)/2':y='(h-text_h)/2':alpha='max(0,min(1,t/0.3))'"
        ],
    )


# ------------------------------------------------------------- Emphasis family


def beat_flash(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """A white hit that decays fast — punctuation between ideas."""
    decay = ctx.value or 0.45
    return (
        [_fit(ctx)],
        [
            # A single blown frame, then an exponential falloff back to normal.
            "drawbox=x=0:y=0:w=iw:h=ih:color=white@0.95:t=fill:enable='lt(t,0.06)'",
            f"eq=brightness='max(0,0.55*exp(-t*{4.0 / decay:.2f}))':eval=frame",
        ],
    )


def beat_pulse(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """A slow breathing brightness — keeps a long hold from going dead."""
    rate = ctx.value or 1.1
    return (
        [
            _fit(ctx),
            f"eq=brightness='0.05*sin(t*{rate:.2f})':"
            f"saturation='1+0.06*sin(t*{rate:.2f})':eval=frame",
        ],
        [],
    )


def beat_shake(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """A sharp knock that settles — impact, rupture, a door slamming."""
    amp = ctx.value or 14.0
    pad = int(amp * 2)
    return (
        [
            f"scale={ctx.width + pad * 2}:{ctx.height + pad * 2}:"
            f"force_original_aspect_ratio=increase",
            f"crop={ctx.width}:{ctx.height}:"
            f"'{pad}+{amp:.1f}*exp(-t*3.2)*sin(t*32)':"
            f"'{pad}+{amp * 0.7:.1f}*exp(-t*3.2)*cos(t*27)'",
        ],
        [],
    )


# -------------------------------------------------------------- Archive family


def paper_redact(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """Censor bars sweep across the frame — suppression, records, erasure."""
    count = int(ctx.value or 3)
    overlay = []
    for index in range(count):
        y = int(ctx.height * (0.30 + index * 0.14))
        width = int(ctx.width * (0.5 - index * 0.08))
        start = 0.3 + index * 0.35
        overlay.append(
            f"drawbox=x={int(ctx.width * 0.14)}:y={y}:"
            f"w='max(1,{width}*max(0,min(1,(t-{start:.2f})/0.30)))':"
            f"h={ctx.scaled(0.055)}:color=black@0.92:t=fill"
        )
    if ctx.text:
        overlay.append(
            _text(
                ctx,
                size=0.038,
                x=f"{int(ctx.width * 0.14)}",
                y=f"{int(ctx.height * 0.72)}",
                colour="0xd8cdb8",
                alpha=f"max(0,min(1,(t-{0.3 + count * 0.35:.2f})/0.4))",
            )
        )
    return ([_fit(ctx), "eq=saturation=0.5:contrast=1.12", "vignette=angle=PI/5"], overlay)


def paper_highlight(ctx: AnimationContext) -> tuple[list[str], list[str]]:
    """A translucent marker sweeps over a line, then the caption lands."""
    y = int(ctx.height * 0.44)
    margin = int(ctx.width * 0.16)
    return (
        [_fit(ctx), "eq=brightness=-0.12"],
        [
            f"drawbox=x={margin}:y={y}:w='max(1,{ctx.width - margin * 2}*min(1,t/0.7))':"
            f"h={ctx.scaled(0.09)}:color={ACCENT}@0.40:t=fill",
            _text(
                ctx,
                size=0.050,
                x="(w-text_w)/2",
                y=f"{y + ctx.scaled(0.012)}",
                colour="white",
                alpha="max(0,min(1,(t-0.45)/0.35))",
            ),
        ],
    )


ANIMATIONS: dict[str, Callable[[AnimationContext], tuple[list[str], list[str]]]] = {
    "vox_title": vox_title,
    "vox_lower_bar": vox_lower_bar,
    "vox_highlight": vox_highlight,
    "vox_stat": vox_stat,
    "map_zoom": map_zoom,
    "map_pin": map_pin,
    "map_reveal": map_reveal,
    "doc_archival": doc_archival,
    "doc_photo": doc_photo,
    "doc_title_card": doc_title_card,
    "doc_timeline": doc_timeline,
    "cine_letterbox": cine_letterbox,
    "cine_handheld": cine_handheld,
    "cine_dolly": cine_dolly,
    "cine_punch": cine_punch,
    "reveal_wipe": reveal_wipe,
    "reveal_bars": reveal_bars,
    "reveal_iris": reveal_iris,
    "reveal_fade_up": reveal_fade_up,
    "type_quote": type_quote,
    "type_stack": type_stack,
    "type_underline": type_underline,
    "type_counter": type_counter,
    "beat_flash": beat_flash,
    "beat_pulse": beat_pulse,
    "beat_shake": beat_shake,
    "paper_redact": paper_redact,
    "paper_highlight": paper_highlight,
}

TEXT_REQUIRED = {
    "vox_title",
    "vox_lower_bar",
    "vox_stat",
    "doc_title_card",
    "doc_timeline",
    "type_quote",
    "type_stack",
    "type_underline",
    "type_counter",
    "paper_highlight",
}

# Presets whose text is a headline rather than a caption read better in serif.
SERIF_PRESETS = {"doc_title_card", "vox_stat", "type_quote", "type_counter"}


def build_animation(name: str, ctx: AnimationContext) -> tuple[list[str], list[str]]:
    preset = ANIMATIONS.get(name)
    if preset is None:
        raise KeyError(name)
    return preset(ctx)
