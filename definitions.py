from collections import OrderedDict

"""

In many cases, there are a number of different jazz chord symbols that can be used to indicate the same
combination of notes; for example, the chord consisting of a diminished triad and a minor seventh, with
a root of C, is commonly written as any of the following: Cø7, Cm7b5, C-7b5.

To avoid complications arising from the many different ways of writing the same chord, every jazz chord
symbol used in this project has the same standard format, comprising the following components, in order:

1. The root note of the chord:
   A capital letter between A and G, followed by '#' or 'b' in the case of sharpened or flattened notes.

2. The "chord quality":
   A string of characters specifying the core "chord quality", which is defined by the specific type of
   triad (major, minor, augmented or diminished) and seventh note that are combined to create the chord.

3. Alterations (if applicable):
   An additional string of characters may be appended, to define any alterations to the core chord, and
   there is no limit to how many alterations may be included in this string. Any sharpened or flattened
   notes are represented by the note number prepended with '#' or 'b' as appropriate; new additions are
   represented by the note position written within parentheses; sus chords are written 'sus4' or 'sus2'.

4. Bass note (if applicable):
   If there is a bass note that is not the root note of the chord, it is represented by a forward slash
   followed by the intended bass note, which is written in the same format as the root note in part (1).

"""


# - The dict chord_quality defines the 12 core chord types, each of which has its own distinctive quality.
# - There are four triads that can be constructed by stacking combinations of major and minor thirds from
#   the root: major (= maj + min), minor (= min + maj), augmented (= maj + maj), diminished (= min + min).
# - There are three seventh notes, defined by their intervals from the root: major, minor, and diminished
#   (there is no augmented seventh, as this is the same as the root with an interval of a perfect octave).
# - Each chord type comprises one of the four key triad chords, and (in 8/12 of the cases) a seventh note.
# - The chord type written as an empty string corresponds to the simple major triad.
# - Each chord is mapped to a tuple containing its constituent triad, and seventh note (where applicable).

chord_quality = {
    '': ('maj', None),
    'm': ('min', None),
    '+': ('aug', None),
    'o': ('dim', None),
    '7': ('maj', 'min'),
    'M7': ('maj', 'maj'),
    'm7': ('min', 'min'),
    'mM7': ('min', 'maj'),
    '+7': ('aug', 'min'),
    '+M7': ('aug', 'maj'),
    'o7': ('dim', 'dim'),
    'ø7': ('dim', 'min')
}


# triad_notes maps each of the four key types of triad to a set containing the relative positions
# in the 12-note chromatic scale of its constituent notes (zero-indexed).

triad_notes = {
    'maj': {0, 4, 7},
    'min': {0, 3, 7},
    'aug': {0, 4, 8},
    'dim': {0, 3, 6}
}


# seventh_notes maps each seventh note to its relative position in the 12-note chromatic scale.

seventh_notes = {
    'maj': 11,
    'min': 10,
    'dim': 9
}


# note_num_idx maps each scale position to its relative position in the 12-note chromatic scale.

note_num_idx = {
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


# note_name_idx maps each note name (including all common enharmonic equivalents) to its relative
# position in the 12-note chromatic scale in the key of C.

note_name_idx = {
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


# Each variable name describes a "flat", "perfect", or "sharp" note from the major scale.
# Each value is the corresponding relative position in the 12-note chromatic scale.

p1 = 0
f2 = 1
p2 = 2
s2 = 3
f3 = 3
p3 = 4
p4 = 5
s4 = 6
f5 = 6
p5 = 7
s5 = 8
f6 = 8
p6 = 9
f7 = 10
p7 = 11


chord_name = OrderedDict([
    (frozenset([0, 4, 7, 10]), '7'),
    (frozenset([0, 4, 7, 11]), 'M7'),
    (frozenset([0, 4, 8, 10]), '+7'),
    (frozenset([0, 4, 8, 11]), '+M7'),
    (frozenset([0, 3, 7, 10]), 'm7'),
    (frozenset([0, 3, 7, 11]), 'mM7'),
    (frozenset([0, 3, 6, 9]), 'o7'),
    (frozenset([0, 3, 6, 10]), 'ø7'),
    (frozenset([0, 4, 7]), ''),
    (frozenset([0, 4, 8]), '+'),
    (frozenset([0, 3, 7]), 'm'),
    (frozenset([0, 3, 6]), 'o')
])


QUAVER_DURATION = 30
MINIM_DURATION = 120
