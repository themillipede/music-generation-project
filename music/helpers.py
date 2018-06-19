from numpy import random

def get_note_position_relative_to_key_note(key_label, note_label, note_positions):
    """
    :param key_label: the key of the piece.
    :param note_label: the note name, without specification of the octave.
    :param note_positions: dict mapping each note to its position relative to the tonic of the key scale.
    :return: the position of the note relative to the tonic of the key scale (where tonic is position 0).
    """
    if note_label == 'rr':
        return 12
    return (note_positions[note_label] - note_positions[key_label]) % 12


def get_chord_under_note(note_id, chord_list, note_list):q
    """
    :param note_id: the ID of the note
    :param chord_list:
    :param note_list:
    :return:
    """
    chord_dict = {}
    current_chord = 0
    current_note = 0
    note_total = 0
    chord_total = 0
    while note_total < sum(note_list):
        while note_total <= chord_total:
            chord_dict[current_note] = current_chord
            note_total += note_list[current_note]
        chord_total += chord_list[current_chord]
    return chord_dict


def get_next_note_label(note_probs):
    """
    :param note_probs: dict mapping each note to its probability of following the previous note.
    :return: the next note in the sequence
    """
    note_list = note_probs.keys()
    prob_list = note_probs.values()
    draw = random.choice(note_list, 1, p=prob_list)
    return draw[0]


def get_next_note_duration(duration_probs, remaining_time):
    """
    :param duration_probs: dict mapping each note duration to its probability of following the previous one.
    :param remaining_time: the fraction of a bar available to fill (notes must not straddle bars).
    :return: the next note duration in the sequence.
    """
    duration_list = duration_probs.keys()
    prob_list = duration_probs.values()
    draw = random.choice(duration_list, 1, p=prob_list)
    return draw[0]

def get_parent_chord(chord):
    parent_chords = {
        'maj7': 0,
        'dom7': 0,
        'min7': 0,
        'hdim': 0,
        'dim7': 0
    }
    if chord_suffix
    return parent_chord

# Data is stored in three tables: "song", "note", and "chord", with the following structures:
# song: | song_id | key | time | title |
# note: | note_id | song_id | position_number | note_label | note_length |
# chord: | chord_id | song_id | position_number | chord_label | chord_length |

{
  "fall": {
    "base_note": "fgacbcdcbarfgacbcdcbarabccbagbfgard",
    "accidental": "ssnsnsnnfnrssnsnsnnfnnnnsnnnfssnrn",
    "octave": [],
    "rhythm": []
  }
}