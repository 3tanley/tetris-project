"""HANDLING window, styled after TETR.IO's settings panel.

Every change is saved to settings.json and applied to the running bot at once:
tap length (< DAS), DAS-to-wall hold (DAS + DCD + ARR), soft drop (SDF) and the
finesse/speed cost model the planner uses to pick key sequences."""
from dataclasses import replace

import AppKit
import objc
from Foundation import NSObject

from . import core, planner, templates as T
from .handling import FRAME_MS, SDF_INF, Handling


def _rgb(r, g, b, a=1.0):
    return AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(r / 255, g / 255, b / 255, a)


C = {
    "page": _rgb(7, 9, 17), "panel": _rgb(25, 28, 38), "border": _rgb(36, 41, 53),
    "row": _rgb(18, 20, 26), "track": _rgb(11, 13, 17), "knob": _rgb(25, 28, 38), "knob_edge": _rgb(52, 58, 76),
    "title": _rgb(104, 116, 148), "label": _rgb(104, 116, 148), "dim": _rgb(58, 64, 84),
    "value": _rgb(170, 182, 222), "check_on": _rgb(118, 132, 180), "check_off": _rgb(15, 17, 22),
    "check_text": _rgb(152, 167, 216), "seg_off": _rgb(35, 41, 58), "seg_off_hi": _rgb(55, 63, 88),
    "seg_off_text": _rgb(133, 156, 218), "seg_on": _rgb(14, 15, 20), "seg_on_text": _rgb(236, 238, 245),
    "section": _rgb(19, 21, 28), "section_text": _rgb(126, 137, 170), "white": _rgb(250, 250, 252),
}


def _font(size, name="DINCondensed-Bold"):
    return AppKit.NSFont.fontWithName_size_(name, size) or AppKit.NSFont.boldSystemFontOfSize_(size)


def _text(s, size, color, font="DINCondensed-Bold", kern=1.2):
    return AppKit.NSAttributedString.alloc().initWithString_attributes_(s, {
        AppKit.NSFontAttributeName: _font(size, font),
        AppKit.NSForegroundColorAttributeName: color,
        AppKit.NSKernAttributeName: kern,
    })


def _draw_text(s, size, color, x, y, font="DINCondensed-Bold", kern=1.2, center_w=None):
    a = _text(s, size, color, font, kern)
    if center_w is not None:
        x += (center_w - a.size().width) / 2
    a.drawAtPoint_((x, y))


def _round_rect(rect, radius, fill, stroke=None):
    p = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, radius, radius)
    fill.setFill()
    p.fill()
    if stroke is not None:
        stroke.setStroke()
        p.setLineWidth_(1.5)
        p.stroke()


# ------------------------------------------------------------------ widgets
class FlippedView(AppKit.NSView):
    def isFlipped(self):
        return True


class Box(FlippedView):
    """Rounded filled rectangle (panel / row background)."""

    def drawRect_(self, rect):
        _round_rect(self.bounds(), self.radius, self.fill, getattr(self, "stroke", None))


class Label(FlippedView):
    def drawRect_(self, rect):
        _draw_text(self.s, self.size, self.color, 0, 0, self.fontname, self.kern,
                   center_w=self.bounds().size.width if self.center else None)


class SliderCell(AppKit.NSSliderCell):
    def drawBarInside_flipped_(self, rect, flipped):
        r = AppKit.NSMakeRect(rect.origin.x, rect.origin.y + rect.size.height / 2 - 3, rect.size.width, 6)
        _round_rect(r, 3, C["track"])

    def drawKnob_(self, rect):
        r = AppKit.NSInsetRect(rect, 2, 0)
        r = AppKit.NSMakeRect(r.origin.x + (r.size.width - 26) / 2, r.origin.y, 26, r.size.height)
        _round_rect(r, 3, C["knob"], C["knob_edge"])


class Check(FlippedView):
    """TETR.IO-style checkbox + label; click anywhere on it to toggle."""

    def drawRect_(self, rect):
        box = AppKit.NSMakeRect(1, 3, 26, 26)
        if self.on:
            _round_rect(box, 3, C["check_on"], C["white"])
            p = AppKit.NSBezierPath.bezierPath()
            p.moveToPoint_((7, 16))
            p.lineToPoint_((12, 22))
            p.lineToPoint_((21, 9))
            p.setLineWidth_(3.5)
            p.setLineCapStyle_(AppKit.NSLineCapStyleRound)
            p.setLineJoinStyle_(AppKit.NSLineJoinStyleRound)
            C["white"].setStroke()
            p.stroke()
        else:
            _round_rect(box, 3, C["check_off"], C["border"])
        _draw_text(self.s, 22, C["check_text"], 38, 4)

    def mouseDown_(self, ev):
        self.on = not self.on
        self.setNeedsDisplay_(True)
        self.cb(self.on)


class Seg(FlippedView):
    """Row of exclusive buttons (OFF / HOLD / TAP)."""

    def drawRect_(self, rect):
        w = self.bounds().size.width
        h = self.bounds().size.height
        n = len(self.options)
        gap = 8
        bw = (w - gap * (n - 1)) / n
        for i, o in enumerate(self.options):
            r = AppKit.NSMakeRect(i * (bw + gap), 0, bw, h)
            if o == self.value:
                _round_rect(r, 2, C["seg_on"], C["border"])
                _draw_text(o, 24, C["seg_on_text"], r.origin.x, 6, center_w=bw)
            else:
                _round_rect(r, 2, C["seg_off"])
                C["seg_off_hi"].setFill()
                AppKit.NSRectFill(AppKit.NSMakeRect(r.origin.x + 2, 1, bw - 4, 2))
                _draw_text(o, 24, C["seg_off_text"], r.origin.x, 6, center_w=bw)

    def mouseDown_(self, ev):
        p = self.convertPoint_fromView_(ev.locationInWindow(), None)
        n = len(self.options)
        i = min(n - 1, max(0, int(p.x / (self.bounds().size.width / n))))
        self.value = self.options[i]
        self.setNeedsDisplay_(True)
        self.cb(self.value)


class Button(FlippedView):
    def drawRect_(self, rect):
        b = self.bounds()
        _round_rect(b, 2, C["seg_off"])
        C["seg_off_hi"].setFill()
        AppKit.NSRectFill(AppKit.NSMakeRect(2, 1, b.size.width - 4, 2))
        _draw_text(self.s, 26, C["seg_off_text"], 0, 5, center_w=b.size.width)

    def mouseDown_(self, ev):
        self.cb()


# ------------------------------------------------------------------ window
_SLIDERS = [
    # key, label, min, max, unit ("ms" or "x"), left label, right label
    ("arr_ms", "ARR", 0.0, 5 * FRAME_MS, "ms", "SLOW", ""),
    ("das_ms", "DAS", 1.0, 20 * FRAME_MS, "ms", "SLOW", "FAST"),
    ("dcd_ms", "DCD", 0.0, 20 * FRAME_MS, "ms", "SLOW", ""),
    ("sdf", "SDF", 5.0, float(SDF_INF), "x", "SLOW", ""),
]
_BOT_SLIDERS = [
    ("key_gap_ms", "KEY GAP", 0.0, 40.0, "ms", "", ""),
    ("max_tap_ms", "MAX TAP", 0.5, 30.0, "ms", "", ""),
]

W = 640


class HandlingWindow(NSObject):
    def initWithBot_(self, bot):
        self = objc.super(HandlingWindow, self).init()
        if self is None:
            return None
        self.bot = bot
        self.h = replace(bot.h)
        self.prev_app = None
        self.sliders = {}
        self._build()
        return self

    # -------------------------------------------------------------- layout
    @objc.python_method
    def _add(self, cls, frame, **attrs):
        v = cls.alloc().initWithFrame_(frame)
        for k, val in attrs.items():
            setattr(v, k, val)
        self.content.addSubview_(v)
        return v

    @objc.python_method
    def _label(self, s, x, y, w, h, size, color, font="DINCondensed-Bold", center=False, kern=1.2):
        return self._add(Label, AppKit.NSMakeRect(x, y, w, h), s=s, size=size, color=color,
                         fontname=font, center=center, kern=kern)

    @objc.python_method
    def _slider_row(self, key, label, lo, hi, unit, left, right, y):
        self._add(Box, AppKit.NSMakeRect(28, y, W - 56, 50), radius=4.0, fill=C["row"])
        self._label(label, 44, y + 12, 120, 34, 32 if len(label) <= 4 else 22, C["label"])
        x0 = 140 if len(label) <= 4 else 160
        sl = AppKit.NSSlider.alloc().initWithFrame_(AppKit.NSMakeRect(x0, y + 8, W - x0 - 190, 30))
        sl.setCell_(SliderCell.alloc().init())
        sl.setMinValue_(0.0)
        sl.setMaxValue_(1000.0)
        sl.setContinuous_(True)
        sl.setTarget_(self)
        sl.setAction_("sliderMoved:")
        sl.setTag_(len(self.sliders))
        self.content.addSubview_(sl)
        if left:
            self._label(left, x0 + 4, y + 33, 60, 16, 13, C["dim"])
        if right:
            self._label(right, x0 + (W - x0 - 190) - 36, y + 33, 50, 16, 13, C["dim"])
        self._add(Box, AppKit.NSMakeRect(W - 178, y + 6, 136, 38), radius=3.0, fill=C["track"])
        field = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(W - 174, y + 15, 58, 22))
        field.setBezeled_(False)
        field.setDrawsBackground_(False)
        field.setTextColor_(C["label"])
        field.setFont_(_font(17, "DINAlternate-Bold"))
        field.setTarget_(self)
        field.setAction_("fieldEdited:")
        field.setTag_(len(self.sliders))
        field.setFocusRingType_(AppKit.NSFocusRingTypeNone)
        self.content.addSubview_(field)
        big = self._label("", W - 114, y + 8, 70, 34, 30, C["value"], "DINAlternate-Bold", kern=0)
        self.sliders[len(self.sliders)] = dict(key=key, lo=lo, hi=hi, unit=unit, slider=sl, field=field, big=big)

    @objc.python_method
    def _check(self, key, text, y, x=28):
        return self._add(Check, AppKit.NSMakeRect(x, y, W - 2 * x, 32), s=text, on=bool(getattr(self.h, key)),
                         cb=lambda on, k=key: self._set(k, on))

    @objc.python_method
    def _seg_section(self, key, title, options, y):
        self._add(Box, AppKit.NSMakeRect(28, y, W - 56, 86), radius=4.0, fill=C["section"])
        self._label(title, 44, y + 10, W - 100, 24, 21, C["section_text"])
        return self._add(Seg, AppKit.NSMakeRect(44, y + 40, W - 88, 36), options=options,
                         value=getattr(self.h, key), cb=lambda v, k=key: self._set(k, v))

    @objc.python_method
    def _build(self):
        H = 1250
        scr = AppKit.NSScreen.mainScreen().visibleFrame()
        h_vis = min(H, scr.size.height - 20)
        style = (AppKit.NSWindowStyleMaskTitled | AppKit.NSWindowStyleMaskClosable
                 | AppKit.NSWindowStyleMaskFullSizeContentView)
        win = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            AppKit.NSMakeRect(0, 0, W, h_vis), style, AppKit.NSBackingStoreBuffered, False)
        win.setTitle_("Handling")
        win.setTitlebarAppearsTransparent_(True)
        win.setAppearance_(AppKit.NSAppearance.appearanceNamed_(AppKit.NSAppearanceNameDarkAqua))
        win.setBackgroundColor_(C["page"])
        win.setReleasedWhenClosed_(False)
        win.setDelegate_(self)
        win.center()
        scroll = AppKit.NSScrollView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, W, h_vis))
        scroll.setHasVerticalScroller_(True)
        scroll.setDrawsBackground_(False)
        self.content = FlippedView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, W, H))
        scroll.setDocumentView_(self.content)
        win.setContentView_(scroll)
        self.win = win

        y = 30
        self._add(Box, AppKit.NSMakeRect(12, y, W - 24, 650), radius=6.0, fill=C["panel"], stroke=C["border"])
        self._add(Box, AppKit.NSMakeRect(28, y + 14, 56, 60), radius=4.0, fill=C["seg_on"])
        self._label("▲", 28, y + 26, 56, 40, 26, C["title"], "Helvetica-Bold", center=True, kern=0)
        self._label("HANDLING", 96, y + 16, 300, 64, 60, C["title"], kern=2.5)
        self._add(Button, AppKit.NSMakeRect(W - 222, y + 20, 100, 44), s="RESET", cb=self._reset)
        self._add(Button, AppKit.NSMakeRect(W - 114, y + 20, 86, 44), s="TEST", cb=self._test)
        y += 90
        for spec in _SLIDERS:
            self._slider_row(*spec, y)
            y += 58
        y += 6
        self.checks = [
            self._check("prevent_accidental_hard_drops", "PREVENT ACCIDENTAL HARD DROPS", y),
            self._check("cancel_das_on_direction_change", "CANCEL DAS WHEN CHANGING DIRECTIONS", y + 38),
            self._check("prefer_soft_drop_over_movement", "PREFER SOFT DROP OVER MOVEMENT", y + 76),
        ]
        y += 124
        self.segs = [
            self._seg_section("irs", "ROTATION BUFFERING (IRS)", ["OFF", "HOLD", "TAP"], y),
            self._seg_section("ihs", "HOLD BUFFERING (IHS)", ["OFF", "HOLD", "TAP"], y + 96),
        ]
        y = 30 + 650 + 24
        self._add(Box, AppKit.NSMakeRect(12, y, W - 24, 525), radius=6.0, fill=C["panel"], stroke=C["border"])
        self._label("BOT", 28, y + 14, 300, 50, 46, C["title"], kern=2.5)
        y += 70
        for spec in _BOT_SLIDERS:
            self._slider_row(*spec, y)
            y += 58
        self.segs.append(self._seg_section("optimize", "INPUT OPTIMIZATION", ["FINESSE", "SPEED"], y))
        self.segs.append(self._seg_section("gravity", "GRAVITY MODE", ["AUTO", "LOW", "HIGH"], y + 96))
        y += 192
        self.checks.append(self._check("check_piece", "CHECK GHOST BEFORE HARD DROP", y))
        self.checks.append(self._check("use_180", "USE 180 ROTATION (X)", y + 36))
        self.info = AppKit.NSTextField.wrappingLabelWithString_("")
        self.info.setFrame_(AppKit.NSMakeRect(28, y + 78, W - 56, 66))
        self.info.setFont_(AppKit.NSFont.monospacedSystemFontOfSize_weight_(11, 0))
        self.info.setTextColor_(C["check_text"])
        self.info.setMaximumNumberOfLines_(5)
        self.content.addSubview_(self.info)
        self._refresh()
        # scroll to top
        self.content.scrollPoint_((0, 0))

    # -------------------------------------------------------------- values
    @objc.python_method
    def _pos_from_value(self, spec, v):
        lo, hi = spec["lo"], spec["hi"]
        f = (v - lo) / (hi - lo) if hi > lo else 0
        if spec["unit"] == "ms" and spec["key"] in ("arr_ms", "das_ms", "dcd_ms"):
            f = 1 - f                      # TETR.IO: right = fast = fewer ms
        return max(0.0, min(1000.0, f * 1000))

    @objc.python_method
    def _value_from_pos(self, spec, pos):
        f = pos / 1000.0
        if spec["key"] in ("arr_ms", "das_ms", "dcd_ms"):
            f = 1 - f
        v = spec["lo"] + f * (spec["hi"] - spec["lo"])
        return round(v) if spec["unit"] == "x" else round(v, 1)

    @objc.python_method
    def _refresh(self):
        for spec in self.sliders.values():
            v = getattr(self.h, spec["key"])
            spec["slider"].setDoubleValue_(self._pos_from_value(spec, v))
            self._show(spec, v)
        for c in self.checks:
            c.setNeedsDisplay_(True)
        for sg in self.segs:
            sg.setNeedsDisplay_(True)
        self._info()

    @objc.python_method
    def _show(self, spec, v):
        if spec["unit"] == "x":
            spec["field"].setStringValue_("")
            spec["big"].s = "∞X" if v >= SDF_INF else f"{int(v)}X"
        else:
            spec["field"].setStringValue_(f"{v:g}MS")
            fr = v / FRAME_MS
            spec["big"].s = (f"{fr:.1f}".rstrip("0").rstrip(".") or "0") + "F" if spec["key"] in (
                "arr_ms", "das_ms", "dcd_ms") else ""
        spec["big"].setNeedsDisplay_(True)

    @objc.python_method
    def _info(self, extra=""):
        h = self.h
        self.info.setStringValue_(
            f"tap held {h.tap_ms():.2f} ms (< DAS {h.das_ms:g} ms) · DAS-to-wall held {h.das_hold_ms():.0f} ms\n"
            f"soft drop {'instant, held ' + format(h.softdrop_ms(), '.0f') + ' ms' if h.sdf_infinite else 'held until it lands'}"
            + ("\n" + extra if extra else ""))

    @objc.python_method
    def _set(self, key, value):
        setattr(self.h, key, value)
        self._apply()

    @objc.python_method
    def _apply(self):
        self.h.openers = self.bot.h.openers      # set in the Openers window
        self.h.mode = self.bot.h.mode            # set in the overlay's MODE row
        self.h.save()
        self.bot.set_handling(replace(self.h))
        self._info()

    def sliderMoved_(self, sender):
        spec = self.sliders[sender.tag()]
        v = self._value_from_pos(spec, sender.doubleValue())
        setattr(self.h, spec["key"], v)
        self._show(spec, v)
        self._apply()

    def fieldEdited_(self, sender):
        spec = self.sliders[sender.tag()]
        txt = sender.stringValue().upper().replace("MS", "").replace("X", "").strip()
        try:
            v = float(txt)
        except ValueError:
            self._show(spec, getattr(self.h, spec["key"]))
            return
        v = max(spec["lo"], min(spec["hi"], v))
        setattr(self.h, spec["key"], v)
        spec["slider"].setDoubleValue_(self._pos_from_value(spec, v))
        self._show(spec, v)
        self._apply()

    @objc.python_method
    def _reset(self):
        keep = {k: getattr(self.h, k) for k in ("optimize", "key_gap_ms", "max_tap_ms", "check_piece", "gravity",
                                                 "use_180", "openers", "mode")}
        self.h = Handling(**keep)
        for c in self.checks:
            c.on = bool(getattr(self.h, _CHECK_KEYS[self.checks.index(c)]))
        for sg, key in zip(self.segs, ("irs", "ihs", "optimize", "gravity")):
            sg.value = getattr(self.h, key)
        self._refresh()
        self._apply()

    @objc.python_method
    def _test(self):
        """Preview the key sequences the planner would use with these settings."""
        names = {"L": "◀", "R": "▶", "DL": "DAS◀", "DR": "DAS▶", "CW": "↻", "CCW": "↺", "180": "180", "SD": "▼"}
        saved = planner.SETTINGS["handling"]
        planner.configure(self.h)
        try:
            g = planner.movegen(core.Board(), "T")
            flat = sorted((min(x for x, _ in c), p) for c, p in g.items() if p.rot == 0)
            parts = [f"{x + 1}:{' '.join(names.get(k, k) for k in p.inputs[:-1]) or '·'}" for x, p in flat]
            ms = sum(p.cost[1] for _, p in flat) / max(1, len(flat))
        finally:
            planner.configure(saved)
        self._info(f"T flat by column ({self.h.optimize.lower()}): " + "  ".join(parts) + f"   avg {ms:.0f} ms")

    # -------------------------------------------------------------- show / close
    def show(self):
        ws = AppKit.NSWorkspace.sharedWorkspace()
        front = ws.frontmostApplication()
        if front is not None and front.processIdentifier() != AppKit.NSRunningApplication.currentApplication().processIdentifier():
            self.prev_app = front
        AppKit.NSApp.activateIgnoringOtherApps_(True)
        self.win.makeKeyAndOrderFront_(None)

    def windowWillClose_(self, note):
        if self.prev_app is not None:
            self.prev_app.activateWithOptions_(0)   # give focus back to the browser


_CHECK_KEYS = ["prevent_accidental_hard_drops", "cancel_das_on_direction_change", "prefer_soft_drop_over_movement",
               "check_piece", "use_180"]


# ------------------------------------------------------------------ openers window
# Translucent like the overlay. Switched-on openers sit on top in priority order (drag a
# row to move it; the first one that can be built is used), switched-off ones below in
# alphabetical order.
OW = 340            # window width
ROW_H = 44          # row pitch (row + gap)
HEAD_H = 26         # section header height
TOP = 64            # space for the title


def _sys_text(s, size, color, bold=False, mono=False):
    font = (AppKit.NSFont.monospacedSystemFontOfSize_weight_(size, 0) if mono else
            AppKit.NSFont.systemFontOfSize_weight_(size, AppKit.NSFontWeightSemibold if bold else 0))
    return AppKit.NSAttributedString.alloc().initWithString_attributes_(s, {
        AppKit.NSFontAttributeName: font, AppKit.NSForegroundColorAttributeName: color})


def _white(a):
    return AppKit.NSColor.colorWithWhite_alpha_(1.0, a)


class OpenerRow(FlippedView):
    """One opener: rank + drag grip (when on), name, PC chance, on/off switch."""

    def mouseDownCanMoveWindow(self):
        return False                     # a drag on a row reorders, it doesn't move the window

    def drawRect_(self, rect):
        b = self.bounds()
        fill = _white(0.24 if self.dragging else 0.12 if self.on else 0.05)
        _round_rect(AppKit.NSInsetRect(b, 0.5, 0.5), 8, fill, _white(0.35) if self.dragging else None)
        x = 14
        if self.on:
            _sys_text(str(self.rank), 13, _white(0.95), bold=True).drawAtPoint_((12, 12))
            _white(0.55).setFill()                       # grip: three short bars
            for k in range(3):
                AppKit.NSBezierPath.fillRect_(AppKit.NSMakeRect(30, 15 + k * 5, 12, 2))
            x = 52
        _sys_text(T.FAMILY_NAMES[self.fam], 13, _white(1.0 if self.on else 0.78), bold=True).drawAtPoint_((x, 4))
        _sys_text(f"{T.PC_RATE[self.fam]:.1%} PC chance", 10, _white(0.6 if self.on else 0.5),
                  mono=True).drawAtPoint_((x, 22))


class OpenerList(FlippedView):
    """The two sections. Drag logic lives in drag_start / drag_move / drag_end so it can
    be driven without real mouse events."""

    def mouseDownCanMoveWindow(self):
        return False

    @objc.python_method
    def setup(self, order, cb):
        self.order = list(order)         # switched-on families, priority first
        self.cb = cb                     # cb(new_order) after every change
        self.drag = None
        self.rows = {}
        w = self.bounds().size.width
        for fam in T.FAMILY_PRIORITY:
            r = OpenerRow.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, ROW_H - 6))
            r.fam, r.on, r.rank, r.dragging = fam, fam in self.order, 0, False
            sw = AppKit.NSSwitch.alloc().initWithFrame_(AppKit.NSMakeRect(w - 52, 7, 42, 24))
            sw.setTarget_(self)
            sw.setAction_("switched:")
            sw.setTag_(T.FAMILY_PRIORITY.index(fam))
            r.addSubview_(sw)
            r.switch = sw
            self.addSubview_(r)
            self.rows[fam] = r
        self.on_head = self._header()
        self.off_head = self._header()
        self.layout_rows(animate=False)

    @objc.python_method
    def _header(self):
        f = AppKit.NSTextField.labelWithString_("")
        f.setFont_(AppKit.NSFont.systemFontOfSize_weight_(10, AppKit.NSFontWeightSemibold))
        f.setTextColor_(_white(0.6))
        self.addSubview_(f)
        return f

    @objc.python_method
    def off_list(self):
        return sorted((f for f in T.FAMILY_PRIORITY if f not in self.order), key=lambda f: T.FAMILY_NAMES[f])

    @objc.python_method
    def on_top(self):
        return HEAD_H

    @objc.python_method
    def layout_rows(self, animate=True):
        w = self.bounds().size.width
        y = 0
        self.on_head.setFrame_(AppKit.NSMakeRect(4, y + 6, w - 8, 16))
        self.on_head.setStringValue_("ON  ·  DRAG TO SET THE ORDER  ·  TOP IS TRIED FIRST" if self.order
                                     else "ON  ·  NONE: ANY OPENER MAY BE USED")
        y += HEAD_H
        frames = {}
        for n, fam in enumerate(self.order):
            frames[fam] = AppKit.NSMakeRect(0, y, w, ROW_H - 6)
            self.rows[fam].rank = n + 1
            y += ROW_H
        self.off_head.setFrame_(AppKit.NSMakeRect(4, y + 6, w - 8, 16))
        self.off_head.setStringValue_("OFF" if self.off_list() else "")
        y += HEAD_H
        for fam in self.off_list():
            frames[fam] = AppKit.NSMakeRect(0, y, w, ROW_H - 6)
            y += ROW_H
        self.frames = frames             # where every row is going (frames animate)
        if animate:
            AppKit.NSAnimationContext.beginGrouping()
            AppKit.NSAnimationContext.currentContext().setDuration_(0.15)
        for fam, fr in frames.items():
            r = self.rows[fam]
            r.on = fam in self.order
            r.switch.setState_(AppKit.NSControlStateValueOn if r.on else AppKit.NSControlStateValueOff)
            if self.drag and self.drag["fam"] == fam:
                continue                 # the dragged row follows the mouse
            (r.animator() if animate else r).setFrame_(fr)
            r.setNeedsDisplay_(True)
        if animate:
            AppKit.NSAnimationContext.endGrouping()

    # --- switching
    def switched_(self, sender):
        fam = T.FAMILY_PRIORITY[sender.tag()]
        self.set_on(fam, sender.state() == AppKit.NSControlStateValueOn)

    @objc.python_method
    def set_on(self, fam, on):
        self.order = [f for f in self.order if f != fam] + ([fam] if on else [])
        self.layout_rows()
        self.cb(list(self.order))

    # --- dragging (switched-on rows only)
    @objc.python_method
    def drag_start(self, y):
        for fam in self.order:
            fr = self.frames[fam]
            if fr.origin.y <= y < fr.origin.y + fr.size.height:
                self.drag = {"fam": fam, "dy": y - fr.origin.y, "from": list(self.order)}
                r = self.rows[fam]
                r.dragging = True
                r.removeFromSuperview()          # bring to front
                self.addSubview_(r)
                r.setNeedsDisplay_(True)
                return True
        return False

    @objc.python_method
    def drag_move(self, y):
        if not self.drag:
            return
        fam = self.drag["fam"]
        top = y - self.drag["dy"]
        lo, hi = self.on_top(), self.on_top() + (len(self.order) - 1) * ROW_H
        top = max(lo - 8, min(hi + 8, top))
        r = self.rows[fam]
        r.setFrameOrigin_((0, top))
        idx = max(0, min(len(self.order) - 1, int(round((top - lo) / ROW_H))))
        if self.order.index(fam) != idx:
            self.order.remove(fam)
            self.order.insert(idx, fam)
            self.layout_rows()

    @objc.python_method
    def drag_end(self):
        if not self.drag:
            return
        fam, before = self.drag["fam"], self.drag["from"]
        self.rows[fam].dragging = False
        self.drag = None
        self.layout_rows()
        if self.order != before:
            self.cb(list(self.order))

    def mouseDown_(self, ev):
        self.drag_start(self.convertPoint_fromView_(ev.locationInWindow(), None).y)

    def mouseDragged_(self, ev):
        self.drag_move(self.convertPoint_fromView_(ev.locationInWindow(), None).y)

    def mouseUp_(self, ev):
        self.drag_end()


class OpenersWindow(NSObject):
    """Which openers the bot may build, and in which order (opened from the overlay).
    Saved in settings.json with the handling settings. A translucent panel like the
    overlay: clicking it doesn't take keyboard focus from the browser."""

    def initWithBot_(self, bot):
        self = objc.super(OpenersWindow, self).init()
        if self is None:
            return None
        self.bot = bot
        self._build()
        return self

    @objc.python_method
    def _build(self):
        n = len(T.FAMILY_PRIORITY)
        H = TOP + 2 * HEAD_H + n * ROW_H + 14
        style = AppKit.NSWindowStyleMaskBorderless | AppKit.NSWindowStyleMaskNonactivatingPanel
        p = AppKit.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            AppKit.NSMakeRect(0, 0, OW, H), style, AppKit.NSBackingStoreBuffered, False)
        p.setLevel_(AppKit.NSStatusWindowLevel)
        p.setOpaque_(False)
        p.setBackgroundColor_(AppKit.NSColor.clearColor())
        p.setAlphaValue_(0.94)
        p.setHasShadow_(True)
        p.setMovableByWindowBackground_(True)
        p.setHidesOnDeactivate_(False)
        p.setFloatingPanel_(True)
        p.setBecomesKeyOnlyIfNeeded_(True)
        p.setReleasedWhenClosed_(False)
        p.setCollectionBehavior_(AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
                                 | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary)
        bg = AppKit.NSVisualEffectView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, OW, H))
        bg.setMaterial_(AppKit.NSVisualEffectMaterialHUDWindow)
        bg.setBlendingMode_(AppKit.NSVisualEffectBlendingModeBehindWindow)
        bg.setState_(AppKit.NSVisualEffectStateActive)
        bg.setWantsLayer_(True)
        bg.layer().setCornerRadius_(12)
        bg.layer().setMasksToBounds_(True)
        p.setContentView_(bg)

        title = AppKit.NSTextField.labelWithString_("Openers")
        title.setFont_(AppKit.NSFont.boldSystemFontOfSize_(15))
        title.setTextColor_(AppKit.NSColor.whiteColor())
        title.setFrame_(AppKit.NSMakeRect(16, H - 34, 200, 20))
        bg.addSubview_(title)
        sub = AppKit.NSTextField.labelWithString_("The bot builds the first one on the list that this bag "
                                                  "allows. The advisor follows whatever you build.")
        sub.setFont_(AppKit.NSFont.systemFontOfSize_(10.5))
        sub.setTextColor_(_white(0.7))
        sub.setFrame_(AppKit.NSMakeRect(16, H - 62, OW - 32, 28))
        sub.cell().setWraps_(True)
        bg.addSubview_(sub)
        close = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(OW - 70, H - 36, 58, 24))
        close.setBezelStyle_(AppKit.NSBezelStyleRounded)
        close.setTitle_("Done")
        close.setTarget_(self)
        close.setAction_("close:")
        bg.addSubview_(close)

        lst_h = 2 * HEAD_H + n * ROW_H
        self.list = OpenerList.alloc().initWithFrame_(AppKit.NSMakeRect(12, H - TOP - lst_h, OW - 24, lst_h))
        self.list.setup(self.bot.h.opener_order(), self._apply)
        bg.addSubview_(self.list)
        scr = AppKit.NSScreen.mainScreen().visibleFrame()
        p.setFrameOrigin_((scr.origin.x + (scr.size.width - OW) / 2, scr.origin.y + (scr.size.height - H) / 2))
        self.win = p

    @objc.python_method
    def _apply(self, order):
        h = replace(self.bot.h)
        h.openers = ",".join(order)
        h.save()
        self.bot.set_handling(h)

    def close_(self, sender):
        self.win.orderOut_(None)

    def show(self):
        self.list.order = self.bot.h.opener_order()
        self.list.layout_rows(animate=False)
        self.win.orderFrontRegardless()
