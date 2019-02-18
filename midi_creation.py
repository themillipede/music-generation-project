import pretty_midi as pm


class MidiMelody:
    def __init__(self):
        self.midi_melody = None

    def _get_pitch_sequence_from_midi(self, pitch_midi):
        song = pm.PrettyMIDI(pitch_midi)
        inst = song.instruments[0].notes
        pitch_list = [note.pitch for note in inst]
        return pitch_list

    def create_midi_melody(self, relative_durations, pitch_midi, quaver_duration=30):
        melody = pm.PrettyMIDI()
        kboard = pm.Instrument(program=0)
        pitch_list = self._get_pitch_sequence_from_midi(pitch_midi)
        end = 0
        idx = 0
        for item in relative_durations:
            if item < 0:
                end = round(end + (-1 * item * quaver_duration))
                continue
            start = end
            end = round(start + (item * quaver_duration))
            pitch = pitch_list[idx]
            idx += 1
            new_note = pm.Note(velocity=100, pitch=pitch, start=start, end=end)
            kboard.notes.append(new_note)
        melody.instruments.append(kboard)
        self.midi_melody = melody

    def write_to_midi_file(self, output_file):
        self.midi_melody.write(output_file)
