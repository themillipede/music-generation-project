import pretty_midi as pm

from definitions import QUAVER_DURATION


class Melody:
    def __init__(self, relative_durations, pitch_midi):
        pitches = self._get_melody_pitches(pitch_midi)
        i = 0
        self.melody = []
        for num_quavers in relative_durations:
            new_note = Note(
                pitch=pitches[i] if num_quavers > 0 else -1,
                duration=abs(num_quavers) * QUAVER_DURATION
            )
            i += 1 if num_quavers > 0 else 0
            self.melody.append(new_note)

    def _get_melody_pitches(self, pitch_midi):
        song = pm.PrettyMIDI(pitch_midi)
        inst = song.instruments[0].notes
        return [note.pitch for note in inst]


class MelodyFromMidi:
    def __init__(self, piece_duration, melody_midi):
        song = pm.PrettyMIDI(melody_midi)
        inst = song.instruments[0].notes
        self.melody = []
        time_elapsed = 0

        for note in inst:
            if note.start > time_elapsed:
                new_rest = Note(-1, note.start - time_elapsed)
                self.melody.append(new_rest)
            new_note = Note(note.pitch, note.end - note.start)
            self.melody.append(new_note)
            time_elapsed = note.end

        if piece_duration > time_elapsed:
            final_rest = Note(-1, piece_duration - time_elapsed)
            self.melody.append(final_rest)


class Note:
    def __init__(self, pitch, duration):
        self.pitch = pitch
        self.duration = duration
        self._extract_note_name_and_octave()
        self.time_remaining = self.duration

    def _extract_note_name_and_octave(self):
        name_octave = pm.note_number_to_name(self.pitch) if self.pitch > -1 else None
        self.name = name_octave.rstrip('0123456789') if name_octave else None
        self.octave = int(name_octave.lstrip(self.name)) if name_octave else None


class EmptyNote(Note):
    def __init__(self):
        self.time_remaining = 0
