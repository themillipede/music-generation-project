import pretty_midi as pm
import string
import json
import re


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
    'maj': {0, 4, 7},
    'min': {0, 3, 7},
    'aug': {0, 4, 8},
    'dim': {0, 3, 6}
}

seven_notes = {
    'maj': 11,
    'min': 10,
    'dim': 9,
    None: 0
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
    def __init__(self, note=None, chord=None, bar=None, duration=None, is_tied=False, is_barline=False):
        self.note = note
        self.chord = chord
        self.bar = bar
        self.duration = duration
        self.is_tied = is_tied
        self.is_barline = is_barline


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


    def get_bars(self):
        self.bars = [Bar(n, duration * 30) for n, duration in enumerate(self.bar_durations)]


    def get_pitch_sequence(self, pitch_data):
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
            self.melody.append(Note(note.pitch, note_duration))
            elapsed_time += note.end - latest_time
            latest_time = note.end

        bar_durations = sum([b.duration for b in self.bars])
        piece_duration = bar_durations + self.pickup_duration
        final_rest_duration = piece_duration - elapsed_time
        if final_rest_duration > 0:
            self.melody.append(Note(duration=final_rest_duration))


    def get_chord_sequence(self):
        """
        :param chord_data: String containing a space-separated sequence of chord symbols.
        Sections within square parentheses that are not contained within outer square parentheses
        represent repeated sections, and any inner sections bounded by square parentheses signify
        first, second, etc. time bars, in order of appearance.
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


    def make_chord_alteration(self, alteration, chordset):
        """
        :param alteration: String indicating the chord alteration, including the label of the affected
            note, and the alteration type: 'b', '#', '()', or 'sus'.
        :param chordset: Set containing the zero-indexed position in the 12-note chromatic scale of
            all the notes in the chord of interest, prior to alteration.
        :return: Chordset after alteration has been applied.
        """
        type = alteration.translate(str.maketrans('', '', string.digits))
        note = int(alteration.translate(str.maketrans('', '', type)))
        #type = alteration.translate(None, string.digits)  # alteration type: 'b', '#', '()', or 'sus'
        #note = int(alteration.translate(None, type))  # name(=number) of note affected by alteration
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
        seven = seven_notes[chord_quality[kind][1]]
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
            (/([A-G][b#]?))?''', re.X)
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
                    note=this_note.pitch,
                    chord=this_chord.chordset,
                    bar=this_bar.number,
                    duration=timestep_duration,
                    is_tied=False,
                    is_barline=is_barline
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
            else:
                this_timestep.is_tied = True

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
        for ts in self.timesteps:
            pass

with open('music/pieces.json') as f:
    piece_data = json.load(f)
for title, details in piece_data.items():
    if not details["chords"] or title == "angel_eyes":
        continue
    print(title)
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
