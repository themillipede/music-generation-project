class Note:

    def __init__(self, pitch=None, duration=None):
        self.pitch = pitch
        self.duration = duration
        self.time_remaining = duration


class Chord:

    def __init__(self, name=None, duration=None):
        self.name = name
        self.duration = duration
        self.chord_family = None
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

    def __init__(self, note, chord, bar, duration, is_tied, is_barline):
        self.note = note
        self.chord = chord
        self.bar = bar
        self.duration = None
        self.is_tied = False
        self.is_barline = False


class Piece:

    def __init__(self, name=None, key_signature=None, time_signature=None):
        self.name = name
        self.key_signature = key_signature
        self.time_signature = time_signature
        self.anacrusis_duration = None

    def get_anacrusis_duration(self):
        pass

    def get_timestep_sequence(self, notes, chords, bars):
        self.timesteps = []
        this_note = Note(duration=0)
        this_chord = Chord(duration=0)
        this_bar = Bar(duration=0)
        n = -1
        c = -1
        b = -1

        while n < len(notes) or c < len(chords) or b < len(bars):
            timestep_duration = min(
                this_note.time_remaining,
                this_chord.time_remaining,
                this_bar.time_remaining
            )
            if timestep_duration > 0:
                this_timestep = Timestep(
                    note=this_note.pitch,
                    chord=this_chord.name,
                    bar=this_bar.number,
                    duration=timestep_duration,
                    is_barline=is_barline
                )
                self.timesteps.append(this_timestep)

            elif self.anacrusis_duration:
                this_chord.time_remaining = self.anacrusis_duration
                this_bar.time_remaining = self.anacrusis_duration

            this_note.time_remaining -= timestep_duration
            if this_note.time_remaining == 0:
                n += 1
                this_note = notes[n]
            else:
                this_timestep.is_tied = True

            this_chord.time_remaining -= timestep_duration
            if this_chord.time_remaining == 0:
                c += 1
                this_chord = chords[c]

            this_bar.time_remaining -= timestep_duration
            if this_bar.time_remaining == 0:
                b += 1
                this_bar = bars[b]
                is_barline = True
            else:
                is_barline = False