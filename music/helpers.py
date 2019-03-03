from numpy import random

def get_note_position_relative_to_key_note(key_label, note_label, note_positions):
    """
    :param key_label: the key of the piece.
    :param note_label: the note name, without specification of the octave.
    :param note_positions: dict mapping each note to its position relative to the tonic of the key scale.
    :return: the position of the note relative to the tonic of the key scale (where tonic is position 0).
    """
    if note_label == 'rr':
        return 12
    return (note_positions[note_label] - note_positions[key_label]) % 12


def get_chord_under_note(note_id, chord_list, note_list):
    """
    :param note_id: the ID of the note
    :param chord_list:
    :param note_list:
    :return:
    """
    chord_dict = {}
    current_chord = 0
    current_note = 0
    note_total = 0
    chord_total = 0
    while note_total < sum(note_list):
        while note_total <= chord_total:
            chord_dict[current_note] = current_chord
            note_total += note_list[current_note]
        chord_total += chord_list[current_chord]
    return chord_dict


def get_next_note_label(note_probs):
    """
    :param note_probs: dict mapping each note to its probability of following the previous note.
    :return: the next note in the sequence
    """
    note_list = note_probs.keys()
    prob_list = note_probs.values()
    draw = random.choice(note_list, 1, p=prob_list)
    return draw[0]


def get_next_note_duration(duration_probs, remaining_time):
    """
    :param duration_probs: dict mapping each note duration to its probability of following the previous one.
    :param remaining_time: the fraction of a bar available to fill (notes must not straddle bars).
    :return: the next note duration in the sequence.
    """
    duration_list = duration_probs.keys()
    prob_list = duration_probs.values()
    draw = random.choice(duration_list, 1, p=prob_list)
    return draw[0]

def get_parent_chord(chord):
    parent_chords = {
        'maj7': 0,
        'dom7': 0,
        'min7': 0,
        'hdim': 0,
        'dim7': 0
    }
    if chord_suffix
    return parent_chord

# Data is stored in three tables: "song", "note", and "chord", with the following structures:
# song: | song_id | key | time | title |
# note: | note_id | song_id | position_number | note_label | note_length |
# chord: | chord_id | song_id | position_number | chord_label | chord_length |

{
  "fall": {
    "base_note": "fgacbcdcbarfgacbcdcbarabccbagbfgard",
    "accidental": "ssnsnsnnfnrssnsnsnnfnnnnsnnnfssnrn",
    "octave": [],
    "rhythm": []
  }
}

map = {
    # Basic chord types
    '': [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
    'm': [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0],
    'o': [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
    '6': [1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0],
    '7': [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
    'm7': [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0],
    'o7': [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
    'm6': [1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0],
    'M7': [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1],

    # Alterations
    'b5': [0, 0, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0],
    '#5': [0, 0, 0, 0, 0, 0, 0, -1, 1, 0, 0, 0],
    'sus2': [0, 0, 1, 0, -1, 0, 0, 0, 0, 0, 0, 0],
    'sus4': [0, 0, 0, 0, -1, 1, 0, 0, 0, 0, 0, 0],

    # Additions
    'b9': [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '#9': [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    'b6': [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    '#11': [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    '(9)': [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    '(11)': [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    '(13)': [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
    '(M7)': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
}

chord_types = [
    'M7',
    'm7',
    '7',
    '7b9',
    ''
    'o7',
    '7#5', # +7
    '6',
    '9',
    'm',
    '7#9',
    'm7b5', # ø7
    '7b5',
    '9sus4',
    '7sus4',
    '7#11',
    'm(M7)', # mM7
    'm6',
    'M7#5', # +M7
    '7(13)',
    'o',
    'M9',
    '7b9sus4',
    'M7#11',
    '7#5b9', # +7b9
    '13#11',
    '13',
    'add9',
    'o(add9)', # o(9)
    'sus4',
    '7b5b9',
    '9b5',
    '7#5#9', # +7#9
    'm6(9)',
    'M7b5',
    '9#11',
    'm11',
    '7sus4b9',
    'm(add9)',
    'mb6',
    'm#5',
    'm7(add M7)',
    '11'
]

chord_types = [
    '',
    'm',
    'M7',
    'M9',
    'M11',
    'M13',
    'm7',
    'm9',
    'm11',
    'm13',
    '7',
    '9',
    '11',
    '13',
    '6',
    'm6',
    'o',
    'o7'
]

alterations = [
    '#5',
    'b5',
    'sus4',
]

additions = [
    '6',
    'b6',
    '(9)',
    '#9',
    'b9',
    '(11)',
    '#11',
    '(13)',
    '(M7)'
]

group1 = [
    'm',
    'M7',
    'M9',
    'M11',
    'M13',
    'o',
    'o7'
]

group2 = [
    '6',
    '7',
    '9',
    '11',
    '13'
]

group3 = [
    # number in brackets
    # number preceded by b or #
    # ma7 in brackets
    # sus number
]

# Section 1: may have one of {m (not followed by 'a'), o, o7} - if none of these occur, then major triad
# Section 2: may have one of {7, 9, 11, 13, ma9} - adds dom/maj 7th and extra note
# Section 3: may have a number preceded by #/b, or (a number or ma7) in parentheses - this can occur multiple times
# Section 4: may have /letter

# ^(\d*)([A-G][b#]?)(m|o(?:7)?)?(M?(?:7|9|11|13)|6)?((?:\((?:\d*|M7)\)|[b#]\d*|sus\d*)+?)(/[A-G][b#]?)?$

seventh_chords = {
    i + str(j): i + '7(%s)' % j if j == 9 else
    i + '7(%s)(%s)' % (j-2, j) if j == 11 else
    i + '7(%s)(%s)(%s)' % (j-4, j-2, j)
    for i in ('', 'm', 'M') for j in (9, 11, 13)}

chord_breakdown = {
    'm': 'b3',
    'o': 'b3b5',
    'o7': 'b3b5(6)',
    '6': '(6)',
    'm6': 'b3(6)',
    '7': 'b7',
    '9': 'b7(2)',
    '11': 'b7(2)(4)',
    '13': 'b7(2)(4)(6)',
    'm7': 'b3b7',
    'm9': 'b3b7(2)',
    'm11': 'b3b7(2)(4)',
    'm13': 'b3b7(2)(4)(6)',
    'M7': '(7)',
    'M9': '(7)(2)',
    'M11': '(7)(2)(4)',
    'M13': '(7)(2)(4)(6)'
}

duration = float(c.group(1)) * 1.2 if c.group(1) else duration = 1.2
root = c.group(2)
second = (
    root + 1 if re.search('b9', c.group(5)) else
    root + 3 if re.search('#9', c.group(5)) else
    root + 2 if re.search('9', c.group(4)) or re.search('\(9\)', c.group(5)) else
    None
)
third = (
    root + 2 if re.search('sus2', c.group(5)) else
    root + 5 if re.search('sus4', c.group(5)) else
    root + 3 if c.group(3) else
    root + 4
)
fourth = (
    root + 6 if re.search('#11', c.group(5)) else
    root + 5 if re.search('11', c.group(4)) or re.search('\(11\)', c.group(5)) else
    None
)
fifth = (
    root + 6 if c.group(3)[0] == 'o' or re.search('b5', c.group(5)) else
    root + 8 if re.search('#5', c.group(5)) else
    root + 7
)
sixth = (
    root + 9 if c.group(4) == '6' or re.search('13', c.group(4)) or re.search('\(13\)', c.group(5)) else
    root + 8 if re.search('b6', c.group(5)) else
    None
)
seventh = (
    root + 9 if c.group(3) == 'o7' else
    root + 11 if c.group(4)[0] == 'M' or re.search('\(M7\)', c.group(5)) else
    root + 10 if c.group(4)[0] != 'M' else
    None
)
print root, second, third, fourth, fifth, sixth, seventh

'''
If a chord includes an extension
that is the diminished or augmented version of a note in the base chord, and the extension
is written as the note number preceded by the flat or the sharp symbol, then the extension
is included without surrounding parentheses (as though it is an alteration rather than an
addition), and the note in the base chord is shown explicitly within parentheses (as though
it is an addition rather than part of the base chord).
'''

def get_chord_breakdown(chord, start):
    alterations = []
    if start == 'M':
        alterations.extend(['(7)'] + ['(%s)' % i for i in range(2, chord[-2:] - 6, 2)])
    if chord in ('m7', ..., '13'):
        alterations.extend(['b7'] + ['(%s)' % i for i in range(2, chord[-2:] - 6, 2)])
    if start in ('m', 'o'):
        alterations.append('b3')
    if chord in ('o', 'o7'):
        alterations.append('b5')
    if chord in ('o7', '6', 'm6'):
        alterations.append('(6)')

def parse_chord_data(chord_sequence):
    """
    :param chord_sequence: String containing a space-separated sequence of chord symbols.
    Sections within square parentheses that are not contained within outer square parentheses
    represent repeated sections, and any inner sections bounded by square parentheses signify
    first, second, etc. time bars, in order of appearance.
    :return: List of all chords, in order of appearance.
    """
    chords = []
    l = chord_sequence.split(" ")
    start_idx = None
    end_idx = None
    for i, item in enumerate(l):
        if item == "[":
            if start_idx:
                end_idx = i
            else:
                start_idx = i + 1
        elif item == "]":
            if start_idx:
                chords.extend(l[start_idx:end_idx])
                start_idx = None
        else:
            chords.append(item)
    return chords

'''
i = 0
j = 2
while i < len(full_breakdown):
    while not alt_compiled_regex.match(full_breakdown[i:j]):
        j += 1
    alteration = full_breakdown[i:j]
    make_chord_alteration(alteration, chordvec)
    i = j
    j = i + 2
print chord, chordvec + root_vec + bass_vec
'''

def get_chord_sequence(chords):
    regex = r"(\d*)([A-G][b#]?)((?:M|m|o)?(?:6|7|9|11|13)?)?((?:\((?:\d+|M7)\)|[b#]\d+|sus\d+)*)(/([A-G][b#]?))?"
    compiled_regex = re.compile(regex)
    for chord in parse_chord_data(chords):
        grouped_regex = compiled_regex.match(chord)
        root = note_map[grouped_regex.group(2)]
        bass = note_map[grouped_regex.group(6)] if grouped_regex.group(6) else root
        chordvec = [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0]
        root_vec = [1 if i == root else 0 for i in range(12)]
        bass_vec = [1 if i == bass else 0 for i in range(12)]
        full_breakdown = chord_breakdown[grouped_regex.group(3)] + grouped_regex.group(4)
        alt_compiled_regex = re.compile(r"(\((?:\d+|M7)\)|[b#]\d+|sus\d+)")
        all_alterations = re.findall(alt_compiled_regex, full_breakdown)
        print chord, all_alterations
        for alteration in all_alterations:
            make_chord_alteration(alteration, chordvec)

test = {
    "name": "afternoon_in_paris",
    "relative_major_key": "Cn",
    "time_signature": "4-4",
    "anacrusis_duration": 60,
    "notes": [
      "e5", "g5",
      "r", "d5", "c5", "b4", "c5", "d5", "e5", "eb5", "g4", "bb4", "d5",
      "c5", "d5", "f5", "r", "c5", "bb4", "a4", "bb4", "c5", "d5", "db5",
      "f4", "ab4", "c5", "bb4", "c5", "eb5", "r", "c5", "ab4", "g4",
      "bb4", "a4", "g4", "bb4", "ab4", "g4", "r", "e5", "g5",
      "r", "d5", "c5", "b4", "c5", "d5", "e5", "eb5", "g4", "bb4", "d5",
      "c5", "d5", "f5", "r", "c5", "bb4", "a4", "bb4", "c5", "d5", "db5",
      "f4", "ab4", "c5", "bb4", "c5", "eb5", "r", "c5", "ab4", "g4",
      "bb4", "a4", "g4", "bb4", "ab4", "g4", "r", "a4", "b4", "c5", "d5",
      "e5", "d5", "c5", "e5", "a4", "b4", "c5", "d5", "e5", "d5", "e5",
      "f5", "e5", "g5", "r", "d5", "c5", "b4", "c5", "d5", "e5", "eb5",
      "g4", "bb4", "d4", "c4", "d5", "f5", "r", "c5", "bb4", "a4", "bb4",
      "c5", "d5", "db5", "f4", "ab4", "c5", "bb4", "c5", "eb5", "r", "c5",
      "ab4", "g4", "bb4", "ab4", "g4", "bb4", "ab4", "g4"
    ],
    "chords": [
      "Cmaj7", "Cmin7", "F7", "Bbmaj7", "Bbmin7", "Eb7", "Abmaj7", "Dmin7",
      "G7b9", "Cmaj7", "Amin7", "Dmin7", "G7", "Cmaj7", "Cmin7", "F7",
      "Bbmaj7", "Bbmin7", "Eb7", "Abmaj7", "Dmin7", "G7b9", "Cmaj7", "Amin7",
      "Dmin7", "G7", "Cmaj7", "Amin7", "Dmin7", "G7", "C#min7", "F#7",
      "Dmin7", "G7", "Cmaj7", "Cmin7", "F7", "Bbmaj7", "Bbmin7", "Eb7",
      "Abmaj7", "Dmin7", "G7b9", "Cmaj7"
    ],
    "note_durations": [
      1,1,1,2,1,1,1,1,1,1,1,1,1,2,1,1,1,2,1,1,1,1,1,1,1,1,1,2,1,1,1,
      2,1,1,1,1,6,1,1,9,6,1,1,
      1,2,1,1,1,1,1,1,1,1,1,2,1,1,1,2,1,1,1,1,1,1,1,1,1,2,1,1,1,2,1,
      1,1,1,6,1,1,9,4,2,1,
      7,1,7,1,7,1,7,1,7,1,7,1,8,7,1,1,
      1,2,1,1,1,1,1,1,1,1,1,2,1,1,1,2,1,1,1,1,1,1,1,1,1,2,1,1,1,2,1,
      1,1,1,6,1,1,17
    ],
    "chord_durations": [
      240, 120, 120, 240, 120, 120, 240, 120, 120, 120, 120, 120, 120,
      240, 120, 120, 240, 120, 120, 240, 120, 120, 360, 120, 240, 240,
      240, 240, 240, 240, 120, 120, 120, 120, 240, 120, 120, 240, 120,
      120, 240, 120, 120, 480
    ],
    "bar_numbers": range(32),
    "bar_durations": [240 for _ in range(32)]
  }


chords = [Chord(name=chord, duration=test["chord_durations"][i]) for i, chord in enumerate(test["chords"])]
notes = [Note(pitch=note, duration=test["note_durations"][i] * 30) for i, note in enumerate(test["notes"])]
bars = [Bar(number=bar, duration=test["bar_durations"][i]) for i, bar in enumerate(test["bar_numbers"])]
piece = Piece(
    name=test["name"],
    key_signature=test["relative_major_key"],
    time_signature=test["time_signature"],
    anacrusis_duration=test["anacrusis_duration"],
)


piece.get_timestep_sequence(notes, chords, bars)
for i in piece.timesteps:
    print i.note, i.chord, i.bar, i.duration, i.is_tied, i.is_barline

type = alteration.translate(None, string.digits) # alteration type: 'b', '#', '()', or 'sus'
note = int(alteration.translate(None, type)) # name(=number) of note affected by alteration
