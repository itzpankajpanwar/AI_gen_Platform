import type React from "react";

import type { SceneProps } from "../lib/types";
import { BarChart, HighlightCallout, MapRoute, StatCounter, Timeline } from "./graphics";
import { KenBurnsPro, SplitCompare } from "./camera";
import { ChapterCard, LowerThird, Quote, TitleReveal } from "./text";

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
  title_reveal: TitleReveal,
  lower_third: LowerThird,
  quote: Quote,
  chapter_card: ChapterCard,
  timeline: Timeline,
  map_route: MapRoute,
  stat_counter: StatCounter,
  bar_chart: BarChart,
  highlight_callout: HighlightCallout,
};

export const TEMPLATE_NAMES = Object.keys(TEMPLATES);
