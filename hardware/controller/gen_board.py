#!/usr/bin/env python3
"""Пишет KiCad 8 проект контроллера. Кикада на машине нет."""

import array
import math
from collections import deque
from pathlib import Path

from kicad_util import A, Q, SHEET, dist_point_seg, dump, num, rotate, seg_dist, uid

OUT = Path("/home/omfg/Projects/sata-library/hardware/controller")
RES = 0.1
N = 1001  # cells 0..1000 cover 0..100 mm
CLEAR_R = 0.25
CLEAR_C = 0.2


def cell_of(v):
    return int(round(v / RES))


def xy_of(i):
    return i * RES


# --- footprints -----------------------------------------------------------

def smd(num, x, y, w, h):
    return {"num": str(num), "x": x, "y": y, "w": w, "h": h, "shape": "rect", "drill": None, "th": False}


def th(num, x, y, drill, pad, shape="circle"):
    return {"num": str(num), "x": x, "y": y, "w": pad, "h": pad, "shape": shape, "drill": drill, "th": True}


def rect_lines(x0, y0, x1, y1, layer, w=0.12):
    return [
        (layer, x0, y0, x1, y0, w),
        (layer, x1, y0, x1, y1, w),
        (layer, x1, y1, x0, y1, w),
        (layer, x0, y1, x0, y0, w),
    ]


def two_pad_smd(pitch, pw, ph, body):
    pads = [smd(1, -pitch / 2, 0, pw, ph), smd(2, pitch / 2, 0, pw, ph)]
    x0, y0, x1, y1 = body
    lines = rect_lines(x0, y0, x1, y1, "F.SilkS", 0.12)
    lines += rect_lines(x0 - 0.3, y0 - 0.3, x1 + 0.3, y1 + 0.3, "F.CrtYd", 0.05)
    return pads, lines


FPS = {}


def add_fp(name, attr, pads, lines, texts, descr):
    FPS[name] = {"attr": attr, "pads": pads, "lines": lines, "texts": texts, "descr": descr}


def build_fps():
    pads, lines = two_pad_smd(2.0, 1.0, 1.3, (-1.0, -0.6, 1.0, 0.6))
    add_fp("R_0805", "smd", pads, lines, [], "0805 resistor")
    add_fp("C_0805", "smd", pads, lines, [], "0805 capacitor")
    led_lines = lines + [("F.SilkS", 0.4, -0.7, 0.4, 0.7, 0.12)]
    add_fp("LED_0805", "smd", pads, led_lines, [("F.SilkS", 1.3, 0, "K", 0.5)], "0805 LED, cathode pin 2")
    zp, zl = two_pad_smd(3.0, 0.9, 1.1, (-1.2, -0.8, 1.2, 0.8))
    zl.append(("F.SilkS", -1.3, -0.9, -1.3, 0.9, 0.15))
    add_fp("D_SOD-123", "smd", zp, zl, [("F.SilkS", -1.6, 1.3, "K", 0.6)], "SOD-123, cathode pin 1")

    sot = [
        smd(1, -0.95, 1.0, 1.0, 0.6),
        smd(2, 0.95, 1.0, 1.0, 0.6),
        smd(3, 0, -1.0, 1.0, 0.6),
    ]
    sl = rect_lines(-1.4, -0.7, 1.4, 0.7, "F.SilkS")
    sl += rect_lines(-1.8, -1.6, 1.8, 1.6, "F.CrtYd", 0.05)
    add_fp("SOT-23", "smd", sot, sl, [("F.Fab", 0, 0, "GDS", 0.4)], "SOT-23 1=G 2=S 3=D")

    sot223 = [
        smd(1, -2.3, -3.0, 1.2, 2.0),
        smd(2, 0, -3.0, 1.2, 2.0),
        smd(3, 2.3, -3.0, 1.2, 2.0),
        smd(2, 0, 2.2, 3.6, 2.0),
    ]
    bl = rect_lines(-3.4, -1.6, 3.4, 1.6, "F.Fab")
    bl += rect_lines(-4.2, -4.4, 4.2, 3.6, "F.CrtYd", 0.05)
    add_fp("SOT-223", "smd", sot223, bl, [], "SOT-223 tab = pin 2")

    to = [
        th(1, -2.54, 0, 1.0, 2.2, "rect"),
        th(2, 0, 0, 1.0, 2.2, "circle"),
        th(3, 2.54, 0, 1.0, 2.2, "circle"),
    ]
    tl = rect_lines(-5.4, 3.0, 5.4, 16.5, "F.Fab", 0.15)
    tl += rect_lines(-6.0, -1.8, 6.0, 17.2, "F.CrtYd", 0.05)
    tl += [("F.Fab", -2.54, 0, -2.54, 3.0, 0.15), ("F.Fab", 0, 0, 0, 3.0, 0.15), ("F.Fab", 2.54, 0, 2.54, 3.0, 0.15)]
    add_fp(
        "TO-220-3_Flat",
        "through_hole",
        to,
        tl,
        [("F.Fab", 0, 10, "FLAT", 0.8)],
        "TO-220 lying flat, body in +Y, 1=G 2=D 3=S, tab=D",
    )

    pf = [smd(1, 0, -2.6, 3.6, 2.2), smd(2, 0, 2.6, 3.6, 2.2)]
    pl = rect_lines(-2.6, -3.8, 2.6, 3.8, "F.SilkS")
    pl += rect_lines(-3.2, -4.6, 3.2, 4.6, "F.CrtYd", 0.05)
    add_fp("Polyfuse_2920", "smd", pf, pl, [], "2920 polyfuse")

    fuse = [th(1, 0, 0, 1.4, 3.2, "rect"), th(2, 22.0, 0, 1.4, 3.2)]
    fl = rect_lines(1.0, -2.6, 21.0, 2.6, "F.SilkS", 0.15)
    fl += rect_lines(-2.2, -3.4, 24.2, 3.4, "F.CrtYd", 0.05)
    add_fp("Fuse_5x20", "through_hole", fuse, fl, [("F.SilkS", 11, -3.6, "5x20", 0.8)], "5x20 mm fuse holder, pitch 22 mm")

    sw = [
        th(1, -3.3, -2.5, 0.9, 1.6),
        th(1, -3.3, 2.5, 0.9, 1.6),
        th(2, 3.3, -2.5, 0.9, 1.6),
        th(2, 3.3, 2.5, 0.9, 1.6),
    ]
    swl = rect_lines(-3.0, -3.0, 3.0, 3.0, "F.SilkS")
    swl += rect_lines(-4.2, -4.0, 4.2, 4.0, "F.CrtYd", 0.05)
    add_fp("SW_Push_6mm", "through_hole", sw, swl, [], "6 mm tactile, paired pins")

    term = [th(1, 0, 0, 1.4, 2.8, "rect"), th(2, 5.08, 0, 1.4, 2.8)]
    tlines = rect_lines(-2.4, -4.2, 7.5, 4.2, "F.SilkS", 0.15)
    tlines += rect_lines(-3.0, -4.8, 8.1, 4.8, "F.CrtYd", 0.05)
    add_fp(
        "Terminal_2P_5.08",
        "through_hole",
        term,
        tlines,
        [("F.SilkS", 0, -3.2, "+", 1.0), ("F.SilkS", 5.08, -3.2, "-", 1.0)],
        "5.08 mm 2-pin screw, pin 1 square +",
    )

    def header_1x(n, name, descr):
        pads = [th(i + 1, i * 2.54, 0, 1.0, 1.7, "rect" if i == 0 else "circle") for i in range(n)]
        span = (n - 1) * 2.54
        lines = rect_lines(-1.4, -1.4, span + 1.4, 1.4, "F.SilkS")
        lines += rect_lines(-1.8, -1.8, span + 1.8, 1.8, "F.CrtYd", 0.05)
        add_fp(name, "through_hole", pads, lines, [("F.SilkS", -2.2, 0, "1", 0.7)], descr)

    header_1x(4, "PinHeader_1x04", "1x4 2.54 mm, pin 1 square")
    header_1x(6, "PinHeader_1x06", "1x6 2.54 mm UART, pin 1 square")

    idc = []
    for i in range(5):
        idc.append(th(i * 2 + 1, 0, i * 2.54, 1.0, 1.7, "rect" if i == 0 else "circle"))
        idc.append(th(i * 2 + 2, 2.54, i * 2.54, 1.0, 1.7))
    il = rect_lines(-1.5, -1.5, 4.1, 11.7, "F.SilkS", 0.12)
    il += rect_lines(-2.0, -2.0, 4.6, 12.2, "F.CrtYd", 0.05)
    il += [("F.SilkS", -1.2, -1.3, -0.2, -0.3, 0.15), ("F.SilkS", -0.2, -1.3, -1.2, -0.3, 0.15)]
    add_fp(
        "PinHeader_2x05_IDC",
        "through_hole",
        idc,
        il,
        [("F.SilkS", -2.4, 0, "1", 0.8)],
        "IDC 2x5: pin1 and pin2 on the end row, then along Y",
    )

    xt = [th(1, 0, 0, 2.5, 5.0, "rect"), th(2, 7.1, 0, 2.5, 5.0)]
    xl = rect_lines(-3.2, -3.6, 10.4, 3.6, "F.SilkS", 0.2)
    xl += rect_lines(-3.8, -4.2, 11.0, 4.2, "F.CrtYd", 0.05)
    add_fp(
        "XT60_Placeholder",
        "through_hole",
        xt,
        xl,
        [("F.SilkS", 3.5, -5.0, "XT60 +12V", 0.9), ("F.SilkS", 3.5, 5.2, "MATCH PART", 0.7)],
        "Placeholder XT60, 5 mm pads, 7.1 mm pitch — match the part in hand",
    )

    esp = []
    for i in range(19):
        y = -11.43 + i * 1.27
        esp.append(smd(i + 1, -9.4, y, 1.5, 0.75))
        esp.append(smd(38 - i, 9.4, y, 1.5, 0.75))
    el = rect_lines(-9.0, -12.75, 9.0, 12.75, "F.SilkS", 0.15)
    el += rect_lines(-9.6, -13.2, 9.6, 13.2, "F.CrtYd", 0.05)
    el += rect_lines(-8.2, -12.75, 8.2, -6.3, "F.SilkS", 0.12)
    add_fp(
        "ESP32-WROOM-32E",
        "smd",
        esp,
        el,
        [("F.SilkS", 0, -10.5, "ANT", 0.8), ("F.Fab", 0, 0, "ESP32-WROOM-32E", 0.6)],
        "ESP32-WROOM-32E, antenna toward -Y",
    )

    def soic(name, n, pitch, row, descr):
        pads = []
        half = (n / 2 - 1) * pitch / 2
        for i in range(n // 2):
            y = -half + i * pitch
            pads.append(smd(i + 1, -row, y, 1.6, min(0.6, pitch * 0.55)))
            pads.append(smd(n - i, row, y, 1.6, min(0.6, pitch * 0.55)))
        body_y = half + pitch
        lines = rect_lines(-row + 1.2, -body_y, row - 1.2, body_y, "F.Fab")
        lines += rect_lines(-row - 1.2, -body_y - 0.6, row + 1.2, body_y + 0.6, "F.CrtYd", 0.05)
        lines.append(("F.SilkS", -row + 1.0, -body_y, -row + 2.2, -body_y + 1.0, 0.12))
        add_fp(name, "smd", pads, lines, [], descr)

    soic("TSSOP-24", 24, 0.65, 3.2, "TSSOP-24 TCA9548A")
    soic("SOIC-16", 16, 1.27, 2.7, "SOIC-16 narrow")

    hole = [th("", 0, 0, 3.2, 3.2)]
    hole[0]["npth"] = True
    hl = [("F.SilkS", -2.3, 0, 2.3, 0, 0.15), ("F.SilkS", 0, -2.3, 0, 2.3, 0.15)]
    hl += rect_lines(-3.0, -3.0, 3.0, 3.0, "F.CrtYd", 0.05)
    add_fp("MountingHole_3.2", "board_only", hole, hl, [], "M3 drill 3.2 mm NPTH")


# --- symbols --------------------------------------------------------------

SYMS = {}


def add_sym(name, ref, pins, lines, power=False, bom=True, board=True, value=None):
    SYMS[name] = {
        "ref": ref,
        "value": name if value is None else value,
        "pins": pins,
        "lines": lines,
        "power": power,
        "bom": bom,
        "board": board,
    }


def pin(num, name, x, y, ang, etype="passive"):
    return {"num": str(num), "name": name, "x": x, "y": y, "ang": ang, "etype": etype}


def h_passive(name, ref, p1="1", p2="2", e1="passive", e2="passive", n1="~", n2="~"):
    add_sym(
        name,
        ref,
        [pin(p1, n1, -3.81, 0, 0, e1), pin(p2, n2, 3.81, 0, 180, e2)],
        [(-2.2, -1.0, 2.2, 1.0)],
    )


def build_syms():
    h_passive("R", "R")
    h_passive("C", "C")
    h_passive("LED", "D", n1="A", n2="K")
    h_passive("D_Zener", "D", n1="K", n2="A")
    h_passive("Fuse", "F")
    h_passive("Polyfuse", "F")
    h_passive("SW", "SW")
    add_sym(
        "Q_PMOS",
        "Q",
        [pin(1, "G", -7.62, 0, 0), pin(2, "D", 7.62, 2.54, 180), pin(3, "S", 7.62, -2.54, 180)],
        [(-5.08, -5.08, 5.08, 5.08)],
    )
    add_sym(
        "Q_NMOS",
        "Q",
        [pin(1, "G", -7.62, 0, 0), pin(3, "D", 7.62, 2.54, 180), pin(2, "S", 7.62, -2.54, 180)],
        [(-5.08, -5.08, 5.08, 5.08)],
    )
    add_sym(
        "AMS1117",
        "U",
        [
            pin(1, "GND", -7.62, 2.54, 0, "power_in"),
            pin(3, "VIN", -7.62, -2.54, 0, "power_in"),
            pin(2, "VOUT", 7.62, 0, 180, "power_out"),
        ],
        [(-5.08, -5.08, 5.08, 5.08)],
        value="AMS1117-3.3",
    )

    def dual(name, ref, left, right, etype, names, value=None):
        n = max(len(left), len(right))
        dy = 2.54
        y0 = (n - 1) * dy / 2
        pins = []
        for i, num in enumerate(left):
            pins.append(pin(num, names.get(num, str(num)), -12.7, y0 - i * dy, 0, etype.get(num, "passive")))
        for i, num in enumerate(right):
            pins.append(pin(num, names.get(num, str(num)), 12.7, y0 - i * dy, 180, etype.get(num, "passive")))
        add_sym(name, ref, pins, [(-10.16, -y0 - 1.27, 10.16, y0 + 1.27)], value=value)

    esp_left = list(range(1, 20))
    esp_right = list(range(38, 19, -1))
    esp_names = {
        1: "GND", 2: "3V3", 3: "EN", 4: "IO36", 5: "IO39", 6: "IO34", 7: "IO35", 8: "IO32",
        9: "IO33", 10: "IO25", 11: "IO26", 12: "IO27", 13: "IO14", 14: "IO12", 15: "GND",
        16: "IO13", 17: "IO9", 18: "IO10", 19: "IO11", 20: "IO6", 21: "IO7", 22: "IO8",
        23: "IO15", 24: "IO2", 25: "IO0", 26: "IO4", 27: "IO16", 28: "IO17", 29: "IO5",
        30: "IO18", 31: "IO19", 32: "NC", 33: "IO21", 34: "IO3", 35: "IO1", 36: "IO22",
        37: "IO23", 38: "GND",
    }
    esp_et = {}
    for n in range(1, 39):
        esp_et[n] = "passive"
    for n in (1, 2, 15, 38):
        esp_et[n] = "power_in"
    for n in (10, 11, 12, 13, 8, 16, 35):
        esp_et[n] = "output"
    for n in (4, 5, 6, 7, 3, 34, 25):
        esp_et[n] = "input"
    esp_et[33] = "bidirectional"
    esp_et[36] = "bidirectional"
    # wider than the generic dual: 19 pins need a taller body, same helper is fine
    dual("ESP32-WROOM-32E", "U", esp_left, esp_right, esp_et, esp_names, "ESP32-WROOM-32E")

    tca_names = {
        1: "A0", 2: "A1", 3: "RESET", 4: "SD0", 5: "SC0", 6: "SD1", 7: "SC1", 8: "SD2", 9: "SC2",
        10: "SD3", 11: "SC3", 12: "GND", 13: "SD4", 14: "SC4", 15: "SD5", 16: "SC5", 17: "SD6",
        18: "SC6", 19: "SD7", 20: "SC7", 21: "A2", 22: "SCL", 23: "SDA", 24: "VCC",
    }
    tca_et = {i: "passive" for i in range(1, 25)}
    tca_et[3] = "input"
    tca_et[12] = "power_in"
    tca_et[24] = "power_in"
    for i in (4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 22, 23):
        tca_et[i] = "bidirectional"
    for i in (1, 2, 21):
        tca_et[i] = "input"
    dual("TCA9548A", "U", list(range(1, 13)), list(range(24, 12, -1)), tca_et, tca_names, "TCA9548A")

    pcf_names = {
        1: "A0", 2: "A1", 3: "A2", 4: "P0", 5: "P1", 6: "P2", 7: "P3", 8: "VSS",
        9: "P4", 10: "P5", 11: "P6", 12: "P7", 13: "INT", 14: "SCL", 15: "SDA", 16: "VDD",
    }
    pcf_et = {i: "bidirectional" for i in range(1, 17)}
    for i in (1, 2, 3, 13):
        pcf_et[i] = "input"
    pcf_et[8] = "power_in"
    pcf_et[16] = "power_in"
    dual("PCF8574", "U", list(range(1, 9)), list(range(16, 8, -1)), pcf_et, pcf_names, "PCF8574")

    def conn(name, pairs, w=7.62):
        pins = []
        n = len(pairs)
        y0 = (n - 1) * 2.54 / 2
        for i, (num, pname) in enumerate(pairs):
            pins.append(pin(num, pname, -w, y0 - i * 2.54, 0, "passive"))
        add_sym(name, "J", pins, [(-w + 2.54, -y0 - 1.5, w - 2.54, y0 + 1.5)])

    conn("XT60", [(1, "+"), (2, "GND")])
    conn("Conn_1x04", [(1, "VIN"), (2, "GND"), (3, "VOUT"), (4, "GND")])
    conn("Conn_1x06", [(1, "3V3"), (2, "GND"), (3, "TX"), (4, "RX"), (5, "EN"), (6, "IO0")])
    conn("Terminal_2", [(1, "+12V_SW"), (2, "GND")])
    idc_pairs = [
        (1, "3V3_AUX"), (2, "GND"), (3, "PRESENT_N"), (4, "GND"), (5, "SDA"),
        (6, "SCL"), (7, "GND"), (8, "NC"), (9, "NC"), (10, "GND"),
    ]
    pins = []
    for i, (num, pname) in enumerate(idc_pairs):
        side = -10.16 if i % 2 == 0 else 10.16
        ang = 0 if i % 2 == 0 else 180
        y = 5.08 - (i // 2) * 2.54
        pins.append(pin(num, pname, side, y, ang, "passive"))
    add_sym("Conn_2x05", "J", pins, [(-7.62, -6.5, 7.62, 6.5)])

    def pwr(name, net, etype):
        add_sym(name, "#PWR", [pin(1, net, 0, 0, 0, etype)], [], power=True, bom=False, board=False, value=net)

    pwr("GND", "GND", "power_in")
    pwr("+3V3", "+3V3", "power_in")
    pwr("+5V", "+5V", "power_in")
    pwr("+12V", "+12V", "power_in")
    pwr("PWR_GND", "GND", "power_out")
    pwr("PWR_+5V", "+5V", "power_out")
    pwr("PWR_+12V", "+12V", "power_out")


# --- parts ----------------------------------------------------------------

PARTS = []


def add_part(ref, sym, value, fp, pins, pcb, sch, rot=0):
    PARTS.append(
        {
            "ref": ref,
            "sym": sym,
            "value": value,
            "fp": fp,
            "pins": {str(k): v for k, v in pins.items()},
            "pcb": pcb,
            "sch": sch,
            "rot": rot,
            "suuid": uid("sym-" + ref),
        }
    )


def build_parts():
    add_part("J1", "XT60", "XT60", "XT60_Placeholder", {1: "12V_RAW", 2: "GND"}, (84, 10), (40, 40))
    # Сток на вход, исток на предохранитель. Наоборот паразитный диод
    # P-канала проводит при перепутанном XT60.
    add_part("Q1", "Q_PMOS", "IRF4905", "TO-220-3_Flat", {1: "PROT_GATE", 2: "12V_RAW", 3: "12V_PROT"}, (70, 22), (90, 40))
    add_part("R1", "R", "100k", "R_0805", {1: "PROT_GATE", 2: "GND"}, (68, 16), (140, 40))
    add_part("D1", "D_Zener", "15V", "D_SOD-123", {1: "12V_PROT", 2: "PROT_GATE"}, (68, 12), (190, 40))
    add_part("F1", "Fuse", "10A", "Fuse_5x20", {1: "12V_PROT", 2: "+12V"}, (56, 36), (240, 40))
    add_part("J2", "Conn_1x04", "LM2596", "PinHeader_1x04", {1: "+12V", 2: "GND", 3: "+5V", 4: "GND"}, (88, 28), (40, 100))
    add_part("U2", "AMS1117", "AMS1117-3.3", "SOT-223", {1: "GND", 2: "+3V3", 3: "+5V"}, (74, 44), (100, 100))
    add_part("C1", "C", "10uF", "C_0805", {1: "+5V", 2: "GND"}, (66, 44), (160, 100))
    add_part("C2", "C", "10uF", "C_0805", {1: "+3V3", 2: "GND"}, (66, 50), (210, 100))
    add_part("C3", "C", "10uF", "C_0805", {1: "+3V3", 2: "GND"}, (32, 8), (40, 150))
    add_part("C4", "C", "100nF", "C_0805", {1: "+3V3", 2: "GND"}, (32, 14), (90, 150))
    add_part("R4", "R", "1k", "R_0805", {1: "LED", 2: "LED_K"}, (24, 18), (150, 150))
    add_part("D2", "LED", "LED", "LED_0805", {1: "LED_K", 2: "GND"}, (16, 18), (200, 150))
    add_part("R2", "R", "10k", "R_0805", {1: "+3V3", 2: "EN"}, (8, 18), (260, 150))
    add_part("SW1", "SW", "EN", "SW_Push_6mm", {1: "EN", 2: "GND"}, (8, 26), (310, 150))
    add_part("R3", "R", "10k", "R_0805", {1: "+3V3", 2: "IO0"}, (8, 34), (370, 150))
    add_part("SW2", "SW", "IO0", "SW_Push_6mm", {1: "IO0", 2: "GND"}, (8, 42), (430, 150))
    add_part("J3", "Conn_1x06", "UART", "PinHeader_1x06", {
        1: "+3V3", 2: "GND", 3: "UART_TX", 4: "UART_RX", 5: "EN", 6: "IO0",
    }, (42, 28), (40, 200))
    add_part("R5", "R", "10k", "R_0805", {1: "+3V3", 2: "TCA_RST"}, (8, 50), (120, 200))
    add_part("R6", "R", "4.7k", "R_0805", {1: "+3V3", 2: "SDA"}, (44, 40), (180, 200))
    add_part("R7", "R", "4.7k", "R_0805", {1: "+3V3", 2: "SCL"}, (52, 40), (230, 200))
    add_part("C5", "C", "100nF", "C_0805", {1: "+3V3", 2: "GND"}, (28, 43), (290, 200))
    add_part("C6", "C", "100nF", "C_0805", {1: "+3V3", 2: "GND"}, (48, 48), (340, 200))

    esp_nets = {
        1: "GND", 2: "+3V3", 3: "EN", 4: "PRESENT3", 5: "PRESENT4", 6: "PRESENT1", 7: "PRESENT2",
        8: "LED", 9: "NC", 10: "SLOT1_EN", 11: "SLOT2_EN", 12: "SLOT3_EN", 13: "SLOT4_EN",
        14: "NC", 15: "GND", 16: "TCA_RST", 17: "NC", 18: "NC", 19: "NC", 20: "NC", 21: "NC",
        22: "NC", 23: "NC", 24: "NC", 25: "IO0", 26: "NC", 27: "NC", 28: "NC", 29: "NC",
        30: "NC", 31: "NC", 32: "NC", 33: "SDA", 34: "UART_RX", 35: "UART_TX", 36: "SCL",
        37: "NC", 38: "GND",
    }
    add_part("U1", "ESP32-WROOM-32E", "ESP32-WROOM-32E", "ESP32-WROOM-32E", esp_nets, (50, 12.75), (460, 120), 0)

    tca = {
        1: "GND", 2: "GND", 3: "TCA_RST", 4: "SDA1", 5: "SCL1", 6: "SDA2", 7: "SCL2",
        8: "SDA3", 9: "SCL3", 10: "SDA4", 11: "SCL4", 12: "GND",
        13: "NC", 14: "NC", 15: "NC", 16: "NC", 17: "NC", 18: "NC", 19: "NC", 20: "NC",
        21: "GND", 22: "SCL", 23: "SDA", 24: "+3V3",
    }
    add_part("U3", "TCA9548A", "TCA9548A", "TSSOP-24", tca, (18, 36), (700, 110))
    pcf = {i: "NC" for i in range(1, 17)}
    pcf.update({1: "GND", 2: "GND", 3: "GND", 8: "GND", 14: "SCL", 15: "SDA", 16: "+3V3"})
    add_part("U4", "PCF8574", "PCF8574", "SOIC-16", pcf, (36, 36), (700, 200))

    for i in range(4):
        n = i + 1
        tx = 16 + i * 22
        hx = tx + 8
        fused = f"12V_F{n}"
        sw = f"12V_SW{n}"
        gate = f"GATE{n}"
        ng = f"NG{n}"
        en = f"SLOT{n}_EN"
        pres = f"PRESENT{n}"
        sda = f"SDA{n}"
        scl = f"SCL{n}"
        y = 270 + i * 75
        add_part(f"F{n+1}", "Polyfuse", "5A", "Polyfuse_2920", {1: "+12V", 2: fused}, (tx, 52), (40, y))
        add_part(f"Q{n+1}", "Q_PMOS", "IRF4905", "TO-220-3_Flat", {1: gate, 2: sw, 3: fused}, (tx, 62), (100, y))
        add_part(f"R{8+i*4}", "R", "100k", "R_0805", {1: gate, 2: fused}, (tx - 9, 56), (160, y))
        add_part(f"Q{n+5}", "Q_NMOS", "2N7002", "SOT-23", {1: ng, 2: "GND", 3: gate}, (tx - 9, 64), (220, y))
        add_part(f"R{9+i*4}", "R", "100k", "R_0805", {1: ng, 2: "GND"}, (tx - 9, 70), (280, y))
        add_part(f"R{10+i*4}", "R", "1k", "R_0805", {1: en, 2: ng}, (tx - 9, 76), (340, y))
        add_part(f"R{11+i*4}", "R", "10k", "R_0805", {1: "+3V3", 2: pres}, (hx, 58), (400, y))
        add_part(f"J{4+2*i}", "Terminal_2", f"SLOT{n}", "Terminal_2P_5.08", {1: sw, 2: "GND"}, (tx, 92), (470, y))
        add_part(
            f"J{5+2*i}",
            "Conn_2x05",
            f"SLOT{n}",
            "PinHeader_2x05_IDC",
            {1: "+3V3", 2: "GND", 3: pres, 4: "GND", 5: sda, 6: scl, 7: "GND", 8: "NC", 9: "NC", 10: "GND"},
            (hx, 78),
            (560, y),
        )


# --- schematic ------------------------------------------------------------

def sheet_pin(part, p):
    return (part["sch"][0] + p["x"], part["sch"][1] - p["y"])


def emit_sym_body(name, sym, lib=False):
    full = name if lib else "controller:" + name
    kids = []
    props = [
        ("Reference", sym["ref"] if lib else sym["ref"], 0, 0, True),
        ("Value", sym["value"], 0, 0, False),
        ("Footprint", "", 0, 0, True),
        ("Datasheet", "~", 0, 0, True),
    ]
    body = [A("symbol"), Q(full)]
    if sym["power"]:
        body.append([A("power")])
        body += [[A("pin_names"), [A("offset"), 0], A("hide")], [A("pin_numbers"), A("hide")]]
    else:
        body.append([A("pin_names"), [A("offset"), 0.254]])
    body.append([A("exclude_from_sim"), A("no")])
    body.append([A("in_bom"), A("yes" if sym["bom"] else "no")])
    body.append([A("on_board"), A("yes" if sym["board"] else "no")])
    for key, val, x, y, hide in props:
        eff = [A("effects"), [A("font"), [A("size"), 1.27, 1.27]]]
        if hide:
            eff.append([A("hide"), A("yes")])
        body.append([A("property"), Q(key), Q(val), [A("at"), x, y, 0], eff])
    graphics = [A("symbol"), Q(name + "_0_1")]
    for x0, y0, x1, y1 in sym["lines"]:
        graphics.append(
            [A("rectangle"), [A("start"), x0, y0], [A("end"), x1, y1],
             [A("stroke"), [A("width"), 0.254], [A("type"), A("default")]],
             [A("fill"), [A("type"), A("none")]]]
        )
    if sym["power"] and name in ("GND", "PWR_GND"):
        graphics.append(
            [A("polyline"),
             [A("pts"), [A("xy"), 0, 0], [A("xy"), 0, -1.2], [A("xy"), -1.0, -2.2], [A("xy"), 1.0, -2.2], [A("xy"), 0, -1.2]],
             [A("stroke"), [A("width"), 0.254], [A("type"), A("default")]],
             [A("fill"), [A("type"), A("none")]]]
        )
    pins = [A("symbol"), Q(name + "_1_1")]
    for p in sym["pins"]:
        hidden = [A("hide"), A("yes")] if sym["power"] else None
        pin_s = [A("pin"), A(p["etype"]), A("line"), [A("at"), p["x"], p["y"], p["ang"]], [A("length"), 0 if sym["power"] else 2.54]]
        if hidden:
            pin_s.append(hidden)
        pin_s.append([A("name"), Q(p["name"]), [A("effects"), [A("font"), [A("size"), 1.0, 1.0]]]])
        pin_s.append([A("number"), Q(p["num"]), [A("effects"), [A("font"), [A("size"), 1.0, 1.0]]]])
        pins.append(pin_s)
    body.append(graphics)
    body.append(pins)
    return body


def build_schematic():
    items = []
    flag = {"GND": False, "+5V": False, "+12V": False}
    flag_sym = {"GND": "PWR_GND", "+5V": "PWR_+5V", "+12V": "PWR_+12V"}
    occupied = {}

    def claim(x, y, net):
        k = (round(x, 3), round(y, 3))
        prev = occupied.get(k)
        if prev is not None and prev != net:
            raise SystemExit(f"схема: точка {k} сети {prev} и {net}")
        occupied[k] = net

    def wire(x1, y1, x2, y2, net):
        claim(x1, y1, net)
        claim(x2, y2, net)
        items.append([A("wire"), [A("pts"), [A("xy"), x1, y1], [A("xy"), x2, y2]],
                      [A("stroke"), [A("width"), 0], [A("type"), A("default")]],
                      [A("uuid"), Q(uid(f"w-{x1:.3f}-{y1:.3f}-{x2:.3f}-{net}"))]])

    def power_at(sym, x, y):
        items.append(sym_inst(sym, f"#PWR{uid(sym+str(x)+str(y))[:6]}", sym if not sym.startswith("PWR") else SYMS[sym]["value"],
                              "", x, y, power=True))

    texts = [
        (20, 12, "Контроллер полки. Байты дисков через эту плату не идут."),
        (20, 18, "ЗАМЕТКА XT60: футпринт — заглушка, площадки 5 мм, шаг 7.1 мм. Перед заказом подогнать под деталь в руках."),
        (20, 24, "USB data is a purchased hub, not this board"),
        (20, 30, "IRF4905 слота: исток на предохранителе, сток на клемму, затвор к истоку 100 кОм — без прошивки выключен."),
        (20, 36, "2N7002: сток к затвору IRF4905, исток на GND, затвор к GND 100 кОм и к GPIO через 1 кОм."),
        (20, 42, "Вход: сток IRF4905 на XT60+, исток на предохранитель, затвор на GND через 100 кОм, стабилитрон 15 В затвор-исток."),
        (20, 230, "IDC 2x5: контакты 1 и 2 — ряд торца, дальше по длинной стороне 3/4, 5/6, 7/8, 9/10. Квадрат на контакте 1. Кабель прямой."),
        (20, 236, "Подтяжек I2C на разъёмах слота нет. Корневые 4.7 кОм стоят до TCA9548A. Канал 0 — слот 1."),
        (20, 242, "PCF8574 0x20 на корневой шине, запас, к слотам не подключён. PRESENT_N внешняя подтяжка 10 кОм к 3.3 В."),
        (20, 248, "Антенна ESP32 у кромки платы, под ней медь не лить. TO-220 лежат плашмя."),
    ]
    # The notes at y=40 collide with parts. Real note block is placed up top; the y=40 lines above
    # are rewritten below to a free band.
    texts = [
        (20, 8, "Контроллер полки. Байты дисков через эту плату не идут."),
        (620, 8, "ЗАМЕТКА XT60: футпринт — заглушка. Площадки около 5 мм, шаг 7.1 мм."),
        (620, 14, "Перед заказом подогнать футпринт под XT60, который в руках."),
        (620, 20, "USB data is a purchased hub, not this board"),
        (620, 28, "Слот: полифуз 5 А, затем IRF4905 верхним ключом. Затвор к истоку 100 кОм."),
        (620, 34, "2N7002 тянет затвор силового ключа к земле. Свой затвор: 100 кОм на GND и 1 кОм от GPIO."),
        (620, 40, "Входной IRF4905: сток на XT60+, исток к предохранителю 10 А, затвор к GND 100 кОм, стабилитрон 15 В."),
        (620, 250, "IDC: 1 и 2 в ряду торца, дальше 3/4 5/6 7/8 9/10. Квадрат и треугольник на контакте 1. Кабель прямой."),
        (620, 256, "I2C подтяжки 4.7 кОм только на корне до TCA9548A. На гребенке слота их нет."),
        (620, 262, "PCF8574 адрес 0x20, запас, выводы P0-P7 не разведены на слоты."),
        (620, 268, "PRESENT внешние 10 кОм к 3.3 В. Антенна у кромки, под ней медь не лить."),
    ]
    for x, y, text in texts:
        items.append([A("text"), Q(text), [A("at"), x, y, 0],
                      [A("effects"), [A("font"), [A("size"), 1.6, 1.6]]],
                      [A("uuid"), Q(uid("t-" + text[:24]))]])

    sym_items = []
    for part in PARTS:
        sym = SYMS[part["sym"]]
        for pdef in sym["pins"]:
            net = part["pins"].get(pdef["num"], "NC")
            sx, sy = sheet_pin(part, pdef)
            claim(sx, sy, net)
            if net == "NC":
                items.append([A("no_connect"), [A("at"), sx, sy], [A("uuid"), Q(uid("nc-" + part["ref"] + pdef["num"]))]])
                continue
            if pdef["x"] < -0.01:
                end = (sx - 5.08, sy)
                ang = 180
            elif pdef["x"] > 0.01:
                end = (sx + 5.08, sy)
                ang = 0
            elif pdef["y"] > 0:
                end = (sx, sy - 5.08)
                ang = 90
            else:
                end = (sx, sy + 5.08)
                ang = 270
            wire(sx, sy, end[0], end[1], net)
            if net in ("GND", "+3V3", "+5V", "+12V"):
                sym_items.append(place_power(net, end[0], end[1], part["ref"] + pdef["num"]))
                claim(end[0], end[1], net)
                if net in flag and not flag[net]:
                    # second symbol at the same point: power_out driver
                    sym_items.append(place_power(flag_sym[net], end[0], end[1], "flag" + net))
                    flag[net] = True
            else:
                items.append([A("label"), Q(net), [A("at"), end[0], end[1], ang],
                              [A("effects"), [A("font"), [A("size"), 1.27, 1.27]],
                               [A("justify"), A("left"), A("bottom")]],
                              [A("uuid"), Q(uid("lb-" + part["ref"] + pdef["num"]))]])
                claim(end[0], end[1], net)
        sym_items.append(place_part(part))
    for net, done in flag.items():
        if not done:
            raise SystemExit(f"нет силового флага {net}")
    return sym_items, items


def place_power(sym_name, x, y, tag):
    ref = "#PWR" + uid(tag + sym_name)[:4]
    return sym_instance(sym_name, ref, SYMS[sym_name]["value"], "", x, y, True)


def place_part(part):
    fp = "" if not SYMS[part["sym"]]["board"] else "controller:" + part["fp"]
    return sym_instance(part["sym"], part["ref"], part["value"], fp, part["sch"][0], part["sch"][1], False, part["suuid"])


def sym_instance(sym, ref, value, fp, x, y, power, suuid=None):
    suuid = suuid or uid("pwr-" + ref + sym + str(x) + str(y))
    pins = []
    for p in SYMS[sym]["pins"]:
        pins.append([A("pin"), Q(p["num"]), [A("uuid"), Q(uid("pin-" + suuid + p["num"]))]])
    bom = A("no") if power else A("yes")
    board = A("no") if power else A("yes")
    node = [A("symbol"),
            [A("lib_id"), Q("controller:" + sym)],
            [A("at"), x, y, 0],
            [A("unit"), 1],
            [A("exclude_from_sim"), A("no")],
            [A("in_bom"), bom],
            [A("on_board"), board],
            [A("dnp"), A("no")],
            [A("uuid"), Q(suuid)],
            [A("property"), Q("Reference"), Q(ref), [A("at"), x, y - 2.54, 0],
             [A("effects"), [A("font"), [A("size"), 1.27, 1.27]]]],
            [A("property"), Q("Value"), Q(value), [A("at"), x, y + 2.54, 0],
             [A("effects"), [A("font"), [A("size"), 1.27, 1.27]]]],
            [A("property"), Q("Footprint"), Q(fp), [A("at"), x, y, 0],
             [A("effects"), [A("font"), [A("size"), 1.27, 1.27]], [A("hide"), A("yes")]]],
            [A("property"), Q("Datasheet"), Q("~"), [A("at"), x, y, 0],
             [A("effects"), [A("font"), [A("size"), 1.27, 1.27]], [A("hide"), A("yes")]]]]
    node.extend(pins)
    node.append([A("instances"),
                 [A("project"), Q("controller"),
                  [A("path"), Q("/" + SHEET),
                   [A("reference"), Q(ref)],
                   [A("unit"), 1]]]])
    return node


def write_sch(sym_items, graphics):
    lib = [A("lib_symbols")]
    for name, sym in SYMS.items():
        lib.append(emit_sym_body(name, sym, lib=False))
    body = [A("kicad_sch"),
            [A("version"), 20231120],
            [A("generator"), Q("eeschema")],
            [A("generator_version"), Q("8.0.4")],
            [A("uuid"), Q(SHEET)],
            [A("paper"), Q("A1")],
            [A("title_block"),
             [A("title"), Q("sata-library control board")],
             [A("date"), Q("2026-11-18")],
             [A("rev"), Q("1")],
             [A("comment"), 1, Q("Contract hardware/INTERFACE.md")],
             [A("comment"), 2, Q("KiCad DRC was not run")]],
            lib]
    body.extend(graphics)
    body.extend(sym_items)
    body.append([A("sheet_instances"), [A("path"), Q("/"), [A("page"), Q("1")]]])
    text = dump(body) + "\n"
    (OUT / "controller.kicad_sch").write_text(text, encoding="utf-8")
    lib_only = [A("kicad_symbol_lib"), [A("version"), 20231120], [A("generator"), Q("kicad_symbol_editor")],
                [A("generator_version"), Q("8.0.4")]]
    for name, sym in SYMS.items():
        lib_only.append(emit_sym_body(name, sym, lib=True))
    (OUT / "libs" / "controller.kicad_sym").write_text(dump(lib_only) + "\n", encoding="utf-8")


def write_tables():
    (OUT / "sym-lib-table").write_text(
        "(sym_lib_table\n  (lib (name \"controller\") (type \"KiCad\") "
        "(uri \"${KIPRJMOD}/libs/controller.kicad_sym\") (options \"\") (descr \"project symbols\"))\n)\n",
        encoding="utf-8",
    )
    (OUT / "fp-lib-table").write_text(
        "(fp_lib_table\n  (lib (name \"controller\") (type \"KiCad\") "
        "(uri \"${KIPRJMOD}/libs/controller.pretty\") (options \"\") (descr \"project footprints\"))\n)\n",
        encoding="utf-8",
    )
    pro = {
        "board": {"design_settings": {"rules": {
            "min_clearance": 0.2, "min_track_width": 0.2, "min_via_diameter": 0.6, "min_via_drill": 0.3,
            "min_hole_clearance": 0.25, "min_copper_edge_clearance": 0.3,
        }}},
        "libraries": {"pinned_footprint_libs": ["controller"], "pinned_symbol_libs": ["controller"]},
        "meta": {"filename": "controller.kicad_pro", "version": 1},
        "net_settings": {"classes": [{
            "name": "Default", "clearance": 0.2, "trace_width": 0.25, "via_dia": 0.8, "via_drill": 0.4,
            "uvia_dia": 0.3, "uvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
        }], "meta": {"version": 3}, "netclass_patterns": []},
        "sheets": [[SHEET, "Root"]],
        "text_variables": {},
    }
    import json
    (OUT / "controller.kicad_pro").write_text(json.dumps(pro, indent=2) + "\n", encoding="utf-8")


# --- pads, tracks, router -------------------------------------------------

PADS = []
TRACKS = []
VIAS = []
TABS = []


def flatten_pads():
    PADS.clear()
    TABS.clear()
    for part in PARTS:
        fp = FPS[part["fp"]]
        rot = part["rot"]
        for pad in fp["pads"]:
            x, y = rotate(pad["x"], pad["y"], rot)
            w, h = pad["w"], pad["h"]
            if rot % 180 == 90:
                w, h = h, w
            PADS.append({
                "ref": part["ref"], "num": pad["num"], "x": part["pcb"][0] + x, "y": part["pcb"][1] + y,
                "w": w, "h": h, "shape": pad["shape"], "drill": pad["drill"], "th": pad["th"],
                "npth": pad.get("npth", False),
                "net": part["pins"].get(pad["num"], "NC"),
            })
        if part["fp"] == "TO-220-3_Flat":
            cx, cy = rotate(0, 9.6, rot)
            TABS.append({"x": part["pcb"][0] + cx, "y": part["pcb"][1] + cy, "w": 11.2, "h": 14.0,
                         "net": part["pins"].get("2", "NC")})


def pad_xy(ref, num):
    hits = [p for p in PADS if p["ref"] == ref and p["num"] == str(num)]
    if not hits:
        raise SystemExit(f"нет пада {ref}.{num}")
    return hits[0]["x"], hits[0]["y"]


def add_seg(x1, y1, x2, y2, w, layer, net, kind):
    if abs(x1 - x2) < 1e-6 and abs(y1 - y2) < 1e-6:
        return
    TRACKS.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "w": w, "layer": layer, "net": net, "kind": kind})


def add_poly(pts, w, layer, net, kind):
    for a, b in zip(pts, pts[1:]):
        add_seg(a[0], a[1], b[0], b[1], w, layer, net, kind)


def add_via(x, y, net, d=1.0, drill=0.5):
    for v in VIAS:
        if v["net"] == net and abs(v["x"] - x) < 0.05 and abs(v["y"] - y) < 0.05:
            return
    VIAS.append({"x": x, "y": y, "net": net, "d": d, "drill": drill})


def add_power_vias(x, y, net):
    add_via(x - 0.7, y, net, 1.2, 0.6)
    add_via(x + 0.7, y, net, 1.2, 0.6)


def layer_of(pad):
    return (0, 1) if pad["th"] else (0,)


def index(x, y, layer):
    return (layer * N + y) * N + x


def in_board_cell(x, y):
    return 0 <= x < N and 0 <= y < N


def mark_rect(blocked, cx, cy, hw, hh, extra, layers):
    minx = cx - hw - extra
    maxx = cx + hw + extra
    miny = cy - hh - extra
    maxy = cy + hh + extra
    ix0, ix1 = max(0, cell_of(minx)), min(N - 1, cell_of(maxx))
    iy0, iy1 = max(0, cell_of(miny)), min(N - 1, cell_of(maxy))
    limit = extra * extra + 1e-6
    for iy in range(iy0, iy1 + 1):
        cy_ = xy_of(iy)
        dy = max(abs(cy_ - cy) - hh, 0.0)
        for ix in range(ix0, ix1 + 1):
            dx = max(abs(xy_of(ix) - cx) - hw, 0.0)
            if dx * dx + dy * dy <= limit:
                for layer in layers:
                    blocked[index(ix, iy, layer)] = 1


def mark_disk(blocked, cx, cy, r, layers):
    if r <= 0:
        return
    rcell = int(math.ceil(r / RES))
    cxi, cyi = cell_of(cx), cell_of(cy)
    for dy in range(-rcell, rcell + 1):
        for dx in range(-rcell, rcell + 1):
            if dx * dx + dy * dy > (r / RES) * (r / RES) + 1e-6:
                continue
            x, y = cxi + dx, cyi + dy
            if not in_board_cell(x, y):
                continue
            for layer in layers:
                blocked[index(x, y, layer)] = 1


def mark_capsule(blocked, x1, y1, x2, y2, r, layers):
    minx, maxx = min(x1, x2) - r, max(x1, x2) + r
    miny, maxy = min(y1, y2) - r, max(y1, y2) + r
    ix0, ix1 = max(0, cell_of(minx)), min(N - 1, cell_of(maxx))
    iy0, iy1 = max(0, cell_of(miny)), min(N - 1, cell_of(maxy))
    for iy in range(iy0, iy1 + 1):
        cy = xy_of(iy)
        for ix in range(ix0, ix1 + 1):
            if dist_point_seg(xy_of(ix), cy, x1, y1, x2, y2) <= r + 1e-6:
                for layer in layers:
                    blocked[index(ix, iy, layer)] = 1


def pad_layers(pad):
    return (0, 1) if pad["th"] or pad["npth"] else (0,)


def build_blocked(net, half):
    blocked = bytearray(N * N * 2)
    reach = half + CLEAR_R
    for pad in PADS:
        if pad["net"] == net or pad["npth"]:
            continue
        layers = pad_layers(pad)
        if pad["shape"] == "circle":
            mark_disk(blocked, pad["x"], pad["y"], pad["w"] / 2 + reach, layers)
        else:
            mark_rect(blocked, pad["x"], pad["y"], pad["w"] / 2, pad["h"] / 2, reach, layers)
    for pad in PADS:
        if pad["npth"]:
            mark_disk(blocked, pad["x"], pad["y"], pad["drill"] / 2 + reach, (0, 1))
    for t in TRACKS:
        if t["net"] == net:
            continue
        layers = (0,) if t["layer"] == "F.Cu" else (1,)
        mark_capsule(blocked, t["x1"], t["y1"], t["x2"], t["y2"], t["w"] / 2 + reach, layers)
    for v in VIAS:
        if v["net"] == net:
            continue
        mark_disk(blocked, v["x"], v["y"], v["d"] / 2 + reach, (0, 1))
    for tab in TABS:
        if tab["net"] == net:
            continue
        mark_rect(blocked, tab["x"], tab["y"], tab["w"] / 2, tab["h"] / 2, half, (0,))
    # antenna keep-out is the rectangle between the module pads, not a fat capsule
    mark_rect(blocked, 50, 3.5, 8, 3.5, half + 0.15, (0, 1))
    # board edge
    mark_capsule(blocked, 0, 0, 100, 0, 0.4 + half, (0, 1))
    mark_capsule(blocked, 0, 100, 100, 100, 0.4 + half, (0, 1))
    mark_capsule(blocked, 0, 0, 0, 100, 0.4 + half, (0, 1))
    mark_capsule(blocked, 100, 0, 100, 100, 0.4 + half, (0, 1))
    for hx, hy in ((4, 4), (96, 4), (4, 96), (96, 96)):
        mark_disk(blocked, hx, hy, 1.6 + reach, (0, 1))
    return blocked


def source_cells(net):
    cells = []
    for t in TRACKS:
        if t["net"] != net:
            continue
        layer = 0 if t["layer"] == "F.Cu" else 1
        steps = int(math.hypot(t["x2"] - t["x1"], t["y2"] - t["y1"]) / RES) + 1
        for s in range(steps + 1):
            a = s / steps
            cells.append((cell_of(t["x1"] + (t["x2"] - t["x1"]) * a),
                          cell_of(t["y1"] + (t["y2"] - t["y1"]) * a), layer))
    for v in VIAS:
        if v["net"] != net:
            continue
        cells.append((cell_of(v["x"]), cell_of(v["y"]), 0))
        cells.append((cell_of(v["x"]), cell_of(v["y"]), 1))
    return cells


def pad_cells(pad):
    out = []
    ix, iy = cell_of(pad["x"]), cell_of(pad["y"])
    rad = max(pad["w"], pad["h"]) / 2
    span = int(math.ceil(rad / RES))
    for dy in range(-span, span + 1):
        for dx in range(-span, span + 1):
            cx, cy = xy_of(ix + dx), xy_of(iy + dy)
            if abs(cx - pad["x"]) <= pad["w"] / 2 + 1e-6 and abs(cy - pad["y"]) <= pad["h"] / 2 + 1e-6:
                out.append((ix + dx, iy + dy))
    if not out:
        out.append((ix, iy))
    return out


def route_pad(net, pad, width, prefer, kind):
    blocked = build_blocked(net, width / 2)
    targets = set()
    free_target = []
    for x, y in pad_cells(pad):
        if not in_board_cell(x, y):
            continue
        layers = (0, 1) if pad["th"] else (0,)
        for layer in layers:
            if not blocked[index(x, y, layer)]:
                targets.add((x, y, layer))
                free_target.append((x, y, layer))
    if not targets:
        return False
    parent = array.array("i", [-1]) * (N * N * 2)
    dq = deque()
    starts = source_cells(net)
    if not starts:
        return False
    for x, y, layer in starts:
        if not in_board_cell(x, y):
            continue
        i = index(x, y, layer)
        if blocked[i] or parent[i] != -1:
            continue
        parent[i] = i
        dq.append(i)
    found = None
    while dq:
        i = dq.popleft()
        layer = i // (N * N)
        rem = i % (N * N)
        y, x = divmod(rem, N)
        if (x, y, layer) in targets and i != parent[i]:
            found = i
            break
        if (x, y, layer) in targets and parent[i] == i and len(starts) == 1:
            found = i
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not in_board_cell(nx, ny):
                continue
            j = index(nx, ny, layer)
            if parent[j] != -1 or blocked[j]:
                continue
            parent[j] = i
            dq.append(j)
        j = index(x, y, 1 - layer)
        if parent[j] == -1 and not blocked[j]:
            parent[j] = i
            dq.append(j)
    if found is None:
        return False
    path = []
    i = found
    seen = set()
    while i not in seen:
        seen.add(i)
        layer = i // (N * N)
        rem = i % (N * N)
        y, x = divmod(rem, N)
        path.append((xy_of(x), xy_of(y), layer))
        if parent[i] == i:
            break
        i = parent[i]
    path.reverse()
    layer_name = {0: "F.Cu", 1: "B.Cu"}
    i = 0
    while i < len(path) - 1:
        if path[i][2] != path[i + 1][2]:
            add_via(path[i + 1][0], path[i + 1][1], net)
            i += 1
            continue
        j = i + 1
        while j + 1 < len(path) and path[j + 1][2] == path[i][2]:
            dx1 = path[j][0] - path[j - 1][0]
            dy1 = path[j][1] - path[j - 1][1]
            dx2 = path[j + 1][0] - path[j][0]
            dy2 = path[j + 1][1] - path[j][1]
            if abs(dx1 * dy2 - dy1 * dx2) > 1e-6:
                break
            if dx1 * dx2 < -1e-9 or dy1 * dy2 < -1e-9:
                break
            j += 1
        add_seg(path[i][0], path[i][1], path[j][0], path[j][1], width, layer_name[path[i][2]], net, kind)
        i = j
    add_seg(path[-1][0], path[-1][1], pad["x"], pad["y"], width, layer_name[path[-1][2]], net, kind)
    return True


def pad_hit(pad, x1, y1, x2, y2):
    if pad["shape"] == "circle":
        return dist_point_seg(pad["x"], pad["y"], x1, y1, x2, y2) <= pad["w"] / 2 + 0.02
    return dist_seg_aabb(x1, y1, x2, y2, pad) <= 0.02


def point_on_pad(pad, x, y):
    if pad["shape"] == "circle":
        return math.hypot(pad["x"] - x, pad["y"] - y) <= pad["w"] / 2 + 0.02
    return abs(pad["x"] - x) <= pad["w"] / 2 + 0.02 and abs(pad["y"] - y) <= pad["h"] / 2 + 0.02


def connected_keys():
    parent = {}

    def add(k):
        parent.setdefault(k, k)

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    def union(a, b):
        add(a)
        add(b)
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i, pad in enumerate(PADS):
        if pad["net"] in ("", "NC") or pad["npth"]:
            continue
        add(("p", i))
    for i, pad in enumerate(PADS):
        if pad["npth"] or pad["net"] in ("", "NC"):
            continue
        for j, other in enumerate(PADS):
            if j <= i or other["ref"] != pad["ref"] or other["num"] != pad["num"]:
                continue
            union(("p", i), ("p", j))
    nodes = []
    for ti, t in enumerate(TRACKS):
        for end, x, y in ((0, t["x1"], t["y1"]), (1, t["x2"], t["y2"])):
            k = ("e", ti, end)
            add(k)
            nodes.append((k, x, y, t["layer"], t["net"]))
        union(("e", ti, 0), ("e", ti, 1))
    for vi, v in enumerate(VIAS):
        add(("v", vi))
    for a, (ka, xa, ya, la, na) in enumerate(nodes):
        for b, (kb, xb, yb, lb, nb) in enumerate(nodes):
            if b <= a or na != nb or la != lb:
                continue
            if math.hypot(xa - xb, ya - yb) <= 0.08:
                union(ka, kb)
        for vi, v in enumerate(VIAS):
            if v["net"] != na:
                continue
            if math.hypot(xa - v["x"], ya - v["y"]) <= 0.08:
                union(ka, ("v", vi))
        for i, pad in enumerate(PADS):
            if pad["net"] != na or pad["npth"]:
                continue
            if la == "B.Cu" and not pad["th"]:
                continue
            if math.hypot(xa - pad["x"], ya - pad["y"]) <= 0.15:
                union(ka, ("p", i))
    # T junctions
    for a, (ka, xa, ya, la, na) in enumerate(nodes):
        for ti, t in enumerate(TRACKS):
            if t["net"] != na or t["layer"] != la:
                continue
            if dist_point_seg(xa, ya, t["x1"], t["y1"], t["x2"], t["y2"]) <= 0.08:
                union(ka, ("e", ti, 0))
    for ti, t in enumerate(TRACKS):
        for vi, v in enumerate(VIAS):
            if v["net"] != t["net"]:
                continue
            if dist_point_seg(v["x"], v["y"], t["x1"], t["y1"], t["x2"], t["y2"]) <= t["w"] / 2 + 0.02:
                union(("v", vi), ("e", ti, 0))
        for i, pad in enumerate(PADS):
            if pad["net"] != t["net"] or pad["npth"]:
                continue
            if t["layer"] == "B.Cu" and not pad["th"]:
                continue
            if pad_hit(pad, t["x1"], t["y1"], t["x2"], t["y2"]):
                union(("e", ti, 0), ("p", i))
    for vi, v in enumerate(VIAS):
        for i, pad in enumerate(PADS):
            if pad["net"] != v["net"] or pad["npth"]:
                continue
            if point_on_pad(pad, v["x"], v["y"]):
                union(("v", vi), ("p", i))
    groups = {}
    for i, pad in enumerate(PADS):
        if pad["net"] in ("", "NC") or pad["npth"]:
            continue
        groups.setdefault(pad["net"], set()).add(find(("p", i)))
    return groups


def unconnected(net):
    touching = set()
    for i, pad in enumerate(PADS):
        if pad["net"] != net or pad["npth"]:
            continue
        hit = False
        for t in TRACKS:
            if t["net"] != net:
                continue
            if t["layer"] == "B.Cu" and not pad["th"]:
                continue
            if pad_hit(pad, t["x1"], t["y1"], t["x2"], t["y2"]):
                hit = True
                break
        if not hit:
            for v in VIAS:
                if v["net"] == net and point_on_pad(pad, v["x"], v["y"]):
                    hit = True
                    break
        if hit:
            touching.add(i)
    return [p for i, p in enumerate(PADS) if p["net"] == net and not p["npth"] and i not in touching]


def finish(net, width, prefer, kind, fallback=None):
    guard = 0
    while True:
        pending = unconnected(net)
        if not pending:
            return True
        if not any(t["net"] == net for t in TRACKS) and not any(v["net"] == net for v in VIAS):
            # seed at the first pad: a zero-length anchor via on its layer so source exists
            seed = pending[0]
            add_via(seed["x"], seed["y"], net) if seed["th"] else add_seg(seed["x"], seed["y"], seed["x"], seed["y"] + 0.01, width, "F.Cu", net, kind)
            pending = pending[1:]
            if not pending:
                return True
        pad = pending[0]
        if not route_pad(net, pad, width, prefer, kind):
            if fallback is None or not route_pad(net, pad, fallback, prefer, kind):
                print("  no path", net, pad["ref"], pad["num"], pad["x"], pad["y"])
                return False
        guard += 1
        if guard > 80:
            return False


def explicit_power():
    # 12 В входа — по нижнему слою. На верхнем дорожка к стоку
    # прошла бы сквозь исток и стабилитрон.
    raw = pad_xy("J1", "1")
    drain = pad_xy("Q1", "2")
    add_poly([raw, (raw[0], 4), (drain[0], 4), drain], 2.0, "B.Cu", "12V_RAW", "power")
    src = pad_xy("Q1", "3")
    f_in = pad_xy("F1", "1")
    add_poly([src, (src[0], 40), (f_in[0], 40), f_in], 2.0, "B.Cu", "12V_PROT", "power")
    f_out = pad_xy("F1", "2")
    add_poly([f_out, (f_out[0], 46), (88, 46), (16, 46)], 2.0, "B.Cu", "+12V", "power")
    vin = pad_xy("J2", "1")
    add_power_vias(vin[0], 46, "+12V")
    add_poly([(vin[0], 46), vin], 2.0, "F.Cu", "+12V", "power")
    for i in range(4):
        n = i + 1
        tx = pad_xy(f"F{n+1}", "1")[0]
        top = pad_xy(f"F{n+1}", "1")
        bot = pad_xy(f"F{n+1}", "2")
        source = pad_xy(f"Q{n+1}", "3")
        drain_s = pad_xy(f"Q{n+1}", "2")
        term = pad_xy(f"J{4+2*i}", "1")
        add_power_vias(tx, 46, "+12V")
        add_poly([(tx, 46), top], 2.0, "F.Cu", "+12V", "power")
        add_poly([bot, (source[0], bot[1]), source], 2.0, "F.Cu", f"12V_F{n}", "power")
        add_poly([drain_s, term], 2.0, "F.Cu", f"12V_SW{n}", "power")
        gnd = pad_xy(f"J{4+2*i}", "2")
        add_poly([gnd, (gnd[0], 95)], 1.5, "B.Cu", "GND", "gndret")
    add_poly([(14, 95), (90, 95)], 1.5, "B.Cu", "GND", "gndret")
    xtg = pad_xy("J1", "2")
    add_poly([xtg, (98, xtg[1]), (98, 92), (90, 92), (90, 95)], 1.5, "B.Cu", "GND", "gndret")


def escape_esp():
    # Left-row signals sit against the antenna keep-out. A straight stub
    # brings each net out to x=35, where the router has room.
    for pad in PADS:
        if pad["ref"] != "U1" or pad["x"] > 50 or pad["net"] in ("GND", "+3V3", "NC", ""):
            continue
        x1, y1, x2 = pad["x"], pad["y"], 35.0
        blocked = False
        for other in PADS:
            if other["ref"] == pad["ref"] and other["num"] == pad["num"]:
                continue
            if other["net"] == pad["net"]:
                continue
            if other["shape"] == "circle":
                gap = dist_point_seg(other["x"], other["y"], x1, y1, x2, y1) - other["w"] / 2 - 0.125
            else:
                gap = dist_seg_aabb(x1, y1, x2, y1, other) - 0.125
            if gap < CLEAR_C:
                blocked = True
                break
        if blocked:
            print("skip escape", pad["num"], pad["net"])
            continue
        add_seg(x1, y1, x2, y1, 0.25, "F.Cu", pad["net"], "signal")


def escape_headers():
    # Pin 6 of the 2x5 sits between ground pins. Bring SDA and SCL out
    # below the header before the maze router runs.
    for i in range(4):
        ref = f"J{5+2*i}"
        sda = pad_xy(ref, "5")
        scl = pad_xy(ref, "6")
        n = i + 1
        add_poly(
            [scl, (scl[0] + 2.2, scl[1]), (scl[0] + 2.2, 90), (sda[0] - 6, 90)],
            0.25, "F.Cu", f"SCL{n}", "signal",
        )
        add_poly(
            [sda, (sda[0] - 2.2, sda[1]), (sda[0] - 2.2, 89.2), (sda[0] - 6, 89.2)],
            0.25, "F.Cu", f"SDA{n}", "signal",
        )


def route_rest():
    prefer_b = 1
    prefer_f = 0
    # thin branches onto the power copper
    for net, kind in (
        ("12V_RAW", "tee"), ("12V_PROT", "tee"), ("+12V", "tee"),
        ("12V_F1", "tee"), ("12V_F2", "tee"), ("12V_F3", "tee"), ("12V_F4", "tee"),
    ):
        print("route", net, flush=True)
        if not finish(net, 0.4, prefer_f, kind):
            print("FAIL tee", net)
            return False
    print("route GND", flush=True)
    if not finish("GND", 0.4, prefer_b, "gnd", fallback=0.25):
        print("FAIL gnd")
        return False
    print("route 3V3", flush=True)
    if not finish("+3V3", 0.4, prefer_f, "signal", fallback=0.25):
        print("FAIL 3v3")
        return False
    print("route 5V", flush=True)
    if not finish("+5V", 0.5, prefer_f, "signal"):
        print("FAIL 5v")
        return False
    done = {"GND", "+3V3", "+5V", "+12V", "12V_RAW", "12V_PROT", "12V_F1", "12V_F2", "12V_F3", "12V_F4", "NC"}
    nets = []
    for pad in PADS:
        if pad["net"] not in done and pad["net"] not in nets:
            nets.append(pad["net"])
    for net in nets:
        print("route", net, flush=True)
        if not finish(net, 0.25, prefer_b, "signal"):
            print("FAIL signal", net)
            return False
    return True


def dist_point_aabb(px, py, pad):
    dx = max(abs(px - pad["x"]) - pad["w"] / 2, 0.0)
    dy = max(abs(py - pad["y"]) - pad["h"] / 2, 0.0)
    return math.hypot(dx, dy)


def dist_seg_aabb(x1, y1, x2, y2, pad):
    steps = max(1, int(math.hypot(x2 - x1, y2 - y1) / 0.05))
    best = min(dist_point_aabb(x1, y1, pad), dist_point_aabb(x2, y2, pad))
    if best == 0.0:
        return 0.0
    for s in range(1, steps):
        a = s / steps
        d = dist_point_aabb(x1 + (x2 - x1) * a, y1 + (y2 - y1) * a, pad)
        if d < best:
            best = d
            if best == 0.0:
                return 0.0
    return best


def pad_gap(a, b):
    if a["shape"] == "circle" and b["shape"] == "circle":
        return math.hypot(a["x"] - b["x"], a["y"] - b["y"]) - a["w"] / 2 - b["w"] / 2
    if a["shape"] == "circle":
        return dist_point_aabb(a["x"], a["y"], b) - a["w"] / 2
    if b["shape"] == "circle":
        return dist_point_aabb(b["x"], b["y"], a) - b["w"] / 2
    dx = abs(a["x"] - b["x"]) - a["w"] / 2 - b["w"] / 2
    dy = abs(a["y"] - b["y"]) - a["h"] / 2 - b["h"] / 2
    if dx >= 0 and dy >= 0:
        return math.hypot(dx, dy)
    return max(dx, dy)


def check_board():
    problems = []
    for i, a in enumerate(PADS):
        if a["net"] in ("", "NC"):
            continue
        for b in PADS[i + 1:]:
            if b["net"] in ("", "NC"):
                continue
            if a["npth"] and b["npth"]:
                continue
            if not a["npth"] and not b["npth"] and a["net"] == b["net"]:
                continue
            if a["ref"] == b["ref"] and a["num"] == b["num"]:
                continue
            gap = pad_gap(a, b)
            if gap < CLEAR_C:
                problems.append(f"pad {a['ref']}.{a['num']} {a['net']} — {b['ref']}.{b['num']} {b['net']} gap {gap:.2f}")
                if len(problems) > 25:
                    return problems
    for i, t in enumerate(TRACKS):
        for u in TRACKS[i + 1:]:
            if t["net"] == u["net"] or t["layer"] != u["layer"]:
                continue
            gap = seg_dist((t["x1"], t["y1"]), (t["x2"], t["y2"]), (u["x1"], u["y1"]), (u["x2"], u["y2"]))
            gap -= t["w"] / 2 + u["w"] / 2
            if gap < CLEAR_C:
                problems.append(f"track {t['net']} / {u['net']} {t['layer']} gap {gap:.2f}")
                if len(problems) > 30:
                    return problems
        for pad in PADS:
            if pad["net"] == t["net"] or pad["npth"] or pad["net"] in ("", "NC"):
                continue
            if t["layer"] == "B.Cu" and not pad["th"]:
                continue
            reach = t["w"] / 2 + max(pad["w"], pad["h"]) / 2 + CLEAR_C
            minx = min(t["x1"], t["x2"]) - reach
            maxx = max(t["x1"], t["x2"]) + reach
            miny = min(t["y1"], t["y2"]) - reach
            maxy = max(t["y1"], t["y2"]) + reach
            if pad["x"] < minx or pad["x"] > maxx or pad["y"] < miny or pad["y"] > maxy:
                continue
            if t["layer"] == "F.Cu" and False:
                pass
            if pad["shape"] == "circle":
                gap = dist_point_seg(pad["x"], pad["y"], t["x1"], t["y1"], t["x2"], t["y2"]) - pad["w"] / 2
            else:
                gap = dist_seg_aabb(t["x1"], t["y1"], t["x2"], t["y2"], pad)
            gap -= t["w"] / 2
            if gap < CLEAR_C:
                problems.append(f"track {t['net']} pad {pad['ref']}.{pad['num']} {pad['net']} gap {gap:.2f}")
                if len(problems) > 40:
                    return problems
    for t in TRACKS:
        if t["kind"] == "power" and t["w"] + 1e-6 < 2.0:
            problems.append(f"12V width {t['w']} {t['net']}")
        if t["kind"] == "gndret" and t["w"] + 1e-6 < 1.5:
            problems.append(f"gnd width {t['w']}")
        for x, y in ((t["x1"], t["y1"]), (t["x2"], t["y2"]), ((t["x1"] + t["x2"]) / 2, (t["y1"] + t["y2"]) / 2)):
            if 42 <= x <= 58 and 0 <= y <= 7:
                problems.append(f"antenna track {t['net']} {x:.1f},{y:.1f}")
                break
    for hx, hy in ((4, 4), (96, 4), (4, 96), (96, 96)):
        for pad in PADS:
            if pad["npth"] or pad["net"] in ("", "NC") and not pad["th"]:
                continue
            gap = dist_point_aabb(hx, hy, pad) - 1.6
            if gap < CLEAR_C:
                problems.append(f"hole ({hx},{hy}) pad {pad['ref']}.{pad['num']} gap {gap:.2f}")
        for t in TRACKS:
            gap = dist_point_seg(hx, hy, t["x1"], t["y1"], t["x2"], t["y2"]) - 1.6 - t["w"] / 2
            if gap < CLEAR_C:
                problems.append(f"hole ({hx},{hy}) track {t['net']} gap {gap:.2f}")
    groups = connected_keys()
    for net, roots in groups.items():
        if len(roots) > 1:
            problems.append(f"open {net} parts {len(roots)}")
    return problems


def write_mod(name, fp):
    node = [A("footprint"), Q(name),
            [A("version"), 20240108],
            [A("generator"), Q("pcbnew")],
            [A("generator_version"), Q("8.0.4")],
            [A("layer"), Q("F.Cu")],
            [A("descr"), Q(fp["descr"])],
            [A("attr"), A(fp["attr"])]]
    node.append(fp_text("reference", "REF**", 0, -2.4, "F.SilkS"))
    node.append(fp_text("value", name, 0, 2.8, "F.Fab"))
    for layer, x1, y1, x2, y2, w in fp["lines"]:
        node.append(fp_line(x1, y1, x2, y2, layer, w))
    for layer, x, y, text, h in fp["texts"]:
        node.append(fp_text("user", text, x, y, layer, h))
    for pad in fp["pads"]:
        node.append(fp_pad(pad, None, 0))
    (OUT / "libs" / "controller.pretty" / f"{name}.kicad_mod").write_text(dump(node) + "\n", encoding="utf-8")


def fp_text(kind, text, x, y, layer, h=0.8):
    return [A("fp_text"), A(kind), Q(text), [A("at"), x, y, 0], [A("layer"), Q(layer)],
            [A("effects"), [A("font"), [A("size"), h, h], [A("thickness"), 0.12]]]]


def fp_line(x1, y1, x2, y2, layer, w):
    return [A("fp_line"), [A("start"), x1, y1], [A("end"), x2, y2],
            [A("stroke"), [A("width"), w], [A("type"), A("solid")]], [A("layer"), Q(layer)]]


def fp_pad(pad, net_id, net_name):
    kind = A("np_thru_hole") if pad.get("npth") else (A("thru_hole") if pad["th"] else A("smd"))
    shape = A(pad["shape"])
    node = [A("pad"), Q(pad["num"]), kind, shape, [A("at"), pad["x"], pad["y"]], [A("size"), pad["w"], pad["h"]]]
    if pad["drill"]:
        node.append([A("drill"), pad["drill"]])
    if pad["th"] or pad.get("npth"):
        node.append([A("layers"), Q("*.Cu"), Q("*.Mask")])
    else:
        node.append([A("layers"), Q("F.Cu"), Q("F.Paste"), Q("F.Mask")])
    if net_id is not None:
        node.append([A("net"), net_id, Q(net_name)])
    return node


def write_pcb(net_of):
    items = [A("kicad_pcb"),
             [A("version"), 20240108],
             [A("generator"), Q("pcbnew")],
             [A("generator_version"), Q("8.0.4")],
             [A("general"), [A("thickness"), 1.6], [A("legacy_teardrops"), A("no")]],
             [A("paper"), Q("A3")],
             layers_node(),
             [A("setup"), [A("pad_to_mask_clearance"), 0], [A("allow_soldermask_bridges_in_footprints"), A("no")]]]
    items.append([A("net"), 0, Q("")])
    for name, i in net_of.items():
        items.append([A("net"), i, Q(name)])
    for part in PARTS:
        items.append(board_fp(part, net_of))
    for idx, (x, y) in enumerate(((4, 4), (96, 4), (4, 96), (96, 96))):
        hole = {"ref": f"H{idx+1}", "fp": "MountingHole_3.2", "value": "M3", "pcb": (x, y), "rot": 0,
                "pins": {"": "NC"}, "suuid": uid("hole" + str(idx))}
        items.append(board_fp(hole, net_of, hole=True))
    for t in TRACKS:
        items.append([A("segment"), [A("start"), t["x1"], t["y1"]], [A("end"), t["x2"], t["y2"]],
                      [A("width"), t["w"]], [A("layer"), Q(t["layer"])],
                      [A("net"), net_of[t["net"]]], [A("uuid"), Q(uid(f"seg-{t['x1']:.2f}-{t['y1']:.2f}-{t['net']}"))]])
    for v in VIAS:
        items.append([A("via"), [A("at"), v["x"], v["y"]], [A("size"), v["d"]], [A("drill"), v["drill"]],
                      [A("layers"), Q("F.Cu"), Q("B.Cu")], [A("net"), net_of[v["net"]]],
                      [A("uuid"), Q(uid(f"via-{v['x']:.2f}-{v['y']:.2f}-{v['net']}"))]])
    for x1, y1, x2, y2 in ((0, 0, 100, 0), (100, 0, 100, 100), (100, 100, 0, 100), (0, 100, 0, 0)):
        items.append([A("gr_line"), [A("start"), x1, y1], [A("end"), x2, y2],
                      [A("stroke"), [A("width"), 0.1], [A("type"), A("solid")]],
                      [A("layer"), Q("Edge.Cuts")], [A("uuid"), Q(uid(f"edge-{x1}-{y1}"))]])
    items.append([A("gr_text"), Q("USB data is a purchased hub, not this board"),
                  [A("at"), 50, 43, 0], [A("layer"), Q("F.SilkS")],
                  [A("uuid"), Q(uid("silk-usb"))],
                  [A("effects"), [A("font"), [A("size"), 0.7, 0.7], [A("thickness"), 0.12]]]])
    items.append([A("gr_text"), Q("UART"), [A("at"), 42, 28, 0], [A("layer"), Q("F.SilkS")],
                  [A("uuid"), Q(uid("silk-uart"))],
                  [A("effects"), [A("font"), [A("size"), 0.8, 0.8], [A("thickness"), 0.12]]]])
    for i in range(4):
        tx = 16 + 22 * i
        items.append([A("gr_text"), Q(f"SLOT{i+1}"), [A("at"), tx + 5, 89, 0], [A("layer"), Q("F.SilkS")],
                      [A("uuid"), Q(uid(f"silk-slot{i}"))],
                      [A("effects"), [A("font"), [A("size"), 0.8, 0.8], [A("thickness"), 0.12]]]])
    gnd = net_of["GND"]
    for layer, name in (("F.Cu", "GND-F"), ("B.Cu", "GND-B")):
        items.append(gnd_zone(gnd, layer, name))
    items.append(keepout())
    (OUT / "controller.kicad_pcb").write_text(dump(items) + "\n", encoding="utf-8")


def layers_node():
    pairs = [
        (0, "F.Cu", "signal"), (2, "B.Cu", "signal"),
        (9, "F.Adhes", "user"), (11, "B.Adhes", "user"),
        (13, "F.Paste", "user"), (15, "B.Paste", "user"),
        (5, "F.SilkS", "user"), (7, "B.SilkS", "user"),
        (1, "F.Mask", "user"), (3, "B.Mask", "user"),
        (17, "Dwgs.User", "user"), (19, "Cmts.User", "user"),
        (21, "Eco1.User", "user"), (23, "Eco2.User", "user"),
        (25, "Edge.Cuts", "user"), (27, "Margin", "user"),
        (29, "F.CrtYd", "user"), (31, "B.CrtYd", "user"),
        (33, "F.Fab", "user"), (35, "B.Fab", "user"),
    ]
    # KiCad canonical ids are not these. Use the real 0..49 map.
    rows = [
        (0, "F.Cu", "signal", None),
        (31, "B.Cu", "signal", None),
        (32, "B.Adhes", "user", "B.Adhesive"),
        (33, "F.Adhes", "user", "F.Adhesive"),
        (34, "B.Paste", "user", None),
        (35, "F.Paste", "user", None),
        (36, "B.SilkS", "user", "B.Silkscreen"),
        (37, "F.SilkS", "user", "F.Silkscreen"),
        (38, "B.Mask", "user", None),
        (39, "F.Mask", "user", None),
        (40, "Dwgs.User", "user", "User.Drawings"),
        (41, "Cmts.User", "user", "User.Comments"),
        (42, "Eco1.User", "user", "User.Eco1"),
        (43, "Eco2.User", "user", "User.Eco2"),
        (44, "Edge.Cuts", "user", None),
        (45, "Margin", "user", None),
        (46, "B.CrtYd", "user", "B.Courtyard"),
        (47, "F.CrtYd", "user", "F.Courtyard"),
        (48, "B.Fab", "user", None),
        (49, "F.Fab", "user", None),
    ]
    node = [A("layers")]
    for num, name, kind, alias in rows:
        row = [num, Q(name), A(kind)]
        if alias:
            row.append(Q(alias))
        node.append(row)
    return node


def board_fp(part, net_of, hole=False):
    fp = FPS[part["fp"]]
    node = [A("footprint"), Q("controller:" + part["fp"]),
            [A("layer"), Q("F.Cu")],
            [A("uuid"), Q(uid("fp-" + part["ref"]))],
            [A("at"), part["pcb"][0], part["pcb"][1], part["rot"]],
            [A("descr"), Q(fp["descr"])],
            fp_text("reference", part["ref"], 0, -2.6, "F.SilkS", 0.7),
            fp_text("value", part["value"], 0, 3.0, "F.Fab", 0.6),
            [A("path"), Q("/" + part["suuid"])],
            [A("sheetname"), Q("Root")],
            [A("sheetfile"), Q("controller.kicad_sch")],
            [A("attr"), A(fp["attr"])]]
    for layer, x1, y1, x2, y2, w in fp["lines"]:
        node.append(fp_line(x1, y1, x2, y2, layer, w))
    for layer, x, y, text, h in fp["texts"]:
        node.append(fp_text("user", text, x, y, layer, h))
    for pad in fp["pads"]:
        net = "NC" if hole else part["pins"].get(pad["num"], "NC")
        if net in ("", "NC"):
            node.append(fp_pad(pad, 0, ""))
        else:
            node.append(fp_pad(pad, net_of[net], net))
    return node


def gnd_zone(net_id, layer, name):
    pts = [A("pts"),
           [A("xy"), 0.8, 0.8], [A("xy"), 41.8, 0.8], [A("xy"), 41.8, 7.2],
           [A("xy"), 58.2, 7.2], [A("xy"), 58.2, 0.8], [A("xy"), 99.2, 0.8],
           [A("xy"), 99.2, 99.2], [A("xy"), 0.8, 99.2]]
    return [A("zone"), [A("net"), net_id], [A("net_name"), Q("GND")], [A("layer"), Q(layer)],
            [A("uuid"), Q(uid("zone-" + name))], [A("name"), Q(name)],
            [A("hatch"), A("edge"), 0.5],
            [A("connect_pads"), A("yes"), [A("clearance"), 0.3]],
            [A("min_thickness"), 0.25],
            [A("filled_areas_thickness"), A("no")],
            [A("fill"), [A("thermal_gap"), 0.3], [A("thermal_bridge_width"), 0.4]],
            [A("polygon"), pts]]


def keepout():
    pts = [A("pts"), [A("xy"), 42, 0], [A("xy"), 58, 0], [A("xy"), 58, 7], [A("xy"), 42, 7]]
    return [A("zone"), [A("net"), 0], [A("net_name"), Q("")],
            [A("layers"), Q("F.Cu"), Q("B.Cu")],
            [A("uuid"), Q(uid("keep-ant"))], [A("name"), Q("antenna")],
            [A("hatch"), A("edge"), 0.5],
            [A("connect_pads"), [A("clearance"), 0]],
            [A("min_thickness"), 0.25],
            [A("filled_areas_thickness"), A("no")],
            [A("keepout"), [A("tracks"), A("not_allowed")], [A("vias"), A("not_allowed")],
             [A("pads"), A("allowed")], [A("copperpour"), A("not_allowed")], [A("footprints"), A("allowed")]],
            [A("fill"), [A("thermal_gap"), 0.5], [A("thermal_bridge_width"), 0.5]],
            [A("polygon"), pts]]


def write_bom():
    rows = {}
    order = []
    for part in PARTS:
        key = (part["value"], part["fp"])
        if key not in rows:
            rows[key] = []
            order.append(key)
        rows[key].append(part["ref"])
    notes = {
        "ESP32-WROOM-32E": "модуль с антенной на плате, антенный конец к кромке",
        "IRF4905": "P-канал TO-220, 1=G 2=D 3=S, прижать к плате",
        "2N7002": "SOT-23, 1=G 2=S 3=D",
        "AMS1117-3.3": "SOT-223, 1=GND 2=VOUT 3=VIN, вкладка = VOUT",
        "TCA9548A": "TSSOP-24, адрес 0x70, A0 A1 A2 на GND",
        "PCF8574": "SOIC-16, адрес 0x20, запас, к слотам не подключён",
        "10A": "держатель 5x20, шаг 22 мм",
        "5A": "полифуз 2920, удержание около 5 А",
        "15V": "SOD-123, катод к истоку входного IRF4905",
        "XT60": "заглушка: сверить площадки с деталью в руках",
        "LM2596": "покупной модуль 12→5 В, на штыри VIN GND VOUT GND",
        "SLOT1": "клемма 5.08 мм, контакт 1 квадрат +",
        "UART": "гребёнка прошивки 1x6",
    }
    lines = ["ref,qty,value,footprint,notes"]
    for key in order:
        refs = rows[key]
        value, fp = key
        note = notes.get(value, "")
        if value.startswith("SLOT"):
            note = notes["SLOT1"] if "Terminal" in fp or fp.startswith("Terminal") else "IDC 2x5, контакт 1 квадрат"
        if fp == "Terminal_2P_5.08":
            note = "клемма 5.08 мм 2 контакта, контакт 1 = +12V_SW, квадрат"
        if fp == "PinHeader_2x05_IDC":
            note = "вилка 2x5 IDC, контакт 1 квадрат и треугольник"
        ref = " ".join(refs)
        lines.append(f"\"{ref}\",{len(refs)},{value},{fp},\"{note}\"")
    lines.append('"H1 H2 H3 H4",4,M3,MountingHole_3.2,"сверло 3.2 мм, центры (4,4) (96,4) (4,96) (96,96)"')
    (OUT / "BOM.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_png():
    w = h = 500
    scale = 5
    buf = bytearray([240, 236, 220]) * (w * h)

    def plot(x, y, r, g, b, rad=0.6):
        ix, iy = int(x * scale), int(y * scale)
        rr = max(1, int(rad * scale))
        for dy in range(-rr, rr + 1):
            for dx in range(-rr, rr + 1):
                px, py = ix + dx, iy + dy
                if 0 <= px < w and 0 <= py < h and dx * dx + dy * dy <= rr * rr:
                    o = (py * w + px) * 3
                    buf[o:o + 3] = bytes((r, g, b))

    for t in TRACKS:
        steps = int(math.hypot(t["x2"] - t["x1"], t["y2"] - t["y1"]) * 4) + 1
        col = (180, 40, 40) if t["layer"] == "F.Cu" else (40, 70, 160)
        for s in range(steps + 1):
            a = s / steps
            plot(t["x1"] + (t["x2"] - t["x1"]) * a, t["y1"] + (t["y2"] - t["y1"]) * a, *col, t["w"] / 2)
    for p in PADS:
        plot(p["x"], p["y"], 20, 20, 20, max(p["w"], p["h"]) / 2)
    import struct, zlib
    raw = b"".join(b"\x00" + bytes(buf[y * w * 3:(y + 1) * w * 3]) for y in range(h))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    Path("/tmp/controller_board.png").write_bytes(png)


def main():
    build_fps()
    build_syms()
    build_parts()
    sym_items, graphics = build_schematic()
    write_sch(sym_items, graphics)
    write_tables()
    for name, fp in FPS.items():
        write_mod(name, fp)
    flatten_pads()
    explicit_power()
    escape_esp()
    escape_headers()
    ok = route_rest()
    problems = check_board()
    nets = {}
    for pad in PADS:
        if pad["net"] not in ("", "NC") and pad["net"] not in nets:
            nets[pad["net"]] = len(nets) + 1
    for t in TRACKS:
        if t["net"] not in nets:
            nets[t["net"]] = len(nets) + 1
    write_pcb(nets)
    write_bom()
    write_png()
    print("route", "ok" if ok else "FAIL")
    print("problems", len(problems))
    for line in problems[:40]:
        print(line)
    if problems or not ok:
        raise SystemExit(1)
    print("board ok", len(TRACKS), "tracks", len(VIAS), "vias", len(PADS), "pads")


if __name__ == "__main__":
    main()
