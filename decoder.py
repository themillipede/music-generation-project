import numpy as np
from definitions import chord_name, p1, f2, p2, s2, f3, p3, p4, s4, f5, p5, s5, f6, p6, f7, p7


def chord_decoder(chordvec):
    pass


def note_decoder(notevec):
    onehot = np.argmax(notevec)


def root_decoder(rootvec):
    onehot = np.argmax(rootvec)
    root = note_idx_name[onehot] if onehot < 12 else None
    return root


def bass_decoder(bassvec):
    onehot = np.argmax(bassvec)
    bass = note_idx_name[onehot] if onehot < 12 else None
    return bass


# If there is no minor or major 3rd, and there is a 4th or a 2nd, it is a sus chord.
# Note that although theoretically there could be, say, a sus4#9 chord, whose sharp
# ninth is enharmonically equivalent to a minor third, this chord would be written
# more correctly as m(add11), and so there's no need to check whether the note in
# that position is actually a #9 or a minor 3rd.

# if there is a b5 and no 5 and no #5, OR there is a b5 and no 5 and an 11
# (the 11 indicates that the b5 is a b5 rather than a #11, because there can't be an 11 AND a #11)
# unless minor 3rd and no major seventh


def decode_chord(chordset):
    alts = []

    if {f3, p3}.isdisjoint(chordset) and (p4 in chordset or p2 in chordset):
        sus4_valid = not {f2, p2}.issubset(chordset)
        alts.append('sus4') if p4 in chordset and sus4_valid else alts.append('sus2')
        chordset.remove(p4) if p4 in chordset and sus4_valid else chordset.remove(p2)
        chordset.add(p3)

    invalid = [{1, 2}, {2, 3, 4}, {1, 3, 4}, {5, 6, 7}, {5, 6, 8, 9}, {7, 8, 9}, {10, 11}]
    minimum = [{p1}, {f3, p3}, {f5, p5, s5}]
    contains_invalid_combination = any(i.issubset(chordset) for i in invalid)
    excludes_required_category = any(j.isdisjoint(chordset) for j in minimum)
    invalid = contains_invalid_combination or excludes_required_category
    if invalid:
        return "invalid"

    o_or_o7_or_ø7_chord = {f3, f5}.issubset(chordset) and {p3, p5, p7}.isdisjoint(chordset)
    if not o_or_o7_or_ø7_chord:
        if f5 in chordset and p5 not in chordset and (s5 not in chordset or p4 in chordset):
            alts.append('b5')
            chordset.remove(f5)
            chordset.add(p5)
        elif {s5, f3}.issubset(chordset) and {p3, p5}.isdisjoint(chordset):
            alts.append('#5')
            chordset.remove(s5)
            chordset.add(p5)

    chord = next(i for i in chord_name if i.issubset(chordset))
    core_chord = chord_name[chord]
    chordset -= chord

    extensions = ['b9', 'add9', '#9', 'add11', '#11', 'b13', 'add13']
    for i, note in enumerate([f2, p2, s2, p4, s4, f6, p6]):
        if note in chordset:
            alts.append(extensions[i])
    if len(core_chord) > 0 and core_chord[-1] == '7':
        seventh_exts = ['13', '11', '9']
        for i, ext in enumerate(seventh_exts):
            if 'add' + ext in alts:
                valid = True
                for r in seventh_exts[i + 1:]:
                    if not ('add' + r in alts or 'b' + r in alts or '#' + r in alts):
                        valid = False
                if valid:
                    core_chord = core_chord.replace('7', ext)
                    for j in seventh_exts[i:]:
                        if 'add' + j in alts:
                            alts.remove('add' + j)
                    break
    elif len(core_chord) == 0 or (len(core_chord) > 0 and core_chord[-1] != '7'):
        if 'add13' in alts:
            alts.remove('add13')
            alts.append('add6')

    return core_chord + ''.join(alts)



#print(decode_chord(set([p1, f2, f3, p4, f5, f6])))
#print(decode_chord(set([p1, p3, p4, s4, s5, f7])))
#print(decode_chord(set([p1, s2, p3, p4, f5, f6, f7])))
#print(decode_chord(set([p1, f2, p2, p4, p5, f6, f7])))
#print(decode_chord(set([p1, f3, p5, f6, f7])))
print(decode_chord(set([p1, s2, p3, s5])))


def timestep_vectors(piece):
    note_pitch = np.eye(38, dtype=int)[
        [36 if ts.same_note else ts.note_pitch - 48 if ts.note_pitch > 0 else 37 for ts in piece]
    ]
    root = np.eye(13, dtype=int)[[note_name_idx[ts.root] if ts.root else 12 for ts in piece]]
    bass = np.eye(13, dtype=int)[[note_name_idx[ts.bass] if ts.bass else 12 for ts in piece]]
    chord = np.array([[i in ts.full_chordset for i in range(12)] for ts in piece], dtype=int)
    duration = np.eye(24, dtype=int)[[int(ts.duration / 10 - 1) for ts in piece]]
    return np.concatenate([note_pitch, root, bass, chord, duration], axis=1)
