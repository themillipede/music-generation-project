"""
The "Piece" Class
=================

This has attributes pertaining to the piece as a whole, and on initialisation, uses the input melody, chord and bar
sequences to create an ordered list of timesteps, which describes the whole piece. Each timestep contains all of the
attributes required for modelling, plus a few more (which though not required or used at this stage, are included as
they could be useful when trying different modelling approaches).


The "Timestep" Class
====================

A timestep here can be thought of as a cross-section of the piece at a particular point in time. But whereas a more
typical approach would be to divide each bar into a fixed number of smaller sections, each of the same duration, and
treat these as the timesteps (which results in quantisation of piece elements), here we create a new timestep only
when there is a change to either the note, the chord, or the bar. This means that timesteps can have different
durations, but that the duration is capped at the length of a full bar. Notes that are tied from a previous bar are
flagged within the relevant timestep, so that no information is lost. The fact that the timesteps can take different
durations means that any rhythm can be accommodated precisely, and the capping at the length of a bar means that it
is feasible to represent all durations of notes that may realistically arise within a bar in a softmax for modelling.
"""

from note_parsing import Note
from chord_parsing import Chord
from bar_parsing import Bar

from definitions import QUAVER_DURATION


class Piece:
    def __init__(self, title, composer, pickup_duration, melody, chords, bars):
        self.title = title
        self.composer = composer
        self.pickup_duration = pickup_duration * QUAVER_DURATION
        self.timesteps = []
        this_note = Note(-1, 0)
        this_chord = Chord(None, None, set(), 0)
        this_bar = Bar(-1, 0)
        n = -1
        c = -1
        b = -1

        while n < len(melody) or c < len(chords) or b < len(bars):
            timestep_duration = min(
                this_note.time_remaining,
                this_chord.time_remaining,
                this_bar.time_remaining
            )
            if timestep_duration > 0:  # This will never be true on the first loop.
                this_timestep = Timestep(
                    note_pitch=this_note.pitch,
                    root=this_chord.root,
                    bass=this_chord.bass,
                    full_chordset=this_chord.full_chordset,
                    duration=timestep_duration,
                    same_note=same_note,
                    is_barline=is_barline,
                    bar_number=this_bar.number,
                    note_name=this_note.name,
                    note_octave=this_note.octave,
                    core_chordset=this_chord.core_chordset
                )
                self.timesteps.append(this_timestep)
            elif self.pickup_duration > 0:
                this_chord.time_remaining = self.pickup_duration
                this_bar.time_remaining = self.pickup_duration

            this_note.time_remaining -= timestep_duration
            if this_note.time_remaining == 0:
                n += 1
                if n < len(melody):
                    this_note = melody[n]
                same_note = False
            else:
                same_note = True

            this_chord.time_remaining -= timestep_duration
            if this_chord.time_remaining == 0:
                c += 1
                if c < len(chords):
                    this_chord = chords[c]

            this_bar.time_remaining -= timestep_duration
            if this_bar.time_remaining == 0:
                b += 1
                if b < len(bars):
                    this_bar = bars[b]
                    is_barline = True
            else:
                is_barline = False


class Timestep:
    """
    Every unique note/chord/bar combination has its own timestep. There are four (currently) redundant timestep
    attributes (note_name, note_octave, core_chordset, and bar_number), which are included because they may end
    up being used for alternative approaches to the modelling task. E.g. the chord representation core_chordset
    will map to multiple full_chordsets, and so any full_chordset in the dataset is likely to show up much less
    than its corresponding core_chordset. If there are not enough data points for effective training when using
    full_chordset, it may turn out that core_chordset (which still captures the essence of the chord) proves to
    be more fruitful.
    """
    def __init__(self, note_pitch, root, bass, full_chordset, duration,
                 same_note, is_barline=None, bar_number=None,
                 note_name=None, note_octave=None, core_chordset=None):

        self.note_pitch = note_pitch
        self.root = root
        self.bass = bass
        self.full_chordset = full_chordset
        self.duration = duration
        self.same_note = same_note
        self.is_barline = is_barline
        self.bar_number = bar_number
        self.note_name = note_name
        self.note_octave = note_octave
        self.core_chordset = core_chordset
