"""
parsers/ddb.py — D&D Beyond PDF parser

Handles text-layer D&D Beyond PDF exports.
Entry point: parse_pdf_file(tmp_path) -> dict
"""

import re
import uuid
from pathlib import Path

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    from pypdf import PdfReader
    PYPDF_SUPPORT = True
except ImportError:
    PYPDF_SUPPORT = False


# ── Public entry point ────────────────────────────────────────────────────────

def parse_pdf_file(tmp_path: Path) -> dict:
    """
    Orchestrates PDF parsing. Always cleans up tmp_path.
    Returns a dict of extracted fields, or {'error': ..., 'fatal': True}.
    """
    result = {}
    log = []

    # ── Form fields (fillable PDFs) ───────────────────────────────────────────
    if PYPDF_SUPPORT:
        try:
            reader = PdfReader(str(tmp_path), strict=False)
            fields = reader.get_form_text_fields() or {}
            log.append(f'Form fields: {len(fields)}')

            field_map = {
                'CharacterName':  ('charName', str),
                'CharacterName 2':('charName', str),
                'PlayerName':     ('playerName', str),
                'ClassLevel':     ('classes', str),
                'Race ':          ('race', str),
                'Race':           ('race', str),
                'Background':     ('background', str),
                'Alignment':      ('alignment', str),
                'HPMax':          ('maxhp', int),
                'HPCurrent':      ('hp', int),
                'AC':             ('ac', int),
                'Speed':          ('speed', int),
                'PassiveWisdom':  ('passivePerception', int),
                'ProfBonus':      ('proficiencyBonus', int),
                'STR':            ('str', int),
                'DEX':            ('dex', int),
                'CON':            ('con', int),
                'INT':            ('int', int),
                'WIS':            ('wis', int),
                'CHA':            ('cha', int),
                'SpellSaveDC':    ('spellSaveDC', int),
                'SpellAtkBonus':  ('spellAttackBonus', int),
            }
            for pdf_key, (json_key, cast) in field_map.items():
                val = str(fields.get(pdf_key, '') or '').strip()
                if val and val not in ('0', ''):
                    try:
                        parsed = cast(val) if cast != str else val
                        if json_key not in result:
                            result[json_key] = parsed
                    except (ValueError, TypeError):
                        pass

            # Spell slots
            for name_set in [
                ['SlotsTotal 1','SlotsTotal 2','SlotsTotal 3','SlotsTotal 4','SlotsTotal 5',
                 'SlotsTotal 6','SlotsTotal 7','SlotsTotal 8','SlotsTotal 9'],
                ['Slots1','Slots2','Slots3','Slots4','Slots5','Slots6','Slots7','Slots8','Slots9'],
            ]:
                slots = [{'max': 0, 'used': 0} for _ in range(9)]
                for idx, fname in enumerate(name_set):
                    val = str(fields.get(fname, '') or '').strip()
                    if val:
                        try: slots[idx]['max'] = int(val)
                        except ValueError: pass
                if any(s['max'] > 0 for s in slots):
                    result['spellSlots'] = slots
                    break

            log.append(f'Form extraction: {len(result)} fields')
        except Exception as e:
            log.append(f'Form fields failed: {e}')

    # ── Text extraction ───────────────────────────────────────────────────────
    if len(result) < 4:
        text = ''

        if PDF_SUPPORT:
            try:
                with pdfplumber.open(str(tmp_path)) as pdf:
                    text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
                log.append(f'pdfplumber: {len(text)} chars')

                # Detect visual-render format (values in image layer, not text)
                ddb_markers = ['CHARACTER NAME', 'CLASS & LEVEL', 'HIT POINTS', 'ARMOR', 'SAVING THROWS']
                class_names = ['Warlock','Fighter','Wizard','Barbarian','Rogue','Cleric',
                               'Druid','Ranger','Monk','Paladin','Sorcerer','Artificer','Bard']
                is_visual = (
                    sum(1 for m in ddb_markers if m in text) >= 3
                    and len(text) < 1500
                    and not any(v in text for v in class_names)
                )
                if is_visual:
                    return {'error': 'visual_render', 'fatal': True,
                            'message': 'Visual-render PDF — falling back to Claude API.'}
            except Exception as e:
                log.append(f'pdfplumber failed: {e}')

        if not text and PYPDF_SUPPORT:
            try:
                reader = PdfReader(str(tmp_path), strict=False)
                text = '\n'.join((page.extract_text() or '') for page in reader.pages)
                log.append(f'pypdf fallback: {len(text)} chars')
            except Exception as e:
                log.append(f'pypdf failed: {e}')

        if text:
            extract_from_text(text, result)
            log.append(f'Text extraction: {len(result)} fields')

    print('DDB parse:', ' | '.join(log))

    result.setdefault('charName', 'Imported Character')
    result.setdefault('hp', result.get('maxhp', 10))
    return result


# ── Text extraction ───────────────────────────────────────────────────────────

def fix_concat(s: str) -> str:
    """Fix camelCase concatenation from PDF renderer: HideousLaughter → Hideous Laughter"""
    return re.sub(r'([a-z])([A-Z])', r'\1 \2', s).strip()


def extract_from_text(text: str, result: dict) -> None:
    """
    Extract all character fields from D&D Beyond text-layer PDF text.

    D&D Beyond header structure (consistent across all exports):
      Line 1: "ClassName Level [/ ClassName Level] PlayerName"
      Line 2: "CharacterName CLASS&LEVEL PLAYERNAME"
      Line 3: "Race Background (Milestone)"
      Line 4: "CHARACTERNAME SPECIES BACKGROUND EXPERIENCEPOINTS"
    """

    # ── Identity ──────────────────────────────────────────────────────────────

    # Name: on line containing CLASS&LEVEL — [^\n] prevents crossing newlines
    if 'charName' not in result:
        m = re.search(r'^([A-Z][^\n]{1,50}?)\s+CLASS(?:&|\s*)LEVEL',
                      text, re.MULTILINE | re.IGNORECASE)
        if m:
            result['charName'] = m.group(1).strip()
        if 'charName' not in result:
            m = re.search(r'^([A-Z][^\n]{1,50})\s*\nCHARACTER\s*NAME',
                          text, re.MULTILINE | re.IGNORECASE)
            if m:
                result['charName'] = m.group(1).strip()

    # Class + level (handles multiclass "Wizard 4 / Sorcerer 2")
    CLASS_PAT = r'(?:Artificer|Barbarian|Bard|Cleric|Druid|Fighter|Monk|Paladin|Ranger|Rogue|Sorcerer|Warlock|Wizard)'
    if 'classes' not in result:
        m = re.search(
            rf'^({CLASS_PAT}\s+\d+(?:\s*/\s*{CLASS_PAT}\s+\d+)*)',
            text, re.IGNORECASE | re.MULTILINE
        )
        if m: result['classes'] = m.group(1).strip()

    # Level: sum digits from the classes string
    if 'level' not in result and 'classes' in result:
        levels = re.findall(r'\d+', result['classes'])
        if levels: result['level'] = sum(int(l) for l in levels)

    # Player name: last token on the class line, after all class/level tokens
    if 'playerName' not in result:
        m = re.search(
            rf'^{CLASS_PAT}\s+\d+(?:\s*/\s*{CLASS_PAT}\s+\d+)*\s+(\S+)',
            text, re.IGNORECASE | re.MULTILINE
        )
        if m:
            pname = m.group(1).strip()
            if len(pname) > 1 and pname not in ('/', '--'):
                result['playerName'] = pname

    # Race (longer matches first to avoid partial matches)
    RACE_PAT = (r'\b(Githyanki|Githzerai|High Elf|Wood Elf|Hill Dwarf|Mountain Dwarf|'
                r'Lightfoot Halfling|Stout Halfling|Rock Gnome|Forest Gnome|'
                r'Half-Elf|Half-Orc|Fire Genasi|Water Genasi|Air Genasi|Earth Genasi|'
                r'Human|Elf|Dwarf|Halfling|Gnome|Tiefling|Dragonborn|Aasimar|Tabaxi|'
                r'Tortle|Genasi|Orc|Leonin|Satyr|Fairy|Harengon|Owlin|Changeling|'
                r'Kalashtar|Warforged|Shifter)\b')
    if 'race' not in result:
        m = re.search(RACE_PAT, text, re.IGNORECASE)
        if m: result['race'] = m.group(1)

    # Background: between race and (Milestone) on line 3
    if 'background' not in result:
        m = re.search(
            rf'{RACE_PAT}\s+(.+?)\s+(?:\(Milestone\)|Milestone|XP|\d{{4,}})',
            text, re.IGNORECASE
        )
        if m:
            bg = m.group(2).strip().rstrip('/')  .strip()
            if 0 < len(bg) < 60:
                result['background'] = bg

    # ── Core stats ────────────────────────────────────────────────────────────

    # Initiative + AC + MaxHP from combined line: "+3 14 27 --"
    if 'ac' not in result or 'maxhp' not in result:
        m = re.search(r'([+-]\d+)\s+(\d+)\s+(\d+)\s+(?:--|\d+)', text)
        if m:
            if 'initiative' not in result: result['initiative'] = m.group(1)
            if 'ac' not in result: result['ac'] = int(m.group(2))
            if 'maxhp' not in result:
                result['maxhp'] = int(m.group(3))
                result.setdefault('hp', int(m.group(3)))

    # Ability scores — each label followed 1-2 lines later by its value
    for stat, label in [('str','STRENGTH'), ('dex','DEXTERITY'), ('con','CONSTITUTION'),
                        ('int','INTELLIGENCE'), ('wis','WISDOM'), ('cha','CHARISMA')]:
        if stat not in result:
            m = re.search(label + r'[^\n]*\n(?:[^\n]*\n)?(\d+)', text)
            if m:
                val = int(m.group(1))
                if 1 <= val <= 30:
                    result[stat] = val

    # Speed
    if 'speed' not in result:
        m = re.search(r'(\d+)\s*ft\.\s*\(Walking\)', text, re.IGNORECASE)
        if not m: m = re.search(r'Speed\D{0,10}(\d+)', text, re.IGNORECASE)
        if m: result['speed'] = int(m.group(1))

    # Passive scores (handles both "10 PASSIVE PERCEPTION" and "10 PASSIVEPERCEPTION")
    for key, pat in [
        ('passivePerception',    r'(\d+)\s+PASSIVE\s*PERCEPTION'),
        ('passiveInsight',       r'(\d+)\s+PASSIVE\s*INSIGHT'),
        ('passiveInvestigation', r'(\d+)\s+PASSIVE\s*INVESTIGATION'),
    ]:
        if key not in result:
            m = re.search(pat, text, re.IGNORECASE)
            if m: result[key] = int(m.group(1))

    # Proficiency bonus
    if 'proficiencyBonus' not in result:
        m = re.search(r'\+(\d+)\s+PROFICIENCY\s*BONUS', text, re.IGNORECASE)
        if not m: m = re.search(r'\+(\d+)\s+PROFICIENCYBONUS', text, re.IGNORECASE)
        if m: result['proficiencyBonus'] = int(m.group(1))

    # ── Defenses ─────────────────────────────────────────────────────────────

    senses = re.findall(r'((?:Darkvision|Blindsight|Tremorsense|Truesight)\s+\d+\s*ft\.?)',
                        text, re.IGNORECASE)
    if senses: result['senses'] = ', '.join(dict.fromkeys(senses))

    m = re.search(r'Resistances?\s*-\s*([A-Za-z,\s]+?)(?:\s+Total|\s+SUCCESSES|\n)',
                  text, re.IGNORECASE)
    if m: result['damageResist'] = m.group(1).strip()

    # ── Proficiencies ─────────────────────────────────────────────────────────

    # Saving throws (bullet marker = proficient)
    save_lines = re.findall(
        r'[•·]\s*([+-]\d+)\s+(Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)',
        text
    )
    if save_lines:
        result['saveProficiencies'] = ', '.join(f'{s} {b}' for b, s in save_lines)

    # Skills — P=proficient, E=expertise, H=half prof (Jack of All Trades)
    skill_pat = re.findall(
        r'([PHE]\s+)?([+-]\d+)\s+(Acrobatics|Animal\s*Handling|Arcana|Athletics|Deception|'
        r'History|Insight|Intimidation|Investigation|Medicine|Nature|Perception|'
        r'Performance|Persuasion|Religion|Sleight\s*of\s*Hand|Stealth|Survival)\s+'
        r'(STR|DEX|CON|INT|WIS|CHA)',
        text, re.IGNORECASE
    )
    if skill_pat:
        all_s, prof_s = [], []
        for marker, bonus, skill, _ in skill_pat:
            skill_clean = fix_concat(re.sub(r'\s+', ' ', skill.strip()))
            entry = f'{skill_clean} {bonus}'
            all_s.append(entry)
            if marker and marker.strip() in ('P', 'E'):
                prof_s.append(entry)
        result['skillProficiencies'] = ', '.join(all_s)
        if prof_s: result['skillProficienciesProf'] = ', '.join(prof_s)

    # Languages — stop collecting when a line yields nothing after stripping bleed
    m = re.search(r'=== LANGUAGES ===\s*\n(.*?)(?:INT\s*DEX\s*DEX\s*WIS|=== ACTIONS|SENSES|TM\s*&)',
                  text, re.DOTALL | re.IGNORECASE)
    if m:
        lang_pieces = []
        for line in m.group(1).split('\n'):
            line = line.strip()
            if not line: continue
            if re.search(r'PROFICIENCIES|TRAINING|ACTIONS|SPEED', line, re.IGNORECASE): break
            cleaned = re.sub(r'^.*?(?:STR|DEX|CON|INT|WIS|CHA)\s+', '', line, flags=re.IGNORECASE)
            cleaned = re.sub(r'^\d+\s+\d+\s*ft\..*', '', cleaned).strip()
            cleaned = re.sub(r'^ABILITYSAVEDC\s*', '', cleaned, flags=re.IGNORECASE).strip()
            if re.match(r'^[+\-]?\d+\s*$', cleaned): continue
            if re.match(r'^[A-Z]{3,}\s*$', cleaned): continue
            if not cleaned: break   # empty after strip = no language content on this line
            lang_pieces.append(cleaned)
        if lang_pieces:
            result['languages'] = re.sub(r'\s{2,}', ' ', ' '.join(lang_pieces)).strip()

    # Armor / Weapons / Tools
    prof_parts = []
    armor_m = re.search(r'=== ARMOR ===\s*\n([^\n]+)', text)
    if armor_m:
        al = armor_m.group(1).strip()
        if not re.match(r'^[+\-]?\d+', al) and 'WEAPONS' not in al:
            prof_parts.append(f'Armor: {al}')

    weapons_m = re.search(r'=== WEAPONS ===\s*\n(.*?)(?:=== TOOLS|=== LANGUAGES|=== ACTIONS|\Z)',
                          text, re.DOTALL | re.IGNORECASE)
    if weapons_m:
        wparts = []
        for line in weapons_m.group(1).split('\n'):
            line = line.strip()
            if not line: continue
            if re.search(r'===|ABILITYSAVEDC', line, re.IGNORECASE): break
            pm = re.search(r'PROFICIENCY\s*BONUS\s+(.+?)$', line, re.IGNORECASE)
            if pm:
                wparts.append(pm.group(1).strip())
                continue
            am = re.search(r'(?:STR|DEX|CON|INT|WIS|CHA)\s+(.+?)$', line, re.IGNORECASE)
            if am:
                piece = am.group(1).strip()
                if re.match(r'^[A-Za-z,\s\+\-\']+$', piece) and len(piece) > 1:
                    wparts.append(piece)
                continue
            if not re.match(r'^[+\-]?\d+', line):
                wparts.append(line)
        wval = re.sub(r'\s{2,}', ' ', ' '.join(wparts)).strip().strip(',').strip()
        if wval: prof_parts.append(f'Weapons: {wval}')

    tools_m = re.search(r'=== TOOLS ===\s*\n(.*?)(?:=== LANGUAGES|=== ACTIONS|\Z)',
                        text, re.DOTALL | re.IGNORECASE)
    if tools_m:
        tparts = []
        for line in tools_m.group(1).split('\n'):
            line = line.strip()
            if not line: continue
            if re.search(r'===|ABILITYSAVEDC', line, re.IGNORECASE): break
            am = re.search(r'(?:STR|DEX|CON|INT|WIS|CHA)\s+(.+?)$', line, re.IGNORECASE)
            if am:
                piece = am.group(1).strip()
                if re.match(r'^[A-Za-z,\s\+\-\']+$', piece) and len(piece) > 1:
                    tparts.append(piece)
                continue
            if not re.match(r'^[+\-]?\d+', line):
                tparts.append(line)
        tval = re.sub(r'ABILITYSAVEDC\s*', '', ' '.join(tparts), flags=re.IGNORECASE)
        tval = re.sub(r'\s{2,}', ' ', tval).strip()
        if tval: prof_parts.append(f'Tools: {tval}')

    if prof_parts: result['proficienciesTraining'] = ' | '.join(prof_parts)

    # ── Weapon attacks ────────────────────────────────────────────────────────
    ws = re.search(r'NAME\s+HIT\s+DAMAGE/TYPE\s+NOTES\s*\n(.*?)(?:SENSES|TM\s*&)',
                   text, re.DOTALL | re.IGNORECASE)
    if ws:
        attacks = []
        for line in ws.group(1).split('\n'):
            line = re.sub(r'^\d+\s+PASSIVE\w+\s*', '', line.strip(), flags=re.IGNORECASE)
            line = re.sub(r'^(?:Darkvision|Blindsight|Tremorsense|Truesight)\s+\d+\s*ft\.?\s*',
                          '', line, flags=re.IGNORECASE)
            line = line.strip()
            if not line: continue
            wm = re.match(r'^([A-Z][A-Za-z\s\']+?)\s+([+-]\d+)\s+([\dd+\-]+\s+\w+)\s*(.*)', line)
            if wm:
                attacks.append({
                    'name': wm.group(1).strip(),
                    'hit': wm.group(2).strip(),
                    'range': '',
                    'damage': f'{wm.group(3).strip()} {wm.group(4).strip()}'.strip()
                })
        if attacks: result['attacks'] = attacks

    # ── Spellcasting ─────────────────────────────────────────────────────────

    # Primary: spellcasting page header "CHA 13 +5" or "INT / CHA 13 / 14 +5 / +6"
    sp = re.search(
        r'SPELLCASTING\s*(?:ABILITY|CLASS).*?((?:INT|CHA|WIS)(?:\s*/\s*(?:INT|CHA|WIS))?)\s+'
        r'(\d+(?:\s*/\s*\d+)?)\s+\+(\d+)',
        text, re.DOTALL | re.IGNORECASE
    )
    if sp:
        abbrev = sp.group(1).split('/')[0].strip().upper()
        ability_map = {'INT': 'Intelligence', 'CHA': 'Charisma', 'WIS': 'Wisdom'}
        if 'spellSaveDC' not in result: result['spellSaveDC'] = int(sp.group(2).split('/')[0])
        if 'spellAttackBonus' not in result: result['spellAttackBonus'] = int(sp.group(3))
        result['spellcastingAbility'] = ability_map.get(abbrev, abbrev)

    # Fallback: extract from feature text "Spell DC N, Spell Attack +N"
    if 'spellSaveDC' not in result:
        m = re.search(r'Spell\s+DC\s+(\d+),?\s+Spell\s+Attack\s+\+(\d+)', text, re.IGNORECASE)
        if m:
            result['spellSaveDC'] = int(m.group(1))
            result['spellAttackBonus'] = int(m.group(2))
    if 'spellcastingAbility' not in result:
        m = re.search(r'using\s+(INT|CHA|WIS)\s+as\s+your\s+spellcasting', text, re.IGNORECASE)
        if m:
            ability_map = {'INT': 'Intelligence', 'CHA': 'Charisma', 'WIS': 'Wisdom'}
            result['spellcastingAbility'] = ability_map.get(m.group(1).upper(), m.group(1))

    # Spell slots
    slots = [{'max': 0, 'used': 0} for _ in range(9)]
    for m in re.finditer(r'===\s*(\d+)(?:st|nd|rd|th)\s*LEVEL\s*===\s*(\d+)', text, re.IGNORECASE):
        lvl, count = int(m.group(1)), int(m.group(2))
        if 1 <= lvl <= 9: slots[lvl-1]['max'] = count
    if any(s['max'] > 0 for s in slots):
        result['spellSlots'] = slots

    # Spell list grouped by level
    # SOURCE_KW: spell name ends just before the source column
    SOURCE_KW = (r'(?:Magic\s+Initiate\s*\([^)]*\)|Clockwork\s+Magic[^\s,\n]*|'
                 r'Reach\s+to\s+the\s+Blaze|Githyanki\s+Psionics|Eldritch\s+Invocations|'
                 r'Warlock|Sorcerer|Cleric|Druid|Wizard|Bard|Paladin|Ranger|Artificer|'
                 r'Fighter|Rogue|Monk|Barbarian)')

    level_map = {}
    for m in re.finditer(r'===\s*(CANTRIPS|(\d+)(?:st|nd|rd|th)\s*LEVEL)\s*===', text, re.IGNORECASE):
        level_map[m.start()] = ('Cantrips' if 'CANTRIP' in m.group(1).upper()
                                else f'Level {m.group(2)}')

    by_level: dict = {}
    for m in re.finditer(r'^O\s+(.+)', text, re.MULTILINE):
        pos = m.start()
        level = 'Cantrips'
        for lpos, lname in sorted(level_map.items()):
            if lpos < pos: level = lname
        line = m.group(1).strip()
        nm = re.match(rf'^(.+?)\s+{SOURCE_KW}(?:\s|$)', line)
        if nm:
            spell_name = nm.group(1).strip()
        else:
            nm2 = re.match(r'^(.+?)\s{2,}', line)
            spell_name = nm2.group(1).strip() if nm2 else line.split()[0]
        spell_name = fix_concat(re.sub(r'\s+', ' ', spell_name).strip())
        if spell_name and len(spell_name) < 60:
            by_level.setdefault(level, []).append(spell_name)

    parts = []
    for lvl in ['Cantrips','Level 1','Level 2','Level 3','Level 4','Level 5',
                'Level 6','Level 7','Level 8','Level 9']:
        if lvl in by_level:
            parts.append(f'{lvl}: {", ".join(by_level[lvl])}')
    if parts: result['spellList'] = '\n'.join(parts)

    # ── Features & feats ─────────────────────────────────────────────────────
    features = []
    seen: set = set()
    for m in re.finditer(
        r'^\*\s+([A-Z][A-Za-z\s\'\/]+?)\s+•\s+[\w\s]+?\n((?:(?!^\*\s+[A-Z]|^===).)*)',
        text, re.MULTILINE | re.DOTALL
    ):
        name = m.group(1).strip()
        if name in seen or len(name) > 60: continue
        seen.add(name)
        desc = re.sub(r'\s+', ' ', m.group(2)).strip()
        if len(desc) > 300: desc = desc[:297] + '...'
        if name and desc:
            features.append({'name': name, 'desc': desc})
    if features: result['features'] = features[:30]
