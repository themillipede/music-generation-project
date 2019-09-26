import note_parsing, chord_parsing, bar_parsing

from definitions import QUAVER_DURATION


class Piece:
    def __init__(self, title, composer, pickup_duration, melody, chords, bars):
        self.title = title
        self.composer = composer
        self.pickup_duration = pickup_duration * QUAVER_DURATION
        self.timesteps = []
        this_note = note_parsing.EmptyNote()
        this_chord = chord_parsing.EmptyChord()
        this_bar = bar_parsing.EmptyBar()
        n = -1
        c = -1
        b = -1

        while n < len(melody) or c < len(chords) or b < len(bars):
            timestep_duration = min(
                this_note.time_remaining,
                this_chord.time_remaining,
                this_bar.time_remaining
            )
            if timestep_duration > 0:  # This will never be true on the first loop.
                this_timestep = Timestep(
                    note_name=this_note.name,
                    note_octave=this_note.octave,
                    note_pitch=this_note.pitch,
                    root=this_chord.root,
                    bass=this_chord.bass,
                    core_chordset=this_chord.core_chordset,
                    full_chordset=this_chord.full_chordset,
                    bar_number=this_bar.number,
                    duration=timestep_duration,
                    is_barline=is_barline,
                    same_note=same_note
                )
                self.timesteps.append(this_timestep)
            elif self.pickup_duration > 0:
                this_chord.time_remaining = self.pickup_duration
                this_bar.time_remaining = self.pickup_duration

            this_note.time_remaining -= timestep_duration
            if this_note.time_remaining == 0:
                n += 1
                if n < len(melody):
                    this_note = melody[n]
                same_note = False
            else:
                same_note = True

            this_chord.time_remaining -= timestep_duration
            if this_chord.time_remaining == 0:
                c += 1
                if c < len(chords):
                    this_chord = chords[c]

            this_bar.time_remaining -= timestep_duration
            if this_bar.time_remaining == 0:
                b += 1
                if b < len(bars):
                    this_bar = bars[b]
                    is_barline = True
            else:
                is_barline = False


class Timestep:
    """
    Every unique note/chord/bar combination has its own timestep. There are four (currently) redundant timestep
    attributes (note_name, note_octave, core_chordset, and bar_number), which are included because they may end
    up being used for alternative approaches to the modelling task. E.g. the chord representation core_chordset
    will map to multiple full_chordsets, and so any full_chordset in the dataset is likely to show up much less
    than its corresponding core_chordset. If there are not enough data points for effective training when using
    full_chordset, it may turn out that core_chordset (which still captures the essence of the chord) proves to
    be more fruitful.
    """
    def __init__(self, note_pitch, root, bass, full_chordset, duration,
                 same_note, note_name=None, note_octave=None,
                 bar_number=None, is_barline=None, core_chordset=None):

        self.note_name = note_name
        self.note_octave = note_octave
        self.note_pitch = note_pitch
        self.root = root
        self.bass = bass
        self.core_chordset = core_chordset
        self.full_chordset = full_chordset
        self.bar_number = bar_number
        self.duration = duration
        self.is_barline = is_barline
        self.same_note = same_note
