import math
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

try:
    import winsound
except ImportError:  # pragma: no cover - fallback non-Windows
    winsound = None


MAX_MS = 85 * 60 * 1000


class Timer:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.remaining_ms = 0
        self.deadline = 0.0
        self.running = False

    def value(self):
        if not self.running:
            return self.remaining_ms
        return max(0, math.ceil((self.deadline - self.clock()) * 1000))

    def add(self, minutes):
        self.remaining_ms = max(0, min(MAX_MS, self.value() + minutes * 60_000))
        if self.running:
            self.deadline = self.clock() + self.remaining_ms / 1000

    def start(self):
        if not self.running and self.remaining_ms > 0:
            self.deadline = self.clock() + self.remaining_ms / 1000
            self.running = True

    def pause(self):
        self.remaining_ms = self.value()
        self.running = False

    def reset(self):
        self.remaining_ms = 0
        self.running = False

    def tick(self):
        if self.running and self.value() == 0:
            self.pause()
            return True
        return False


def format_time(ms):
    seconds = math.ceil(ms / 1000)
    if seconds < 3600:
        return f"{seconds // 60:02}:{seconds % 60:02}"
    return f"{seconds // 3600:02}:{seconds % 3600 // 60:02}:{seconds % 60:02}"


class CuteTimerApp:
    BG = "#0d1015"
    PANEL = "#141820"
    TEXT = "#eeeaf2"
    MUTED = "#aaa5b2"
    PURPLE = "#b99ad9"
    PINK = "#f49ac2"
    GREEN = "#9bd47b"
    YELLOW = "#f7dc78"

    def __init__(self, root):
        self.root = root
        self.timer = Timer()
        self.compact = False
        self.micro = False
        self.finish_until = 0.0
        self.feedback_until = 0.0
        self.feedback_text = ""
        self.gesture_job = None
        self.wheel_active = False
        self.last_second = None
        self.cat_frame = 0
        self.animation_started = time.monotonic()
        pet_dir = Path(__file__).resolve().parent.parent / "desain" / "pets"
        self.cat_images_full = [tk.PhotoImage(file=pet_dir / f"frame-{i:02}.png") for i in range(1, 5)]
        self.cat_images_small = [image.subsample(2) for image in self.cat_images_full]
        self.cat_images_micro = [image.subsample(3) for image in self.cat_images_full]

        root.title("Cute Timer")
        root.configure(bg=self.BG)
        root.geometry("900x620")
        root.minsize(360, 90)
        root.protocol("WM_DELETE_WINDOW", root.destroy)

        self.full = tk.Frame(root, bg=self.BG, padx=30, pady=20)
        self.small = tk.Frame(root, bg=self.BG, padx=10, pady=6)
        self.micro_view = tk.Frame(root, bg=self.BG, padx=4)
        self._build_full()
        self._build_compact()
        self._build_micro()
        for canvas in (self.display_small, self.display_micro):
            canvas.bind("<Double-Button-1>", self._on_double_click)
            canvas.bind("<Triple-Button-1>", self._on_triple_click)

        root.bind("<space>", lambda _e: self.start())
        root.bind("<Key-p>", lambda _e: self.pause())
        root.bind("<Key-r>", lambda _e: self.reset())
        root.bind("<Key-a>", lambda _e: self.show_add_menu())
        root.bind("<Key-1>", lambda _e: self.add(10))
        root.bind("<Key-2>", lambda _e: self.add(15))
        root.bind("<Key-3>", lambda _e: self.add(20))
        root.bind("<Key-h>", lambda _e: self.help())
        root.bind("<Key-m>", lambda _e: self.set_compact(True) if self.micro else self.set_micro())
        root.bind("<Key-q>", lambda _e: root.destroy())
        root.bind("<Configure>", self._on_resize)

        self._show_mode(False)
        self._update()

    def _button(self, parent, text, command, small=False):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=self.PANEL,
            fg=self.TEXT,
            activebackground="#252b36",
            activeforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground="#736c7c",
            font=("Consolas", 8 if small else 11),
            padx=3 if small else 14,
            pady=4 if small else 10,
            cursor="hand2",
            takefocus=True,
        )

    def _build_full(self):
        header = tk.Frame(self.full, bg=self.BG)
        header.pack(fill="x")
        tk.Label(header, text="✿ Welcome to Cute Timer! ✿", bg=self.BG, fg=self.PINK, font=("Consolas", 14, "bold")).pack(side="left")
        self._button(header, "▣ COMPACT", lambda: self.set_compact(True)).pack(side="right")
        self._button(header, "▣ MICRO", self.set_micro).pack(side="right", padx=6)
        tk.Label(self.full, text="Ketik 'h' untuk bantuan", bg=self.BG, fg=self.MUTED, font=("Consolas", 10)).pack(anchor="w")

        hero = tk.Frame(self.full, bg=self.BG)
        hero.pack(pady=(12, 8))
        tk.Label(hero, text="╭──────────────────╮\n│ Ayo semangat! 💪  │\n│ Kamu pasti bisa! ✨│\n╰──────────────────╯", justify="left", bg=self.BG, fg=self.PURPLE, font=("Consolas", 11)).pack(side="left", padx=18)
        timer_panel = tk.Frame(self.full, bg=self.PANEL, highlightthickness=1, highlightbackground="#8a8190")
        timer_panel.pack(fill="both", expand=True, padx=80, pady=6)
        self.display_full = tk.Canvas(timer_panel, height=150, bg=self.PANEL, highlightthickness=0)
        self.display_full.pack(fill="both", expand=True, padx=15, pady=(12, 0))
        self.units_full = tk.Label(timer_panel, bg=self.PANEL, fg=self.MUTED, font=("Consolas", 10))
        self.units_full.pack(pady=(0, 10))

        controls = tk.Frame(self.full, bg=self.BG)
        controls.pack(pady=12)
        for text, command in (("▶ START\n(spasi)", self.start), ("Ⅱ PAUSE\n(p)", self.pause), ("↻ RESET\n(r)", self.reset), ("＋10 MENIT", lambda: self.add(10)), ("＋15 MENIT", lambda: self.add(15)), ("＋20 MENIT", lambda: self.add(20))):
            self._button(controls, text, command).pack(side="left", padx=5)

        self.status_full = tk.Label(self.full, bg=self.BG, fg=self.PURPLE, font=("Consolas", 12, "bold"))
        self.status_full.pack()
        tk.Label(self.full, text="💡 Fokus pada proses, hasil akan mengikuti. ✨   Maksimum 01:25:00", bg=self.BG, fg=self.MUTED, font=("Consolas", 10)).pack(side="bottom", pady=(8, 0))

    def _build_compact(self):
        self.display_small = tk.Canvas(self.small, bg=self.BG, highlightthickness=0)
        self.display_small.pack(fill="both", expand=True)

    def _build_micro(self):
        restore = self._button(self.micro_view, "×", lambda: self.set_compact(True), small=True)
        restore.pack(side="left", fill="y")
        grip = tk.Label(self.micro_view, text="⠿", bg=self.BG, fg=self.MUTED, cursor="fleur", font=("Consolas", 12))
        grip.pack(side="left", padx=4)
        self.display_micro = tk.Canvas(self.micro_view, bg=self.BG, highlightthickness=0)
        self.display_micro.pack(side="left", fill="both", expand=True)
        for widget in (grip, self.display_micro):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._drag)

    def _on_double_click(self, _event):
        self._cancel_double_click()
        self.gesture_job = self.root.after(250, self._toggle_from_gesture)

    def _on_triple_click(self, event):
        self._cancel_double_click()
        minutes = 10 if event.x >= event.widget.winfo_width() / 2 else -10
        self._show_feedback("+10" if minutes > 0 else "−10")
        self.add(minutes)

    def _cancel_double_click(self):
        if self.gesture_job:
            self.root.after_cancel(self.gesture_job)
            self.gesture_job = None

    def _toggle_from_gesture(self):
        self.gesture_job = None
        if self.timer.running:
            self._show_feedback("STOP")
            self.pause(wheel=True)
        else:
            self._show_feedback("PLAY")
            self.start()

    def _show_feedback(self, text):
        self.feedback_text = text
        self.feedback_until = time.monotonic() + 1.2

    def _start_drag(self, event):
        self.drag_offset = event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y()

    def _drag(self, event):
        self.root.geometry(f"+{event.x_root - self.drag_offset[0]}+{event.y_root - self.drag_offset[1]}")

    def _on_resize(self, event):
        if event.widget is self.root and not self.micro:
            should_compact = event.width < 600 or event.height < 420
            if should_compact != self.compact:
                self._show_mode(should_compact)

    def _show_mode(self, compact, micro=False):
        self.compact = compact
        self.micro = micro
        self.root.attributes("-topmost", compact)
        self.root.overrideredirect(micro)
        self.root.minsize(1, 1) if micro else self.root.minsize(360, 90)
        self.full.pack_forget()
        self.small.pack_forget()
        self.micro_view.pack_forget()
        (self.micro_view if micro else self.small if compact else self.full).pack(fill="both", expand=True)
        self.root.after_idle(self._draw_time)

    def set_compact(self, compact):
        self._show_mode(compact)
        self.root.geometry("480x105" if compact else "900x620")

    def set_micro(self):
        self._show_mode(True, micro=True)
        self.root.geometry("240x52")

    def start(self):
        self.wheel_active = False
        self.timer.start()
        self._refresh_text()

    def pause(self, wheel=False):
        self.wheel_active = wheel
        self.timer.pause()
        self._refresh_text()

    def reset(self):
        self.wheel_active = False
        self.timer.reset()
        self.finish_until = 0
        self._refresh_text()

    def add(self, minutes):
        self.timer.add(minutes)
        self.finish_until = 0
        self._refresh_text()

    def show_add_menu(self):
        menu = tk.Menu(self.root, tearoff=False, bg=self.PANEL, fg=self.TEXT, activebackground=self.PURPLE)
        for minutes in (10, 15, 20):
            menu.add_command(label=f"+{minutes} menit", command=lambda m=minutes: self.add(m))
        menu.tk_popup(self.root.winfo_rootx() + self.root.winfo_width() // 2, self.root.winfo_rooty() + self.root.winfo_height() // 2)

    def help(self):
        messagebox.showinfo("Bantuan Cute Timer", "Klik +10/+15/+20, lalu START.\n\nSpace: mulai\nP: jeda\nR: reset\nA: menu tambah waktu\n1/2/3: tambah 10/15/20 menit\nM: buka/tutup Micro\nDouble-click timer: jeda/lanjut\nTriple-click kiri/kanan: −10/+10 menit\nQ: keluar")

    def _finish(self):
        self.finish_until = time.monotonic() + 6
        if winsound:
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
        else:
            self.root.bell()

    def _status(self):
        if time.monotonic() < self.finish_until:
            return "✨ FINISH! Hebat! ✨"
        if self.timer.running:
            return "● BERJALAN"
        return "Ⅱ JEDA" if self.timer.value() else "○ SIAP"

    def _refresh_text(self):
        status = self._status()
        color = self.GREEN if self.timer.running else self.YELLOW if self.finish_until > time.monotonic() else self.PURPLE
        self.status_full.configure(text=status, fg=color)
        self.units_full.configure(text="JAM   :   MENIT   :   DETIK" if format_time(self.timer.value()).count(":") == 2 else "MENIT   :   DETIK")
        self._draw_time()

    def _draw_time(self):
        text = format_time(self.timer.value())
        for canvas in (self.display_full, self.display_small, self.display_micro):
            if canvas.winfo_ismapped():
                if canvas is self.display_small and time.monotonic() < self.finish_until:
                    self._draw_finish(canvas)
                else:
                    self._seven_segment(canvas, text)
                    self._draw_wheel(canvas) if self._wheel_size(canvas) else self._draw_cat(canvas)
                    if canvas is not self.display_full and time.monotonic() < self.feedback_until:
                        self._draw_feedback(canvas)

    def _draw_finish(self, canvas):
        canvas.delete("all")
        width = max(canvas.winfo_width(), 200)
        height = max(canvas.winfo_height(), 40 if canvas is self.display_micro else 60)
        elapsed = 6 - max(0, self.finish_until - time.monotonic())
        images = self.cat_images_micro if canvas is self.display_micro else self.cat_images_small
        cat = images[int(elapsed * 8) % len(images)]
        x = -cat.width() + (width + cat.width()) * (elapsed % 3.5) / 3.5
        canvas.create_image(x, height / 2, image=cat, anchor="w")
        for cx, cy, delay in ((width * .23, height * .35, 0), (width * .72, height * .3, .55)):
            burst = (elapsed - delay) % 1.5
            if burst < .8:
                radius = 8 + burst * 30
                for angle in range(0, 360, 45):
                    dx, dy = math.cos(math.radians(angle)), math.sin(math.radians(angle))
                    canvas.create_line(cx + dx * radius * .55, cy + dy * radius * .55,
                                       cx + dx * radius, cy + dy * radius,
                                       fill=self.PINK if angle % 90 else self.YELLOW, width=2)

    def _draw_cat(self, canvas):
        compact = canvas is not self.display_full
        images = self.cat_images_micro if canvas is self.display_micro else self.cat_images_small if compact else self.cat_images_full
        cat = images[self.cat_frame]
        if canvas is self.display_micro:
            progress = ((time.monotonic() - self.animation_started) % 4) / 4
            x = canvas.winfo_width() - cat.width() - 8 + 6 * progress
            canvas.create_image(x, (canvas.winfo_height() - cat.height()) / 2, image=cat, anchor="nw", tags="walking-cat")
            return
        width = max(canvas.winfo_width(), 200)
        duration = 5 if compact else 8
        progress = ((time.monotonic() - self.animation_started) % duration) / duration
        x = -cat.width() + (width + cat.width()) * progress
        canvas.create_image(x, 0, image=cat, anchor="nw", tags="walking-cat")

    def _wheel_size(self, canvas):
        return 36 if canvas is self.display_micro else 64 if canvas is self.display_small and self.wheel_active else 0

    def _draw_wheel(self, canvas):
        diameter = self._wheel_size(canvas)
        radius = diameter / 2
        cx, cy = canvas.winfo_width() - radius - 3, canvas.winfo_height() / 2
        canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                           outline=self.PINK, width=2, tags="cat-wheel")
        rotation = (time.monotonic() - self.animation_started) * 180
        for angle in range(0, 360, 60):
            dx = math.cos(math.radians(angle + rotation)) * (radius - 3)
            dy = math.sin(math.radians(angle + rotation)) * (radius - 3)
            canvas.create_line(cx, cy, cx + dx, cy + dy, fill=self.PURPLE, width=1, tags="wheel-spoke")
        images = self.cat_images_micro if canvas is self.display_micro else self.cat_images_small
        canvas.create_image(cx, cy, image=images[self.cat_frame], tags="walking-cat")

    def _draw_feedback(self, canvas):
        progress = 1 - max(0, self.feedback_until - time.monotonic()) / 1.2
        wheel_size = self._wheel_size(canvas)
        x = 16 if self.feedback_text == "−10" else canvas.winfo_width() - (wheel_size + 28 if wheel_size else 24)
        feedback = canvas.create_text(x, canvas.winfo_height() / 2 - progress * 12,
                                      text=self.feedback_text, fill=self.YELLOW if self.cat_frame % 2 else self.PINK,
                                      font=("Consolas", 9 if canvas is self.display_micro else 14, "bold"),
                                      tags="action-feedback")
        left, top, right, bottom = canvas.bbox(feedback)
        background = canvas.create_rectangle(left - 3, top - 1, right + 3, bottom + 1,
                                             fill=self.BG, outline=self.PURPLE, tags="feedback-background")
        canvas.tag_lower(background, feedback)

    def _seven_segment(self, canvas, text):
        canvas.delete("all")
        micro = canvas is self.display_micro
        width = canvas.winfo_width() if micro else max(canvas.winfo_width(), 200)
        height = max(canvas.winfo_height(), 40 if canvas is self.display_micro else 60)
        wheel_size = self._wheel_size(canvas)
        cat_height = 0 if wheel_size else 28 if canvas is self.display_small else 56
        timer_width = width - wheel_size - 8 if wheel_size else width
        scale = min(timer_width / 460, max((height - cat_height - 12) / 89, .25))
        digit_w, digit_h, thick, gap = 42 * scale, 82 * scale, 7 * scale, 10 * scale
        total = sum(char.isdigit() for char in text) * digit_w + text.count(":") * 14 * scale + (len(text) - 1) * gap
        x = (timer_width - total) / 2
        y = cat_height + 4 + max(0, (height - cat_height - 4 - digit_h) / 2)
        segments = {
            "0": "abcedf", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg",
            "5": "acdfg", "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg",
        }
        # ponytail: polygons stay local; a custom widget is unnecessary for one display.
        def line(x1, y1, x2, y2):
            canvas.create_line(x1, y1, x2, y2, fill=self.TEXT, width=thick, capstyle=tk.ROUND)

        for char in text:
            if char == ":":
                radius = 3.5 * scale
                for cy in (y + digit_h * .34, y + digit_h * .68):
                    canvas.create_oval(x, cy - radius, x + radius * 2, cy + radius, fill=self.PINK, outline="")
                x += 14 * scale + gap
                continue
            active = segments[char]
            coords = {
                "a": (x + thick, y, x + digit_w - thick, y),
                "b": (x + digit_w, y + thick, x + digit_w, y + digit_h / 2 - thick),
                "c": (x + digit_w, y + digit_h / 2 + thick, x + digit_w, y + digit_h - thick),
                "d": (x + thick, y + digit_h, x + digit_w - thick, y + digit_h),
                "e": (x, y + digit_h / 2 + thick, x, y + digit_h - thick),
                "f": (x, y + thick, x, y + digit_h / 2 - thick),
                "g": (x + thick, y + digit_h / 2, x + digit_w - thick, y + digit_h / 2),
            }
            for name in active:
                line(*coords[name])
            x += digit_w + gap

    def _update(self):
        if self.timer.tick():
            self._finish()
        second = math.ceil(self.timer.value() / 1000)
        frame = int((time.monotonic() - self.animation_started) * 8) % 4
        if second != self.last_second or frame != self.cat_frame:
            self.last_second, self.cat_frame = second, frame
            self._refresh_text()
        elif time.monotonic() < self.finish_until:
            self._draw_time()
        self.root.after(100, self._update)


def self_test():
    now = [10.0]
    timer = Timer(lambda: now[0])
    assert format_time(0) == "00:00"
    assert format_time(3_599_000) == "59:59"
    assert format_time(3_600_000) == "01:00:00"
    timer.add(10)
    timer.start()
    now[0] += 2
    assert timer.value() == 598_000
    timer.add(20)
    assert timer.value() == 1_798_000
    timer.add(100)
    assert timer.value() == MAX_MS
    timer.pause()
    now[0] += 2
    assert timer.value() == MAX_MS
    timer.reset()
    assert timer.value() == 0 and not timer.running
    timer.add(10)
    timer.start()
    now[0] += 600
    assert timer.tick() and timer.value() == 0
    timer.add(-10)
    assert timer.value() == 0
    print("Self-test desktop timer: OK")


def ui_self_test():
    root = tk.Tk()
    root.withdraw()
    app = CuteTimerApp(root)
    root.update()

    def buttons(widget):
        return [child for child in widget.winfo_children() for child in ([child] if isinstance(child, tk.Button) else []) + buttons(child)]

    def label_texts(widget):
        return [child.cget("text") for child in widget.winfo_children() if isinstance(child, tk.Label)] + [text for child in widget.winfo_children() for text in label_texts(child)]

    click_time = 1_000

    def click(widget, count, x=20):
        nonlocal click_time
        for index in range(count):
            event_time = click_time + index * 50
            widget.event_generate("<ButtonPress-1>", x=x, y=20, time=event_time)
            widget.event_generate("<ButtonRelease-1>", x=x, y=20, time=event_time + 10)
        click_time += 1_000

    controls = {button.cget("text"): button for button in buttons(root)}
    controls["＋10 MENIT"].invoke()
    assert app.timer.value() == 600_000
    controls["▶ START\n(spasi)"].invoke()
    assert app.timer.running
    controls["Ⅱ PAUSE\n(p)"].invoke()
    assert not app.timer.running
    controls["↻ RESET\n(r)"].invoke()
    assert app.timer.value() == 0
    controls["＋15 MENIT"].invoke()
    controls["＋20 MENIT"].invoke()
    assert app.timer.value() == 2_100_000
    assert "MENIT   :   DETIK" in label_texts(root)
    app.add(100)
    assert "JAM   :   MENIT   :   DETIK" in label_texts(root)
    app.reset()
    app.add(15)
    app.add(20)
    root.deiconify()
    app.set_compact(False)
    root.update()
    app._draw_time()
    assert len(app.cat_images_full) == len(app.cat_images_small) == len(app.cat_images_micro) == 4
    assert (app.cat_images_full[0].width(), app.cat_images_full[0].height()) == (84, 56)
    assert (app.cat_images_small[0].width(), app.cat_images_small[0].height()) == (42, 28)
    first_x = app.display_full.coords(app.display_full.find_withtag("walking-cat")[0])[0]
    app.animation_started -= 1
    app._draw_time()
    second_x = app.display_full.coords(app.display_full.find_withtag("walking-cat")[0])[0]
    assert second_x > first_x
    app.set_compact(True)
    root.update()
    assert app.compact and app.small.winfo_manager() == "pack"
    assert bool(root.attributes("-topmost"))
    assert (root.winfo_width(), root.winfo_height()) == (480, 105)
    assert not buttons(app.small)
    app._draw_time()
    assert app.display_small.find_withtag("walking-cat")
    app._seven_segment(app.display_small, "35:00")
    timer_bbox = app.display_small.bbox("all")
    assert abs((timer_bbox[0] + timer_bbox[2]) / 2 - app.display_small.winfo_width() / 2) <= 2
    controls["▣ MICRO"].invoke()
    root.update()
    timer_area_width = app.display_micro.winfo_width() - app._wheel_size(app.display_micro) - 8
    for text in ("35:00", "01:05:00"):
        app._seven_segment(app.display_micro, text)
        timer_bbox = app.display_micro.bbox("all")
        assert abs((timer_bbox[0] + timer_bbox[2]) / 2 - timer_area_width / 2) <= 2
    app._draw_time()
    assert app.compact and app.micro and bool(root.overrideredirect())
    assert (root.winfo_width(), root.winfo_height()) == (240, 52)
    assert app.display_micro.find_withtag("cat-wheel")
    assert bool(root.attributes("-topmost")) and app.display_micro.find_withtag("walking-cat")
    assert app.display_micro.bbox("all")[3] < app.display_micro.winfo_height()
    app.animation_started = time.monotonic()
    app._seven_segment(app.display_micro, "35:00")
    timer_bbox = app.display_micro.bbox("all")
    app._draw_wheel(app.display_micro)
    cat_id = app.display_micro.find_withtag("walking-cat")[0]
    cat_bbox = app.display_micro.bbox(cat_id)
    wheel_bbox = app.display_micro.bbox("cat-wheel")
    first_spoke = app.display_micro.coords(app.display_micro.find_withtag("wheel-spoke")[0])
    assert timer_bbox[2] < wheel_bbox[0] and wheel_bbox[0] < cat_bbox[0] < cat_bbox[2] < wheel_bbox[2]
    app.animation_started -= .5
    app._seven_segment(app.display_micro, "35:00")
    app._draw_wheel(app.display_micro)
    second_spoke = app.display_micro.coords(app.display_micro.find_withtag("wheel-spoke")[0])
    assert second_spoke != first_spoke
    app.start()
    click(app.display_micro, 2)
    root.after(300, root.quit)
    root.mainloop()
    assert app.micro and not app.timer.running
    next(button for button in buttons(app.micro_view) if button.cget("text") == "×").invoke()
    root.update()
    assert not app.micro and not bool(root.overrideredirect()) and 2_099_000 <= app.timer.value() <= 2_100_000
    app.start()
    before = app.timer.value()
    click(app.display_small, 3, app.display_small.winfo_width() - 5)
    root.after(300, root.quit)
    root.mainloop()
    gained = app.timer.value() - before
    assert app.timer.running and 599_000 <= gained <= 600_000
    app._draw_time()
    plus_feedback = app.display_small.find_withtag("action-feedback")
    assert plus_feedback and app.display_small.itemcget(plus_feedback[0], "text") == "+10"
    first_feedback_y = app.display_small.coords(plus_feedback[0])[1]
    app.feedback_until -= .2
    app._draw_time()
    assert app.display_small.coords(app.display_small.find_withtag("action-feedback")[0])[1] < first_feedback_y
    before = app.timer.value()
    click(app.display_small, 3)
    root.after(300, root.quit)
    root.mainloop()
    lost = before - app.timer.value()
    assert app.timer.running and 600_000 <= lost <= 601_000
    app._draw_time()
    minus_feedback = app.display_small.find_withtag("action-feedback")
    assert minus_feedback and app.display_small.itemcget(minus_feedback[0], "text") == "−10"
    assert app.display_small.coords(minus_feedback[0])[0] < app.display_small.winfo_width() / 2
    click(app.display_small, 2)
    root.after(300, root.quit)
    root.mainloop()
    app._draw_time()
    assert not app.timer.running and app.display_small.find_withtag("cat-wheel")
    stop_feedback = app.display_small.find_withtag("action-feedback")
    assert stop_feedback and app.display_small.itemcget(stop_feedback[0], "text") == "STOP"
    click(app.display_small, 2)
    root.after(300, root.quit)
    root.mainloop()
    app._draw_time()
    assert app.timer.running and not app.display_small.find_withtag("cat-wheel")
    play_feedback = app.display_small.find_withtag("action-feedback")
    assert play_feedback and app.display_small.itemcget(play_feedback[0], "text") == "PLAY"
    app.finish_until = time.monotonic() + 6
    app._draw_time()
    assert app.display_small.find_all()
    assert winsound is not None
    root.destroy()
    print("Self-test UI desktop: OK")


if __name__ == "__main__":
    if "--ui-self-test" in sys.argv:
        ui_self_test()
    elif "--self-test" in sys.argv:
        self_test()
    else:
        window = tk.Tk()
        CuteTimerApp(window)
        window.mainloop()
