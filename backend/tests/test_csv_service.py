from app.services.csv_service import parse_csv
from tests.conftest import make_csv


def test_valid_timeline_is_parsed_in_order(settings):
    result = parse_csv(make_csv(60, seconds_each=2), settings)

    assert result.valid
    assert result.total == 60
    assert not result.errors
    assert result.duration_seconds == 120
    assert [p.order_index for p in result.prompts] == list(range(1, 61))
    assert (result.prompts[0].start_seconds, result.prompts[0].end_seconds) == (0, 2)
    assert (result.prompts[-1].start_seconds, result.prompts[-1].end_seconds) == (118, 120)


def test_example_from_the_spec(settings):
    data = b'start,end,prompt\n0,5,"p1 prompt"\n5,7,"p2 prompt"\n'
    result = parse_csv(data, settings)

    assert result.valid
    assert result.total == 2
    assert result.duration_seconds == 7
    assert result.prompts[0].duration == 5
    assert result.prompts[1].duration == 2


def test_uneven_segment_lengths_are_fine(settings):
    data = b'start,end,prompt\n0,1.5,"a"\n1.5,10,"b"\n10,10.25,"c"\n'
    result = parse_csv(data, settings)

    assert result.valid
    assert result.duration_seconds == 10.25


def test_rows_out_of_order_are_sorted_by_start(settings):
    data = b'start,end,prompt\n5,7,"second"\n0,5,"first"\n'
    result = parse_csv(data, settings)

    assert result.valid
    assert [p.text for p in result.prompts] == ["first", "second"]
    assert [p.order_index for p in result.prompts] == [1, 2]


def test_timecode_format_is_accepted(settings):
    data = b'start,end,prompt\n00:00,01:30,"a"\n01:30,02:00,"b"\n'
    result = parse_csv(data, settings)

    assert result.valid
    assert result.duration_seconds == 120
    assert result.prompts[0].duration == 90


def test_gap_in_timeline_is_rejected(settings):
    data = b'start,end,prompt\n0,5,"a"\n6,8,"b"\n'
    result = parse_csv(data, settings)

    assert not result.valid
    assert any("Gap in the timeline" in error for error in result.errors)
    assert "5s and 6s" in " ".join(result.errors)


def test_overlapping_segments_are_rejected(settings):
    data = b'start,end,prompt\n0,5,"a"\n3,8,"b"\n'
    result = parse_csv(data, settings)

    assert not result.valid
    assert any("Overlapping" in error for error in result.errors)


def test_timeline_must_start_at_zero(settings):
    data = b'start,end,prompt\n2,5,"a"\n'
    result = parse_csv(data, settings)

    assert not result.valid
    assert any("Gap in the timeline" in error for error in result.errors)


def test_end_before_start_is_rejected(settings):
    data = b'start,end,prompt\n0,5,"a"\n5,5,"b"\n'
    result = parse_csv(data, settings)

    assert not result.valid
    assert any("must be greater than" in error for error in result.errors)


def test_non_numeric_times_are_rejected(settings):
    data = b'start,end,prompt\n0,abc,"a"\n'
    result = parse_csv(data, settings)

    assert not result.valid
    assert any("must be seconds or mm:ss" in error for error in result.errors)


def test_missing_columns_are_reported(settings):
    result = parse_csv(b'id,prompt\n1,"old format"\n', settings)

    assert not result.valid
    assert any("'start'" in error for error in result.errors)
    assert any("'end'" in error for error in result.errors)


def test_empty_prompt_is_rejected(settings):
    result = parse_csv(b'start,end,prompt\n0,5,""\n', settings)

    assert not result.valid
    assert any("prompt is empty" in error for error in result.errors)


def test_empty_file(settings):
    result = parse_csv(b"", settings)

    assert not result.valid
    assert result.errors == ["CSV file is empty"]


def test_too_many_prompts(settings, monkeypatch):
    monkeypatch.setattr(settings, "max_prompts", 10)
    result = parse_csv(make_csv(11), settings)

    assert not result.valid
    assert any("maximum is 10" in error for error in result.errors)


def test_blank_trailing_lines_are_ignored(settings):
    result = parse_csv(b'start,end,prompt\n0,2,"one"\n,,\n2,4,"two"\n', settings)

    assert result.valid
    assert result.total == 2
