import { useEffect, useState } from "react";
import { continueRender, delayRender, staticFile } from "remotion";

export const SANS = "NotoDevanagariSans";
export const SERIF = "NotoDevanagariSerif";

const FACES: [string, string][] = [
  [SANS, "fonts/NotoSansDevanagari-Regular.ttf"],
  [SERIF, "fonts/NotoSerifDevanagari-Regular.ttf"],
];

/**
 * Devanagari needs its own faces, and a render must not start before they are
 * ready or the first frames come out in a fallback font. delayRender holds the
 * renderer until document.fonts confirms both are loaded.
 */
export const useDevanagariFonts = (): boolean => {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const handle = delayRender("Loading Devanagari fonts");
    Promise.all(
      FACES.map(async ([family, path]) => {
        const face = new FontFace(family, `url(${staticFile(path)})`);
        await face.load();
        document.fonts.add(face);
      }),
    )
      .then(() => setReady(true))
      .catch(() => setReady(true)) // render in a fallback rather than hang forever
      .finally(() => continueRender(handle));
  }, []);

  return ready;
};
