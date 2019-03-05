import pretty_midi as pm
import string
import json
import re
import numpy as np
import pickle


class Note:
    def __init__(self, pitch=None, duration=None):
        self.pitch = pitch
        self.duration = duration
        self.name = None
        self.octave = None
        self.time_remaining = duration

    def get_note_name_and_octave(self):
        name_octave = pm.note_number_to_name(self.pitch)
        self.name = name_octave.translate(str.maketrans('', '', string.digits))
        self.octave = int(name_octave.translate(str.maketrans('', '', self.name)))


class Chord:
    def __init__(self, root=None, kind=None, alts=None, bass=None, chordset=None, duration=None):
        self.root = root
        self.kind = kind
        self.alts = alts
        self.bass = bass
        self.chordset = chordset
        self.duration = duration
        self.time_remaining = duration


class Bar:
    def __init__(self, number=None, duration=None):
        self.number = number
        self.duration = duration
        self.time_remaining = duration


class Timestep:
    """
    Every unique note/chord/bar combination gets its own timestep.
    """
    def __init__(self, note_name=None, note_octave=None, note_pitch=None, root=None, bass=None, chord=None,
                 bar=None, duration=None, is_tied=False, is_barline=False, same_note=False):
        self.note_name = note_name
        self.note_octave = note_octave
        self.note_pitch = note_pitch
        self.root = root
        self.bass = bass
        self.chord = chord
        self.bar = bar
        self.duration = duration
        self.is_tied = is_tied
        self.is_barline = is_barline
        self.same_note = same_note


class Piece:
    def __init__(self, name, composer, key_signature, time_signature, pickup_duration,
                 bar_durations, chord_symbols, note_durations):
        self.name = name
        self.composer = composer
        self.key_signature = key_signature
        self.time_signature = time_signature
        self.pickup_duration = pickup_duration
        self.bar_durations = bar_durations
        self.chord_symbols = chord_symbols
        self.note_durations = note_durations
        self.bars = None
        self.chords = None
        self.melody = []
        self.timesteps = []
        self.timestep_vectors = []


    def get_bars(self):
        self.bars = [Bar(n, duration * 30) for n, duration in enumerate(self.bar_durations)]


    def get_pitch_sequence(self, pitch_data):
        '''
        :param pitch_data: MIDI file containing a sequence of notes that matches the number of notes in the relevant
            piece, and the pitches of those notes (in order), but not necessarily with the correct note durations.
        :return: List containing, for each note of the piece (in order), just the number indicating its pitch.
        '''
        song = pm.PrettyMIDI(pitch_data)
        inst = song.instruments[0].notes
        pitch_list = [note.pitch for note in inst]
        return pitch_list


    def create_midi_melody(self, pitch_data, output_file, duration=30):
        melody = pm.PrettyMIDI()
        kboard = pm.Instrument(program=0)
        pitches = self.get_pitch_sequence(pitch_data)
        end = 0
        ix = 0
        for item in self.note_durations:
            if item < 0:
                end = round(end + (-1 * item * duration))
                continue
            start = end
            end = round(start + (item * duration))
            pitch = pitches[ix]
            ix += 1
            new_note = pm.Note(velocity=100, pitch=pitch, start=start, end=end)
            kboard.notes.append(new_note)
        melody.instruments.append(kboard)
        melody.write(output_file)


    def _midi_melody(self, relative_durations, pitch_midi):
        melody = pm.PrettyMIDI()
        kboard = pm.Instrument(program=0)
        pitch_list = self._get_melody_pitches(pitch_midi)
        end = 0
        idx = 0
        for item in relative_durations:
            duration = abs(item) * QUAVER_DURATION
            start = end
            end = round(start + duration)
            if item < 0:
                continue
            pitch = pitch_list[idx]
            idx += 1
            new_note = pm.Note(100, pitch, start, end)
            kboard.notes.append(new_note)
        melody.instruments.append(kboard)
        self.midi_melody = melody


    def get_melody(self, midi_data):
        song = pm.PrettyMIDI(midi_data)
        inst = song.instruments[0].notes
        latest_time = 0
        elapsed_time = 0

        for note in inst:
            if note.start > latest_time:
                rest_duration = note.start - latest_time
                self.melody.append(Note(duration=rest_duration))
            note_duration = note.end - note.start
            next_note = Note(note.pitch, note_duration)
            next_note.get_note_name_and_octave()
            self.melody.append(next_note)
            elapsed_time += note.end - latest_time
            latest_time = note.end

        bar_durations = sum([b.duration for b in self.bars])
        piece_duration = bar_durations + self.pickup_duration
        final_rest_duration = piece_duration - elapsed_time
        if final_rest_duration > 0:
            self.melody.append(Note(duration=final_rest_duration))


    def get_chord_sequence(self):
        """
        :param chord_data: String containing a space-separated sequence of chord symbols and square parentheses.
        Sections within parentheses that are not nested within outer parentheses represent repeated sections,
        while any nested sections signify first, second, time bars, in order of appearance.
        :return: List of all chords, in order of appearance.
        """
        chords = []
        l = self.chord_symbols.split(' ')
        start_idx = None
        end_idx = None
        open_parens = 0
        for i, item in enumerate(l):
            if item == '[':
                if open_parens == 0:
                    start_idx = i + 1
                elif l[i - 1] != ']':
                    end_idx = i
                open_parens += 1
            elif item == ']':
                if open_parens == 1 and l[i - 1] != ']':
                    chords.extend(l[start_idx:i])
                elif open_parens == 2 and l[i + 1] != ']':
                    chords.extend(l[start_idx:end_idx])
                open_parens -= 1
            else:
                chords.append(item)
        return chords


    def make_chord_alteration(self, alt, chordset):
        """
        :param alteration: String indicating the chord alteration, including the label of the affected
            note, and the alteration type: 'b', '#', '()', or 'sus'.
        :param chordset: Set containing the zero-indexed position in the 12-note chromatic scale of
            all the notes in the chord of interest, prior to alteration.
        :return: Chordset after alteration has been applied.
        """
        type = alt.translate(str.maketrans('', '', string.digits))  # 'b', '#', '()', or 'sus'
        note = int(alt.translate(str.maketrans('', '', type)))  # number of note affected
        index = note_num_idx[note]  # position of affected note in the chromatic scale, zero-indexed
        if type in ['b', '#']:
            chordset.discard(index)
            if type == 'b':
                chordset.add(index - 1)
            elif type == '#':
                chordset.add(index + 1)
        elif type in ['()', 'sus']:
            chordset.add(index)
            if type == 'sus':
                chordset -= {3, 4}


    def get_chord(self, chord, chord_regex, alts_regex):
        chord_match = chord_regex.match(chord)
        time = chord_match.group(1) or 1
        root = chord_match.group(2)
        kind = chord_match.group(3)
        alts = chord_match.group(4)
        bass = chord_match.group(5) or root

        chord_flavour = kind.translate(str.maketrans('', '', string.digits))
        extension = kind.translate(str.maketrans('', '', chord_flavour))
        if extension in ('9', '11', '13'):
            kind = chord_flavour + str(7)
            exts = set(range(9, int(extension) + 1, 2))
        else:
            exts = set()

        triad = triad_notes[chord_quality[kind][0]]
        seven = seventh_notes[chord_quality[kind][1]]
        chordset = (triad|exts)
        chordset.add(seven)
        alts_lst = re.findall(alts_regex, alts)
        for alt in alts_lst:
            self.make_chord_alteration(alt, chordset)
        return Chord(root, kind, alts, bass, chordset, round(float(time)*120))


    def get_chords(self):
        chord_regex = re.compile(r'''
            (\d*(?:\.\d+)?)
            ([A-G][b#]?)
            ([m\+oø]?(?:M?(?:7|9|11|13))?)?
            ((?:\((?:\d+)\)|[b#]\d+|sus\d+)*)
            (?:/([A-G][b#]?))?''', re.X)
        alts_regex = re.compile(r'(\((?:\d+)\)|[b#]\d+|sus\d+)')
        chord_sequence = self.get_chord_sequence()
        self.chords = [self.get_chord(chord, chord_regex, alts_regex) for chord in chord_sequence]


    def get_timesteps(self):
        this_note = Note(duration=0)
        this_chord = Chord(duration=0)
        this_bar = Bar(duration=0)
        n = -1
        c = -1
        b = -1

        while n < len(self.melody) or c < len(self.chords) or b < len(self.bars):
            timestep_duration = min(
                this_note.time_remaining,
                this_chord.time_remaining,
                this_bar.time_remaining
            )
            if timestep_duration > 0:
                this_timestep = Timestep(
                    note_name=this_note.name,
                    note_octave=this_note.octave,
                    note_pitch=this_note.pitch,
                    root=this_chord.root,
                    bass=this_chord.bass,
                    chord=this_chord.chordset,
                    bar=this_bar.number,
                    duration=timestep_duration,
                    is_tied=False,
                    is_barline=is_barline,
                    same_note=same_note
                )
                self.timesteps.append(this_timestep)
            elif self.pickup_duration:
                this_chord.time_remaining = self.pickup_duration
                this_bar.time_remaining = self.pickup_duration

            this_note.time_remaining -= timestep_duration
            if this_note.time_remaining == 0:
                n += 1
                if n < len(self.melody):
                    this_note = self.melody[n]
                same_note = False
            else:
                this_timestep.is_tied = True
                same_note = True

            this_chord.time_remaining -= timestep_duration
            if this_chord.time_remaining == 0:
                c += 1
                if c < len(self.chords):
                    this_chord = self.chords[c]

            this_bar.time_remaining -= timestep_duration
            if this_bar.time_remaining == 0:
                b += 1
                if b < len(self.bars):
                    this_bar = self.bars[b]
                    is_barline = True
            else:
                is_barline = False


    def get_timestep_vectors(self):
        prev_note = -1
        for timestep in self.timesteps:
            note_name_vec = [0 if i != note_name_idx[timestep.note_name] else 1 for i in range(12)]
            note_octave_vec = [0 if i != timestep.note_octave else 1 for i in range(3)]
            # If 1 then note_name_vec and note_octave_vec should both be 0.
            curr_note = timestep.note_pitch
            same_note_vec = [0] if curr_note != prev_note else [1]
            prev_note = curr_note
            root_vec = [0 if i != note_name_idx[timestep.root] else 1 for i in range(12)]
            bass_vec = [0 if i != note_name_idx[timestep.bass] else 1 for i in range(12)]
            if timestep.chord is None:
                chord_vec = [0 for _ in range(12)]
            else:
                chord_vec = [0 if i not in timestep.chord else 1 for i in range(12)]
            # Between 1 triplet semiquaver and 24 triplet semiquavers (i.e. 1 bar).
            duration_vec = [0 if (i + 1) * 10 != timestep.duration else 1 for i in range(24)]
            timestep_vector = (note_name_vec + note_octave_vec + same_note_vec
                               + root_vec + bass_vec + chord_vec + duration_vec)
            self.timestep_vectors.append(timestep_vector)


def timesteps():
    note_name_vecs = np.eye(13)[[12 if ts.same_note is True else note_name_idx[ts.note_name] for ts in piece]]
    note_octave_vecs = np.eye(3)[[ts.note_octave - 3 for ts in piece]]
    root_vecs = np.eye(12)[[note_name_idx[ts.root] for ts in piece]]
    bass_vecs = np.eye(12)[[note_name_idx[ts.root] for ts in piece]]
    chord_vecs = np.eye(12)[[ts.full_chordset for ts in piece]]
    duration_vecs = np.eye(24)[[ts.duration / 10 - 1 for ts in piece]]


with open('music/pieces.json') as f:
    piece_data = json.load(f)
i = 0
piece_list = []
for title, details in piece_data.items():
    i += 1
    if i > 20:
        break
    else:
        print(i)
    if not details["chords"]:
        continue
    piece = Piece(
        title,
        details['composer'],
        details['keysig'],
        details['timesig'],
        details['pickup']*30,
        eval(details['bars']),
        details['chords'],
        details['notes']
    )
    piece.get_bars()
    piece.create_midi_melody('PitchMIDI/' + piece.name + '_pitches.MID', piece.name + '.MID')
    piece.get_melody(piece.name + '.MID')
    piece.get_chords()
    piece.get_timesteps()
    piece.get_timestep_vectors()
    piece_list.append(np.array(piece.timestep_vectors))

with open('music_timesteps.pkl', 'wb') as f:
    pickle.dump(piece_list, f, pickle.HIGHEST_PROTOCOL)



############################################################



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



############################################################


import os, sys, inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import json
import re
import string
import pretty_midi as pm
from midi_creation import create_midi_melody, get_pitch_sequence_from_midi
from music.notes import Note, Bar

with open('music/pieces.json') as f:
    data = json.load(f)

for title in data:
    if not data[title]['notes']:
        continue
    filename = '%s.MID' % title
    file = 'Composition/%s' % filename
    try:
        create_midi_melody(data[title]['notes'], file, 'ParsedMIDI/%s' % filename, duration=0.3)
        print
        title
    except:
        print
        "Error - %s" % title


def get_midi_details(filename):
    song = pm.PrettyMIDI(filename)
    inst = song.instruments[0].notes
    for note in inst:
        print
        round(note.start, 1), round(note.end, 1)


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
    'M13': '(7)(2)(4)(6)',
    'mM7': 'b3(7)',
    'mM9': 'b3(7)(2)',
    'mM11': 'b3(7)(2)(4)',
    'mM13': 'b3(7)(2)(4)(6)'
}

'''
_: major triad
m: minor triad
o: diminished triad
+: augmented triad
o7: diminished triad + diminished seventh interval
ø7: diminished triad + minor seventh interval
7: major triad + minor seventh interval
m7: minor triad + minor seventh interval
M7: major triad + major seventh interval
+7: augmented triad + minor seventh interval
mM7: minor triad + major seventh interval
+M7: augmented triad + major seventh interval

if 9, 11, 13: add relevant notes
if _, m, M, +, o, or ø, the corresponding seventh is implied

regex = r"(\d*)([A-G][b#]?)((?:m|\+|o|ø)?(?:M?(?:7|9|11|13))?)?((?:\((?:\d+)\)|[b#]\d+|sus\d+)*)(/([A-G][b#]?))?"

if group 3:
    end = ...
    start = ...
    if end is a number > 7:
        chord_type = chord_quality[start + str(7)]
        third = chord_type[0]
        seventh = chord_type[1]
        extra_notes = range(9, end + 1, 2)
'''

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

triad_notes = {
    'maj': set([0, 4, 7]),
    'min': set([0, 3, 7]),
    'aug': set([0, 4, 8]),
    'dim': set([0, 3, 6])
}

seven_notes = {
    'maj': 11,
    'min': 10,
    'dim': 9
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

note_position = {
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


def make_chord_alteration(alteration, chordset, position_map):
    """
    :param alteration: String indicating the chord alteration, including the label of the affected
        note, and the alteration type: 'b', '#', '()', or 'sus'.
    :param chordvec: 12-dimensional binary vector representing the 12 notes of the chromatic scale,
        with positions 0, 4, and 7 set to 1, representing the major triad.
    :return: Altered chordvec, with positions set to 1 indicating notes present in the chord.
    """
    type = alteration.translate(None, string.digits)  # alteration type: 'b', '#', '()', or 'sus'
    note = int(alteration.translate(None, type))  # name(=number) of note affected by alteration
    index = position_map[note]  # position of affected note in the chromatic scale, zero-indexed
    if type in ['b', '#']:
        chordset.discard(index)
        if type == 'b':
            chordset.add(index - 1)
        elif type == '#':
            chordset.add(index + 1)
    elif type in ['()', 'sus']:
        chordset.add(index)
        if type == 'sus':
            chordset.discard([position_map[3]])


def get_chord_sequence(chord_symbols):
    """
    :param chord_data: String containing a space-separated sequence of chord symbols.
    Sections within square parentheses that are not contained within outer square parentheses
    represent repeated sections, and any inner sections bounded by square parentheses signify
    first, second, etc. time bars, in order of appearance.
    :return: List of all chords, in order of appearance.
    """
    chords = []
    l = chord_symbols.split(" ")
    start_idx = None
    end_idx = None
    open_parens = 0
    for i, item in enumerate(l):
        if item == '[':
            if open_parens == 0:
                start_idx = i + 1
            elif l[i - 1] != ']':
                end_idx = i
            open_parens += 1
        elif item == ']':
            if open_parens == 1 and l[i - 1] != ']':
                chords.extend(l[start_idx:i])
            elif l[i + 1] != ']':
                chords.extend(l[start_idx:end_idx])
            open_parens -= 1
        else:
            chords.append(item)


def get_chord(chord, chord_regex, alts_regex, chord_quality):
    chord_match = chord_regex.match(chord)
    root = chord_match.group(2)
    type = chord_match.group(3)
    alts = chord_match.group(4)
    bass = chord_match.group(5) or root

    chord_flavour = type.translate(None, string.digits)
    extension = type.translate(None, chord_flavour)
    if extension in ('9', '11', '13'):
        type = chord_flavour + str(7)
        exts = set(range(9, int(extension) + 1, 2))
    elif not extension:
        exts = set()

    triad = triad_notes[chord_quality[type[0]]]
    seven = seven_notes[chord_quality[type[1]]]
    chordset = triad.add(seven).add(exts)
    alts_lst = re.findall(alts_regex, alts)
    for alt in alts_lst:
        make_chord_alteration(alt, chordset)


def get_chords(chords, note_position, chord_breakdown):
    chord_regex = re.compile(
        r'(\d*)'
        r'([A-G][b#]?)'
        r'([m\+oø]?(?:M?(?:7|9|11|13))?)?'
        r'((?:\((?:\d+)\)|[b#]\d+|sus\d+)*)'
        r'(/([A-G][b#]?))?')
    alts_regex = re.compile(r'(\((?:\d+)\)|[b#]\d+|sus\d+)')
    chord_sequence = get_chord_sequence(chords)
    chord_list = [get_chord(chord, chord_regex, alts_regex, chord_quality) for chord in chord_sequence]
    return chord_list


# chords = "[ 2CM7 Cm7 F7 2BbM7 Bbm7 Eb7 2AbM7 Dm7 G7b9 [ CM7 Am7 Dm7 G7 ] [ 3CM7 Am7 ] ] 2Dm7 2G7 2CM7 2Am7 2Dm7 2G7 C#m7 F#7 Dm7 G7 2CM7 Cm7 F7 2BbM7 Bbm7 Eb7 2AbM7 Dm7 G7b9 CM7 Am7 Dm7 G7"
chords = "2C7b5sus4/G Cm7 F13 2Ebo7 2Dm7 G7 G7#5"
get_chord_sequence(chords)