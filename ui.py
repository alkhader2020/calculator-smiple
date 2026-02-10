import tkinter as tk
from engine import safe_calculate
from utils import fmt_number


class Button3D(tk.Frame):
    def __init__(
        self,
        parent,
        text,
        command,
        w=74,
        h=52,
        face="#7a7a7a",
        top="#9a9a9a",
        shadow="#111111",
        fg="white",
        font=("Segoe UI", 10, "bold"),
        press_offset=2,
        label_relx=0.5,
    ):
        super().__init__(parent, width=w, height=h, bg=parent["bg"])
        self.command = command
        self.w, self.h = w, h
        self.face = face
        self.top = top
        self.shadow = shadow
        self.press_offset = press_offset
        self.label_relx = label_relx

        self.pack_propagate(False)

        # Softer shadow
        self.shadow_frame = tk.Frame(self, bg=shadow)
        self.shadow_frame.place(x=2, y=2, width=w, height=h)

        # Face
        self.face_frame = tk.Frame(self, bg=face)
        self.face_frame.place(x=0, y=0, width=w, height=h)

        # Top highlight (fake gradient)
        self.top_strip = tk.Frame(self.face_frame, bg=top)
        self.top_strip.place(x=0, y=0, width=w, height=int(h * 0.38))

        # Text
        self.label = tk.Label(self.face_frame, text=text, bg=face, fg=fg, font=font)
        self.label.place(relx=self.label_relx, rely=0.55, anchor="center")

        # Bindings
        for widget in (self, self.face_frame, self.label, self.top_strip):
            widget.bind("<Enter>", self.on_enter)
            widget.bind("<Leave>", self.on_leave)
            widget.bind("<ButtonPress-1>", self.on_press)
            widget.bind("<ButtonRelease-1>", self.on_release)

        self._hovered = False
        self._pressed = False

    def on_enter(self, _):
        self._hovered = True
        if not self._pressed:
            hover = self._mix(self.face, "#ffffff", 0.08)
            self.face_frame.configure(bg=hover)
            self.label.configure(bg=hover)

    def on_leave(self, _):
        self._hovered = False
        if not self._pressed:
            self.face_frame.configure(bg=self.face)
            self.label.configure(bg=self.face)

    def on_press(self, _):
        self._pressed = True
        self.face_frame.place_configure(x=self.press_offset, y=self.press_offset)

    def on_release(self, _):
        self._pressed = False
        self.face_frame.place_configure(x=0, y=0)

        # click only if still hovered
        x, y = self.winfo_pointerxy()
        if self.winfo_containing(x, y) in (self, self.face_frame, self.label, self.top_strip):
            self.command()

        # restore hover/normal
        if self._hovered:
            self.on_enter(None)
        else:
            self.on_leave(None)

    def _mix(self, c1, c2, t):
        def h2rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

        def rgb2h(rgb):
            return "#{:02x}{:02x}{:02x}".format(*rgb)

        r1, g1, b1 = h2rgb(c1)
        r2, g2, b2 = h2rgb(c2)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return rgb2h((r, g, b))


class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculator Pro - 3D")
        self.root.resizable(False, False)

        self.expr = ""
        self.last_result = None
        self.mem = 0.0

        # Body + LCD
        self.BODY_BG = "#1a1a1a"
        self.LCD_BG = "#e8f4f8"
        self.LCD_TEXT = "#003333"

        root.configure(bg=self.BODY_BG)

        # Bezel
        self.bezel = tk.Frame(
            root,
            bg="#0d0d0d",
            highlightthickness=1,
            highlightbackground="#333333"
        )
        self.bezel.pack(padx=10, pady=10, fill="both", expand=True)

        # ---------------- LCD (Improved: padding + reflection) ----------------
        display_frame = tk.Frame(self.bezel, bg=self.BODY_BG, height=92)
        display_frame.pack(padx=8, pady=8, fill="x")
        display_frame.pack_propagate(False)

        # Inner shadow (recess)
        recess = tk.Frame(display_frame, bg="#0b0b0b")
        recess.pack(fill="both", expand=True, padx=1, pady=1)

        lcd_panel = tk.Frame(
            recess,
            bg=self.LCD_BG,
            highlightthickness=1,
            highlightbackground="#7a7a7a"
        )
        lcd_panel.pack(fill="both", expand=True, padx=6, pady=6)

        # Reflection layers (stronger / premium feel)
        reflection1 = tk.Frame(lcd_panel, bg="#f7fbff")
        reflection1.place(x=0, y=0, relwidth=1, height=12)
        reflection2 = tk.Frame(lcd_panel, bg="#ffffff")
        reflection2.place(x=0, y=12, relwidth=1, height=6)
        reflection2.configure(bg="#f1f8ff")

        self.expr_label = tk.Label(
            lcd_panel, text="",
            bg=self.LCD_BG, fg="#667085",
            font=("Consolas", 9), anchor="e"
        )
        self.expr_label.pack(fill="x", padx=16, pady=(10, 0))  # ✅ more right padding

        self.res_label = tk.Label(
            lcd_panel, text="0",
            bg=self.LCD_BG, fg=self.LCD_TEXT,
            font=("Consolas", 26, "bold"), anchor="e"
        )
        self.res_label.pack(fill="x", padx=16, pady=(0, 2))   # ✅ more right padding

        self.err_label = tk.Label(
            lcd_panel, text="",
            bg=self.LCD_BG, fg="#c41e3a",
            font=("Consolas", 8), anchor="w"
        )
        self.err_label.pack(fill="x", padx=16, pady=(0, 10))

        # ---------------- Button pad ----------------
        pad = tk.Frame(self.bezel, bg=self.BODY_BG)
        pad.pack(padx=8, pady=(0, 8), fill="both", expand=True)

        for c in range(4):
            pad.columnconfigure(c, weight=1)

        def lighten(hex_color, factor=0.18):
            r = int(int(hex_color[1:3], 16) + (255 - int(hex_color[1:3], 16)) * factor)
            g = int(int(hex_color[3:5], 16) + (255 - int(hex_color[3:5], 16)) * factor)
            b = int(int(hex_color[5:7], 16) + (255 - int(hex_color[5:7], 16)) * factor)
            return f"#{r:02x}{g:02x}{b:02x}"

        def ui_to_engine(key: str) -> str:
            return {"×": "*", "÷": "/"}.get(key, key)

        # ✅ Improved colors (numbers higher contrast)
        NUM_FACE = "#cfcfcf"     # a bit brighter than before
        OP_FACE = "#2a2a2a"
        MEM_FACE = "#4a7ba7"
        CLR_FACE = "#c41e3a"
        EQ_FACE  = "#2d5016"

        layout = [
            [("MC", MEM_FACE, "white", 1, 1), ("MR", MEM_FACE, "white", 1, 1), ("M+", MEM_FACE, "white", 1, 1), ("M-", MEM_FACE, "white", 1, 1)],
            [("C",  CLR_FACE, "white", 1, 1), ("⌫", OP_FACE, "white", 1, 1), ("±", OP_FACE, "white", 1, 1), ("%", OP_FACE, "white", 1, 1)],
            [("(",  OP_FACE, "white", 1, 1), (")",  OP_FACE, "white", 1, 1), ("^", OP_FACE, "white", 1, 1), ("÷", OP_FACE, "white", 1, 1)],
            [("7",  NUM_FACE, "#333", 1, 1), ("8",  NUM_FACE, "#333", 1, 1), ("9",  NUM_FACE, "#333", 1, 1), ("×", OP_FACE, "white", 1, 1)],
            [("4",  NUM_FACE, "#333", 1, 1), ("5",  NUM_FACE, "#333", 1, 1), ("6",  NUM_FACE, "#333", 1, 1), ("-", OP_FACE, "white", 1, 1)],
            [("1",  NUM_FACE, "#333", 1, 1), ("2",  NUM_FACE, "#333", 1, 1), ("3",  NUM_FACE, "#333", 1, 1), ("+", OP_FACE, "white", 1, 1)],
            [("0",  NUM_FACE, "#333", 2, 1), (".",  NUM_FACE, "#333", 1, 1), ("=", EQ_FACE,  "white", 1, 2)],
        ]

        occupied = set()

        for r, row in enumerate(layout):
            c = 0
            for (key, face, fg, colspan, rowspan) in row:
                while (r, c) in occupied:
                    c += 1

                # ✅ Better highlights:
                # numbers: stronger top highlight
                if face == NUM_FACE:
                    top_color = lighten(face, 0.28)
                elif face == EQ_FACE:
                    top_color = lighten(face, 0.32)  # ✅ "=" highlight stronger
                else:
                    top_color = lighten(face, 0.18)

                shadow = "#121212"  # ✅ softer shadow than before

                engine_key = ui_to_engine(key)

                # ✅ Bigger font for × ÷
                if key in ("×", "÷"):
                    font = ("Segoe UI", 12, "bold")
                else:
                    font = ("Segoe UI", 10, "bold")

                # ✅ 0 text a bit left (like real calculators)
                label_relx = 0.40 if key == "0" else 0.5

                # ✅ "=" deeper press
                press_offset = 3 if key == "=" else 2

                btn = Button3D(
                    pad,
                    text=key,
                    command=lambda k=engine_key: self.on_button(k),
                    w=74 * colspan + 6 * (colspan - 1),
                    h=52 * rowspan + 6 * (rowspan - 1),
                    face=face,
                    top=top_color,
                    shadow=shadow,
                    fg=fg,
                    font=font,
                    press_offset=press_offset,
                    label_relx=label_relx
                )
                btn.grid(row=r, column=c, columnspan=colspan, rowspan=rowspan, padx=3, pady=3, sticky="nsew")

                if rowspan > 1:
                    for rr in range(r + 1, r + rowspan):
                        for cc in range(c, c + colspan):
                            occupied.add((rr, cc))

                c += colspan

        # Keyboard binds
        root.bind("<Return>", lambda e: self.on_button("="))
        root.bind("<BackSpace>", lambda e: self.on_button("⌫"))
        root.bind("<Escape>", lambda e: self.on_button("C"))
        for ch in "0123456789+-*/().^":
            root.bind(ch, self.on_key_typed)
        root.bind("%", self.on_key_typed)

        self.refresh()

    def on_key_typed(self, event):
        if event.char:
            self.on_button(event.char)

    def set_error(self, msg: str):
        self.err_label.config(text=msg)

    def clear_error(self):
        self.err_label.config(text="")

    def _fit_result_text(self, text: str, max_len: int = 14) -> str:
        text = str(text)
        if len(text) <= max_len:
            return text
        try:
            x = float(text.replace(",", ""))
            return f"{x:.10g}"
        except Exception:
            return text[:max_len]

    def refresh(self):
        if self.last_result is not None:
            self.res_label.config(text=self._fit_result_text(fmt_number(self.last_result)))
        else:
            self.res_label.config(text="0")
        self.expr_label.config(text=self.expr)

    def on_button(self, t: str):
        self.clear_error()

        if t == "C":
            self.expr = ""
            self.last_result = None
            self.refresh()
            return

        if t == "⌫":
            self.expr = self.expr[:-1]
            self.refresh()
            return

        if t == "MC":
            self.mem = 0.0
            self.set_error("Memory cleared")
            return

        if t == "MR":
            self.expr += fmt_number(self.mem)
            self.refresh()
            return

        if t == "M+":
            if self.last_result is not None:
                self.mem += float(self.last_result)
                self.set_error(f"Memory = {fmt_number(self.mem)}")
            else:
                self.set_error("No result")
            return

        if t == "M-":
            if self.last_result is not None:
                self.mem -= float(self.last_result)
                self.set_error(f"Memory = {fmt_number(self.mem)}")
            else:
                self.set_error("No result")
            return

        if t == "±":
            if not self.expr:
                self.expr = "-"
                self.refresh()
                return

            i = len(self.expr) - 1
            while i >= 0 and (self.expr[i].isdigit() or self.expr[i] == "."):
                i -= 1
            start = i + 1

            if start == len(self.expr):
                self.expr += "-"
            else:
                if start > 0 and self.expr[start - 1] == "-" and (start - 2 < 0 or self.expr[start - 2] in "+-*/^("):
                    self.expr = self.expr[:start - 1] + self.expr[start:]
                else:
                    self.expr = self.expr[:start] + "-" + self.expr[start:]
            self.refresh()
            return

        if t == "%":
            i = len(self.expr) - 1
            while i >= 0 and self.expr[i].isspace():
                i -= 1
            j = i
            while j >= 0 and (self.expr[j].isdigit() or self.expr[j] == "."):
                j -= 1
            start = j + 1

            if start <= i:
                try:
                    num = float(self.expr[start:i + 1])
                    self.expr = self.expr[:start] + fmt_number(num / 100.0) + self.expr[i + 1:]
                except Exception:
                    self.set_error("Percent error")
            else:
                self.set_error("Enter number then %")
            self.refresh()
            return

        if t == "=":
            self.evaluate()
            return

        allowed = set("0123456789+-*/().^")
        if t in allowed:
            self.expr += t
            self.refresh()

    def evaluate(self):
        expr = self.expr.strip()
        if not expr:
            self.set_error("Enter expression first")
            return
        try:
            result = safe_calculate(expr)
            self.last_result = result
            self.expr = fmt_number(result)
            self.refresh()
        except ZeroDivisionError:
            self.set_error("Cannot divide by zero")
        except ValueError as e:
            self.set_error(str(e))
        except Exception:
            self.set_error("Invalid expression")
