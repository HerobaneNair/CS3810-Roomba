"""
CS3810 Mini-Project 1 - Priority Queue Helper
==============================================

This file is COMPLETE. You may use it as-is; you do not need to modify it.

A binary-heap priority queue that supports *decrease-key*: pushing an item
that is already present replaces its old priority instead of creating a
duplicate entry. That is what makes node reopening in A* clean.

Two details worth understanding, because they affect your results:

1.  Lazy deletion. Removing an item does not pull it out of the heap; it
    marks the heap entry as dead and `pop()` skips dead entries. This means
    `len(self.heap)` is NOT the frontier size. Use `len(queue)`, which
    counts live entries only, when you report max_frontier_size.

2.  The insertion counter breaks ties deterministically and in FIFO order
    among equal priorities. Without it, heapq would try to compare the
    items themselves and raise TypeError on ties. Keeping it means your
    node counts are reproducible.

Items must be hashable. Your states are, if you built them as
((row, col), frozenset(...)) per the handout.

Usage
-----
    pq = PriorityQueue()
    pq.push(state, f_value)
    if state in pq:            # membership test
        pq.push(state, better)  # replaces the old priority
    best = pq.pop()            # lowest priority value first
    size = len(pq)             # live entries
"""

import heapq


class PriorityQueue:
    """A priority queue with decrease-key functionality."""

    def __init__(self):
        self.heap = []
        self.entry_finder = {}
        self.counter = 0

    def push(self, item, priority):
        """Insert `item`, or update its priority if already present."""
        if item in self.entry_finder:
            self.remove(item)
        entry = [priority, self.counter, item]
        self.counter += 1
        self.entry_finder[item] = entry
        heapq.heappush(self.heap, entry)

    def remove(self, item):
        """Mark an existing item as removed. Raises KeyError if absent."""
        entry = self.entry_finder.pop(item)
        entry[-1] = None  # Mark as removed

    def pop(self):
        """Remove and return the item with the lowest priority value."""
        while self.heap:
            priority, count, item = heapq.heappop(self.heap)
            if item is not None:
                del self.entry_finder[item]
                return item
        raise KeyError('pop from empty priority queue')

    def __contains__(self, item):
        return item in self.entry_finder

    def __len__(self):
        return len(self.entry_finder)

    def __bool__(self):
        return bool(self.entry_finder)
