import pretty_midi as pm

from collections import defaultdict
from numpy import random

def get_note_transition_frequencies(file_list):
    transition_freqencies = defaultdict(lambda: defaultdict(int))
    for melody_input in file_list:
        melody = pm.PrettyMIDI(melody_input).instruments[0].notes
        for i in range(len(melody) - 1):
            start_note = melody[i].pitch
            next_note = melody[i + 1].pitch
            transition_freqencies[start_note][next_note] += 1
    return transition_freqencies

def get_note_transition_probabilities(transition_frequencies):
    transition_probs = {}
    for start_note, next_notes in transition_frequencies.items():
        total = sum(next_notes.values())
        probs = {note: count * 1.0 / total for note, count in next_notes.items()}
        transition_probs[start_note] = probs
    return transition_probs

def get_next_note(transition_probs):
    note_list = list(transition_probs.keys())
    prob_list = list(transition_probs.values())
    draw = random.choice(note_list, 1, p=prob_list)
    return draw[0]