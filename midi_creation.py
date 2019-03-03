import pretty_midi as pm

from definitions import QUAVER_DURATION


class MidiMelody:
    def __init__(self, relative_durations, pitch_midi):
        melody = pm.PrettyMIDI()
        kboard = pm.Instrument(program=0)
        pitch_list = self.get_melody_pitches(pitch_midi)
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

    def get_melody_pitches(self, pitch_midi):
        song = pm.PrettyMIDI(pitch_midi)
        inst = song.instruments[0].notes
        return [note.pitch for note in inst]

    def write_midi_to_file(self, output_file):
        self.midi_melody.write(output_file)
