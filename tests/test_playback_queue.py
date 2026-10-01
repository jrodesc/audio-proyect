import pytest

from src.core.playback_queue import PlaybackQueue


class FixedRandom:
    def __init__(self, *values):
        self.values = iter(values)

    def randrange(self, stop):
        value = next(self.values)
        assert 0 <= value < stop
        return value


def test_empty_queue_has_no_current_item_and_stays_empty():
    queue = PlaybackQueue()

    assert queue.current is None
    assert queue.advance() is None
    assert queue.position == -1


def test_ordered_queue_advances_and_stops_at_end():
    tracks = ["a", "b"]
    queue = PlaybackQueue()

    assert queue.load(tracks) == "a"
    assert queue.advance() == "b"
    assert queue.advance() is None
    assert queue.advance() is None
    assert queue.position == len(tracks)


def test_queue_can_start_at_selected_track():
    queue = PlaybackQueue()

    assert queue.load(["a", "b", "c"], start=1) == "b"
    assert queue.advance() == "c"


def test_skip_moves_to_next_track_and_finishes_at_end():
    queue = PlaybackQueue()

    assert queue.load(["current", "next"]) == "current"
    assert queue.skip() == "next"
    assert queue.skip() is None
    assert queue.current is None


def test_invalid_start_is_rejected():
    queue = PlaybackQueue()

    with pytest.raises(ValueError):
        queue.load(["a"], start=1)


def test_shuffle_visits_each_track_once():
    queue = PlaybackQueue(FixedRandom(2, 1, 0))

    visited = [queue.load(["a", "b", "c"], shuffle=True)]
    visited.extend(queue.advance() for _ in range(3))

    assert visited == ["c", "a", "b", None]
    assert queue.mode == "random"


def test_clear_resets_queue_state():
    queue = PlaybackQueue()
    queue.load(["a", "b"], shuffle=True)

    queue.clear()

    assert queue.items == []
    assert queue.position == -1
    assert queue.mode == "ordered"
    assert queue.current is None
