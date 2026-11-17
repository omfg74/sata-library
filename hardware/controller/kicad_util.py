"""S-expression helpers for the KiCad 8 files this tree writes."""

import math
import uuid

SHEET = "7c1a9e2e-4b6d-4f0a-9c31-2a6e5d8b1f40"
NS = uuid.UUID(SHEET)


def uid(name):
    return str(uuid.uuid5(NS, name))


def num(v):
    x = float(v)
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    s = f"{x:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


class A(str):
    pass


class Q(str):
    pass


def dump(node):
    if isinstance(node, A):
        return str(node)
    if isinstance(node, Q):
        return '"' + str(node).replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(node, bool):
        raise TypeError("bool")
    if isinstance(node, (int, float)):
        return num(node)
    if isinstance(node, list):
        return "(" + " ".join(dump(x) for x in node) + ")"
    raise TypeError(type(node))


def rotate(x, y, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (x * c - y * s, x * s + y * c)


def dist_point_seg(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    l2 = vx * vx + vy * vy
    if l2 < 1e-12:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / l2))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def seg_dist(a, b, c, d):
    return min(
        dist_point_seg(a[0], a[1], c[0], c[1], d[0], d[1]),
        dist_point_seg(b[0], b[1], c[0], c[1], d[0], d[1]),
        dist_point_seg(c[0], c[1], a[0], a[1], b[0], b[1]),
        dist_point_seg(d[0], d[1], a[0], a[1], b[0], b[1]),
    )
