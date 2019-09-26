from definitions import QUAVER_DURATION


class BarSequence:
    def __init__(self, relative_durations):
        self.bars = [
            Bar(number=n, duration=num_quavers * QUAVER_DURATION)
            for n, num_quavers in enumerate(relative_durations)
        ]


class Bar:
    def __init__(self, number, duration):
        self.number = number
        self.duration = duration
        self.time_remaining = self.duration
