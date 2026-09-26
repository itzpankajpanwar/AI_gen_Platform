// Remotion Studio resolves staticFile() against ./public, but the film's fonts
// live in ../assets/fonts so ffmpeg and Remotion cannot drift apart. A render
// through the Python pipeline stages them itself; this is the studio's copy.
import { cpSync, mkdirSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const from = join(here, "..", "assets", "fonts");
const to = join(here, "public", "fonts");

mkdirSync(to, { recursive: true });
for (const name of readdirSync(from).filter((file) => /\.(ttf|otf|woff2?)$/i.test(file))) {
  cpSync(join(from, name), join(to, name));
}
