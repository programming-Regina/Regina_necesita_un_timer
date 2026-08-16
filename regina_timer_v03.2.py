import tkinter as tk
from tkinter import ttk
import winsound
import time
import math

# Regina Timer — v0.3.2
# Windows / Python 3 
# Timer visual diseñado para bajar la fricción de arranque y forzar pausas en el hiperfoco.

BG = "#111318"
PANEL = "#1b1e25"
TEXT = "#f4f4f5"
MUTED = "#9ca3af"
GREEN = "#39d353"
YELLOW = "#f4c542"
RED = "#ef4444"
REST = "#7c5cff"
REST2 = "#ffb347"

class ReginaTimer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Regina Timer")
        self.configure(bg=BG)
        self.geometry("360x540")
        self.minsize(340, 500)
        self.attributes("-topmost", True)

        self.running = False
        self.paused = False
        self.mode = tk.StringVar(value="Ciclos")

        self.minutes = tk.IntVar(value=25)
        self.work_min = tk.IntVar(value=45)
        self.rest_min = tk.IntVar(value=10)
        self.cycles = tk.IntVar(value=3)

        self.cycle_no = 1
        self.phase = "work"
        self.total_seconds = 30 * 60
        self.remaining = self.total_seconds
        self.last_tick = None

        self.reminder_every = tk.IntVar(value=60)
        self.next_reminder = None
        self.reminder_job = None
        self.reminder_active = False
        self.last_reminder_tick = None

        self._build()
        self._set_new_timer()
        self._update_ui()

    def _build(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground=PANEL, background=PANEL,
                        foreground=TEXT, arrowcolor=TEXT)

        # Header 
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=18, pady=(14, 4))

        tk.Label(
            top, text="REGINA NECESITA UN TIMER", bg=BG, fg=TEXT,
            font=("Segoe UI", 13, "bold")
        ).pack(side="left")
        
        self.canvas = tk.Canvas(
            self, width=300, height=300, bg=BG, highlightthickness=0
        )
        self.canvas.pack(pady=(0, 0))

        # Numero dentro del dial para que sea mas compacto
        self.phase_label = tk.Label(
            self, text="TRABAJO", bg=BG, fg=GREEN,
            font=("Segoe UI", 9, "bold")
        )
        # Etiquetas ocultas
        self.phase_label.pack_forget()

        self.time_label = tk.Label(
            self, text="30:00", bg=BG, fg=TEXT,
            font=("Segoe UI", 34, "bold")
        )
        self.time_label.pack_forget()

        self.status_label = tk.Label(
            self, text="Listo", bg=BG, fg=MUTED,
            font=("Segoe UI", 8)
        )
        self.status_label.pack()

        # Controles
        controls = tk.Frame(self, bg=BG)
        controls.pack(fill="x", padx=14, pady=7)

        self.start_btn = tk.Button(
            controls, text="▶  INICIAR", command=self.start,
            bg=GREEN, fg="#07110a", bd=0,
            font=("Segoe UI", 11, "bold"),
            padx=12, pady=9
        )
        self.start_btn.pack(
            side="left", fill="x", expand=True, padx=(0, 4)
        )

        self.pause_btn = tk.Button(
            controls, text="Ⅱ  PAUSA", command=self.pause,
            bg=PANEL, fg=TEXT, bd=0,
            font=("Segoe UI", 10),
            padx=10, pady=9
        )
        self.pause_btn.pack(
            side="left", fill="x", expand=True, padx=4
        )

        self.reset_btn = tk.Button(
            controls, text="↺", command=self.reset,
            bg=PANEL, fg=TEXT, bd=0,
            font=("Segoe UI", 11),
            width=4, pady=9
        )
        self.reset_btn.pack(side="left", padx=(4, 0))

        # Seteos visibles desde el principio
        settings = tk.Frame(self, bg=PANEL)
        settings.pack(fill="x", padx=14, pady=(0, 8))

        mode_row = tk.Frame(settings, bg=PANEL)
        mode_row.pack(fill="x", padx=10, pady=(7, 4))

        tk.Label(
            mode_row, text="Modo", bg=PANEL, fg=TEXT,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        self.mode_combo = ttk.Combobox(
            mode_row, textvariable=self.mode,
            values=["Ciclos", "Tiempo mínimo"],
            state="readonly", width=16
        )
        self.mode_combo.pack(side="right")
        self.mode_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: self._mode_changed()
        )

        self.cycle_frame = tk.Frame(settings, bg=PANEL)
        self.cycle_frame.pack(fill="x", padx=10, pady=2)

        self._spinrow(
            self.cycle_frame, "Trabajo (min)", self.work_min, 1, 240
        )
        self._spinrow(
            self.cycle_frame, "Descanso (min)", self.rest_min, 1, 120
        )
        self._spinrow(
            self.cycle_frame, "Ciclos", self.cycles, 1, 20
        )

        self.single_frame = tk.Frame(settings, bg=PANEL)
        self._spinrow(
            self.single_frame, "Tiempo mínimo (min)", self.minutes, 1, 240
        )

        reminder = tk.Frame(settings, bg=PANEL)
        reminder.pack(fill="x", padx=10, pady=(5, 7))

        tk.Label(
            reminder, text="Aviso agua/postura cada",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 8)
        ).pack(side="left")

        tk.Spinbox(
            reminder, from_=0, to=240, increment=15, width=5,
            textvariable=self.reminder_every,
            bg=BG, fg=TEXT, buttonbackground=PANEL,
            bd=0, relief="flat"
        ).pack(side="right")

        tk.Label(
            reminder, text="min  (0 = apagado)",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 8)
        ).pack(side="right", padx=5)

    def _spinrow(self, parent, label, var, lo, hi):
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", pady=2)

        tk.Label(
            row, text=label, bg=PANEL, fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(side="left")

        tk.Spinbox(
            row, from_=lo, to=hi, width=6,
            textvariable=var, bg=BG, fg=TEXT,
            buttonbackground=PANEL, bd=0, relief="flat"
        ).pack(side="right")

    def _mode_changed(self):
        if self.running:
            return

        self._set_new_timer()

        if self.mode.get() == "Ciclos":
            self.single_frame.pack_forget()
            self.cycle_frame.pack(fill="x", padx=10, pady=2)
        else:
            self.cycle_frame.pack_forget()
            self.single_frame.pack(fill="x", padx=10, pady=2)

        self._update_ui()

    def _set_new_timer(self):
        if self.mode.get() == "Ciclos":
            self.phase = "work"
            self.cycle_no = 1
            self.total_seconds = max(1, self.work_min.get()) * 60
        else:
            self.phase = "work"
            self.total_seconds = max(1, self.minutes.get()) * 60

        self.remaining = self.total_seconds
        self.next_reminder = (
            self.reminder_every.get() * 60
            if self.reminder_every.get() else None
        )

    def start(self):
        if self.running and not self.paused:
            return

        if not self.running:
            self._set_new_timer()

        self.running = True
        self.paused = False
        self.last_tick = time.monotonic()
        self.status_label.config(text="En marcha")
        self._update_buttons()
        self._start_reminder()
        self.after(100, self._tick)

    def pause(self):
        if not self.running:
            return

        if self.paused:
            return

        self.paused = True
        self.status_label.config(text="Pausado")
        self._update_buttons()

    def reset(self):
        self.running = False
        self.paused = False
        self._stop_reminder()
        self._set_new_timer()
        self.status_label.config(text="Listo", fg=MUTED, bg=BG)
        self._update_buttons()
        self._update_ui()

    def _update_buttons(self):
        if self.running and not self.paused:
            self.start_btn.config(
                text="●  EN MARCHA",
                state="disabled",
                bg="#26302a",
                fg="#7fa987"
            )
            self.pause_btn.config(state="normal", text="Ⅱ  PAUSA")
        elif self.running and self.paused:
            self.start_btn.config(
                text="▶  CONTINUAR",
                state="normal",
                bg=GREEN,
                fg="#07110a"
            )
            self.pause_btn.config(state="disabled")
        else:
            self.start_btn.config(
                text="▶  INICIAR",
                state="normal",
                bg=GREEN,
                fg="#07110a"
            )
            self.pause_btn.config(
                state="disabled",
                text="Ⅱ  PAUSA"
            )

    def _tick(self):
        if not self.running or self.paused:
            return

        now = time.monotonic()
        elapsed = now - self.last_tick
        self.last_tick = now
        self.remaining -= elapsed

        if self.remaining <= 0:
            self.remaining = 0
            self._phase_finished()
            return

        self._update_ui()
        self.after(100, self._tick)

    def _phase_finished(self):
        self._soft_beep()

        if self.mode.get() == "Ciclos":
            if self.phase == "work":
                # Fin del trabajo -> descanso.
                self.phase = "rest"
                self.total_seconds = max(1, self.rest_min.get()) * 60
                self.remaining = self.total_seconds
                self.status_label.config(
                    text=f"DESCANSO — ciclo {self.cycle_no}/{self.cycles.get()}"
                )
                self._update_ui()
                self._update_buttons()
                self.after(100, self._tick)
            else:
                # Fin del descanso -> monstruo bailando y empieza el trabajo.
                if self.cycle_no >= self.cycles.get():
                    self.running = False
                    self.status_label.config(text="Ciclos terminados")
                    self._update_buttons()
                    self._celebrate(duration_ms=2800)
                    self._update_ui()
                else:
                    self.cycle_no += 1
                    self.phase = "work"
                    self.total_seconds = max(1, self.work_min.get()) * 60
                    self.remaining = self.total_seconds
                    self.status_label.config(
                        text=f"Trabajo — ciclo {self.cycle_no}/{self.cycles.get()}"
                    )
                    self._update_ui()
                    self._update_buttons()
                    self._celebrate(duration_ms=2600)
                    self.after(100, self._tick)
        else:
            # Modo de tiempo minimo: cero es la base, no el momento de parar.
            self.running = False
            self.status_label.config(
                text="MÍNIMO CUMPLIDO — podés seguir si querés"
            )
            self._update_buttons()
            self._celebrate(duration_ms=2800)
            self._update_ui()

    def _start_reminder(self):
        if self.reminder_active:
            return

        if self.reminder_every.get() <= 0:
            return

        self.reminder_active = True
        self.next_reminder = self.reminder_every.get() * 60
        self.last_reminder_tick = time.monotonic()
        self._schedule_reminder()

    def _schedule_reminder(self):
        if self.reminder_job is not None:
            return

        if self.reminder_active:
            self.reminder_job = self.after(1000, self._reminder_tick)

    def _reminder_tick(self):
        self.reminder_job = None

        if not self.reminder_active:
            return

        if self.paused:
            self.last_reminder_tick = time.monotonic()
            self._schedule_reminder()
            return

        if self.reminder_every.get() <= 0:
            self._stop_reminder()
            return

        now = time.monotonic()
        elapsed = now - self.last_reminder_tick
        self.last_reminder_tick = now

        if self.next_reminder is not None:
            self.next_reminder -= elapsed

        if self.next_reminder is not None and self.next_reminder <= 0:
            self._reminder()
            self.next_reminder = self.reminder_every.get() * 60

        self._schedule_reminder()

    def _stop_reminder(self):
        self.reminder_active = False
        self.next_reminder = None
        self.last_reminder_tick = None

        if self.reminder_job is not None:
            try:
                self.after_cancel(self.reminder_job)
            except Exception:
                pass
            self.reminder_job = None

    def _reminder(self):
        # Notificacion mas suave y corta. no interrumpe el timer.
        try:
            winsound.Beep(520, 90)
        except Exception:
            winsound.MessageBeep(winsound.MB_OK)

        old = self.status_label.cget("text")
        old_fg = self.status_label.cget("fg")
        old_bg = self.status_label.cget("bg")

        self.status_label.config(
            text="HIDRATARSE  ·  CORREGIR POSTURA",
            fg="#000000",
            bg=RED
        )

        self.after(
            5000,
            lambda old=old, old_fg=old_fg, old_bg=old_bg: self.status_label.config(
                text=old if self.running or self.reminder_active else self.status_label.cget("text"),
                fg=old_fg,
                bg=old_bg
            )
        )

    def _soft_beep(self):
        # mas suave.
        try:
            winsound.Beep(440, 90)
            winsound.Beep(554, 110)
        except Exception:
            winsound.MessageBeep(winsound.MB_OK)

    def _celebrate(self, duration_ms=2600):
        # Monstruo que baila
        self._animate_happy(0, max(1, duration_ms // 100))

    def _animate_happy(self, n, max_frames):
        if n >= max_frames:
            self.canvas.delete("happy")
            self._update_ui()
            return

        self.canvas.delete("happy")

        w = self.canvas.winfo_width() or 390
        h = self.canvas.winfo_height() or 390
        cx = w / 2
        cy = h / 2 - 5

        # rebotar.
        phase = n % 8
        sway = [-18, -10, 0, 10, 18, 10, 0, -10][phase]
        bounce = [4, 0, -5, 0, 4, 0, -5, 0][phase]

        # cuerpo y cabeza.
        self.canvas.create_oval(
            cx - 42 + sway, cy - 52 + bounce,
            cx + 42 + sway, cy + 32 + bounce,
            fill=REST, outline="", tags="happy"
        )

        # cara.
        self.canvas.create_oval(
            cx - 20 + sway, cy - 27 + bounce,
            cx - 13 + sway, cy - 20 + bounce,
            fill=TEXT, outline="", tags="happy"
        )
        self.canvas.create_oval(
            cx + 13 + sway, cy - 27 + bounce,
            cx + 20 + sway, cy - 20 + bounce,
            fill=TEXT, outline="", tags="happy"
        )

        # bracitos.
        arm_y = cy + 8 + bounce
        self.canvas.create_line(
            cx - 36 + sway, arm_y,
            cx - 62 + sway, arm_y - (32 if phase in (0,1,2,3) else -8),
            fill=REST, width=7, capstyle="round", tags="happy"
        )
        self.canvas.create_line(
            cx + 36 + sway, arm_y,
            cx + 62 + sway, arm_y - (-8 if phase in (0,1,2,3) else 32),
            fill=REST, width=7, capstyle="round", tags="happy"
        )

        # patas.
        leg_y = cy + 45 + bounce
        self.canvas.create_line(
            cx - 13 + sway, leg_y,
            cx - 28 + sway, leg_y + (30 if phase % 2 == 0 else 12),
            fill=REST, width=7, capstyle="round", tags="happy"
        )
        self.canvas.create_line(
            cx + 13 + sway, leg_y,
            cx + 28 + sway, leg_y + (12 if phase % 2 == 0 else 30),
            fill=REST, width=7, capstyle="round", tags="happy"
        )

        self.canvas.create_text(
            cx, cy + 72,
            text="¡DESCANSO!",
            fill=TEXT,
            font=("Segoe UI", 12, "bold"),
            tags="happy"
        )

        self.after(100, lambda: self._animate_happy(n + 1, max_frames))

    def _draw(self):
        self.canvas.delete("dial")

        w = max(self.canvas.winfo_width(), 300)
        h = max(self.canvas.winfo_height(), 300)
        cx, cy = w / 2, h / 2
        r = min(w, h) * 0.38

        # aro compacto.
        self.canvas.create_oval(
            cx-r, cy-r, cx+r, cy+r,
            outline="#2b303b", width=20, tags="dial"
        )

        if self.total_seconds > 0:
            frac = max(
                0, min(1, self.remaining / self.total_seconds)
            )
            color = self._progress_color(frac)
            extent = 360 * frac

            self.canvas.create_arc(
                cx-r, cy-r, cx+r, cy+r,
                start=90, extent=-extent,
                style="arc", outline=color, width=20,
                tags="dial"
            )

        # marcas de 5 segundos.
        for i in range(0, 60, 5):
            ang = math.radians(i * 6 - 90)
            r1 = r + 10
            r2 = r + 16
            x1 = cx + math.cos(ang) * r1
            y1 = cy + math.sin(ang) * r1
            x2 = cx + math.cos(ang) * r2
            y2 = cy + math.sin(ang) * r2

            self.canvas.create_line(
                x1, y1, x2, y2,
                fill="#303641", width=1, tags="dial"
            )

        # tiempo y fase dentro del dial.
        mins = int(self.remaining) // 60
        secs = int(self.remaining) % 60
        time_color = TEXT
        phase_color = self._progress_color(
            max(0, min(1, self.remaining / self.total_seconds))
            if self.total_seconds else 0
        )
        phase_text = "DESCANSO" if self.phase == "rest" else "TRABAJO"

        self.canvas.create_text(
            cx, cy - 8,
            text=f"{mins:02d}:{secs:02d}",
            fill=time_color,
            font=("Segoe UI", 34, "bold"),
            tags="dial"
        )
        self.canvas.create_text(
            cx, cy + 32,
            text=phase_text,
            fill=phase_color,
            font=("Segoe UI", 9, "bold"),
            tags="dial"
        )

    def _progress_color(self, frac):
        if self.phase == "rest":
            return REST if frac > 0.5 else REST2

        if frac > 0.5:
            return GREEN
        if frac > 0.15:
            return YELLOW
        return RED

    def _update_ui(self):
        mins = int(self.remaining) // 60
        secs = int(self.remaining) % 60
        self.time_label.config(text=f"{mins:02d}:{secs:02d}")

        frac = (
            self.remaining / self.total_seconds
            if self.total_seconds else 0
        )

        if self.phase == "rest":
            self.phase_label.config(
                text="DESCANSO", fg=self._progress_color(frac)
            )
        else:
            self.phase_label.config(
                text="TRABAJO", fg=self._progress_color(frac)
            )

        self._draw()

if __name__ == "__main__":
    app = ReginaTimer()
    app.mainloop()
