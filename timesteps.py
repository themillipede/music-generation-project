import note_parsing, chord_parsing, bar_parsing


class Piece:
    def __init__(self, title, composer, pickup_duration, melody, chords, bars):
        self.title = title
        self.composer = composer
        self.pickup_duration = pickup_duration
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
            if timestep_duration > 0:
                this_timestep = Timestep(
                    note_name=this_note.name,
                    note_octave=this_note.octave,
                    note_pitch=this_note.pitch,
                    root=this_chord.root,
                    bass=this_chord.bass,
                    type_chordset=this_chord.type_chordset,
                    full_chordset=this_chord.full_chordset,
                    bar_number=this_bar.number,
                    duration=timestep_duration,
                    is_tied=False,
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
                this_timestep.is_tied = True
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
    Every unique note/chord/bar combination gets its own timestep.
    """
    def __init__(self, note_name, note_octave, note_pitch, root, bass, type_chordset,
                 full_chordset, bar_number, duration, is_tied, is_barline, same_note):
        self.note_name = note_name
        self.note_octave = note_octave
        self.note_pitch = note_pitch
        self.root = root
        self.bass = bass
        self.type_chordset = type_chordset
        self.full_chordset = full_chordset
        self.bar_number = bar_number
        self.duration = duration
        self.is_tied = is_tied
        self.is_barline = is_barline
        self.same_note = same_note
