// Speech-aligned segments (from ffmpeg silencedetect on gps.mp3, 29.88s).
// start = when the line's audio begins; the scene fills until the next start.
export interface Seg {
  start: number;
  text: string;
  emphasis?: string; // a word/phrase to punch
  scene: string;
}

export const TOTAL = 30.0;

export const SEGMENTS: Seg[] = [
  { start: 0.30,  scene: "shutdown", emphasis: "GPS",        text: "अगर कल सुबह दुनिया का GPS बंद हो जाए…" },
  { start: 2.93,  scene: "maps",     emphasis: "Google Maps", text: "तो सिर्फ Google Maps ही बंद नहीं होगा।" },
  { start: 4.96,  scene: "planes",   emphasis: "Planes",     text: "Planes को navigation में problems होंगी।" },
  { start: 7.21,  scene: "ships",    emphasis: "Ships",      text: "Ships को routes maintain करने में दिक्कत आएगी।" },
  { start: 9.83,  scene: "systems",  emphasis: "systems",    text: "Banking systems, telecom networks और कई modern systems भी प्रभावित हो सकते हैं।" },
  { start: 14.05, scene: "where",    emphasis: "आप कहां हैं", text: "क्योंकि GPS सिर्फ ये बताने के लिए नहीं है कि आप कहां हैं।" },
  { start: 17.85, scene: "time",     emphasis: "time signal", text: "ये दुनिया के कई systems को एक बेहद precise time signal भी देता है।" },
  { start: 22.40, scene: "hook",     emphasis: "interesting", text: "और सबसे interesting बात?" },
  { start: 23.97, scene: "ask",      emphasis: "location",   text: "आपके फोन में GPS सिर्फ satellites से location नहीं पूछता…" },
  { start: 27.32, scene: "reveal",   emphasis: "time",       text: "वो अंतरिक्ष में घूम रहे satellites से time भी मांगता है।" },
];
