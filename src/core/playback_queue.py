"""Pure playback queue ordering and position management."""
import random


class PlaybackQueue:
    def __init__(self, randomizer=None):
        self.randomizer = randomizer or random.SystemRandom()
        self.items = []
        self.position = -1
        self.mode = "ordered"

    def load(self, items, shuffle=False, start=0):
        self.items = list(items)
        self.position = start if self.items else -1
        self.mode = "random" if shuffle else "ordered"
        if shuffle and len(self.items) > 1:
            chosen = self.randomizer.randrange(len(self.items))
            self.items[0], self.items[chosen] = self.items[chosen], self.items[0]
        return self.current

    @property
    def current(self):
        return self.items[self.position] if 0 <= self.position < len(self.items) else None

    def advance(self):
        next_position = self.position + 1
        if self.mode == "random" and next_position < len(self.items):
            other = next_position + self.randomizer.randrange(len(self.items) - next_position)
            self.items[next_position], self.items[other] = self.items[other], self.items[next_position]
        self.position = next_position
        return self.current

    def clear(self):
        self.items = []
        self.position = -1
        self.mode = "ordered"
