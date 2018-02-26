import pretty_midi as pm

scale_positions = {
    "flats": {0: 0, 1: 5, 2: 10, 3: 3, 4: 8, 5: 1, 6: 6, 7: 11},
    "sharps": {0: 0, 1: 7, 2: 2, 3: 9, 4: 4, 5: 11, 6: 6, 7: 1}
}

scale_steps = {str(k1) + k[0]: v1 for k, v in scale_positions.items() for k1, v1 in v.items()}

def normalise_midi_melody_key(melody, scale_steps, key_code, normalised_melody_output):
    normalised_melody = pm.PrettyMIDI()
    kboard = pm.Instrument(program=0)
    distance_from_standard_root = scale_steps[key_code]
    for note in melody:
        normalised_pitch = note.pitch - distance_from_standard_root
        normalised_note = pm.Note(velocity=note.velocity, pitch=normalised_pitch,
                                  start=note.start, end=note.end)
        kboard.notes.append(normalised_note)
    normalised_melody.instruments.append(kboard)
    normalised_melody.write(normalised_melody_output)