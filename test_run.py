import json
import numpy as np

from definitions import note_name_idx
from note_parsing import Melody
from chord_parsing import ChordProgression
from bar_parsing import BarSequence
from timesteps import Piece


def timestep_vectors(piece):
    note_pitch = np.eye(38, dtype=int)[
        [36 if ts.same_note else ts.note_pitch - 48 if ts.note_pitch > 0 else 37 for ts in piece]
    ]
    root = np.eye(13, dtype=int)[[note_name_idx[ts.root] if ts.root else 12 for ts in piece]]
    bass = np.eye(13, dtype=int)[[note_name_idx[ts.bass] if ts.bass else 12 for ts in piece]]
    chord = np.array([[i in ts.full_chordset for i in range(12)] for ts in piece], dtype=int)
    duration = np.eye(24, dtype=int)[[int(ts.duration / 10 - 1) for ts in piece]]
    return np.concatenate([note_pitch, root, bass, chord, duration], axis=1)


with open('test_data.json') as f:
    piece_data = json.load(f)

for title, details in piece_data.items():
    print(title)
    if not details["chords"]:
        continue
    melody = Melody(details['notes'], 'PitchMIDI/' + title + '_pitches' + '.MID')
    chords = ChordProgression(details['chords'])
    bars = BarSequence(eval(details['bars']))
    piece = Piece(title, details['composer'], details['pickup'], melody.melody, chords.chords, bars.bars)
    vectors = timestep_vectors(piece.timesteps)
    print(vectors)
