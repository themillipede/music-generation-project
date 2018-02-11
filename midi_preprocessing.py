import pretty_midi as pm
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("midi_input")
parser.add_argument("midi_output")
args = parser.parse_args()

song = pm.PrettyMIDI(args.midi_input)
inst = song.instruments[0].notes
note_list = sorted([[note.start, note.end, note.pitch, note.velocity] for note in inst])

def normalise_note_events(notes):
    start_time = notes[0][0]
    for note in notes:
        note[0] -= start_time
        note[1] -= start_time

def extend_short_notes(notes):
    for i, note in enumerate(notes[:-1]):
        gap = note_list[i + 1][0] - note[1]
        if 0 < gap < 0.15:
            note[1] = note_list[i + 1][0]

def round_to_nearest_x(number, x):
    low_x = x * (number // x)
    return low_x if number % x < x/2 else low_x + x

def round_note_durations(notes):
    for note in notes:
        note[0] = round(round_to_nearest_x(note[0], 0.3), 1)
        note[1] = round(round_to_nearest_x(note[1], 0.3), 1)

def remove_note_overlap(notes):
    for i, note in enumerate(notes[:-1]):
        if note[1] > notes[i + 1][0]:
            note[1] = notes[i + 1][0]

normalise_note_events(note_list)
extend_short_notes(note_list)
round_note_durations(note_list)
remove_note_overlap(note_list)

melody = pm.PrettyMIDI()
kboard = pm.Instrument(program=0)
for i, note in enumerate(note_list):
    diff = round(note_list[i][1] - note_list[i][0], 1)
    if diff <= 0:
        continue
    new_note = pm.Note(velocity=100, pitch=note[2], start=round(note[0], 1), end=round(note[1], 1))
    kboard.notes.append(new_note)
melody.instruments.append(kboard)

melody.write(args.midi_output)