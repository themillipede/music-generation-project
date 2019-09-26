"""
The "Note" Class
================

This represents a single note (or rest) in a melody, and always has at least a pitch and a duration. The pitch
is an integer value corresponding to the pitch of the note in MIDI format, unless the note object represents a
rest, in which case the pitch has value -1. Note that when converting pitch to vector format for modelling, we
use a vector that spans a 3-octave range (rather than the full range of possible pitches, which is very large),
because this more than covers the entire (limited) range of pitches in the pieces in the dataset.

The quaver, which is the most frequently-occurring note duration, takes a value of 30. Since the only thing that
matters regarding note durations is that the the durations of different notes are correct relative to each other
(since it is very straightforward to change them later when converting to sheet music or audio formats), they
have been specifically chosen such that all time denominations appearing in the dataset (which covers almost all
time denominations that one might realistically see in this type of music) can take integer values. This helps
to keep calculations straightforward and avoid rounding errors.

Upon initialisation, two more Note attributes are calculated from the pitch -- the name and the octave. The name
takes one of 12 string values, corresponding to the letter-based name of the note (e.g. 'C', 'A', 'F#', where any
non-natural note uses its sharp rather than flat version), and the octave takes an integer value corresponding to
the octave of the note in MIDI format. If the note is a rest, then these both take the value None.


The "Melody" Class
==================

This represents the sequence of notes that form the melody of a single piece. It has a single attribute, melody,
which is a list of Note objects in order, and which fully describes the melody of the piece. There are two main
methods via which a Melody might be created from raw data: (1) By combining a list of relative note durations for
the sequence of notes and a MIDI file containing the pitches of the notes in order, and (2) By inputting the MIDI
representation of the full melody, in addition to the total piece duration.

Note that the reason for including method (1) is that, in the absence of clean musical data in the desired format,
it became more efficient for me to create my own from the non-computer-readable lead sheets that I wanted to use
in my dataset. I found that, rather than creating the MIDI melodies directly by playing them into a digital piano
(which seemed good in theory, but required either impeccable precision with timing, or lots of post-processing to
tidy up all the timing issues, which turned out to be impossible to automate fully given the range of timing error),
a much more efficient approach was to separate out the gathering of note pitches and note durations, and combine the
two parts later. I did this by making both a MIDI file of the note pitches in the correct order (by playing them
into a digital piano, without worrying about the timing), and a list of relative note durations in order (where the
most frequently-occurring note duration, the quaver, had a relative duration of 1 -- the quickest to type!). The
result of combining these two components is the same as that of reading in a perfect MIDI representation of the lead
sheet (which is what method (2) does), and the process of creating the raw data takes surprisingly little time.
"""

import pretty_midi as pm

from definitions import QUAVER_DURATION


class Melody:
    def __init__(self, melody):
        self.melody = melody

    @classmethod
    def from_duration_list_and_pitch_midi(cls, relative_durations, pitch_midi):
        song = pm.PrettyMIDI(pitch_midi)
        inst = song.instruments[0].notes
        i = 0
        melody = []
        for num_quavers in relative_durations:
            new_note = Note(
                pitch=inst[i].pitch if num_quavers > 0 else -1,
                duration=round(abs(num_quavers) * QUAVER_DURATION)
            )
            i += 1 if num_quavers > 0 else 0
            melody.append(new_note)
        return cls(melody)

    @classmethod
    def from_full_midi_melody(cls, melody_midi, piece_duration):
        song = pm.PrettyMIDI(melody_midi)
        inst = song.instruments[0].notes
        melody = []
        time_elapsed = 0

        for note in inst:
            if note.start > time_elapsed:
                new_rest = Note(-1, note.start - time_elapsed)
                melody.append(new_rest)
            new_note = Note(note.pitch, note.end - note.start)
            melody.append(new_note)
            time_elapsed = note.end

        if piece_duration > time_elapsed:
            final_rest = Note(-1, piece_duration - time_elapsed)
            melody.append(final_rest)
        return cls(melody)


class Note:
    def __init__(self, pitch, duration):
        self.pitch = pitch
        self.duration = duration
        self._extract_note_name_and_octave()
        self.time_remaining = self.duration

    def _extract_note_name_and_octave(self):
        name_octave = pm.note_number_to_name(self.pitch) if self.pitch > -1 else None
        self.name = name_octave.rstrip('0123456789') if name_octave else None
        self.octave = int(name_octave.lstrip(self.name)) if name_octave else None
