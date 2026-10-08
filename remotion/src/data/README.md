# Map data

`india-states.geo.json` was missing from the repository: the root `.gitignore`
had a bare `data/` rule, which git applies at **every** depth, so this folder
was silently excluded and `geomap.tsx` could not build.

The rule is now anchored (`/data/`) so only the runtime data directory at the
repo root is ignored, and this folder is tracked.

The file currently holds **India's national outline only**, derived from the
`world-atlas` dependency. `geo_map`'s `highlight` parameter (which emphasises a
single state) therefore has nothing to match until a real state-level
FeatureCollection — one feature per state, each with `properties.name` — is
dropped in here to replace it.
