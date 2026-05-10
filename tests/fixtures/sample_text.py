"""
Realistic minimal D&D Beyond text-layer PDF text for parser unit tests.

Structured to satisfy the actual regexes in parsers/ddb.py:
  - charName: line with "CLASS & LEVEL"
  - classes: CLASS_PAT + digit
  - level: sum of class digits
  - playerName: token after class/level block
  - ability scores: STRENGTH newline value
  - speed: N ft. (Walking)
  - passive perception: N PASSIVE PERCEPTION
  - spell slots: === 1st LEVEL === 4
"""

DDB_SAMPLE_TEXT = """\
Wizard 5 TSmith
Aria Moonwhisper CLASS & LEVEL PLAYER NAME
High Elf Sage (Milestone)
CHARACTERNAME SPECIES BACKGROUND EXPERIENCEPOINTS

+2 14 32 --

STRENGTH
10

DEXTERITY
10

CONSTITUTION
14

INTELLIGENCE
18

WISDOM
12

CHARISMA
10

30 ft. (Walking)

12 PASSIVE PERCEPTION
14 PASSIVE INSIGHT
11 PASSIVE INVESTIGATION

+3 PROFICIENCY BONUS

Darkvision 60 ft.

=== CANTRIPS ===
=== 1st LEVEL === 4
=== 2nd LEVEL === 3
=== 3rd LEVEL === 2
"""

# A self-contained minimal valid PDF (no content; pypdf can open it without error)
MINIMAL_PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
    b"xref\n0 4\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"trailer\n<< /Size 4 /Root 1 0 R >>\n"
    b"startxref\n190\n%%EOF\n"
)
