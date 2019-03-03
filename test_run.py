import json
import numpy as np

from definitions import note_name_idx
from note_parsing import Melody
from chord_parsing import ChordProgression
from bar_parsing import BarSequence
from timesteps import Piece

with open('test_data.json') as f:
    piece_data = json.load(f)

piece_list = []
for title, details in piece_data.items():
    print(title)
    if not details["chords"]:
        continue
    melody = Melody(details['notes'], title + '.MID')
    chords = ChordProgression(details['chords'])
    bars = BarSequence(eval(details['bars']))
    piece = Piece(title, details['composer'], details['pickup'], melody.melody, chords.chords, bars.bars)
    piece_list.append(piece)


def timestep_vectors(piece):
    note_pitch = np.eye(38)[[36 if ts.same_note else ts.note_pitch - 48 if ts.note_pitch else 37 for ts in piece]]
    root = np.eye(12)[[note_name_idx[ts.root] for ts in piece]]
    bass = np.eye(12)[[note_name_idx[ts.root] for ts in piece]]
    chord = np.eye(12)[[ts.full_chordset for ts in piece]]
    duration = np.eye(24)[[ts.duration / 10 - 1 for ts in piece]]


print(timestep_vectors(piece_list[1].timesteps))
