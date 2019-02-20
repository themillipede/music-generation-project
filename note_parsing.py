import pretty_midi as pm

from .definitions import QUAVER_DURATION


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


class Note:
    def __init__(self, pitch, duration):
        self.pitch = pitch
        self.duration = duration
        self._extract_note_name_and_octave()
        self.time_remaining = self.duration

    def _extract_note_name_and_octave(self):
        name_octave = pm.note_number_to_name(self.pitch)
        self.name = name_octave.rstrip('0123456789')
        self.octave = int(name_octave.lstrip(self.name))
