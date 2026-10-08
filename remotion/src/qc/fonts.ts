import { useEffect, useState } from "react";
import { continueRender, delayRender, staticFile } from "remotion";
import { DISPLAY, SANS } from "./theme";

/**
 * This film's on-screen typography is English and numeric only — labels,
 * counters, data — so it is set in Inter, with Inter Display for headline
 * sizes where the tighter optical face reads better. The narration carries
 * the Hindi; nothing Devanagari is ever drawn, which is also why these
 * templates can rely on ordinary CSS text layout.
 *
 * A render must not start before the faces resolve or the first frames come
 * out in a fallback, so delayRender holds the renderer until they do.
 */
const FACES: [string, string, number][] = [
  [SANS, "fonts/Inter-Regular.otf", 400],
  [SANS, "fonts/Inter-Medium.otf", 500],
  [SANS, "fonts/Inter-SemiBold.otf", 600],
  [DISPLAY, "fonts/InterDisplay-Light.otf", 300],
  [DISPLAY, "fonts/InterDisplay-SemiBold.otf", 600],
];

export const useFilmFonts = (): boolean => {
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const handle = delayRender("Loading Inter");
    Promise.all(
      FACES.map(async ([family, path, weight]) => {
        const face = new FontFace(family, `url(${staticFile(path)})`, { weight: String(weight) });
        await face.load();
        document.fonts.add(face);
      }),
    )
      .then(() => setReady(true))
      .catch(() => setReady(true))
      .finally(() => continueRender(handle));
  }, []);
  return ready;
};
