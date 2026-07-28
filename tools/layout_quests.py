#!/usr/bin/env python3
"""Lay quest chapters out as layered DAGs so dependency lines stop crossing.

THE PROBLEM
Quest positions were hand-assigned per quest as the book grew. Act 8 ended up with its
entry at x=4.5 and its six boss quests at x=16-20, all hanging off that one node, so every
edge dragged diagonally across the whole chapter and the tree was unreadable on screen.

THE APPROACH
Layered (Sugiyama-style) drawing:

  1. LAYER   - a quest's column is the longest path from a chapter root, so every edge
               points strictly rightwards.
  2. DUMMIES - an edge spanning more than one column gets a placeholder node in each
               column it passes through. THIS IS NOT OPTIONAL. Without it the crossing
               count only sees edges between adjacent columns, long edges are invisible to
               the optimiser, and "improving" the layout can make the picture worse - a
               first attempt here took act 8 from 10 crossings to 12 while reporting
               success.
  3. ORDER   - median heuristic sweeps (down, then up) followed by adjacent-swap
               transpose, keeping the best arrangement seen.
  4. PLACE   - x = layer * COL_W; y = rank spread symmetrically about 0. Dummies occupy
               a rank so real nodes route around them, but are never written out.

Dependencies pointing OUTSIDE the chapter (the link from the previous act) are ignored for
layering - that node is a root of its own chapter. Only x and y are rewritten; shape, size
and every other field are untouched.

Run:  tools/layout_quests.py [chapter ...]      (default: every chapter)
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from questfile import Chapter  # noqa: E402

COL_W = 3.0
ROW_H = 1.75
SWEEPS = 8


def _order(cols, layer, edges):
    """Return (ordering, crossings) after median sweeps + transpose."""
    adj_up, adj_dn = {}, {}
    for u, v in edges:
        adj_up.setdefault(v, []).append(u)
        adj_dn.setdefault(u, []).append(v)

    def rankmap():
        return {n: k for c in cols for k, n in enumerate(cols[c])}

    def crossings():
        r = rankmap()
        tot = 0
        by_layer = {}
        for u, v in edges:
            by_layer.setdefault(layer[u], []).append((r[u], r[v]))
        for pairs in by_layer.values():
            for a in range(len(pairs)):
                for b in range(a + 1, len(pairs)):
                    (u1, v1), (u2, v2) = pairs[a], pairs[b]
                    if (u1 - u2) * (v1 - v2) < 0:
                        tot += 1
        return tot

    def sweep(order, adj):
        for c in order:
            col = cols.get(c)
            if not col:
                continue
            r = rankmap()
            base = {n: k for k, n in enumerate(col)}
            def key(n):
                ns = sorted(r[m] for m in adj.get(n, []) if m in r)
                return (ns[len(ns) // 2] if ns else base[n], base[n])
            col.sort(key=key)

    def transpose():
        moved = True
        while moved:
            moved = False
            for c in sorted(cols):
                col = cols[c]
                for k in range(len(col) - 1):
                    cur = crossings()
                    col[k], col[k + 1] = col[k + 1], col[k]
                    if crossings() < cur:
                        moved = True
                    else:
                        col[k], col[k + 1] = col[k + 1], col[k]

    hi = max(cols)
    best, best_x = {c: list(v) for c, v in cols.items()}, crossings()
    for _ in range(SWEEPS):
        sweep(range(1, hi + 1), adj_up)
        sweep(range(hi - 1, -1, -1), adj_dn)
        transpose()
        x = crossings()
        if x < best_x:
            best_x, best = x, {c: list(v) for c, v in cols.items()}
    return best, best_x


def layout(path, verbose=True):
    ch = Chapter(path)
    ids = [Chapter.qid(b) for b in ch.blocks]
    inside = set(ids)
    parents = {i: [d for d in Chapter.deps(b) if d in inside and d != i]
               for b, i in zip(ch.blocks, ids)}

    layer, visiting = {}, set()
    def depth(n):
        if n in layer:
            return layer[n]
        if n in visiting:
            return 0
        visiting.add(n)
        d = 0 if not parents[n] else 1 + max(depth(p) for p in parents[n])
        visiting.discard(n)
        layer[n] = d
        return d
    for i in ids:
        depth(i)

    children = {i: [] for i in ids}
    for i in ids:
        for p in parents[i]:
            children[p].append(i)

    # DFS seed so siblings start adjacent
    seen, dfs = set(), []
    def walk(n):
        if n in seen:
            return
        seen.add(n)
        dfs.append(n)
        for c in sorted(children[n]):
            walk(c)
    for r in sorted(i for i in ids if not parents[i]):
        walk(r)
    for i in ids:
        walk(i)
    seed = {n: k for k, n in enumerate(dfs)}

    # split long edges with dummy nodes, one per intermediate column
    edges, dummies = [], 0
    for v in ids:
        for u in parents[v]:
            span = layer[v] - layer[u]
            if span <= 1:
                edges.append((u, v))
                continue
            prev = u
            for c in range(layer[u] + 1, layer[v]):
                d = f'~dummy{dummies}'
                dummies += 1
                layer[d] = c
                seed[d] = seed[u]
                edges.append((prev, d))
                prev = d
            edges.append((prev, v))

    cols = {}
    for n in layer:
        cols.setdefault(layer[n], []).append(n)
    for c in cols:
        cols[c].sort(key=lambda n: seed.get(n, 0))

    cols, nx = _order(cols, layer, edges)

    for k, (b, i) in enumerate(zip(ch.blocks, ids)):
        col = cols[layer[i]]
        y = (col.index(i) - (len(col) - 1) / 2.0) * ROW_H
        ch.blocks[k] = Chapter.set_pos(b, round(layer[i] * COL_W, 2), round(y, 2))
    ch.save()

    if verbose:
        print(f'{os.path.basename(path):<22} {len(ids):>3} quests  '
              f'{len(cols)} cols  {dummies:>2} dummies  {nx:>3} crossings')
    return nx


def main():
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'config/ftbquests/quests/chapters/*.snbt')))
    for f in files:
        layout(f)
    return 0


if __name__ == '__main__':
    sys.exit(main())
