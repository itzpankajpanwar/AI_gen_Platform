export interface SceneProps {
  /** Filename of the generated still, resolved from the public dir. Optional for pure-graphic scenes. */
  image: string;
  /** Which template renders this scene. */
  template: string;
  /** Primary copy — headline, caption, number, quote. */
  text: string;
  /** Free-form template inputs from the CSV's animation_params column. */
  params: Record<string, string>;
  /** Accent colour for graphics, so a whole film can be re-themed at once. */
  accent: string;
  /** Ink colour used on light surfaces. */
  ink: string;
}

export const DEFAULT_SCENE: SceneProps = {
  image: "",
  template: "ken_burns_pro",
  text: "",
  params: {},
  accent: "#E0A65C",
  ink: "#0B0D10",
};
