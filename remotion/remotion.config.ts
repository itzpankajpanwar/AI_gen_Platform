import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
// Scenes are composited into the film by ffmpeg afterwards, so each clip is
// encoded near-losslessly here and only compressed once, at final assembly.
Config.setCodec("h264");
Config.setCrf(16);
