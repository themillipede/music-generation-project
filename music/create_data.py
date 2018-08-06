import os, sys, inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import json
import re
import string
from midi_creation import create_midi_melody, get_pitch_sequence_from_midi
'''
with open('music/pieces.json') as f:
    data = json.load(f)

for title in data:
    if not data[title]['notes']:
        continue
    filename = '%s.MID' % title
    file = 'Composition/%s' % filename
    try:
        create_midi_melody(data[title]['notes'], file, 'ParsedMIDI/%s' % filename, duration=0.3)
        print title
    except:
        print "Error - %s" % title

def get_midi_details(filename):
    song = pm.PrettyMIDI(filename)
    inst = song.instruments[0].notes
    for note in inst:
        print round(note.start, 1), round(note.end, 1)

def get_note_sequence(midi_file, piece, bars):
    notes = []
    song = pm.PrettyMIDI(midi_file)
    inst = song.instruments[0].notes
    latest_time = 0
    total_time = 0
    for note in inst:
        if note.start > latest_time:
            rest_duration = note.start - latest_time
            notes.append(Note(duration=rest_duration))
        note_duration = note.end - note.start
        notes.append(Note(pitch=note.pitch, duration=note_duration))
        total_time += note.end - latest_time
        latest_time = note.end
    final_rest_duration = sum([b.duration for b in bars]) + piece.anacrusis_duration - total_time
    if final_rest_duration > 0:
        notes.append(Note(duration=final_rest_duration))
    return notes

def get_bar_sequence(data, title):
    b = 0
    bars = []
    for duration in data[title]['bars']:
        bar = Bar(number=b, duration=duration)
        bars.append(bar)
        b += 1
    return bars
'''
def parse_chord_data(string):
    chords = []
    l = string.split(" ")
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
                for j in range(start_idx, end_idx):
                    chords.append(l[j])
                start_idx = None
        else:
            chords.append(item)
    return chords

chord_breakdown = {
    '': '',
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

position_map = {
    1: 0,
    2: 2,
    3: 4,
    4: 5,
    5: 7,
    6: 9,
    7: 11,
    9: 2,
    11: 5,
    13: 9
}

note_map = {
    'C': 0,
    'C#': 1,
    'Db': 1,
    'D': 2,
    'D#': 3,
    'Eb': 3,
    'E': 4,
    'Fb': 4,
    'E#': 5,
    'F': 5,
    'F#': 6,
    'Gb': 6,
    'G': 7,
    'G#': 8,
    'Ab': 8,
    'A': 9,
    'A#': 10,
    'Bb': 10,
    'B': 11,
    'Cb': 11,
    'B#': 0
}

def make_chord_alterations(alteration, chordvec):
    alt_type = alteration.translate(None, string.digits)
    alt_note = int(alteration.translate(None, alt_type))
    alt_note_index = position_map[alt_note]
    if alt_type in ['b', '#']:
        chordvec[alt_note_index] = 0
        if alt_type == 'b':
            chordvec[alt_note_index - 1] = 1
        elif alt_type == '#':
            chordvec[alt_note_index + 1] = 1
    else:
        chordvec[alt_note_index] = 1
        if alt_type == 'sus':
            chordvec[position_map[3]] = 0

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
        alt_compiled_regex = re.compile(r"(\((\d+|M7)\)|[b#]\d+|sus\d+)")
        i = 0
        j = 2
        while i < len(full_breakdown):
            while not alt_compiled_regex.match(full_breakdown[i:j]):
                j += 1
            alteration = full_breakdown[i:j]
            make_chord_alterations(alteration, chordvec)
            i = j
            j = i + 2
        print chord, chordvec + root_vec + bass_vec






#chords = "[ 2CM7 Cm7 F7 2BbM7 Bbm7 Eb7 2AbM7 Dm7 G7b9 [ CM7 Am7 Dm7 G7 ] [ 3CM7 Am7 ] ] 2Dm7 2G7 2CM7 2Am7 2Dm7 2G7 C#m7 F#7 Dm7 G7 2CM7 Cm7 F7 2BbM7 Bbm7 Eb7 2AbM7 Dm7 G7b9 CM7 Am7 Dm7 G7"
chords = "2C7b5sus4/G Cm7 F13 2Ebo7 2Dm7 G7 G7#5"
get_chord_sequence(chords)

'''
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
    'ma7',
    'm7',
    '7',
    '7b9',
    ''
    'o7',
    '7#5',
    '6',
    '9',
    'm',
    '7#9',
    'm7b5',
    '7b5',
    '9sus4',
    '7sus4',
    '7#11',
    'm(ma7)',
    'm6',
    'ma7#5',
    '7(13)',
    'o',
    'ma9',
    '7b9sus4',
    'ma7#11',
    '7#5b9',
    '13#11',
    '13',
    'add9',
    'o(add9)',
    'sus4',
    '7b5b9',
    '9b5',
    '7#5#9',
    'm6(9)',
    'ma7b5',
    '9#11',
    'm11',
    '7sus4b9',
    'm(add9)',
    'mb6',
    'm#5',
    'm7(add ma7)',
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
print root, second, third, fourth, fifth, sixth, seventh'''