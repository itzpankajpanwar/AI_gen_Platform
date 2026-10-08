"""The film's locked visual system.

One film, one visual world. Everything an image generation can drift on —
stock, palette, lens, light, grain — is pinned here and appended to every
prompt, so a plate shot in chapter 1 and a plate shot in chapter 13 read as
the same production.

Two colours carry the whole documentary, and they mean something:

    SYSTEM  cold electric blue   the algorithm, data, the invisible machine
    HUMAN   warm sodium amber    the street, the worker, the city at night

Nothing else is introduced. When the picture is cold you are inside the
system; when it is warm you are in the world the system is moving through.
That contrast is the thesis, not decoration.
"""

# ----------------------------------------------------------------- palette
SYSTEM = "#4DA3FF"   # data, UI, optimisation, the machine
HUMAN  = "#E8A33D"   # sodium light, the street, human labour
INK    = "#07080A"   # near-black base
PAPER  = "#EDF1F5"   # the only light surface, used sparingly

# ------------------------------------------------------------------- stock
# Appended to every single image prompt. This is the consistency contract.
STOCK = (
    "photorealistic cinematic documentary still, shot on ARRI Alexa with 35mm anamorphic prime, "
    "naturalistic practical lighting only, shallow depth of field, deep soft shadows, "
    "restrained low contrast, muted cool-slate and warm-sodium colour palette, "
    "fine 35mm film grain, subtle lens falloff, "
    "no on-image text, no watermark, no logos, no brand names, no lens flare, "
    "no cartoon, no illustration, no 3d render look, 16:9"
)

# Context modifiers reused by whole groups of plates, so a group cannot drift.
INDIA = ("contemporary Indian metropolitan reality, authentic and unstyled, "
         "documentary realism, real wear and texture")
NIGHT = "night, sodium vapour street light, cool ambient sky, warm pools of practical light"
DAY   = "overcast daylight, soft directional light, no harsh sun"
COLD  = "cold blue-grey fluorescent and LED light, clinical, low saturation"

def prompt(body: str, *mods: str) -> str:
    """One asset's full prompt: subject, then its group modifiers, then the stock."""
    parts = [body.rstrip(". ")] + [m for m in mods if m] + [STOCK]
    return ", ".join(parts)


# =====================================================================
# THE ASSET LIBRARY
# =====================================================================
# Every photoreal plate in the film, generated ONCE and referenced by key.
# A key used by four chapters costs one generation. Keys are grouped by the
# world they belong to, which is also the order they are introduced.
#
# Scene specs reference these keys only. Nothing generates ad hoc.

ASSETS: dict[str, str] = {}

def _add(group_mods, items):
    for key, body in items.items():
        ASSETS[key] = prompt(body, *group_mods)


# ------------------------------------------------- the customer's world
# Introduced in ch1, returned to in ch14. The film opens and closes here.
_add((INDIA, NIGHT), {
 "apt_living_night":
   "A modest contemporary Indian apartment living room at night seen wide, one warm lamp, "
   "a sofa, a quiet unremarkable evening, a person sitting with a phone, face not visible",
 "apt_sofa_phone_glance":
   "Over-shoulder medium shot of a person on a sofa holding a phone low, "
   "the phone screen bright but illegible, warm room light behind",
 "phone_macro_thumb":
   "Extreme macro of a thumb resting on a dark smartphone screen, "
   "the screen off and reflective, skin texture and fingerprint visible, soft key light",
 "phone_macro_press":
   "Extreme macro of a thumb pressing a smartphone screen, the glass flexing imperceptibly, "
   "cool screen light spilling onto the fingertip, shallow focus",
 "phone_on_table_dark":
   "A smartphone face-up on a dark wooden table, screen dark, a single warm reflection "
   "across the glass, overhead close shot",
 "apt_door_inside_night":
   "An apartment front door seen from inside a dim hallway, closed, "
   "a thin line of corridor light under it, wide static shot",
 "apt_door_opening":
   "An apartment door opening inward at night, corridor light falling across the floor, "
   "a hand on the latch, no face visible",
 "apt_handover":
   "A sealed plain delivery bag passing between two pairs of hands at a doorway at night, "
   "corridor light behind, close shot, no faces",
 "apt_bag_counter":
   "A plain sealed delivery bag set down on a kitchen counter under one warm light, "
   "still life, close shot",
 "apt_corridor_night":
   "A long apartment building corridor at night, repeating doors, cool overhead tube light, "
   "nobody in frame, wide perspective shot",
 "building_exterior_night":
   "A mid-rise Indian residential apartment building at night seen from the street, "
   "scattered lit windows, parked two-wheelers below, wide static shot",
})

# ------------------------------------------------------------- the city
# The spine of ch3, ch8, ch9, ch11, ch14. Every map and network graphic is
# cut against these, so the city must feel like one real place throughout.
_add((INDIA,), {
 "city_aerial_dusk":
   "High aerial wide of a dense Indian city at dusk, tight blocks of low-rise rooftops, "
   "arterial roads threading through, haze on the horizon, lights just coming on",
 "city_aerial_night":
   "High aerial wide of the same dense Indian city at night, grid of warm street light, "
   "dark unlit rooftops, arterial roads as rivers of light",
 "city_rooftops_dense":
   "Elevated view across densely packed Indian rooftops at dusk, water tanks and cables, "
   "receding into haze, compressed telephoto",
 "city_street_night":
   "A busy Indian neighbourhood street at night, shopfronts open, two-wheelers, pedestrians, "
   "sodium light and shop light mixing, handheld documentary wide",
 "city_traffic_dense":
   "Dense slow Indian city traffic at night seen from street level, autorickshaws and "
   "motorcycles threading between cars, red tail lights, long lens compression",
 "city_flyover_night":
   "A city flyover at night from a low angle, vehicle light trails above, concrete piers, "
   "cool sky behind warm lamps",
 "city_intersection_top":
   "Top-down drone view of a busy Indian road intersection at night, vehicles as points of "
   "light, lane markings visible, perfectly vertical camera",
 "city_lane_narrow":
   "A narrow residential Indian lane at night, parked two-wheelers, a single streetlight, "
   "shutters down, quiet, wide shot",
})

# ------------------------------------------------------- the dark store
# ch4-ch7 live here, ch11 returns. The most important group in the film:
# it has to look operational and ordinary, never futuristic.
_add((INDIA,), {
 "ds_exterior_night":
   "An unmarked commercial ground-floor unit at night in an Indian commercial strip, "
   "roller shutter half raised, one bright doorway spilling cold light onto the pavement, "
   "two-wheelers parked outside, no signage, wide static shot",
 "ds_exterior_day":
   "The same unmarked ground-floor commercial unit by day, shutter up, plain façade, "
   "no signage, a goods vehicle at the kerb, wide static shot",
 "ds_doorway_from_inside":
   "Looking out from inside a brightly lit storeroom through its doorway to a dark street, "
   "silhouettes of parked two-wheelers outside, wide shot",
})
_add((COLD,), {
 "ds_aisle_wide":
   "Interior of a compact urban fulfilment storeroom, tall steel shelving racks in tight "
   "parallel aisles packed with everyday packaged groceries, concrete floor, overhead tube "
   "lights, no customers, wide symmetrical shot down one aisle",
 "ds_aisle_low":
   "Low wide angle looking up a narrow aisle of packed grocery shelving, racks converging "
   "overhead, concrete floor in foreground, nobody in frame",
 "ds_shelf_face_macro":
   "Macro of one shelf face of packed everyday grocery packets and bottles, generic "
   "unbranded packaging, small white barcode shelf labels on the rail, shallow focus",
 "ds_bin_labels_macro":
   "Extreme macro of a printed alphanumeric shelf location label on a steel rack rail, "
   "slightly worn, shallow focus falling off fast",
 "ds_chiller":
   "A glass-door refrigerated cabinet in a storeroom stacked with milk pouches and cartons, "
   "cold interior light, condensation on the glass, medium shot",
 "ds_topdown_floor":
   "Overhead floor-plan photograph of a compact fulfilment storeroom taken from the ceiling "
   "with the camera aimed straight down at ninety degrees, orthographic nadir view, the whole "
   "room visible at once corner to corner, shelving racks read as long parallel rectangles "
   "seen from directly above, wide clear strips of bare concrete floor between them forming "
   "aisles, no perspective convergence, no horizon, no walls visible from the side, "
   "flat even overhead light, architectural survey clarity",
 "ds_picker_aisle":
   "A warehouse worker in a plain uniform moving quickly along a grocery shelving aisle "
   "carrying a plastic tote, slight motion blur on the body, face not emphasised",
 "ds_picker_reach":
   "A worker's hands lifting a packet from a shelf into a plastic tote, close shot, "
   "shelf labels out of focus behind",
 "ds_picker_scanner":
   "A worker's hands holding a rugged handheld barcode scanner over a tote of groceries, "
   "the scanner screen glowing but illegible, close shot",
 "ds_packing_station":
   "A plain steel packing bench in a storeroom with stacked folded carry bags, a tape "
   "dispenser, a small label printer and totes of groceries waiting, medium wide shot",
 "ds_scan_macro":
   "Extreme macro of a barcode on a grocery packet with a thin red scanner line "
   "falling across it, shallow focus",
 "ds_bagging":
   "Workers' hands lowering grocery packets into a plain carry bag on a packing bench, "
   "close shot, even cold light",
 "ds_label_printer":
   "Extreme macro of a small thermal label printer extruding a printed order label, "
   "the paper curling, shallow focus",
 "ds_bag_sealed":
   "A plain sealed delivery carry bag standing closed on a steel bench with a printed "
   "label stuck to it, cold overhead light, clean still life close shot",
 "ds_inbound":
   "Stacked crates and cartons of inbound grocery stock just inside a storeroom roller "
   "shutter at night, a hand truck beside them, wide shot",
 "ds_handover":
   "An Indian warehouse worker handing a sealed delivery bag to an Indian delivery rider in "
   "a helmet at a storeroom doorway at night, both South Asian, cold light inside and warm "
   "sodium street light outside, medium shot",
 "ds_riders_outside":
   "Several helmeted delivery riders waiting beside their parked motorcycles outside a lit "
   "commercial doorway at night, insulated delivery boxes on the bikes, no branding, wide",
})

# ---------------------------------------------------------- the products
# The order itself. Four plates, reused in ch1, ch5, ch7, ch14.
_add((COLD,), {
 "p_milk":
   "Macro still life of a plain polythene milk pouch on a cold steel surface, "
   "condensation beads, generic unbranded packaging, shallow focus",
 "p_chips":
   "Macro still life of a plain foil snack packet standing on a cold steel surface, "
   "generic unbranded packaging, soft specular highlight along the foil",
 "p_shampoo":
   "Macro still life of a plain white plastic shampoo bottle on a cold steel surface, "
   "generic unbranded packaging, soft gradient highlight",
 "p_drink":
   "Macro still life of a plain glass bottle of a cold soft drink on a steel surface, "
   "condensation running down the glass, generic unbranded, shallow focus",
 "p_four_items":
   "Four everyday grocery items — a milk pouch, a foil snack packet, a white plastic "
   "bottle and a cold glass drink bottle — arranged in a row on a cold steel surface, "
   "generic unbranded packaging, even light, clean product still",
})

# ------------------------------------------------------------- the rider
_add((INDIA, NIGHT), {
 "rider_waiting_portrait":
   "A delivery rider in a plain unbranded jacket and helmet standing beside a motorcycle "
   "at night, visor up, face in shadow, insulated delivery box behind the seat, medium shot",
 "rider_phone_mount":
   "Close shot of a rider's gloved hand and a phone clamped to motorcycle handlebars at "
   "night, the screen bright but illegible, street light behind",
 "rider_bag_load":
   "A sealed delivery bag being lowered into an insulated box on the back of a motorcycle "
   "at night, close shot, hands only",
 "rider_moving_track":
   "Tracking shot alongside a delivery motorcycle moving through a city street at night, "
   "rider in plain jacket and helmet, background streaked with motion blur",
 "rider_through_traffic":
   "A delivery motorcycle threading between slow cars and autorickshaws at night from a "
   "low rear angle, tail lights ahead, compressed long lens",
 "rider_lane_arrive":
   "A delivery motorcycle slowing to a stop in a narrow residential lane at night, "
   "single streetlight, parked two-wheelers, wide shot",
 "rider_lobby_stairs":
   "A helmeted delivery rider carrying a plain sealed bag up a dim apartment building "
   "stairwell at night, cool tube light, motion in the step, medium shot from above",
})

# ------------------------------------------------- the old way (ch13)
# Deliberately warmer, wider and slower than the dark store, so the
# comparison reads before a single word of narration lands.
_add((INDIA, DAY), {
 "sm_aisle":
   "A large traditional supermarket aisle with shoppers pushing trolleys, bright even "
   "ceiling light, long sightlines, promotional shelf ends, wide shot",
 "sm_queue":
   "A queue of shoppers with full trolleys waiting at a supermarket checkout counter, "
   "bright retail light, patient boredom, medium wide shot",
 "sm_parking":
   "A half-full open parking area outside a city retail building, two-wheelers and cars, "
   "overcast flat light, wide shot",
 "sm_shopper_car":
   "A shopper loading grocery bags into the back of a car in a parking area, "
   "flat overcast light, medium shot, face not visible",
})

# ------------------------------------------- the machine's own hardware
# Used only where the film must show that the "system" is physical too.
_add((COLD,), {
 "dc_aisle":
   "A dark data centre aisle, two walls of server racks, hundreds of small status lights, "
   "cold blue ambient light, perspective receding, nobody present, wide shot",
 "dc_fibre_macro":
   "Extreme macro of bundled fibre optic patch cables in a server rack, "
   "cool light, very shallow focus",
})

ASSET_KEYS = frozenset(ASSETS)

if __name__ == "__main__":
    print(f"{len(ASSETS)} keyed plates")
    for k in sorted(ASSETS):
        print(f"  {k}")
