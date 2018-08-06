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

    def __init__(self, note=None, chord=None, bar=None, duration=None, is_tied=False, is_barline=False):
        self.note = note
        self.chord = chord
        self.bar = bar
        self.duration = duration
        self.is_tied = is_tied
        self.is_barline = is_barline


class Piece:

    def __init__(self, name=None, key_signature=None, time_signature=None, anacrusis_duration=None):
        self.name = name
        self.key_signature = key_signature
        self.time_signature = time_signature
        self.anacrusis_duration = anacrusis_duration

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
                    is_tied=False,
                    is_barline=is_barline
                )
                self.timesteps.append(this_timestep)
            elif self.anacrusis_duration:
                this_chord.time_remaining = self.anacrusis_duration
                this_bar.time_remaining = self.anacrusis_duration

            this_note.time_remaining -= timestep_duration
            if this_note.time_remaining == 0:
                n += 1
                if n < len(notes):
                    this_note = notes[n]
            else:
                this_timestep.is_tied = True

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