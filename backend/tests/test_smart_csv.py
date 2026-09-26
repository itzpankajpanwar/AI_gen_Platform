import pytest

from app.services.csv_service import parse_csv, resolve_music_beds
from app.services.style import StyleError, parse_grain, parse_valued
from app.services.style import TRANSITIONS

HEADER = "start,end,prompt,transition,ken_burns,grade,grain,music,text_type,text_value,narration,voice\n"


def build(rows: str) -> bytes:
    return (HEADER + rows).encode("utf-8")


def test_full_row_parses_every_column(settings):
    data = build(
        '0,5,"a railway station",fadeblack,zoom_in:1.15,warm,medium,somber.mp3,'
        'date_stamp,"14 अप्रैल, 1891","भारत के इतिहास में",narrator_a\n'
    )
    result = parse_csv(data, settings)

    assert result.valid, result.errors
    scene = result.prompts[0]
    assert scene.transition == "fadeblack"
    assert scene.ken_burns == "zoom_in"
    assert scene.ken_burns_scale == 1.15
    assert scene.grade == "warm"
    assert scene.grain == 18
    assert scene.music == "somber.mp3"
    assert scene.text_type == "date_stamp"
    assert scene.text_value == "14 अप्रैल, 1891"
    assert scene.narration == "भारत के इतिहास में"
    assert scene.voice == "narrator_a"


def test_three_column_csv_still_works(settings):
    result = parse_csv(b'start,end,prompt\n0,5,"one"\n5,7,"two"\n', settings)

    assert result.valid
    assert result.total == 2
    assert result.prompts[0].transition is None
    assert result.prompts[0].narration is None


def test_empty_cells_mean_not_applied(settings):
    result = parse_csv(build('0,4,"scene",,,,,,,,,\n'), settings)

    scene = result.prompts[0]
    assert result.valid, result.errors
    assert (scene.transition, scene.ken_burns, scene.grade, scene.grain) == (None, None, None, None)
    assert (scene.text_type, scene.narration, scene.music) == (None, None, None)


@pytest.mark.parametrize(
    "cell,message",
    [
        ("transition", "unknown transition"),
        ("ken_burns", "unknown ken_burns"),
        ("grade", "unknown grade"),
        ("grain", "unknown grain"),
        ("text_type", "unknown text_type"),
    ],
)
def test_unknown_vocabulary_is_rejected_with_options(settings, cell, message):
    columns = {
        "transition": '0,4,"s",nonsense,,,,,,,,',
        "ken_burns": '0,4,"s",,nonsense,,,,,,,',
        "grade": '0,4,"s",,,nonsense,,,,,,',
        "grain": '0,4,"s",,,,nonsense,,,,,',
        "text_type": '0,4,"s",,,,,,nonsense,"x",,',
    }
    result = parse_csv(build(columns[cell] + "\n"), settings)

    assert not result.valid
    assert any(message in error for error in result.errors)
    assert any("expected one of" in error or "expected light" in error for error in result.errors)


def test_text_type_without_value_is_rejected(settings):
    result = parse_csv(build('0,4,"s",,,,,,center_title,,,\n'), settings)

    assert not result.valid
    assert any("needs a text_value" in error for error in result.errors)


def test_text_value_without_type_warns(settings):
    result = parse_csv(build('0,4,"s",,,,,,,"orphan text",,\n'), settings)

    assert result.valid
    assert any("no text will show" in warning for warning in result.warnings)


def test_transition_longer_than_its_scenes_is_rejected(settings):
    data = build('0,4,"first",,,,,,,,,\n4,5,"second",dissolve:3,,,,,,,,\n')
    result = parse_csv(data, settings)

    assert not result.valid
    assert any("longer than" in error for error in result.errors)


def test_grain_accepts_names_and_numbers(settings):
    assert parse_grain("light") == 8
    assert parse_grain("42") == 42
    assert parse_grain("") is None
    with pytest.raises(StyleError):
        parse_grain("200")


def test_valued_cell_splitting():
    assert parse_valued("dissolve:0.8", TRANSITIONS, "transition") == ("dissolve", 0.8)
    assert parse_valued("dissolve", TRANSITIONS, "transition") == ("dissolve", None)
    assert parse_valued("", TRANSITIONS, "transition") == ("", None)
    with pytest.raises(StyleError):
        parse_valued("dissolve:soon", TRANSITIONS, "transition")


def test_unknown_columns_are_ignored_with_a_warning(settings):
    data = b'start,end,prompt,sparkle\n0,4,"scene",yes\n'
    result = parse_csv(data, settings)

    assert result.valid
    assert any("sparkle" in warning for warning in result.warnings)


def test_narrated_count(settings):
    data = build('0,4,"a",,,,,,,,"line one",\n4,8,"b",,,,,,,,,\n8,12,"c",,,,,,,,"line three",\n')
    result = parse_csv(data, settings)

    assert result.narrated_count == 2


# ------------------------------------------------------------------ music beds


def test_music_continues_until_changed(settings):
    data = build(
        '0,4,"a",,,,,somber.mp3,,,,\n'
        '4,8,"b",,,,,,,,,\n'
        '8,12,"c",,,,,,,,,\n'
        '12,16,"d",,,,,tension.mp3,,,,\n'
        '16,20,"e",,,,,,,,,\n'
    )
    result = parse_csv(data, settings)
    beds = resolve_music_beds(result.prompts)

    assert beds == [("somber.mp3", 0.0, 12.0), ("tension.mp3", 12.0, 20.0)]


def test_music_stop_keyword_ends_the_bed(settings):
    data = build(
        '0,4,"a",,,,,somber.mp3,,,,\n'
        '4,8,"b",,,,,stop,,,,\n'
        '8,12,"c",,,,,,,,,\n'
    )
    beds = resolve_music_beds(parse_csv(data, settings).prompts)

    assert beds == [("somber.mp3", 0.0, 4.0)]


def test_no_music_column_means_no_beds(settings):
    beds = resolve_music_beds(parse_csv(b'start,end,prompt\n0,4,"a"\n', settings).prompts)

    assert beds == []
