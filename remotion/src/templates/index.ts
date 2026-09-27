import type React from "react";

import type { SceneProps } from "../lib/types";
import { BarChart, HighlightCallout, MapRoute, StatCounter, Timeline } from "./graphics";
import { GeoMap } from "./geomap";
import { CutoutReveal, KenBurnsPro, SplitCompare } from "./camera";
import { ChapterCard, LowerThird, Quote, TitleReveal, WordMark } from "./text";
import { EndCard, InfoCard, IntroCard, Parallax, PullQuote } from "./premium";

/**
 * The template registry.
 *
 * Adding an effect is: write a component that takes SceneProps, register it
 * here, and add its name to the CSV vocabulary on the Python side. Nothing
 * else in the pipeline changes.
 */
export const TEMPLATES: Record<string, React.FC<SceneProps>> = {
  ken_burns_pro: KenBurnsPro,
  split_compare: SplitCompare,
  cutout_reveal: CutoutReveal,
  title_reveal: TitleReveal,
  word_mark: WordMark,
  lower_third: LowerThird,
  quote: Quote,
  chapter_card: ChapterCard,
  timeline: Timeline,
  map_route: MapRoute,
  geo_map: GeoMap,
  parallax: Parallax,
  pull_quote: PullQuote,
  info_card: InfoCard,
  intro_card: IntroCard,
  end_card: EndCard,
  stat_counter: StatCounter,
  bar_chart: BarChart,
  highlight_callout: HighlightCallout,
};

export const TEMPLATE_NAMES = Object.keys(TEMPLATES);
