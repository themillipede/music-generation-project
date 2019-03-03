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