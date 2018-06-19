import pretty_midi as pm

def get_pitch_sequence_from_midi(pitch_input):
    song = pm.PrettyMIDI(pitch_input)
    inst = song.instruments[0].notes
    pitch_list = [note.pitch for note in inst]
    return pitch_list

def create_midi_melody(note_durations, pitch_input, melody_output, duration=0.3):
    melody = pm.PrettyMIDI()
    kboard = pm.Instrument(program=0)
    pitches = get_pitch_sequence_from_midi(pitch_input)
    end = 0
    ix = 0
    for item in note_durations:
        if item < 0:
            end = round(end + (-1 * item * duration), 1)
            continue
        start = end
        end = round(start + (item * duration), 1)
        pitch = pitches[ix]
        ix += 1
        new_note = pm.Note(velocity=100, pitch=pitch, start=start, end=end)
        kboard.notes.append(new_note)
    melody.instruments.append(kboard)
    melody.write(melody_output)