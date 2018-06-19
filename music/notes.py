class PitchObject:

    def __init__(self, name, duration):
        self.name = name
        self.duration = duration
        self.bar_number = None
        self.beat_of_bar = None
        self.beat_of_piece = None
        self.piece = None
        self.next = None

    def get_bar_number(self, prev, piece):
        self.bar_number = prev.bar_number + (prev.beat_of_bar + prev.duration) // piece.beats_per_bar

    def get_beat_of_bar(self, prev, piece):
        self.beat_of_bar = (prev.beat_of_bar + prev.duration) % piece.beats_per_bar


class Note(PitchObject):

    def __init__(self, piece_position=None, bar_position=None):
        self.piece_position = piece_position
        self.bar_position = bar_position

    def get_beat_of_note(self, prev_note, piece):
        self.beat_of_bar = (prev_note.beat_of_bar + prev_note.duration) % piece.beats_per_bar

    def get_beat_of_piece(self, prev):
        pass


class Chord(PitchObject):

    def __init__(self):
        self.chord_family = None

    def get_chord_family(self, name):
        pass


class Bar:

    def __init__(self, number=None):
        self.number = number
        self.beats_in_bar = 8


class TimeStep:

    """
    Every unique note/chord/bar combination gets its own timestep.
    """

    def __init__(self, note=None, chord=None, bar=None):
        self.note = note
        self.chord = chord
        self.bar = bar
        self.duration = None
        self.is_front_tied = None
        self.is_back_tied = None
        self.beat_of_bar = None
        self.is_bar_line = False

class Piece:

    def __init__(self, name=None, starting_beat=0):
        self.name = name
        self.beats_per_bar = 8
        self.starting_beat = starting_beat
        self.start_note = None
        self.start_chord = None

    def get_upbeat_duration(self):
        pass

    def get_timestep_sequence(self):
        pass

def find_next_timestep(last_timestep):
    pass


pieces = {
    "fall": [Note()]
}

# Store three time pointers, for note, chord, and bar.
# Increment the time every time one of them changes, and create new timestep.

def create_timesteps(piece):

    timesteps = []

    start_note = piece.start_note
    start_chord = piece.start_chord
    next_bar = 0

    if start_note.bar_number < start_chord.bar_number:
        curr_chord = None
        next_chord = start_chord
        timestep = TimeStep(curr_note, None)
        curr_note = curr_note.next

    while curr_note.next != None:
        timestep = find_next_timestep(curr_note, curr_chord, curr_bar, piece)
        timesteps.append(timestep)

        if first_note.bar_number < first_chord.bar_number:
            timestep = TimeStep(first_note)
        else:
            timestep = TimeStep(first_note, first_chord)

# If beat % beats_per_bar == 0, then is_bar_line = True


def find_next_timestep(next_note, next_chord, next_bar, piece):

    if next_bar.time < next_note.time and next_bar.time < next_chord.time:
        timestep = TimeStep(next_note.prev, next_chord.prev, is_bar_line=True, is_back_tied=True)
        next_bar = next_bar.next

    else:
        if next_note.time < next_chord.time:
            timestep = TimeStep(next_note, next_chord.prev)
            timestep_beat = next_note.beat_of_bar
            next_note = next_note.next

        elif next_chord.time < next_note.time:
            timestep = TimeStep(next_note.prev, next_chord, is_back_tied=True)
            timestep_beat = next_chord.beat_of_bar
            next_chord = next_chord.next

        else:
            timestep = TimeStep(next_note, next_chord)
            timestep_beat = next_note.beat_of_bar
            next_note = next_note.next
            next_chord = next_chord.next

        if timestep_beat % next_bar.prev.beats_in_bar == 0:
            timestep.is_bar_line = True
            curr_bar = next_bar

    return timestep


def find_next_timestep(curr_note, curr_chord, curr_bar, piece):

    next_bar = curr_bar.next
    next_note = curr_note.next
    next_chord = curr_chord.next

    if next_bar.time < next_note.time and next_bar.time < next_chord.time:
        timestep = TimeStep(curr_note, curr_chord, is_bar_line=True, is_back_tied=True)
        curr_bar = next_bar

    else:
        if next_note.time < next_chord.time:
            timestep = TimeStep(next_note, curr_chord)
            timestep_beat = next_note.beat_of_bar
            curr_note = next_note

        elif next_chord.time < next_note.time:
            timestep = TimeStep(curr_note, next_chord, is_back_tied=True)
            timestep_beat = next_chord.beat_of_bar
            curr_chord = next_chord

        else:
            timestep = TimeStep(next_note, next_chord)
            timestep_beat = next_note.beat_of_bar
            curr_note = next_note
            curr_chord = next_chord

        if timestep_beat % curr_bar.beats_in_bar == 0:
            timestep.is_bar_line = True
            curr_bar = next_bar

    return timestep

# Do we need to make the previous timestep "is_front_tied = True" if the current timestep has "is_front_tied = False"?
# Seems redundant, given that you can't have one without the other, but might it influence the music generation?