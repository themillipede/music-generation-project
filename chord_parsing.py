import re

from definitions import chord_quality, triad_notes, seventh_notes, note_num_idx, MINIM_DURATION


def compile_chord_regex():
    num_minims_regex = '(\d*(?:\.\d+)?)'
    root_regex = '([A-G][b#]?)'
    core_regex = '([m\+oø]?(?:M?(?:7|9|11|13))?)?'
    alts_regex = '((?:[b#]\d+|(?:sus|add)\d+)*)'
    bass_regex = '(?:/([A-G][b#]?))?'
    chord_regex = (
        num_minims_regex +
        root_regex +
        core_regex +
        alts_regex +
        bass_regex
    )
    return re.compile(chord_regex)


def compile_alts_regex():
    alts_regex = '[b#]\d+|(?:add|sus)\d+'
    return re.compile(alts_regex)


compiled_chord_regex = compile_chord_regex()
compiled_alts_regex = compile_alts_regex()


class ChordProgression:
    def __init__(self, chord_string):
        """
        chord_string is a string containing a space-separated series of chord symbols and square parentheses.
        Sections within parentheses that are not nested within outer parentheses represent repeated sections,
        while any nested sections signify first and second time bars, in order of appearance (note that this
        will only work for sections with a maximum of one repeat). This function "unpacks" chord_string into
        a list of Chord objects in chronological order (i.e. the order in which they would be played).
        """
        chords = []
        l = chord_string.split(' ')
        start_idx = None
        end_idx = None
        open_parens = 0
        for i, item in enumerate(l):
            if item == '[':
                if open_parens == 0:
                    start_idx = i + 1
                elif l[i - 1] != ']':
                    end_idx = i
                open_parens += 1
            elif item == ']':
                if open_parens == 1 and l[i - 1] != ']':
                    chords.extend(l[start_idx:i])
                elif open_parens == 2 and l[i + 1] != ']':
                    chords.extend(l[start_idx:end_idx])
                open_parens -= 1
            else:
                chords.append(item)
        self.chords = [Chord.from_symbol(i) for i in chords]


class Chord:
    def __init__(self, root, bass, full_chordset, duration, core_chordset=None):
        self.root = root
        self.bass = bass
        self.core_chordset = core_chordset
        self.full_chordset = full_chordset
        self.duration = duration
        self.time_remaining = duration

    @classmethod
    def from_symbol(cls, chord_symbol):
        duration, root, core, alts, bass = Chord._constituents(chord_symbol)
        core_chordset = Chord._construct_core_chordset(core)
        full_chordset = Chord._construct_full_chordset(alts, core_chordset)
        return cls(root, bass, full_chordset, duration, core_chordset)

    @staticmethod
    def _constituents(chord_symbol):
        chord_match = compiled_chord_regex.match(chord_symbol)
        num_minims = float(chord_match.group(1) or 1)
        duration = round(num_minims * MINIM_DURATION)
        root = chord_match.group(2)
        core = chord_match.group(3)
        alts = chord_match.group(4)
        bass = chord_match.group(5) or root

        ext_note = core.strip('mM+oø7')
        if ext_note and int(ext_note) in (9, 11, 13):
            exts = range(9, int(ext_note) + 1, 2)
            core = core.replace(ext_note, '7')
            alts += ''.join('add%s' % i for i in exts)
        return duration, root, core, alts, bass

    @staticmethod
    def _make_alteration(full_chordset, alt):
        """
        alt is a string comprising the concatenation of the chord alteration
        ('b', '#', 'add', or 'sus') and the position of the affected note.
        """
        alt_type = alt.rstrip('0123456789')
        alt_note = int(alt.lstrip(alt_type))
        alt_idx = note_num_idx[alt_note]
        if alt_type in ('b', '#'):
            full_chordset.discard(alt_idx)
            if alt_type == 'b':
                full_chordset.add(alt_idx - 1)
            elif alt_type == '#':
                full_chordset.add(alt_idx + 1)
        elif alt_type in ('add', 'sus'):
            full_chordset.add(alt_idx)
            if alt_type == 'sus':
                full_chordset -= {3, 4}

    @staticmethod
    def _construct_core_chordset(core):
        triad, seventh = chord_quality[core]
        triad_indices = triad_notes[triad]
        seventh_index = seventh_notes[seventh] if seventh else 0
        core_chordset = (triad_indices | {seventh_index})
        return core_chordset

    @staticmethod
    def _construct_full_chordset(alts, core_chordset):
        alts_list = re.findall(compiled_alts_regex, alts)
        full_chordset = core_chordset.copy()
        for alt in alts_list:
            Chord._make_alteration(full_chordset, alt)
        return full_chordset
