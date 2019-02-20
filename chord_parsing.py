import re

from .definitions import chord_quality, triad_notes, seventh_notes, note_num_idx, MINIM_DURATION


def compile_chord_regex():
    num_minims_regex = '(\d*(?:\.\d+)?)'
    root_regex = '([A-G][b#]?)'
    type_regex = '([m\+oø]?(?:M?(?:7|9|11|13))?)?'
    alts_regex = '((?:[b#]\d+|(?:sus|add)\d+)*)'
    bass_regex = '(?:/([A-G][b#]?))?'
    chord_regex = (
        num_minims_regex +
        root_regex +
        type_regex +
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
        :param chord_string: String containing a space-separated series of chord symbols and
            square parentheses. Sections within parentheses that are not nested within outer
            parentheses represent repeated sections, while any nested sections signify first
            and second time bars, in order of appearance (this will not work for > 1 repeat).
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
        self.chords = [Chord(i) for i in chords]


class Chord:
    def __init__(self, chord_symbol):
        self._extract_chord_components(chord_symbol)
        self._construct_type_chordset()
        self._construct_full_chordset()
        self.time_remaining = self.duration

    def _extract_chord_components(self, chord_symbol):
        chord_match = compiled_chord_regex.match(chord_symbol)
        num_minims = float(chord_match.group(1) or 1)
        self.duration = round(num_minims * MINIM_DURATION)
        self.root = chord_match.group(2)
        self.type = chord_match.group(3)
        self.alts = chord_match.group(4)
        self.bass = chord_match.group(5) or self.root

        ext_note = self.type.strip('mM+oø7')
        if ext_note and int(ext_note) in (9, 11, 13):
            exts = range(9, int(ext_note) + 1, 2)
            self.type = self.type.replace(ext_note, '7')
            self.alts += ''.join('add%s' % i for i in exts)

    def _make_chord_alteration(self, alt):
        """
        :param alt: String comprising the concatenation of the chord alteration
            ('b', '#', 'add', or 'sus'), and the position of the affected note.
        """
        alt_type = alt.rstrip('0123456789')
        alt_note = alt.lstrip(alt_type)
        alt_idx = note_num_idx[alt_note]
        if alt_type in ('b', '#'):
            self.full_chordset.discard(alt_idx)
            if alt_type == 'b':
                self.full_chordset.add(alt_idx - 1)
            elif alt_type == '#':
                self.full_chordset.add(alt_idx + 1)
        elif alt_type in ('add', 'sus'):
            self.full_chordset.add(alt_idx)
            if alt_type == 'sus':
                self.full_chordset -= {3, 4}

    def _construct_type_chordset(self):
        triad_type, seventh_type = chord_quality[self.type]
        triad_indices = triad_notes[triad_type]
        seventh_index = seventh_notes[seventh_type]
        self.type_chordset = (triad_indices | {seventh_index})

    def _construct_full_chordset(self):
        alts_list = re.findall(compiled_alts_regex, self.alts)
        self.full_chordset = self.type_chordset
        for alt in alts_list:
            self._make_chord_alteration(alt)
