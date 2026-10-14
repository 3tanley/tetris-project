"""Overlay window (Start/Stop + live stats) and the Cmd+Shift+K hotkey."""
import time

import AppKit
import objc
import Quartz
from Foundation import NSObject, NSTimer
from PyObjCTools import AppHelper

from . import hotkey
from .controller import Bot, screen_access_ok
from .keys import accessibility_ok

W, H = 270, 282
MODES = [("BLITZ", "Blitz", True), ("SPRINT", "Sprint", True), ("VOD", "VOD Review", False)]   # (key, label, ready)
SOLVE_H = 250

# four.lol colours
_FOUR = {"I": (97, 175, 220), "O": (240, 210, 90), "T": (142, 61, 158), "S": (110, 180, 90),
         "Z": (217, 87, 98), "L": (230, 140, 60), "J": (45, 100, 176), "G": (136, 136, 136), "X": (190, 190, 190)}


def _c(rgb, a=1.0):
    return AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, a)


class DiagramView(AppKit.NSView):
    """Draws a setup / solution diagram: rows top->bottom, letters = pieces,
    lowercase = already placed (dimmed), G = earlier stack, X = DPC leftover.
    Optional: `hint` cells outlined, `labels` [(row, col, text)], `well` column shaded."""

    def isFlipped(self):
        return True

    def drawRect_(self, rect):
        rows = getattr(self, "rows", None) or []
        if not rows:
            return
        b = self.bounds()
        n = len(rows)
        cell = min(22.0, (b.size.width - 4) / 10.0, (b.size.height - 4) / max(n, 1))
        x0 = (b.size.width - 10 * cell) / 2
        y0 = b.size.height - n * cell - 2
        _c((0, 0, 0), 0.35).setFill()
        AppKit.NSBezierPath.fillRect_(AppKit.NSMakeRect(x0, y0, 10 * cell, n * cell))
        well = getattr(self, "well", None)
        if well is not None:                    # sprint: the tetris well
            _c((255, 255, 255), 0.08).setFill()
            AppKit.NSBezierPath.fillRect_(AppKit.NSMakeRect(x0 + well * cell, y0, cell, n * cell))
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch == ".":
                    continue
                key = ch.upper()
                col = _FOUR.get(key, (200, 200, 200))
                alpha = 0.32 if ch.islower() else 1.0
                r = AppKit.NSMakeRect(x0 + i * cell + 0.5, y0 + j * cell + 0.5, cell - 1, cell - 1)
                _c(col, alpha).setFill()
                AppKit.NSBezierPath.fillRect_(r)        # source-over (NSRectFill would punch holes)
                if not ch.islower() and key not in "GX":       # four.lol-style top highlight
                    _c(tuple(min(255, v + 45) for v in col), alpha).setFill()
                    AppKit.NSBezierPath.fillRect_(
                        AppKit.NSMakeRect(r.origin.x, r.origin.y, r.size.width, max(1.5, cell * 0.12)))
        # the suggested next placement: white outline
        AppKit.NSColor.whiteColor().setStroke()
        for j, i in getattr(self, "hint", None) or []:
            path = AppKit.NSBezierPath.bezierPathWithRect_(
                AppKit.NSMakeRect(x0 + i * cell + 1.5, y0 + j * cell + 1.5, cell - 3, cell - 3))
            path.setLineWidth_(2)
            path.stroke()
        # piece order of the planned pieces after the one in play
        for j, i, text in getattr(self, "labels", None) or []:
            AppKit.NSAttributedString.alloc().initWithString_attributes_(text, {
                AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(max(8.0, cell * 0.6)),
                AppKit.NSForegroundColorAttributeName: AppKit.NSColor.whiteColor(),
            }).drawAtPoint_((x0 + i * cell + cell * 0.28, y0 + j * cell + cell * 0.1))


class BagView(AppKit.NSView):
    """Pieces counter: the 7 pieces of the current bag. Spawned pieces solid (in spawn
    order), pieces already in the queue faint, unseen ones as empty slots."""

    def isFlipped(self):
        return True

    def drawRect_(self, rect):
        info = getattr(self, "info", None)
        b = self.bounds()
        label = "bag –" if not info else f"bag {info['bag']}  {len(info['spawned'])}/7"
        AppKit.NSAttributedString.alloc().initWithString_attributes_(label, {
            AppKit.NSFontAttributeName: AppKit.NSFont.monospacedSystemFontOfSize_weight_(10, 0),
            AppKit.NSForegroundColorAttributeName: AppKit.NSColor.lightGrayColor(),
        }).drawAtPoint_((0, 5))
        if not info:
            return
        cells = [(p, 1.0) for p in info["spawned"]] + [(p, 0.35) for p in info["upcoming"]]
        cells += [(None, 0.0)] * (7 - len(cells))
        size = 18.0
        x0 = 92.0
        for i, (p, a) in enumerate(cells[:7]):
            r = AppKit.NSMakeRect(x0 + i * (size + 3), 2, size, size)
            if p is None:
                _c((255, 255, 255), 0.25).setStroke()
                path = AppKit.NSBezierPath.bezierPathWithRect_(r)
                path.setLineWidth_(1)
                path.stroke()
                continue
            _c(_FOUR[p], a).setFill()
            AppKit.NSBezierPath.fillRect_(r)
            AppKit.NSAttributedString.alloc().initWithString_attributes_(p, {
                AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(11),
                AppKit.NSForegroundColorAttributeName: _c((255, 255, 255), max(a, 0.6)),
            }).drawAtPoint_((r.origin.x + 5, r.origin.y + 2))
        if info.get("extra"):
            AppKit.NSAttributedString.alloc().initWithString_attributes_(f"extra {info['extra']}", {
                AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(10),
                AppKit.NSForegroundColorAttributeName: _c(_FOUR[info["extra"]]),
            }).drawAtPoint_((0, 18))


class SolvePanel(NSObject):
    """Second translucent panel under the main one: the solve being built."""

    def initWithFrame_(self, rect):
        self = objc.super(SolvePanel, self).init()
        if self is None:
            return None
        style = AppKit.NSWindowStyleMaskBorderless | AppKit.NSWindowStyleMaskNonactivatingPanel
        p = AppKit.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, AppKit.NSBackingStoreBuffered, False)
        p.setLevel_(AppKit.NSStatusWindowLevel)
        p.setOpaque_(False)
        p.setBackgroundColor_(AppKit.NSColor.clearColor())
        p.setAlphaValue_(0.92)
        p.setHasShadow_(True)
        p.setMovableByWindowBackground_(True)
        p.setHidesOnDeactivate_(False)
        p.setFloatingPanel_(True)
        p.setBecomesKeyOnlyIfNeeded_(True)
        p.setIgnoresMouseEvents_(False)
        p.setCollectionBehavior_(AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
                                 | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
                                 | AppKit.NSWindowCollectionBehaviorStationary)
        w, h = rect.size.width, rect.size.height
        bg = AppKit.NSVisualEffectView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        bg.setMaterial_(AppKit.NSVisualEffectMaterialHUDWindow)
        bg.setBlendingMode_(AppKit.NSVisualEffectBlendingModeBehindWindow)
        bg.setState_(AppKit.NSVisualEffectStateActive)
        bg.setWantsLayer_(True)
        bg.layer().setCornerRadius_(12)
        bg.layer().setMasksToBounds_(True)
        p.setContentView_(bg)
        self.title = AppKit.NSTextField.labelWithString_("Solve")
        self.title.setFrame_(AppKit.NSMakeRect(12, h - 28, w - 24, 18))
        self.title.setFont_(AppKit.NSFont.boldSystemFontOfSize_(13))
        self.title.setTextColor_(AppKit.NSColor.whiteColor())
        bg.addSubview_(self.title)
        self.sub = AppKit.NSTextField.wrappingLabelWithString_("")
        self.sub.setFrame_(AppKit.NSMakeRect(12, h - 74, w - 24, 46))
        self.sub.setFont_(AppKit.NSFont.monospacedSystemFontOfSize_weight_(10, 0))
        self.sub.setTextColor_(AppKit.NSColor.lightGrayColor())
        self.sub.setMaximumNumberOfLines_(3)
        bg.addSubview_(self.sub)
        self.diagram = DiagramView.alloc().initWithFrame_(AppKit.NSMakeRect(10, 8, w - 20, h - 86))
        self.diagram.rows = []
        bg.addSubview_(self.diagram)
        self.panel = p
        self.shown = None
        p.orderFrontRegardless()
        return self

    @objc.python_method
    def update(self, display):
        if display is self.shown:
            return
        self.shown = display
        if not display:
            self.title.setStringValue_(getattr(self, "empty_title", "Solve"))
            self.sub.setStringValue_(getattr(self, "empty_sub", "waiting for a game"))
            self.diagram.rows = []
            self.diagram.hint = []
            self.diagram.labels = []
            self.diagram.well = None
        else:
            self.title.setStringValue_(display["title"])
            self.sub.setStringValue_(display["sub"])
            self.diagram.rows = display["rows"]
            self.diagram.hint = display.get("hint") or []
            self.diagram.labels = display.get("labels") or []
            self.diagram.well = display.get("well")
        self.diagram.setNeedsDisplay_(True)


def _wait_modifiers_released(timeout=1.5):
    """Don't start typing while the user still holds Cmd/Shift from the hotkey."""
    mask = Quartz.kCGEventFlagMaskCommand | Quartz.kCGEventFlagMaskShift
    t = time.time()
    while time.time() - t < timeout:
        if not (Quartz.CGEventSourceFlagsState(Quartz.kCGEventSourceStateHIDSystemState) & mask):
            return
        time.sleep(0.01)


class Overlay(NSObject):
    def initWithBot_(self, bot):
        self = objc.super(Overlay, self).init()
        if self is None:
            return None
        self.bot = bot
        self._build()
        return self

    @objc.python_method
    def _label(self, frame, size=12, bold=False, color=None):
        f = AppKit.NSTextField.alloc().initWithFrame_(frame)
        f.setBezeled_(False)
        f.setDrawsBackground_(False)
        f.setEditable_(False)
        f.setSelectable_(False)
        f.setFont_(AppKit.NSFont.boldSystemFontOfSize_(size) if bold else AppKit.NSFont.monospacedSystemFontOfSize_weight_(size, 0))
        f.setTextColor_(color or AppKit.NSColor.whiteColor())
        return f

    @objc.python_method
    def _build(self):
        scr = AppKit.NSScreen.mainScreen().visibleFrame()
        rect = AppKit.NSMakeRect(scr.origin.x + scr.size.width - W - 20, scr.origin.y + scr.size.height - H - 20, W, H)
        style = AppKit.NSWindowStyleMaskBorderless | AppKit.NSWindowStyleMaskNonactivatingPanel
        p = AppKit.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, AppKit.NSBackingStoreBuffered, False)
        p.setLevel_(AppKit.NSStatusWindowLevel)
        p.setOpaque_(False)
        p.setBackgroundColor_(AppKit.NSColor.clearColor())
        p.setAlphaValue_(0.88)
        p.setHasShadow_(True)
        p.setMovableByWindowBackground_(True)
        p.setHidesOnDeactivate_(False)
        p.setFloatingPanel_(True)
        p.setBecomesKeyOnlyIfNeeded_(True)
        p.setCollectionBehavior_(AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
                                 | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
                                 | AppKit.NSWindowCollectionBehaviorStationary)
        bg = AppKit.NSVisualEffectView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, W, H))
        bg.setMaterial_(AppKit.NSVisualEffectMaterialHUDWindow)
        bg.setBlendingMode_(AppKit.NSVisualEffectBlendingModeBehindWindow)
        bg.setState_(AppKit.NSVisualEffectStateActive)
        bg.setWantsLayer_(True)
        bg.layer().setCornerRadius_(12)
        bg.layer().setMasksToBounds_(True)
        p.setContentView_(bg)

        title = self._label(AppKit.NSMakeRect(12, H - 30, 170, 20), 14, True)
        title.setStringValue_("TETR.IO Bot")
        bg.addSubview_(title)
        hint = self._label(AppKit.NSMakeRect(150, H - 29, W - 160, 18), 10, False, AppKit.NSColor.lightGrayColor())
        hint.setStringValue_("⌘⇧K start/stop")
        hint.setAlignment_(AppKit.NSTextAlignmentRight)
        bg.addSubview_(hint)
        self.bagview = BagView.alloc().initWithFrame_(AppKit.NSMakeRect(12, 80, W - 24, 30))
        self.bagview.info = None
        bg.addSubview_(self.bagview)
        self.status = self._label(AppKit.NSMakeRect(12, 112, W - 24, 72), 11)
        self.status.setStringValue_("idle")
        self.status.cell().setWraps_(True)
        bg.addSubview_(self.status)

        # "Bot plays" switch: off (every launch) = advisor, the bot only shows suggestions
        lbl = self._label(AppKit.NSMakeRect(12, 192, 80, 18), 11, True)
        lbl.setStringValue_("BOT PLAYS")
        bg.addSubview_(lbl)
        self.autoplay_note = self._label(AppKit.NSMakeRect(92, 192, W - 150, 18), 10, False,
                                         AppKit.NSColor.lightGrayColor())
        bg.addSubview_(self.autoplay_note)
        self.autoplay = AppKit.NSSwitch.alloc().initWithFrame_(AppKit.NSMakeRect(W - 54, 189, 42, 24))
        self.autoplay.setTarget_(self)
        self.autoplay.setAction_("autoplay:")
        self.autoplay.setState_(AppKit.NSControlStateValueOn if self.bot.autoplay else AppKit.NSControlStateValueOff)
        bg.addSubview_(self.autoplay)
        self._show_autoplay()

        # MODES: one toggle per game mode (only Blitz exists so far)
        lbl = self._label(AppKit.NSMakeRect(12, 224, 50, 18), 11, True)
        lbl.setStringValue_("MODE")
        bg.addSubview_(lbl)
        self.modes = AppKit.NSSegmentedControl.segmentedControlWithLabels_trackingMode_target_action_(
            [m[1] for m in MODES], AppKit.NSSegmentSwitchTrackingSelectOne, self, "mode:")
        self.modes.setFrame_(AppKit.NSMakeRect(58, 220, W - 70, 24))
        self.modes.setControlSize_(AppKit.NSControlSizeSmall)
        self.modes.setFont_(AppKit.NSFont.systemFontOfSize_(11))
        for i, (key, label, ready) in enumerate(MODES):
            self.modes.setEnabled_forSegment_(ready, i)
            if not ready:
                self.modes.setToolTip_forSegment_(f"{label}: coming soon", i)
        keys = [m[0] for m in MODES]
        cur = self.bot.h.mode if self.bot.h.mode in keys and MODES[keys.index(self.bot.h.mode)][2] else "BLITZ"
        self.modes.setSelectedSegment_(keys.index(cur))
        bg.addSubview_(self.modes)

        # 2 x 2 buttons: Start/Stop  Openers… / Handling…  Quit
        bw = (W - 16) / 2.0

        def button(title, action, col, row):
            b = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(8 + col * bw, 8 + row * 36, bw, 32))
            b.setBezelStyle_(AppKit.NSBezelStyleRounded)
            b.setTitle_(title)
            b.setTarget_(self)
            b.setAction_(action)
            bg.addSubview_(b)
            return b

        self.button = button("Start", "toggle:", 0, 1)
        button("Openers…", "openers:", 1, 1)
        button("Handling…", "handling:", 0, 0)
        button("Quit", "quit:", 1, 0)
        self.panel = p
        p.orderFrontRegardless()
        self.solve = SolvePanel.alloc().initWithFrame_(
            AppKit.NSMakeRect(rect.origin.x, rect.origin.y - SOLVE_H - 8, W, SOLVE_H))
        self.next = SolvePanel.alloc().initWithFrame_(
            AppKit.NSMakeRect(rect.origin.x, rect.origin.y - 2 * SOLVE_H - 16, W, SOLVE_H))
        self.next.empty_title = "Next"
        self.next.empty_sub = "planned ahead during T-spin setups"
        self.next.shown = 0
        self.next.update(None)
        # Sprint: one panel in place of Solve + Next, showing where the pieces go
        self.sprint = SolvePanel.alloc().initWithFrame_(
            AppKit.NSMakeRect(rect.origin.x, rect.origin.y - 2 * SOLVE_H - 16, W, 2 * SOLVE_H + 8))
        self.sprint.empty_title = "Sprint 6-3"
        self.sprint.empty_sub = "you play; the panel shows where each piece goes"
        self.sprint.shown = 0
        self.sprint.update(None)
        self._show_panels()
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.15, self, "tick:", None, True)

    def toggle_(self, sender):
        if self.bot.running():
            self.bot.stop()
        else:
            _wait_modifiers_released()
            self.bot.start()

    def autoplay_(self, sender):
        self.bot.set_autoplay(sender.state() == AppKit.NSControlStateValueOn)
        self._show_autoplay()

    @objc.python_method
    def _show_autoplay(self):
        on = self.autoplay.state() == AppKit.NSControlStateValueOn
        sprint = self.bot.sprint()
        self.autoplay.setEnabled_(not sprint)
        self.autoplay_note.setStringValue_("sprint: advice only" if sprint else
                                           "on: bot presses keys" if on else "off: suggestions only")

    @objc.python_method
    def _show_panels(self):
        """Blitz: Solve + Next panels. Sprint: the one Sprint panel."""
        sprint = self.bot.sprint()
        for panel, show in ((self.solve, not sprint), (self.next, not sprint), (self.sprint, sprint)):
            if show:
                panel.panel.orderFrontRegardless()
            else:
                panel.panel.orderOut_(None)

    def mode_(self, sender):
        key, label, ready = MODES[sender.selectedSegment()]
        if not ready:                       # placeholders can't be picked yet
            sender.setSelectedSegment_([m[0] for m in MODES].index(self.bot.h.mode if self.bot.h.mode != key else "BLITZ"))
            return
        from dataclasses import replace
        h = replace(self.bot.h, mode=key)
        h.save()
        self.bot.set_handling(h)
        self._show_autoplay()
        self._show_panels()

    def handling_(self, sender):
        if getattr(self, "hwin", None) is None:
            from .settings_ui import HandlingWindow
            self.hwin = HandlingWindow.alloc().initWithBot_(self.bot)
        self.hwin.show()

    def openers_(self, sender):
        if getattr(self, "owin", None) is None:
            from .settings_ui import OpenersWindow
            self.owin = OpenersWindow.alloc().initWithBot_(self.bot)
        self.owin.show()

    def quit_(self, sender):
        self.bot.stop()
        AppKit.NSApp.terminate_(None)

    def tick_(self, timer):
        s = self.bot.status()
        running = self.bot.running()
        self.button.setTitle_("Stop" if running else "Start")
        if s.get("sprint"):                 # sprint: 6-3 advice
            lines = [
                f"{s['state']}  ·  6-3 stacking",
                f"lines {s['lines']}/40   pieces {s['pieces']}   {s['pps']:.2f} pps",
                f"tetrises {s['tetrises']}   followed {s['followed']}/{s['suggested']}",
                s["advice"][:48],
                (s["msg"] or "")[:48],
            ]
        elif "advice" in s:                 # advisor: the user plays
            lines = [
                f"{s['state']}  ·  {s['stage']}",
                f"pieces {s['pieces']}   {s['pps']:.2f} pps   PCs {s['pcs']}",
                f"followed {s['followed']}/{s['suggested']} suggestions",
                s["advice"][:48],
                (s["msg"] or "")[:48],
            ]
        else:
            lines = [
                f"{s['state']}  ·  {s['stage']}{'  ·  high-G' if s['safe'] else ''}"
                + (f"  ·  {s.get('grav', 0):.0f} rows/s" if s.get('grav', 0) >= 5 else ""),
                f"pieces {s['pieces']}   {s['pps']:.2f} pps",
                f"PCs {s['pcs']}   t-spins {s['tspins']}   ghost fixes {s['fixes']}",
                (s["msg"] or "")[:48],
            ]
        self.status.setStringValue_("\n".join(lines))
        if self.bot.sprint():
            self.sprint.update(s.get("display") if s.get("sprint") else None)
        else:
            self.solve.update(s.get("display"))
            self.next.update(s.get("next"))
        if s.get("bag") != self.bagview.info:
            self.bagview.info = s.get("bag")
            self.bagview.setNeedsDisplay_(True)


def run(config=None, overlay=True, handling=None, autoplay=False):
    app = AppKit.NSApplication.sharedApplication()
    app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
    if not accessibility_ok(prompt=True):
        print("! Grant Accessibility permission to this app (System Settings > Privacy & Security > "
              "Accessibility), then restart. Key presses will not reach the browser until then.")
    if not screen_access_ok(prompt=True):
        print("! Grant Screen Recording permission (System Settings > Privacy & Security > "
              "Screen & System Audio Recording), then restart, or the board can't be seen.")
    bot = Bot(config, handling=handling)
    bot.autoplay = autoplay
    keep = []
    if overlay:
        keep.append(Overlay.alloc().initWithBot_(bot))

    def on_hotkey():
        if bot.running():
            bot.stop()
            print("[hotkey] stop")
        else:
            _wait_modifiers_released()
            bot.start()
            print("[hotkey] start")

    if hotkey.register(on_hotkey):
        print("Ready. Press Cmd+Shift+K (or the overlay's Start button) with TETR.IO on screen.")
    else:
        print("! Could not register Cmd+Shift+K; use the overlay button.")
    AppHelper.runEventLoop(installInterrupt=True)
