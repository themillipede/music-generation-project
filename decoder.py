"""
The functions here decode the model output into machine-readable music, that can be easily transformed into
human-readable sheet music.
"""

import numpy as np
from note_parsing import Note
from chord_parsing import Chord
from bar_parsing import Bar
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
    """
    This reconstructs, from a chord, the chord symbol that will appear on the written sheet music representation
    of the music.

    The binary vector output from the model has an entry for each of the 12 scale positions, with the positions
    set to 1 indicating those that are part of the chord. This vector is used to create a "chordset" containing
    just the note numbers present in the chord. From this set, this function determines the most probable chord
    symbol. Note that some chords can be written in multiple ways -- especially those containing alterations to
    a simpler chord -- and so the decoding may not always label the chords in the way that makes the most sense
    in the context of the whole sequence. However, the heuristics used should do a good job in all but the most
    unusual of cases.
    """
    root = chord.root
    bass = chord.bass
    chordset = chord.full_chordset
    alts = []

    # The 3rd is a defining note of any chord, and every chord includes either a major or minor 3rd, unless the
    # 3rd is "suspended". There are are two types of suspended chords -- "sus4" (where the 3rd is replaced with
    # a perfect 4th), or the less common "sus2" (where the 3rd is replaced with a major 2nd). If there is a 3rd
    # present, we don't need to consider the possibility that the chord is suspended. Otherwise, in order to be
    # valid the chord must have either a perfect 4th or a major 2nd to replace the 3rd, in which case it can be
    # considered a suspended chord. Whether it's "sus4" or "sus2" is determined by what other notes are present
    # in the chord. I.e. if the chord has both a minor and a major 2nd, then we consider it to be sus2, because
    # these two notes could not otherwise be present together in a valid chord (as specified in this work). But
    # if one or zero of these 2nd notes are in the chord, and a perfect 4th is present, then the chord is sus4.
    # To make the remaining chord identification steps easier, once a chord is determined as having a suspended
    # 3rd and this has been recorded in the list of alterations, the note that replaced the 3rd is removed from
    # the chordset, and a major 3rd is added. In this way, we can work backwards to determine the chord origin.
    # NOTE: It could still turn out that the chord is invalid as we proceed through later chord-decoding steps,
    # even if it was valid with respect to the suspended chord options.

    if {f3, p3}.isdisjoint(chordset) and {p2, p4}.intersection(chordset):
        sus_type = 'sus4' if p4 in chordset and not {f2, p2}.issubset(chordset) else 'sus2'
        alts.append(sus_type)
        chordset.remove(p4) if sus_type == 'sus4' else chordset.remove(p2)
        chordset.add(p3)

    # For a chord to be considered valid in this work it must contain at a minimum the root, a (major or minor)
    # 3rd, and a (diminished, perfect or augmented) 5th. Also, it must not contain more than one version of the
    # same scale degree. E.g. There cannot be both a perfect 5th and a diminished 5th in the same chord (though
    # if the diminished 5th can be considered to be an augmented 4th without violating any validity constraints
    # in other chord positions, then the chord can be valid). These constraints are encoded such that the chord
    # must contain at least one note from each set in minimum_requirements, and cannot contain all the notes in
    # any set in invalid_combinations. We also assume that an augmented 6th can only be denoted as a minor 7th.

    minimum_requirements = [{p1}, {f3, p3}, {f5, p5, s5}]
    invalid_combinations = [{1, 2}, {2, 3, 4}, {1, 3, 4}, {5, 6, 7}, {5, 6, 8, 9}, {7, 8, 9}, {10, 11}]
    excludes_required_category = any(j.isdisjoint(chordset) for j in minimum_requirements)
    contains_invalid_combination = any(i.issubset(chordset) for i in invalid_combinations)
    if excludes_required_category or contains_invalid_combination:
        return

    # The next step to deducing the core chord type is to identify alterations to the 5th. First we ensure that
    # we are not dealing with a chord in the diminished family (i.e. o, o7, or ø7), as those need to be treated
    # as diminished chords rather than chords with alterations to the 5th. Then we check for a flattened 5th by
    # seeing if the chord matches the conditions under which there can be no doubt that a note at position 6 is
    # a flattened 5th (rather than, say, a #11). If there is no flattened 5th then we check for a sharpened 5th
    # in a similar way. If we discover any alteration to the 5th, we record it in the alteration list, and then
    # replace the altered 5th with the unaltered 5th in the chordset. NOTE: a flattened 5th takes priority over
    # a sharpened 5th if either would work, since there is a core chord type that contains a sharpened 5th, and
    # in determining the chord symbol we want to prioritise simplicity. This also means that if we don't have a
    # flattened 5th, and we do have a sharpened 5th, we will only consider it a #5 chord if the chord would not
    # ultimately be labelled with the core chord type containing a sharpened 5th (given the rest of the notes).

    is_diminished = {f3, f5}.issubset(chordset) and {p3, p5, p7}.isdisjoint(chordset)
    if p5 not in chordset and not is_diminished:
        flattened5 = f5 in chordset and (s5 not in chordset or p4 in chordset)
        sharpened5 = s5 in chordset and p3 not in chordset and not flattened5
        if flattened5 or sharpened5:
            alts.append('b5') if flattened5 else alts.append('#5')
            chordset.remove(f5) if flattened5 else chordset.remove(s5)
            chordset.add(p5)

    # Now that all the alterations have been dealt with, chordset should contain only the core chord notes plus
    # any additions or extensions. This means that the core chord type can be deduced by comparing the notes in
    # chordvec with those in the 12 pre-defined chord types. The OrderedDict chord_name containing the note set
    # defined for each chord type, is ordered such that for a given combination of notes in chordset, the match
    # that gives the simplest and most logical chord name will be reached first as we iterate through.

    chord_composition = next(i for i in chord_name if i.issubset(chordset))
    core_chord = chord_name[chord_composition]
    chordset -= chord_composition

    # Now there should only be extension notes remaining in chordset. Since there is no ambiguity at this point
    # around the scale degrees from which the remaining notes are derived, we first add them all to the list of
    # alterations in their raw form, and then we go about substituting these labels with changes to the name of
    # the core chord where appropriate (e.g. a M7 chord with the 'add9' extension is more commonly written M9).

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
