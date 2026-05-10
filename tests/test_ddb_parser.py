import pytest
from unittest.mock import patch, MagicMock
from parsers.ddb import fix_concat, extract_from_text, parse_pdf_file
from tests.fixtures.sample_text import DDB_SAMPLE_TEXT


# ── fix_concat ────────────────────────────────────────────────────────────────

def test_splits_camel_case():
    assert fix_concat('HideousLaughter') == 'Hideous Laughter'


def test_leaves_all_caps():
    assert fix_concat('STRENGTH') == 'STRENGTH'


def test_handles_already_spaced():
    assert fix_concat('Eldritch Blast') == 'Eldritch Blast'


# ── extract_from_text ─────────────────────────────────────────────────────────

def test_extracts_charname():
    result = {}
    extract_from_text(DDB_SAMPLE_TEXT, result)
    assert result.get('charName') == 'Aria Moonwhisper'


def test_extracts_classes():
    result = {}
    extract_from_text(DDB_SAMPLE_TEXT, result)
    assert 'Wizard' in result.get('classes', '')
    assert '5' in result.get('classes', '')


def test_extracts_level():
    result = {}
    extract_from_text(DDB_SAMPLE_TEXT, result)
    assert result.get('level') == 5


def test_extracts_level_multiclass_sum():
    text = 'Wizard 4 / Sorcerer 2 PlayerName\nAria CLASS & LEVEL PLAYER NAME\nHuman Sage (Milestone)\n'
    result = {}
    extract_from_text(text, result)
    assert result.get('level') == 6


def test_extracts_ability_scores():
    result = {}
    extract_from_text(DDB_SAMPLE_TEXT, result)
    for stat in ('str', 'dex', 'con', 'int', 'wis', 'cha'):
        val = result.get(stat)
        assert val is not None, f'Missing stat: {stat}'
        assert 1 <= val <= 30, f'{stat}={val} out of range'


def test_extracts_passive_perception():
    result = {}
    extract_from_text(DDB_SAMPLE_TEXT, result)
    assert result.get('passivePerception') == 12


def test_extracts_speed():
    result = {}
    extract_from_text(DDB_SAMPLE_TEXT, result)
    assert result.get('speed') == 30


def test_does_not_overwrite_existing_keys():
    result = {'charName': 'Preloaded'}
    extract_from_text(DDB_SAMPLE_TEXT, result)
    assert result['charName'] == 'Preloaded'


def test_extracts_spell_slots():
    result = {}
    extract_from_text(DDB_SAMPLE_TEXT, result)
    slots = result.get('spellSlots')
    assert slots is not None
    assert slots[0]['max'] == 4   # 1st level
    assert slots[1]['max'] == 3   # 2nd level
    assert slots[2]['max'] == 2   # 3rd level


# ── parse_pdf_file ────────────────────────────────────────────────────────────

def test_defaults_hp_from_maxhp(tmp_path):
    pdf_path = tmp_path / 'char.pdf'
    pdf_path.write_bytes(b'%PDF-1.4 fake')

    with patch('parsers.ddb.PYPDF_SUPPORT', False), \
         patch('parsers.ddb.PDF_SUPPORT', True):
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [MagicMock(extract_text=MagicMock(return_value=(
            'Wizard 5 TSmith\nAria CLASS & LEVEL PLAYER NAME\nHuman Sage (Milestone)\n'
            '+2 14 45 --\n'
            'STRENGTH\n10\nDEXTERITY\n10\nCONSTITUTION\n14\n'
            'INTELLIGENCE\n18\nWISDOM\n12\nCHARISMA\n10\n'
            '30 ft. (Walking)\n12 PASSIVE PERCEPTION\n'
        )))]
        with patch('parsers.ddb.pdfplumber') as mock_plumber:
            mock_plumber.open.return_value = mock_pdf
            result = parse_pdf_file(pdf_path)

    assert result.get('hp') == result.get('maxhp')


def test_returns_fatal_on_visual_render(tmp_path):
    pdf_path = tmp_path / 'visual.pdf'
    pdf_path.write_bytes(b'%PDF-1.4 fake')

    visual_text = 'CHARACTER NAME\nCLASS & LEVEL\nHIT POINTS\nARMOR\nSAVING THROWS\n'

    with patch('parsers.ddb.PYPDF_SUPPORT', False), \
         patch('parsers.ddb.PDF_SUPPORT', True):
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [MagicMock(extract_text=MagicMock(return_value=visual_text))]
        with patch('parsers.ddb.pdfplumber') as mock_plumber:
            mock_plumber.open.return_value = mock_pdf
            result = parse_pdf_file(pdf_path)

    assert result.get('fatal') is True
    assert result.get('error') == 'visual_render'
