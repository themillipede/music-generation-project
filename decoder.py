import numpy as np
from note_parsing import Note, EmptyNote
from chord_parsing import Chord, EmptyChord
from bar_parsing import Bar, EmptyBar
from timesteps import Timestep
from definitions import chord_name, p1, f2, p2, s2, f3, p3, p4, s4, f5, p5, s5, f6, p6, f7, p7


def create_midi_from_output(melody, chords, bars):
    pass  # TODO: convert output into MIDI format


def load_samples(path):
    batch = np.load(path)
    samples = []
    for sample in batch:
        sample_timesteps = [timestep_object_from_vector(tvec) for tvec in sample]
        decoded_sample = decode_timesteps(sample_timesteps)
        samples.append(decoded_sample)
    return samples  # One decoded_sample is a (melody, chords, bars) tuple.


def timestep_object_from_vector(timestep_vector):
    note_vec = timestep_vector[0:38]
    root_vec = timestep_vector[38:51]
    bass_vec = timestep_vector[51:64]
    chord_vec = timestep_vector[64:76]
    duration_vec = timestep_vector[76:100]

    note_idx = np.argmax(note_vec)
    note_pitch = None if note_idx == 36 else -1 if note_idx == 37 else note_idx + 48
    same_note = True if note_pitch is None else False

    root_idx = np.argmax(root_vec)
    root = root_idx if root_idx < 12 else None

    bass_idx = np.argmax(bass_vec)
    bass = bass_idx if bass_idx < 12 else None

    full_chordset = set([i for i, n in enumerate(chord_vec) if n == 1])

    duration_idx = np.argmax(duration_vec)
    duration = (duration_idx + 1) * 10
    return Timestep(note_pitch, root, bass, full_chordset, duration, same_note)


def decode_timesteps(timesteps):
    """
    timesteps is an ordered list of Timestep objects representing a piece of music, transformed from the vector
    output of the model. The function reconnects these timesteps to produce lists of the melody, chord, and bar
    sequences that comprise the piece. These can then be processed further to produce machine or human-readable
    music in the desired format.
    """
    melody = []
    chords = []
    bars = []
    curr_note = EmptyNote()
    curr_chord = EmptyChord()
    bar_number = -1

    first_timestep = timesteps[0]

    if first_timestep.same_note:
        raise RuntimeError("Invalid output: first note is back-tied")

    if not first_timestep.is_barline:  # There's a pickup.
        curr_bar = Bar(bar_number, 0)

    for ts in timesteps:
        if ts.same_note is True:
            curr_note.duration += ts.duration
        else:
            curr_note = Note(ts.pitch, ts.duration)
            melody.append(curr_note)
        if (ts.root, ts.bass, ts.full_chordset) == (curr_chord.root, curr_chord.bass, curr_chord.full_chordset):
            curr_chord.duration += ts.duration
        else:
            curr_chord = Chord(ts.root, ts.bass, ts.full_chordset, ts.duration)
            chords.append(curr_chord)
        if ts.is_barline:
            bar_number += 1
            curr_bar = Bar(bar_number, ts.duration)
            bars.append(curr_bar)
        else:
            curr_bar.duration += ts.duration
    return melody, chords, bars


def get_chord_symbol(chord):
    root = chord.root
    bass = chord.bass
    chordset = chord.full_chordset
    alts = []

    if {f3, p3}.isdisjoint(chordset) and {p2, p4}.intersection(chordset):
        sus_type = 'sus4' if p4 in chordset and not {f2, p2}.issubset(chordset) else 'sus2'
        alts.append(sus_type)
        chordset.remove(p4) if sus_type == 'sus4' else chordset.remove(p2)
        chordset.add(p3)

    minimum_requirements = [{p1}, {f3, p3}, {f5, p5, s5}]
    invalid_combinations = [{1, 2}, {2, 3, 4}, {1, 3, 4}, {5, 6, 7}, {5, 6, 8, 9}, {7, 8, 9}, {10, 11}]
    excludes_required_category = any(j.isdisjoint(chordset) for j in minimum_requirements)
    contains_invalid_combination = any(i.issubset(chordset) for i in invalid_combinations)
    if excludes_required_category or contains_invalid_combination:
        return

    is_diminished = {f3, f5}.issubset(chordset) and {p3, p5, p7}.isdisjoint(chordset)
    if p5 not in chordset and not is_diminished:
        flattened5 = f5 in chordset and (s5 not in chordset or p4 in chordset)
        sharpened5 = s5 in chordset and p3 not in chordset and not flattened5
        if flattened5 or sharpened5:
            alts.append('b5') if flattened5 else alts.append('#5')
            chordset.remove(f5) if flattened5 else chordset.remove(s5)
            chordset.add(p5)

    chord_composition = next(i for i in chord_name if i.issubset(chordset))
    core_chord = chord_name[chord_composition]
    chordset -= chord_composition

    extensions = [(f2, 'b9'), (p2, 'add9'), (s2, '#9'), (p4, 'add11'), (s4, '#11'), (f6, 'b13'), (p6, 'add13')]
    alts.extend([ext for note, ext in extensions if note in chordset])
    if core_chord.endswith('7'):
        latest_ext = '7'
        seventh_substitute = None
        for ext in ['9', '11', '13']:
            if latest_ext == str(int(ext) - 2) and any(i + ext in alts for i in ['add', 'b', '#']):
                latest_ext = ext
                if 'add' + ext in alts:
                    seventh_substitute = ext
                    alts.remove('add' + ext)
        core_chord = core_chord.replace('7', seventh_substitute) if seventh_substitute else core_chord
    elif 'add13' in alts:
        alts.remove('add13')
        alts.insert(0, 'add6')

    chord_symbol = root + core_chord + ''.join(alts)
    chord_symbol += '/' + bass if bass != root else ''
    return chord_symbol
