# -*- coding: utf-8 -*-
"""THE TEN MINUTES — the film script.

One order, followed from a thumb on a screen to a knock on a door, used to
explain the machine behind it. Fourteen chapters.

This file is the screenplay. It holds the narration, the cut, and what every
beat is looking at. It holds no look or style — that lives in `look.py` — and
no timing, because timing is derived from the narration itself.

HOW A SCENE WORKS
    {"n": "<spoken Hindi line>", "hold": 0.8, "beats": [...]}

The scene lasts exactly as long as its narration clip, plus `hold` seconds of
silence after it. One spoken clip per scene, never re-cut, so voice and
picture are locked by construction.

    {"silent": 4.0, "beats": [...]}

A scene with no narration at all — a breath, or a reveal that words would
spoil. There are nine of these and they are deliberate.

HOW A BEAT WORKS
    {"img": "ds_aisle_wide", "kb": "zoom_in:1.08", "w": 1.5}
        a photoreal plate from the keyed library, with a camera move and a
        duration weight (how much of the scene it gets; default 1)

    {"anim": "city_map", "p": {...}, "text": "..."}
        a motion graphic, drawn rather than generated

    {"img": "city_street_night", "anim": "metric_strip", "p": {...}}
        a graphic composited over a plate

Narration is written for the ear, not the page: short sentences, numbers
spoken as words, English technical terms kept where an Indian speaker would
actually keep them (app, order, dark store, inventory, rider). On-screen
typography is English and numeric only — labels, counters, data — exactly the
restrained set the brief calls for.
"""

FILM = {
    "slug": "ten-minutes",
    "title": "THE TEN MINUTES",
    "subtitle": "How a 10-minute delivery actually works",
    "brand": "THE QUIET STORY",
    "fps": 24,
    "width": 1920,
    "height": 1080,
    "grade": "cold_film",
    "grain": 5,
}

# =====================================================================
# 01 — THE ORDER
# =====================================================================
# Open on the ordinary. Do not explain. The job of this chapter is to make a
# button feel heavier than it looks, and to plant the ten minutes as a
# question rather than a boast.
CH01 = {
 "id": 1, "title": "THE ORDER", "music": "quiet_pulse", "ambience": "room_night",
 "scenes": [
  {"silent": 4.2, "beats": [
    {"img": "apt_living_night", "kb": "zoom_in:1.05", "w": 1}]},

  {"n": "रात के पौने दस बजे। शहर के एक साधारण फ़्लैट में किसी को याद आता है कि घर में दूध ख़त्म हो गया है।",
   "hold": 0.6, "beats": [
    {"img": "apt_living_night", "kb": "pan_right", "w": 1.2},
    {"img": "apt_sofa_phone_glance", "kb": "zoom_in:1.07", "w": 1}]},

  {"n": "दस साल पहले इसका मतलब होता — कल सुबह। पाँच साल पहले — शायद आज रात बाहर निकलना पड़ता।",
   "hold": 0.4, "beats": [
    {"img": "city_lane_narrow", "kb": "zoom_out:1.12", "w": 1},
    {"img": "sm_queue", "kb": "pan_left", "w": 1}]},

  {"n": "आज इसका मतलब है — एक ऐप, चार चीज़ें, और एक बटन।",
   "hold": 0.3, "beats": [
    {"img": "phone_macro_thumb", "kb": "zoom_in:1.10", "w": 1}]},

  {"n": "दूध। चिप्स। शैम्पू। एक ठंडा ड्रिंक। कुल तीन सौ पचास रुपये।",
   "hold": 0.5, "beats": [
    {"anim": "phone_ui", "p": {"mode": "cart", "items": "Milk 500ml|Potato chips|Shampoo 180ml|Cold drink 750ml",
                               "prices": "28|40|165|117", "total": "350"}, "w": 1}]},

  {"n": "और फिर, वो बटन।",
   "hold": 0.2, "beats": [
    {"anim": "phone_ui", "p": {"mode": "button", "label": "PLACE ORDER"}, "w": 1}]},

  # The press itself gets silence and a sub-bass hit. Nothing is explained.
  {"silent": 3.4, "beats": [
    {"img": "phone_macro_press", "kb": "zoom_in:1.14", "w": 1.3},
    {"anim": "phone_ui", "p": {"mode": "confirmed", "label": "ORDER PLACED"}, "w": 1}]},

  {"n": "इस बटन के दबने और दरवाज़े पर दस्तक होने के बीच, औसतन दस मिनट का फ़ासला है।",
   "hold": 0.8, "beats": [
    {"anim": "clock", "p": {"value": "10:00", "label": "PROMISED", "mode": "hero"}, "w": 1}]},

  {"n": "दस मिनट में क्या-क्या होता है, ये हमें कभी दिखाई नहीं देता।",
   "hold": 0.5, "beats": [
    {"img": "apt_door_inside_night", "kb": "zoom_in:1.06", "w": 1}]},

  {"n": "इन दस मिनटों में एक पूरी मशीन चलती है। रियल एस्टेट, इन्वेंटरी, एल्गोरिद्म, और इंसानी मेहनत से बनी एक मशीन — जो आपके शहर में, आपके आसपास, चौबीसों घंटे चल रही है।",
   "hold": 0.6, "beats": [
    {"img": "city_aerial_night", "kb": "zoom_out:1.16", "w": 1.4},
    {"img": "ds_riders_outside", "kb": "pan_right", "w": 1},
    {"img": "ds_aisle_wide", "kb": "zoom_in:1.08", "w": 1},
    {"img": "dc_aisle", "kb": "pan_left", "w": 1}]},

  {"n": "ये फ़िल्म उस मशीन के बारे में है। और उसे समझने के लिए हम सिर्फ़ एक ऑर्डर का पीछा करेंगे।",
   "hold": 1.4, "beats": [
    {"anim": "title_card", "text": "THE TEN MINUTES",
     "p": {"sub": "One order, followed end to end", "brand": "THE QUIET STORY"}, "w": 1}]},
 ]}

# =====================================================================
# 02 — THE INVISIBLE SYSTEM
# =====================================================================
# Travel from the glass of the phone into the backend. The order stops being
# a purchase and becomes a signal with three facts attached to it. Ends by
# laying out the seven links the rest of the film walks through.
CH02 = {
 "id": 2, "title": "THE INVISIBLE SYSTEM", "music": "system", "ambience": "server_hum",
 "scenes": [
  {"n": "जब आप ऑर्डर बटन दबाते हैं, तो आपके फ़ोन से जो निकलता है वो सामान नहीं है। एक मैसेज है। कुछ सौ बाइट्स का।",
   "hold": 0.4, "beats": [
    {"anim": "system_diagram", "p": {"mode": "enter"}, "w": 1.3},
    {"img": "dc_fibre_macro", "kb": "zoom_in:1.12", "w": 1}]},

  {"n": "उस मैसेज में तीन बातें लिखी होती हैं — आप कौन हैं, आपको क्या चाहिए, और आप कहाँ हैं।",
   "hold": 0.5, "beats": [
    {"anim": "system_diagram", "p": {"mode": "payload",
      "fields": "CUSTOMER ID|4 ITEMS|28.61° N, 77.21° E"}, "w": 1}]},

  {"n": "ये मैसेज एक सिस्टम में पहुँचता है जिसे ऑर्डर इंजन कहते हैं। और यहीं से, कुछ मिलीसेकंड में, फ़ैसले शुरू होते हैं।",
   "hold": 0.3, "beats": [
    {"anim": "system_diagram", "p": {"mode": "engine"}, "w": 1}]},

  {"n": "सबसे पहले पेमेंट की पुष्टि। फिर आपका पता — जो सिर्फ़ एक पता नहीं, एक निर्देशांक है। अक्षांश और देशांतर।",
   "hold": 0.4, "beats": [
    {"anim": "system_diagram", "p": {"mode": "checks",
      "steps": "PAYMENT AUTHORISED|ADDRESS → COORDINATE|SERVICEABILITY"}, "w": 1}]},

  {"n": "और फिर सबसे अहम सवाल, जिस पर बाक़ी सब टिका है: ये ऑर्डर कहाँ से भेजा जाए?",
   "hold": 0.9, "beats": [
    {"anim": "system_diagram", "p": {"mode": "question", "q": "FULFIL FROM WHERE?"}, "w": 1}]},

  {"n": "क्योंकि दस मिनट की डिलीवरी तेज़ गाड़ियों से नहीं आती। कम दूरी से आती है।",
   "hold": 0.7, "beats": [
    {"img": "city_flyover_night", "kb": "pan_left", "w": 1},
    {"anim": "metric_strip", "img": "city_traffic_dense",
     "p": {"items": "SPEED|NOT THE VARIABLE", "accentfirst": "0"}, "w": 1}]},

  {"n": "आपका ऑर्डर अब इस रास्ते से गुज़रेगा — ऐप से ऑर्डर इंजन, ऑर्डर इंजन से एक डार्क स्टोर, स्टोर में एक पिकर, पिकर से पैकिंग, पैकिंग से एक राइडर, और राइडर से आपका दरवाज़ा।",
   "hold": 0.5, "beats": [
    {"anim": "system_diagram", "p": {"mode": "chain",
      "nodes": "CUSTOMER|APP|ORDER ENGINE|DARK STORE|PICKER|PACKING|RIDER|HOME"}, "w": 1}]},

  {"n": "सात कड़ियाँ। और हर कड़ी पर सेकंड गिने जा रहे हैं।",
   "hold": 1.0, "beats": [
    {"anim": "system_diagram", "p": {"mode": "chain_count",
      "nodes": "CUSTOMER|APP|ORDER ENGINE|DARK STORE|PICKER|PACKING|RIDER|HOME"}, "w": 1}]},
 ]}

# =====================================================================
# 03 — LOCATION INTELLIGENCE
# =====================================================================
# The first real decision. A map of the city, several candidate stores, and
# the insight that the nearest one does not automatically win.
CH03 = {
 "id": 3, "title": "LOCATION INTELLIGENCE", "music": "system", "ambience": "city_night",
 "scenes": [
  {"n": "तो पहला फ़ैसला — कहाँ से?",
   "hold": 0.5, "beats": [
    {"anim": "ch_card", "text": "WHERE FROM?", "p": {"kicker": "DECISION 01"}, "w": 1}]},

  {"n": "आपके शहर के नक्शे पर, कंपनी के पास कई डार्क स्टोर हैं। हर स्टोर एक छोटे इलाक़े की ज़िम्मेदारी उठाता है — आम तौर पर दो से तीन किलोमीटर के दायरे की।",
   "hold": 0.4, "beats": [
    {"img": "city_aerial_dusk", "kb": "zoom_out:1.14", "w": 1},
    {"anim": "city_map", "p": {"mode": "stores", "radius": "1"}, "w": 1.6}]},

  {"n": "आपका ऑर्डर आते ही सिस्टम पास के स्टोर्स की एक छोटी सूची बनाता है। और फिर उन्हें आँकता है।",
   "hold": 0.3, "beats": [
    {"anim": "city_map", "p": {"mode": "candidates"}, "w": 1}]},

  {"n": "दूरी। क्योंकि दूरी सीधे मिनटों में बदलती है।",
   "hold": 0.3, "beats": [
    {"anim": "city_map", "p": {"mode": "evaluate", "metric": "DISTANCE",
      "values": "1.4 km|2.1 km|0.6 km"}, "w": 1}]},

  {"n": "इन्वेंटरी। क्या इस स्टोर में आपकी चारों चीज़ें इस वक़्त मौजूद हैं?",
   "hold": 0.3, "beats": [
    {"anim": "city_map", "p": {"mode": "evaluate", "metric": "INVENTORY",
      "values": "4 of 4|4 of 4|3 of 4"}, "w": 1}]},

  {"n": "क्षमता। इस स्टोर में इस वक़्त कितने ऑर्डर पहले से लाइन में हैं, और कितने पिकर काम पर हैं?",
   "hold": 0.3, "beats": [
    {"anim": "city_map", "p": {"mode": "evaluate", "metric": "CAPACITY",
      "values": "6 queued|19 queued|4 queued"}, "w": 1}]},

  {"n": "और अनुमानित समय — इन सबको जोड़कर निकला एक नंबर।",
   "hold": 0.6, "beats": [
    {"anim": "city_map", "p": {"mode": "evaluate", "metric": "EST. DELIVERY",
      "values": "9 min|16 min|12 min"}, "w": 1}]},

  {"n": "सबसे नज़दीकी स्टोर हमेशा नहीं जीतता। जो स्टोर भरा हुआ है, या जहाँ शैम्पू ख़त्म है, वो हार जाता है — भले ही वो आठ सौ मीटर पास हो।",
   "hold": 0.7, "beats": [
    {"anim": "city_map", "p": {"mode": "reject"}, "w": 1}]},

  {"n": "कुछ मिलीसेकंड में फ़ैसला हो जाता है। और आपका ऑर्डर एक इमारत से जुड़ जाता है जिसे आपने कभी नोटिस नहीं किया होगा।",
   "hold": 0.8, "beats": [
    {"anim": "city_map", "p": {"mode": "select", "label": "STORE 04 — ASSIGNED"}, "w": 1.2},
    {"anim": "clock", "p": {"value": "09:52", "label": "STORE ASSIGNED", "mode": "corner"},
     "img": "ds_exterior_night", "w": 1}]},
 ]}

# =====================================================================
# 04 — THE DARK STORE
# =====================================================================
# Exterior first, then take the walls off. The point to land: this is not a
# shop and not futuristic — it is an ordinary building optimised for seconds.
CH04 = {
 "id": 4, "title": "THE DARK STORE", "music": "room_tone", "ambience": "warehouse",
 "scenes": [
  {"n": "ये इमारत कोई दुकान नहीं है।",
   "hold": 0.6, "beats": [
    {"img": "ds_exterior_night", "kb": "zoom_in:1.06", "w": 1}]},

  {"n": "बाहर से देखें तो ये एक आम कमर्शियल यूनिट है। कोई बोर्ड नहीं, कोई शोरूम नहीं, कोई ग्राहक नहीं। आधा उठा हुआ शटर, और एक दरवाज़े से बाहर गिरती ठंडी रोशनी।",
   "hold": 0.4, "beats": [
    {"img": "ds_exterior_night", "kb": "pan_right", "w": 1},
    {"img": "ds_exterior_day", "kb": "zoom_in:1.07", "w": 1},
    {"img": "ds_doorway_from_inside", "kb": "zoom_out:1.10", "w": 1}]},

  {"n": "इसे डार्क स्टोर कहते हैं। 'डार्क' इसलिए कि ये जनता के लिए बंद है। यहाँ कोई ख़रीदने नहीं आता।",
   "hold": 0.5, "beats": [
    {"anim": "ch_card", "text": "DARK STORE", "p": {"kicker": "CLOSED TO THE PUBLIC"}, "w": 1}]},

  {"n": "ये दुकान नहीं, एक गोदाम है — लेकिन शहर के बीच में।",
   "hold": 0.4, "beats": [
    {"img": "city_rooftops_dense", "kb": "pan_left", "w": 1}]},

  {"silent": 3.0, "beats": [
    {"anim": "store_cutaway", "p": {"mode": "reveal"}, "img": "ds_exterior_night", "w": 1}]},

  {"n": "दीवारें हटाकर देखें तो अंदर का हिसाब साफ़ दिखता है।",
   "hold": 0.3, "beats": [
    {"anim": "store_cutaway", "p": {"mode": "zones"}, "img": "ds_topdown_floor", "w": 1}]},

  {"n": "दो से चार हज़ार वर्ग फ़ुट। ऊँची रैक्स, बहुत तंग गलियाँ। और इनमें रखी दो से छह हज़ार तरह की चीज़ें।",
   "hold": 0.4, "beats": [
    {"anim": "spec_strip", "img": "ds_aisle_wide",
     "p": {"items": "2,000–4,000 sq ft|2,000–6,000 SKUs|2–3 km radius"}, "w": 1.3},
    {"img": "ds_aisle_low", "kb": "zoom_in:1.09", "w": 1}]},

  {"n": "तंग गलियाँ कमी नहीं हैं, डिज़ाइन हैं। जितनी कम दूरी पिकर को चलनी पड़े, उतने कम सेकंड लगेंगे।",
   "hold": 0.5, "beats": [
    {"img": "ds_aisle_wide", "kb": "zoom_in:1.12", "w": 1},
    {"img": "ds_picker_aisle", "kb": "pan_right", "w": 1}]},

  {"n": "यहाँ कुछ भी ग्राहक को लुभाने के लिए नहीं रखा गया। कोई सजावट नहीं, कोई ऑफ़र का बोर्ड नहीं, कोई चौड़ा रास्ता नहीं। हर इंच सिर्फ़ एक काम के लिए है — सामान जल्दी निकालना।",
   "hold": 0.4, "beats": [
    {"img": "ds_shelf_face_macro", "kb": "pan_right", "w": 1},
    {"img": "ds_bin_labels_macro", "kb": "zoom_in:1.14", "w": 1},
    {"img": "ds_chiller", "kb": "zoom_in:1.07", "w": 1}]},

  {"n": "एक तरफ़ रात को आने वाला स्टॉक। दूसरी तरफ़ पैकिंग की मेज़। और बाहर, दरवाज़े पर, इंतज़ार करते राइडर।",
   "hold": 0.4, "beats": [
    {"img": "ds_inbound", "kb": "pan_left", "w": 1},
    {"img": "ds_packing_station", "kb": "zoom_in:1.08", "w": 1},
    {"img": "ds_riders_outside", "kb": "zoom_out:1.12", "w": 1}]},

  {"n": "शहर के इस कोने में, ये इमारत एक छोटा-सा लॉजिस्टिक्स नोड है। और आपके ऑर्डर का अगला पड़ाव यही है।",
   "hold": 0.8, "beats": [
    {"anim": "city_map", "p": {"mode": "node_zoom"}, "w": 1}]},
 ]}

# =====================================================================
# 05 — THE INVENTORY SYSTEM
# =====================================================================
# The film's quietest and most important idea: speed is downstream of knowing
# the truth of every shelf. Physical and digital held in one frame.
CH05 = {
 "id": 5, "title": "INVENTORY", "music": "system", "ambience": "warehouse",
 "scenes": [
  {"n": "अब सबसे नाज़ुक हिस्सा।",
   "hold": 0.7, "beats": [
    {"img": "ds_shelf_face_macro", "kb": "zoom_in:1.08", "w": 1}]},

  {"n": "दस मिनट की डिलीवरी का वादा सिर्फ़ तभी पूरा हो सकता है जब सिस्टम को ठीक-ठीक पता हो कि इस स्टोर में, इस वक़्त, क्या मौजूद है।",
   "hold": 0.4, "beats": [
    {"img": "ds_aisle_wide", "kb": "pan_right", "w": 1},
    {"anim": "inventory_sync", "p": {"mode": "field"}, "w": 1.2}]},

  {"n": "और यही सबसे मुश्किल काम है।",
   "hold": 0.6, "beats": [
    {"img": "ds_aisle_low", "kb": "zoom_out:1.12", "w": 1}]},

  {"n": "आपके चार आइटम इन हज़ारों में कहीं रखे हैं। दूध चिलर में। चिप्स एक ऊपरी रैक पर। शैम्पू दूसरी गली में। ड्रिंक ठंडे कैबिनेट में।",
   "hold": 0.4, "beats": [
    {"anim": "inventory_sync", "p": {"mode": "locate",
      "items": "MILK|CHIPS|SHAMPOO|DRINK", "bins": "A12|C04|B17|D02"}, "w": 1.4},
    {"img": "p_four_items", "kb": "pan_right", "w": 1}]},

  {"n": "हर एक चीज़ का एक डिजिटल जुड़वाँ है — एक रिकॉर्ड, जिसमें लिखा है वो क्या है, कहाँ है, और कितनी है।",
   "hold": 0.4, "beats": [
    {"anim": "inventory_sync", "p": {"mode": "twin", "sku": "MILK 500 ML",
      "bin": "A12", "qty": "14"}, "w": 1}]},

  {"n": "जब पिकर दूध का एक पाउच शेल्फ़ से उठाता है, तो दो चीज़ें एक साथ होती हैं।",
   "hold": 0.3, "beats": [
    {"img": "ds_picker_reach", "kb": "zoom_in:1.10", "w": 1}]},

  {"n": "शेल्फ़ पर गिनती एक कम हो जाती है। और डेटाबेस में भी — चौदह से तेरह।",
   "hold": 0.9, "beats": [
    {"anim": "inventory_sync", "p": {"mode": "decrement", "sku": "MILK 500 ML",
      "bin": "A12", "from": "14", "to": "13"}, "w": 1}]},

  {"n": "अगर ये दोनों गिनतियाँ अलग हो जाएँ, तो पूरा सिस्टम झूठ बोलने लगता है। ऐप किसी को वो चीज़ बेच देगा जो स्टोर में नहीं है।",
   "hold": 0.5, "beats": [
    {"anim": "inventory_sync", "p": {"mode": "drift", "sku": "SHAMPOO 180 ML",
      "bin": "B17", "shelf": "0", "digital": "2"}, "w": 1}]},

  {"n": "इसलिए क्विक कॉमर्स में असली लड़ाई तेज़ी की नहीं, सच्चाई की है। हर शेल्फ़ का सच, हर सेकंड।",
   "hold": 1.2, "beats": [
    {"anim": "ch_card", "text": "NOT SPEED. ACCURACY.",
     "p": {"kicker": "THE REAL CONSTRAINT"}, "w": 1}]},
 ]}

# =====================================================================
# 06 — PICKING OPTIMISATION
# =====================================================================
# The first place the audience sees an algorithm touch a human body. The
# route is drawn over a real top-down plate, not a cartoon floor plan.
CH06 = {
 "id": 6, "title": "THE PICK", "music": "system", "ambience": "warehouse",
 "scenes": [
  {"n": "स्टोर में एक हैंडहेल्ड स्क्रीन पर ऑर्डर आता है।",
   "hold": 0.4, "beats": [
    {"img": "ds_picker_scanner", "kb": "zoom_in:1.09", "w": 1}]},

  {"n": "चार आइटम। चार अलग-अलग जगहें।",
   "hold": 0.5, "beats": [
    {"anim": "pick_route", "p": {"mode": "targets", "bins": "A12|C04|B17|D02",
      "items": "MILK|CHIPS|SHAMPOO|DRINK"}, "img": "ds_topdown_floor", "w": 1}]},

  {"n": "अगर पिकर इन्हें उसी क्रम में उठाए जिस क्रम में आपने ऐप में डाले थे, तो वो स्टोर में बेवजह घूमेगा।",
   "hold": 0.4, "beats": [
    {"anim": "pick_route", "p": {"mode": "naive", "bins": "A12|C04|B17|D02",
      "label": "AS ORDERED", "dist": "94 m"}, "img": "ds_topdown_floor", "w": 1}]},

  {"n": "तो सिस्टम ऑर्डर को फिर से क्रम में लगाता है — लिस्ट के हिसाब से नहीं, रास्ते के हिसाब से।",
   "hold": 0.4, "beats": [
    {"anim": "pick_route", "p": {"mode": "solve", "bins": "A12|C04|B17|D02"},
     "img": "ds_topdown_floor", "w": 1}]},

  {"n": "सी-चार। डी-दो। ए-बारह। बी-सत्रह।",
   "hold": 0.6, "beats": [
    {"anim": "pick_route", "p": {"mode": "optimal", "bins": "C04|D02|A12|B17",
      "label": "OPTIMISED", "dist": "67 m"}, "img": "ds_topdown_floor", "w": 1}]},

  {"n": "ये वही चार चीज़ें हैं, लेकिन अब एक ऐसे रास्ते पर जो सबसे छोटा है।",
   "hold": 0.3, "beats": [
    {"img": "ds_picker_aisle", "kb": "pan_left", "w": 1},
    {"img": "ds_picker_reach", "kb": "zoom_in:1.10", "w": 1}]},

  {"n": "ये एक पुरानी गणितीय समस्या है — कम से कम दूरी में सब जगह पहुँचना। फ़र्क़ ये है कि यहाँ इसे हर ऑर्डर पर, दिन में हज़ारों बार हल करना पड़ता है।",
   "hold": 0.4, "beats": [
    {"anim": "pick_route", "p": {"mode": "repeat"}, "img": "ds_topdown_floor", "w": 1}]},

  {"n": "बचत कुछ सेकंड की होती है। लेकिन दिन के दो हज़ार ऑर्डर पर, कुछ सेकंड घंटों में बदल जाते हैं।",
   "hold": 0.5, "beats": [
    {"anim": "stat_big", "text": "27 m", "p": {"label": "SAVED PER ORDER",
      "foot": "× 2,000 orders/day"}, "w": 1}]},

  {"n": "पिकर के लिए ये एक और पर्ची है। सिस्टम के लिए ये उसका सबसे बड़ा ख़र्च — इंसानी वक़्त।",
   "hold": 0.9, "beats": [
    {"img": "ds_picker_aisle", "kb": "zoom_in:1.08", "w": 1},
    {"anim": "clock", "p": {"value": "08:20", "label": "PICKING COMPLETE", "mode": "corner"},
     "img": "ds_picker_scanner", "w": 1}]},
 ]}

# =====================================================================
# 07 — PACKING
# =====================================================================
# Macro texture chapter. The scan is verification, not counting — and the
# confirmation is deliberately undramatic, as the brief demands.
CH07 = {
 "id": 7, "title": "PACKING", "music": "room_tone", "ambience": "warehouse",
 "scenes": [
  {"n": "टोकरी पैकिंग की मेज़ पर पहुँचती है।",
   "hold": 0.4, "beats": [
    {"img": "ds_packing_station", "kb": "zoom_in:1.07", "w": 1}]},

  {"n": "यहाँ काम जोड़ना नहीं, जाँचना है।",
   "hold": 0.5, "beats": [
    {"img": "ds_scan_macro", "kb": "zoom_in:1.12", "w": 1}]},

  {"n": "हर चीज़ का बारकोड स्कैन होता है। स्कैन का मक़सद गिनती नहीं — पुष्टि है। कि जो उठाया गया, वही है जो मँगाया गया था।",
   "hold": 0.3, "beats": [
    {"anim": "scan_confirm", "p": {"mode": "scanning",
      "items": "MILK 500 ML|POTATO CHIPS|SHAMPOO 180 ML|COLD DRINK 750 ML"},
     "img": "ds_scan_macro", "w": 1.5}]},

  {"n": "दूध। चिप्स। शैम्पू। ड्रिंक।",
   "hold": 0.3, "beats": [
    {"img": "p_milk", "kb": "pan_right", "w": 1},
    {"img": "p_chips", "kb": "zoom_in:1.10", "w": 1},
    {"img": "p_shampoo", "kb": "pan_left", "w": 1},
    {"img": "p_drink", "kb": "zoom_in:1.10", "w": 1}]},

  {"n": "चार में से चार।",
   "hold": 0.7, "beats": [
    {"anim": "scan_confirm", "p": {"mode": "verified", "count": "4", "of": "4"},
     "img": "ds_bagging", "w": 1}]},

  {"n": "बैग बंद होता है, सील लगती है, और एक लेबल छपता है जिस पर आपका ऑर्डर नंबर है।",
   "hold": 0.4, "beats": [
    {"img": "ds_bagging", "kb": "zoom_in:1.08", "w": 1},
    {"img": "ds_label_printer", "kb": "zoom_in:1.13", "w": 1},
    {"img": "ds_bag_sealed", "kb": "zoom_out:1.10", "w": 1}]},

  {"n": "स्क्रीन पर कोई जश्न नहीं होता। बस एक लाइन बदल जाती है — ऑर्डर अब 'पैक्ड' है।",
   "hold": 0.8, "beats": [
    {"anim": "scan_confirm", "p": {"mode": "status", "from": "PICKING", "to": "PACKED"},
     "img": "ds_bag_sealed", "w": 1}]},

  {"n": "और उसी पल, सिस्टम दूसरी तरफ़ देख रहा है। बाहर।",
   "hold": 0.9, "beats": [
    {"img": "ds_doorway_from_inside", "kb": "zoom_in:1.10", "w": 1},
    {"anim": "clock", "p": {"value": "07:50", "label": "PACKED", "mode": "corner"},
     "img": "ds_riders_outside", "w": 1}]},
 ]}

# =====================================================================
# 08 — RIDER ASSIGNMENT
# =====================================================================
# Back to the map, but now the moving pieces are people. Ends by handing the
# film to a single named human for the rest of its running time.
CH08 = {
 "id": 8, "title": "THE DISPATCH", "music": "system", "ambience": "city_night",
 "scenes": [
  {"n": "स्टोर के बाहर, इस वक़्त, कई राइडर हैं।",
   "hold": 0.4, "beats": [
    {"img": "ds_riders_outside", "kb": "pan_right", "w": 1}]},

  {"n": "कोई लौट रहा है। कोई इंतज़ार कर रहा है। किसी के पास पहले से एक ऑर्डर है।",
   "hold": 0.4, "beats": [
    {"anim": "city_map", "p": {"mode": "riders"}, "w": 1.3},
    {"img": "rider_waiting_portrait", "kb": "zoom_in:1.07", "w": 1}]},

  {"n": "सिस्टम को एक चुनना है। और ये फ़ैसला भी दूरी से बड़ा है।",
   "hold": 0.4, "beats": [
    {"anim": "ch_card", "text": "WHICH RIDER?", "p": {"kicker": "DECISION 02"}, "w": 1}]},

  {"n": "राइडर इस वक़्त कहाँ है। स्टोर से कितनी दूर। आपके पते से कितनी दूर।",
   "hold": 0.3, "beats": [
    {"anim": "city_map", "p": {"mode": "rider_eval", "metric": "DISTANCE TO STORE",
      "values": "0.4 km|1.9 km|0.7 km"}, "w": 1}]},

  {"n": "उसके पास पहले से कितना काम है। क्या उसका रास्ता आपके रास्ते से मिलता है।",
   "hold": 0.3, "beats": [
    {"anim": "city_map", "p": {"mode": "rider_eval", "metric": "CURRENT LOAD",
      "values": "idle|1 active|2 active"}, "w": 1}]},

  {"n": "और सड़क की हालत — क्योंकि दो किलोमीटर खाली सड़क और दो किलोमीटर जाम में फ़र्क़ है।",
   "hold": 0.4, "beats": [
    {"anim": "metric_strip", "img": "city_traffic_dense",
     "p": {"items": "2.0 km clear → 5 min|2.0 km congested → 13 min"}, "w": 1}]},

  {"n": "कभी-कभी सिस्टम दो ऑर्डर एक ही राइडर को देता है, अगर दोनों पते एक ही दिशा में हों। इससे लागत घटती है, और समय थोड़ा बढ़ता है।",
   "hold": 0.4, "beats": [
    {"anim": "city_map", "p": {"mode": "batch"}, "w": 1}]},

  {"n": "इस बार चुनाव एक राइडर पर गिरता है जो स्टोर से चार सौ मीटर दूर है, और ख़ाली है।",
   "hold": 0.5, "beats": [
    {"anim": "city_map", "p": {"mode": "rider_select", "label": "RIDER 07 — ASSIGNED"}, "w": 1}]},

  {"n": "उसके फ़ोन पर एक नोटिफ़िकेशन आता है। और उसके लिए, ये दस मिनट अब शुरू होते हैं।",
   "hold": 0.8, "beats": [
    {"img": "rider_phone_mount", "kb": "zoom_in:1.10", "w": 1},
    {"img": "ds_handover", "kb": "pan_left", "w": 1}]},
 ]}

# =====================================================================
# 09 — ROUTE OPTIMISATION
# =====================================================================
# The chapter where the system stops being clean. The road is the variable
# nothing in the warehouse can control.
CH09 = {
 "id": 9, "title": "THE ROAD", "music": "drive", "ambience": "traffic",
 "scenes": [
  {"n": "बैग इंसुलेटेड बॉक्स में जाता है। और राइडर निकलता है।",
   "hold": 0.4, "beats": [
    {"img": "rider_bag_load", "kb": "zoom_in:1.09", "w": 1},
    {"img": "rider_moving_track", "kb": "pan_right", "w": 1.2}]},

  {"n": "फ़ोन पर एक रास्ता है। लेकिन वो रास्ता पत्थर की लकीर नहीं है।",
   "hold": 0.4, "beats": [
    {"anim": "city_map", "p": {"mode": "route", "eta": "7 min", "dist": "2.3 km"}, "w": 1}]},

  {"n": "नेविगेशन सिस्टम हर कुछ सेकंड में सड़क की हालत पढ़ता रहता है — ट्रैफ़िक, सिग्नल, बंद रास्ते।",
   "hold": 0.3, "beats": [
    {"anim": "city_map", "p": {"mode": "traffic"}, "w": 1}]},

  {"n": "आगे एक मुख्य सड़क पर जाम है।",
   "hold": 0.5, "beats": [
    {"img": "city_traffic_dense", "kb": "zoom_in:1.08", "w": 1}]},

  {"n": "रास्ता बदलता है। थोड़ा लंबा, लेकिन तेज़।",
   "hold": 0.7, "beats": [
    {"anim": "city_map", "p": {"mode": "reroute", "eta": "5 min", "dist": "2.7 km"}, "w": 1}]},

  {"n": "यहाँ एक बात समझने लायक़ है। सिस्टम सबसे छोटा रास्ता नहीं खोजता। सबसे कम समय वाला रास्ता खोजता है। ये दोनों एक जैसे बहुत कम होते हैं।",
   "hold": 0.6, "beats": [
    {"anim": "ch_card", "text": "SHORTEST ≠ FASTEST", "p": {"kicker": "THE ROUTING RULE"}, "w": 1}]},

  {"n": "और इस पूरे सफ़र में राइडर सिर्फ़ एक गाड़ी नहीं है। वो सिस्टम का वो हिस्सा है जो असल में शहर से टकराता है — गड्ढे, बारिश, सिग्नल, और लिफ़्ट जो काम नहीं कर रही।",
   "hold": 0.8, "beats": [
    {"img": "rider_through_traffic", "kb": "pan_left", "w": 1},
    {"img": "city_flyover_night", "kb": "zoom_in:1.08", "w": 1},
    {"img": "rider_lobby_stairs", "kb": "zoom_out:1.12", "w": 1}]},
 ]}

# =====================================================================
# 10 — THE TEN-MINUTE CLOCK
# =====================================================================
# The motif pays off. Short, rhythmic, and it lands the film's most
# counter-intuitive fact: most of the ten minutes is road, not software.
CH10 = {
 "id": 10, "title": "THE CLOCK", "music": "system", "ambience": "city_night",
 "scenes": [
  {"n": "अब एक क़दम पीछे हटकर घड़ी देखिए।",
   "hold": 0.6, "beats": [
    {"anim": "clock", "p": {"value": "10:00", "label": "ORDER PLACED", "mode": "hero"}, "w": 1}]},

  {"n": "ऑर्डर स्टोर तक पहुँचा — आठ सेकंड।",
   "hold": 0.25, "beats": [
    {"anim": "clock", "p": {"value": "09:52", "label": "ROUTED TO STORE", "mode": "split",
      "bar": "1"}, "w": 1}]},

  {"n": "पिकिंग पूरी — एक मिनट चालीस।",
   "hold": 0.25, "beats": [
    {"anim": "clock", "p": {"value": "08:20", "label": "PICKED", "mode": "split", "bar": "17"}, "w": 1}]},

  {"n": "पैक्ड और सील — दो मिनट दस।",
   "hold": 0.25, "beats": [
    {"anim": "clock", "p": {"value": "07:50", "label": "PACKED", "mode": "split", "bar": "22"}, "w": 1}]},

  {"n": "राइडर रवाना — दो मिनट पचास।",
   "hold": 0.4, "beats": [
    {"anim": "clock", "p": {"value": "07:10", "label": "DISPATCHED", "mode": "split", "bar": "28"}, "w": 1}]},

  {"n": "और बाक़ी सात मिनट? वो सड़क के हैं।",
   "hold": 1.0, "beats": [
    {"anim": "clock", "p": {"value": "00:00", "label": "ON THE ROAD", "mode": "split", "bar": "100"}, "w": 1}]},

  {"n": "दस मिनट का सबसे बड़ा हिस्सा टेक्नोलॉजी नहीं है। ट्रैफ़िक है।",
   "hold": 1.3, "beats": [
    {"anim": "ch_card", "text": "70% OF IT IS ROAD",
     "p": {"kicker": "WHERE THE TIME ACTUALLY GOES"}, "w": 1}]},
 ]}

# =====================================================================
# 11 — THE CITY AS A MACHINE
# =====================================================================
# The largest visual moment in the film. One order becomes thousands and the
# scale lands before the narration explains it. Ends on held silence.
CH11 = {
 "id": 11, "title": "THE CITY AS A MACHINE", "music": "machine", "ambience": "city_night",
 "scenes": [
  {"n": "अब तक हमने एक ऑर्डर देखा। एक ग्राहक, एक स्टोर, एक पिकर, एक राइडर।",
   "hold": 0.5, "beats": [
    {"anim": "city_map", "p": {"mode": "single_thread"}, "w": 1}]},

  {"n": "लेकिन इसी पल, इसी शहर में, ये अकेला ऑर्डर नहीं है।",
   "hold": 0.8, "beats": [
    {"anim": "city_map", "p": {"mode": "pullback"}, "w": 1}]},

  # The reveal gets silence. Music carries it; the narration stays out.
  {"silent": 5.5, "beats": [
    {"anim": "city_map", "p": {"mode": "network", "intensity": "1"}, "w": 1}]},

  {"n": "एक बड़े शहर में सैकड़ों डार्क स्टोर हैं। हर स्टोर में दर्जनों लोग। सड़कों पर हज़ारों राइडर।",
   "hold": 0.4, "beats": [
    {"anim": "city_map", "p": {"mode": "network", "intensity": "2",
      "counters": "DARK STORES 340|RIDERS 11,200|ORDERS/MIN 480"}, "w": 1}]},

  {"n": "और हर सेकंड, नए ऑर्डर गिर रहे हैं।",
   "hold": 0.5, "beats": [
    {"anim": "city_map", "p": {"mode": "network", "intensity": "3"}, "w": 1}]},

  {"n": "ऊपर से देखें तो ये अब डिलीवरी नहीं दिखती। ये एक बहती हुई व्यवस्था दिखती है।",
   "hold": 0.7, "beats": [
    {"img": "city_aerial_night", "kb": "zoom_out:1.18", "w": 1},
    {"anim": "city_map", "p": {"mode": "network", "intensity": "3"}, "w": 1}]},

  {"n": "स्टॉक रात में बड़े गोदामों से स्टोर्स तक पहुँचता है। ऑर्डर दिन भर स्टोर्स से घरों तक। और डेटा लगातार दोनों दिशाओं में।",
   "hold": 0.4, "beats": [
    {"anim": "city_map", "p": {"mode": "flows",
      "legend": "NIGHT · stock inbound|DAY · orders outbound|ALWAYS · data both ways"}, "w": 1.4},
    {"img": "ds_inbound", "kb": "pan_right", "w": 1}]},

  {"n": "शाम सात से दस बजे के बीच ये मशीन अपनी सबसे तेज़ रफ़्तार पर होती है। और बारिश के एक दिन में, इसका सारा गणित बदल जाता है।",
   "hold": 0.5, "beats": [
    {"anim": "city_map", "p": {"mode": "demand_curve"}, "w": 1.3},
    {"img": "city_street_night", "kb": "zoom_in:1.08", "w": 1}]},

  {"n": "दस मिनट की डिलीवरी एक काम नहीं है। ये एक लगातार चलती मशीन है, जिसमें आपका ऑर्डर कुछ सेकंड के लिए एक चिंगारी बनकर गुज़रा।",
   "hold": 1.2, "beats": [
    {"anim": "city_map", "p": {"mode": "one_spark"}, "w": 1}]},

  {"silent": 4.0, "beats": [
    {"anim": "city_map", "p": {"mode": "network", "intensity": "3", "fade": "1"}, "w": 1}]},
 ]}

# =====================================================================
# 12 — THE ECONOMIC MACHINE
# =====================================================================
# The investigation. A Sankey takes the order apart rupee by rupee, lands on
# a negative number, and then explains the three things that rescue it.
# Every figure here is a representative illustration, said so in narration.
CH12 = {
 "id": 12, "title": "THE ECONOMICS", "music": "investigate", "ambience": "room_night",
 "scenes": [
  {"n": "अब वो सवाल जो सबसे कम पूछा जाता है। ये सब पैसे में कैसे बैठता है?",
   "hold": 0.6, "beats": [
    {"anim": "ch_card", "text": "THE UNIT ECONOMICS", "p": {"kicker": "ONE ORDER, TAKEN APART"}, "w": 1}]},

  {"n": "अपने तीन सौ पचास रुपये के ऑर्डर पर वापस चलिए। ये आँकड़े किसी एक कंपनी के नहीं — ये इस कारोबार की एक आम तस्वीर हैं।",
   "hold": 0.4, "beats": [
    {"anim": "sankey", "p": {"mode": "order", "total": "350"}, "w": 1}]},

  {"n": "इसमें से एक बड़ा हिस्सा — क़रीब तीन सौ रुपये — सामान की अपनी लागत है। ये पैसा कंपनी का नहीं, सप्लायर का है।",
   "hold": 0.4, "beats": [
    {"anim": "sankey", "p": {"mode": "cogs", "total": "350", "cogs": "300", "margin": "50"}, "w": 1}]},

  {"n": "तो कंपनी के पास बचा — पचास रुपये के आसपास। यही वो रक़म है जिससे पूरी मशीन चलनी है।",
   "hold": 0.7, "beats": [
    {"anim": "sankey", "p": {"mode": "margin", "margin": "50"}, "w": 1}]},

  {"n": "अब इसमें से घटाना शुरू करें।",
   "hold": 0.4, "beats": [
    {"anim": "sankey", "p": {"mode": "costs_begin", "margin": "50"}, "w": 1}]},

  {"n": "राइडर की डिलीवरी फ़ीस। एक ऑर्डर पर पच्चीस से चालीस रुपये।",
   "hold": 0.3, "beats": [
    {"anim": "sankey", "p": {"mode": "cost", "label": "LAST-MILE DELIVERY", "value": "32",
      "running": "18"}, "w": 1}]},

  {"n": "पैकेजिंग — बैग, टेप, लेबल। पाँच से दस।",
   "hold": 0.3, "beats": [
    {"anim": "sankey", "p": {"mode": "cost", "label": "PACKAGING", "value": "7",
      "running": "11"}, "w": 1}]},

  {"n": "स्टोर में काम करने वालों की तनख़्वाह, उस दिन के ऑर्डर पर बाँटी हुई।",
   "hold": 0.3, "beats": [
    {"anim": "sankey", "p": {"mode": "cost", "label": "STORE LABOUR", "value": "14",
      "running": "-3"}, "w": 1}]},

  {"n": "स्टोर का किराया और बिजली। और टेक्नोलॉजी — सर्वर, नक्शे, इंजीनियर।",
   "hold": 0.4, "beats": [
    {"anim": "sankey", "p": {"mode": "cost", "label": "RENT · POWER · TECH", "value": "11",
      "running": "-14"}, "w": 1}]},

  {"n": "जोड़िए, और एक अकेले ऑर्डर पर आप अक्सर शून्य से नीचे पहुँच जाते हैं।",
   "hold": 1.0, "beats": [
    {"anim": "sankey", "p": {"mode": "negative", "value": "-14"}, "w": 1}]},

  {"n": "यही क्विक कॉमर्स का असली तनाव है। हर ऑर्डर अपने आप में फ़ायदे का सौदा नहीं होता।",
   "hold": 0.6, "beats": [
    {"anim": "ch_card", "text": "ONE ORDER LOSES MONEY",
     "p": {"kicker": "SO HOW DOES IT SURVIVE?"}, "w": 1}]},

  {"n": "तो ये चलता कैसे है? तीन तरीक़ों से।",
   "hold": 0.5, "beats": [
    {"anim": "sankey", "p": {"mode": "levers_intro"}, "w": 1}]},

  {"n": "पहला — ऑर्डर का आकार। तीन सौ पचास की जगह छह सौ का ऑर्डर आए, तो डिलीवरी की लागत लगभग वही रहती है, लेकिन कमाई बढ़ जाती है।",
   "hold": 0.4, "beats": [
    {"anim": "sankey", "p": {"mode": "lever", "n": "1", "label": "BASKET SIZE",
      "a": "₹350 → ₹600", "b": "delivery cost unchanged"}, "w": 1}]},

  {"n": "दूसरा — घनत्व। एक इलाक़े में जितने ज़्यादा ऑर्डर, उतना कम औसत ख़र्च। एक राइडर एक घंटे में तीन डिलीवरी करे या पाँच — ये फ़र्क़ सीधे मुनाफ़े में दिखता है।",
   "hold": 0.4, "beats": [
    {"anim": "sankey", "p": {"mode": "lever", "n": "2", "label": "ORDER DENSITY",
      "a": "3 drops/hour → 5", "b": "cost per drop falls"}, "w": 1}]},

  {"n": "तीसरा — विज्ञापन। ऐप में जो ब्रांड सबसे ऊपर दिखना चाहते हैं, वो उसके पैसे देते हैं। और ये कमाई लगभग पूरी की पूरी मुनाफ़ा होती है।",
   "hold": 0.5, "beats": [
    {"anim": "sankey", "p": {"mode": "lever", "n": "3", "label": "ADVERTISING",
      "a": "brands pay for placement", "b": "near-pure margin"}, "w": 1}]},

  {"n": "इसलिए इस कारोबार को समझने का सबसे सही तरीक़ा यही है: ये डिलीवरी का धंधा नहीं है। ये घनत्व का धंधा है।",
   "hold": 1.3, "beats": [
    {"anim": "ch_card", "text": "A DENSITY BUSINESS",
     "p": {"kicker": "NOT A DELIVERY BUSINESS"}, "w": 1}]},
 ]}

# =====================================================================
# 13 — WHY DARK STORES EXIST
# =====================================================================
# The structural answer. Old model and new model held side by side, then the
# trade-off stated plainly: the journey did not vanish, it moved.
CH13 = {
 "id": 13, "title": "WHY DARK STORES EXIST", "music": "investigate", "ambience": "room_night",
 "scenes": [
  {"n": "अब एक आख़िरी सवाल। ये सब ज़रूरी क्यों था?",
   "hold": 0.6, "beats": [
    {"anim": "ch_card", "text": "WHY ANY OF THIS EXISTS", "p": {"kicker": "THE STRUCTURAL ANSWER"}, "w": 1}]},

  {"n": "पुराना रास्ता ऐसा था। ग्राहक घर से निकलता, दुकान तक जाता, सामान ढूँढता, लाइन में लगता, और वापस आता।",
   "hold": 0.4, "beats": [
    {"anim": "compare_flow", "p": {"mode": "old",
      "nodes": "CUSTOMER|TRAVEL|STORE|SEARCH|CHECKOUT|TRAVEL|HOME"}, "w": 1.3},
    {"img": "sm_aisle", "kb": "pan_right", "w": 1}]},

  {"n": "इस पूरे रास्ते में सामान एक ही जगह रखा रहता — एक बड़े स्टोर में, शहर से थोड़ा बाहर, जहाँ जगह सस्ती है।",
   "hold": 0.4, "beats": [
    {"img": "sm_parking", "kb": "zoom_out:1.12", "w": 1},
    {"img": "sm_shopper_car", "kb": "pan_left", "w": 1}]},

  {"n": "यानी सामान स्थिर था, और ग्राहक चलता था।",
   "hold": 0.7, "beats": [
    {"anim": "compare_flow", "p": {"mode": "old_summary", "label": "INVENTORY STATIC · CUSTOMER MOVES"}, "w": 1}]},

  {"n": "क्विक कॉमर्स ने इस समीकरण को पलट दिया।",
   "hold": 0.6, "beats": [
    {"anim": "compare_flow", "p": {"mode": "flip"}, "w": 1}]},

  {"n": "अब ग्राहक नहीं चलता। सामान पहले से चलकर उसके पास आ चुका होता है।",
   "hold": 0.4, "beats": [
    {"anim": "compare_flow", "p": {"mode": "new",
      "nodes": "CUSTOMER|DARK STORE|PICK|RIDER|HOME"}, "w": 1}]},

  {"n": "दस मिनट की डिलीवरी का राज़ रफ़्तार नहीं, नज़दीकी है। सामान पहले से ही आपके दो किलोमीटर के अंदर रखा हुआ है।",
   "hold": 0.8, "beats": [
    {"anim": "ch_card", "text": "PROXIMITY, NOT SPEED", "p": {"kicker": "THE WHOLE TRICK"}, "w": 1}]},

  {"n": "लेकिन इसकी एक क़ीमत है।",
   "hold": 0.7, "beats": [
    {"anim": "compare_flow", "p": {"mode": "tradeoff_intro"}, "w": 1}]},

  {"n": "एक बड़े स्टोर की जगह अब सैकड़ों छोटे स्टोर चाहिए। शहर के अंदर, जहाँ किराया सबसे महँगा है।",
   "hold": 0.3, "beats": [
    {"anim": "compare_flow", "p": {"mode": "tradeoff", "n": "1",
      "label": "MORE STORES", "sub": "1 warehouse → 340 city units"}, "w": 1}]},

  {"n": "एक जगह रखे स्टॉक की जगह, वही स्टॉक सैकड़ों जगह रखना पड़ता है। इसका मतलब ज़्यादा इन्वेंटरी, और ज़्यादा जोख़िम कि कुछ बिना बिका रह जाए।",
   "hold": 0.3, "beats": [
    {"anim": "compare_flow", "p": {"mode": "tradeoff", "n": "2",
      "label": "MORE INVENTORY", "sub": "duplicated across every store"}, "w": 1}]},

  {"n": "और एक चेकआउट काउंटर की जगह, अब हर ऑर्डर पर एक पिकर और एक राइडर चाहिए।",
   "hold": 0.5, "beats": [
    {"anim": "compare_flow", "p": {"mode": "tradeoff", "n": "3",
      "label": "MORE LABOUR", "sub": "one picker + one rider, every order"}, "w": 1}]},

  {"n": "ग्राहक का सफ़र घटकर शून्य हो गया। लेकिन वो सफ़र ग़ायब नहीं हुआ। वो सिस्टम के अंदर चला गया।",
   "hold": 1.4, "beats": [
    {"anim": "compare_flow", "p": {"mode": "conclusion",
      "label": "THE JOURNEY DIDN'T DISAPPEAR", "sub": "IT MOVED INSIDE THE SYSTEM"}, "w": 1}]},
 ]}

# =====================================================================
# 14 — THE FINAL REVEAL
# =====================================================================
# Return to the door. The delivery is deliberately ordinary. Then the camera
# pulls back through every scale the film has built, and stops. No slogan.
CH14 = {
 "id": 14, "title": "TEN MINUTES", "music": "resolve", "ambience": "room_night",
 "scenes": [
  {"n": "वापस उसी फ़्लैट में।",
   "hold": 0.8, "beats": [
    {"img": "apt_door_inside_night", "kb": "zoom_in:1.06", "w": 1}]},

  {"silent": 3.2, "beats": [
    {"img": "rider_lane_arrive", "kb": "zoom_in:1.08", "w": 1},
    {"img": "apt_corridor_night", "kb": "pan_right", "w": 1}]},

  {"n": "दरवाज़ा खुलता है। एक सीलबंद बैग हाथ बदलता है। कुल दस मिनट।",
   "hold": 0.5, "beats": [
    {"img": "apt_door_opening", "kb": "zoom_in:1.07", "w": 1},
    {"img": "apt_handover", "kb": "zoom_in:1.10", "w": 1.2}]},

  {"n": "कोई कुछ नहीं कहता। कहने जैसा कुछ हुआ भी नहीं।",
   "hold": 0.9, "beats": [
    {"img": "apt_bag_counter", "kb": "zoom_in:1.06", "w": 1}]},

  {"n": "ये लेन-देन इतना मामूली लगता है कि इसे याद रखने की कोई वजह ही नहीं बनती।",
   "hold": 0.7, "beats": [
    {"anim": "clock", "p": {"value": "00:00", "label": "DELIVERED", "mode": "hero"},
     "img": "apt_bag_counter", "w": 1}]},

  {"n": "लेकिन इन दस मिनटों में एक डिजिटल फ़ैसला हुआ। एक स्टोर चुना गया। एक इन्वेंटरी रिकॉर्ड बदला। एक रास्ता गिना गया। एक इंसान स्टोर में चला। एक इंसान सड़क पर निकला। और एक पूरा शहर-स्तर का नेटवर्क कुछ सेकंड के लिए आपके पते पर आकर टिक गया।",
   "hold": 0.6, "beats": [
    {"img": "apt_bag_counter", "kb": "zoom_out:1.14", "w": 1},
    {"img": "building_exterior_night", "kb": "zoom_out:1.16", "w": 1},
    {"img": "city_rooftops_dense", "kb": "zoom_out:1.18", "w": 1},
    {"img": "city_aerial_night", "kb": "zoom_out:1.20", "w": 1.2},
    {"anim": "city_map", "p": {"mode": "network", "intensity": "3"}, "w": 1.3}]},

  {"n": "और ये सब एक बटन के पीछे छिपा था।",
   "hold": 1.0, "beats": [
    {"anim": "phone_ui", "p": {"mode": "button", "label": "PLACE ORDER"}, "w": 1}]},

  # The film's last held breath: the network, quietly going on without us.
  {"silent": 5.0, "beats": [
    {"anim": "city_map", "p": {"mode": "network", "intensity": "2", "fade": "1"}, "w": 1}]},

  {"n": "अगली बार जब आप वो बटन दबाएँ — ये मशीन अब आपके लिए अदृश्य नहीं रहेगी।",
   "hold": 2.0, "beats": [
    {"img": "phone_macro_thumb", "kb": "zoom_in:1.08", "w": 1}]},

  {"silent": 3.0, "beats": [
    {"img": "city_lane_narrow", "kb": "zoom_out:1.08", "w": 1}]},
 ]}

CHAPTERS = [CH01, CH02, CH03, CH04, CH05, CH06, CH07,
            CH08, CH09, CH10, CH11, CH12, CH13, CH14]
