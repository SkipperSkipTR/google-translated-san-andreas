import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import re
import json
import time
import random
from deep_translator import GoogleTranslator

ALL_LANG_CODES = list(GoogleTranslator().get_supported_languages(as_dict=True).values())

# ── Colour palette ──────────────────────────────────────────────────────────
BG            = "#0d0e14"
BG_CARD       = "#13141e"
BG_LIGHT      = "#1a1b28"
BG_HIGHLIGHT  = "#20223a"
BG_HOVER      = "#252840"
FG            = "#cdd6f4"
FG_DIM        = "#45475a"
FG_MUTED      = "#6c7086"
ACCENT        = "#89b4fa"
ACCENT_DIM    = "#1e3a5f"
ACCENT_BRIGHT = "#b4d0ff"
GREEN         = "#a6e3a1"
GREEN_DIM     = "#1f3a1e"
YELLOW        = "#f9e2af"
YELLOW_DIM    = "#3a2e14"
RED           = "#f38ba8"
RED_DIM       = "#3a1020"
CYAN          = "#89dceb"
PURPLE        = "#cba6f7"
ORANGE        = "#fab387"
TEAL          = "#94e2d5"
BORDER        = "#2a2b3d"
BORDER_BRIGHT = "#3d3f5c"
SEPARATOR_COLOR = "#1e1f2e"

FONT_UI       = ("Segoe UI", 9)
FONT_UI_BOLD  = ("Segoe UI", 9, "bold")
FONT_UI_SM    = ("Segoe UI", 8)
FONT_MONO     = ("Cascadia Code", 10)
FONT_MONO_SM  = ("Cascadia Code", 9)
FONT_TITLE    = ("Segoe UI", 13, "bold")
FONT_LABEL    = ("Segoe UI", 8, "bold")

# Batch separator — single newline
SEPARATOR = "\n"


def strip_gxt_tags(text: str) -> str:
    return re.sub(r'~[a-zA-Z0-9_]+~', '', text).strip()


# ─────────────────────────────────────────────────────────────────────────────
# Tooltip
# ─────────────────────────────────────────────────────────────────────────────
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text   = text
        self.tip    = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _e=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=self.text, font=FONT_UI_SM, fg=FG,
                 bg=BG_HIGHLIGHT, relief="flat", padx=8, pady=4,
                 bd=1, highlightthickness=1,
                 highlightbackground=BORDER_BRIGHT).pack()

    def hide(self, _e=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


# ─────────────────────────────────────────────────────────────────────────────
# PillButton
# ─────────────────────────────────────────────────────────────────────────────
class PillButton(tk.Frame):
    def __init__(self, parent, text, command, icon="", color=ACCENT,
                 text_color="#0d0e14", width=None, small=False, **kw):
        bg = kw.pop("bg", None)
        try:
            pbg = bg or parent.cget("bg")
        except Exception:
            pbg = BG
        super().__init__(parent, bg=pbg, **kw)
        self.command     = command
        self._disabled   = False
        self.color       = color
        self.hover_color = self._adj(color, 25)
        self.text_color  = text_color
        label_text = f"{icon}  {text}" if icon else text
        pad_x = 10 if small else 14
        pad_y = 3  if small else 6
        font  = FONT_UI_SM if small else FONT_UI_BOLD
        self.lbl = tk.Label(self, text=label_text, font=font,
                            fg=text_color, bg=color,
                            padx=pad_x, pady=pad_y, cursor="hand2")
        if width:
            self.lbl.config(width=width)
        self.lbl.pack(fill=tk.X)
        self.lbl.bind("<Button-1>", lambda e: self.invoke())
        self.lbl.bind("<Enter>",    self._enter)
        self.lbl.bind("<Leave>",    self._leave)

    @staticmethod
    def _adj(hex_color, amt):
        r = max(0, min(255, int(hex_color[1:3], 16) + amt))
        g = max(0, min(255, int(hex_color[3:5], 16) + amt))
        b = max(0, min(255, int(hex_color[5:7], 16) + amt))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _enter(self, _e):
        if not self._disabled:
            self.lbl.config(bg=self.hover_color)

    def _leave(self, _e):
        if not self._disabled:
            self.lbl.config(bg=self.color)

    def invoke(self):
        if not self._disabled and self.command:
            self.command()

    def set_state(self, state):
        self._disabled = (state == "disabled")
        if self._disabled:
            self.lbl.config(bg=FG_DIM, fg=BG_LIGHT, cursor="arrow")
        else:
            self.lbl.config(bg=self.color, fg=self.text_color, cursor="hand2")

    def set_text(self, text):
        self.lbl.config(text=text)


# ─────────────────────────────────────────────────────────────────────────────
# ProgressRing
# ─────────────────────────────────────────────────────────────────────────────
class ProgressRing(tk.Canvas):
    def __init__(self, parent, size=36, **kw):
        try:
            pbg = parent.cget("bg")
        except Exception:
            pbg = BG
        super().__init__(parent, width=size, height=size,
                         bg=pbg, highlightthickness=0, **kw)
        self.size   = size
        self._track = self.create_arc(4, 4, size-4, size-4,
                                      start=0, extent=359.9,
                                      outline=BORDER_BRIGHT, width=3, style="arc")
        self._arc   = self.create_arc(4, 4, size-4, size-4,
                                      start=90, extent=0,
                                      outline=ACCENT, width=3, style="arc")
        self._lbl   = self.create_text(size//2, size//2, text="0%",
                                       font=("Segoe UI", 7, "bold"), fill=ACCENT)

    def set(self, pct):
        self.itemconfig(self._arc, extent=-int(pct * 3.6))
        self.itemconfig(self._lbl, text=f"{int(pct)}%")


# ─────────────────────────────────────────────────────────────────────────────
# TranslationCard
# ─────────────────────────────────────────────────────────────────────────────
class TranslationCard(tk.Frame):
    def __init__(self, parent, hop_str, text, on_select,
                 is_selected=False, **kw):
        super().__init__(parent, bg=BG_CARD, **kw)
        self.hop_str   = hop_str
        self.text      = text
        self.on_select = on_select
        self._selected = is_selected
        self._build()

    def _build(self):
        sel          = self._selected
        border_color = ACCENT if sel else BORDER
        bg           = BG_HIGHLIGHT if sel else BG_CARD

        inner = tk.Frame(self, bg=bg, highlightthickness=1,
                         highlightbackground=border_color)
        inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=1)
        self._inner = inner

        header = tk.Frame(inner, bg=bg)
        header.pack(fill=tk.X, padx=10, pady=(7, 3))

        hop_colors = {"3": TEAL, "5": GREEN, "20": CYAN, "50": YELLOW, "100": PURPLE}
        # hop_str may be "filename·N" (from a candidates file) or plain "N" (live)
        if "·" in str(self.hop_str):
            file_part, num_part = str(self.hop_str).rsplit("·", 1)
            hop_col   = hop_colors.get(num_part, ORANGE)
            hop_label = f"⟳ {num_part} hops  ·  {file_part}"
        else:
            hop_col   = hop_colors.get(str(self.hop_str), ORANGE)
            hop_label = f"⟳ {self.hop_str} hops"

        tk.Label(header, text=hop_label,
                 font=FONT_UI_BOLD, fg=hop_col, bg=bg).pack(side=tk.LEFT)
        if sel:
            tk.Label(header, text="● ACTIVE", font=FONT_LABEL,
                     fg=ACCENT_BRIGHT, bg=bg).pack(side=tk.RIGHT)

        txt = tk.Text(inner, height=3, wrap=tk.WORD, font=FONT_MONO,
                      bg=bg, fg=YELLOW if sel else FG,
                      bd=0, padx=10, pady=4, state=tk.DISABLED,
                      relief="flat", selectbackground=ACCENT_DIM)
        txt.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 8))
        txt.config(state=tk.NORMAL)
        txt.insert("1.0", self.text)
        txt.config(state=tk.DISABLED)
        self._txt = txt

        def _on_click(e):
            self.on_select()
            return "break"   # stop event bubbling so it only fires once

        for w in (inner, txt, header):
            w.bind("<Button-1>", _on_click)

        def _hover_in(_e):
            if not sel:
                inner.config(bg=BG_HOVER, highlightbackground=ACCENT_BRIGHT)
        def _hover_out(_e):
            inner.config(bg=bg, highlightbackground=border_color)
        inner.bind("<Enter>", _hover_in)
        inner.bind("<Leave>", _hover_out)


# ─────────────────────────────────────────────────────────────────────────────
# CandidatesFileRow
# ─────────────────────────────────────────────────────────────────────────────
class CandidatesFileRow(tk.Frame):
    def __init__(self, parent, filename, entry_count, on_remove, **kw):
        super().__init__(parent, bg=BG_LIGHT,
                         highlightthickness=1, highlightbackground=BORDER, **kw)
        self.pack(fill=tk.X, padx=4, pady=2)
        tk.Label(self, text="📄", font=FONT_UI, fg=CYAN,
                 bg=BG_LIGHT, padx=6).pack(side=tk.LEFT)
        tk.Label(self, text=filename, font=FONT_MONO_SM, fg=FG,
                 bg=BG_LIGHT, anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(self, text=f"{entry_count} keys", font=FONT_UI_SM,
                 fg=FG_MUTED, bg=BG_LIGHT, padx=6).pack(side=tk.LEFT)
        close = tk.Label(self, text="✕", font=FONT_UI_SM, fg=RED,
                         bg=BG_LIGHT, padx=6, cursor="hand2")
        close.pack(side=tk.RIGHT)
        close.bind("<Button-1>", lambda e: on_remove())


# ─────────────────────────────────────────────────────────────────────────────
# Main App
# ─────────────────────────────────────────────────────────────────────────────
class HyperTranslationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HyperTranslator")
        self.root.geometry("1366x768")
        self.root.configure(bg=BG)
        self.root.minsize(900, 560)

        try:
            self.root.state('zoomed')
        except tk.TclError:
            try:
                self.root.attributes('-zoomed', True)
            except tk.TclError:
                pass

        self.entries              = []   # [(key, current_text)]
        self.original_texts       = {}   # key → original source text
        self.translation_results  = {}   # key → {hop_str: text}
        self.best_selections      = {}   # key → hop_str
        self.committed_keys       = set()
        self.skipped_keys         = set()
        self.running              = False
        self.stop_requested       = False
        self.current_edit_key     = None
        self._src_file_path       = None
        self._cand_files: list    = []   # [{path, data, row}]

        self._apply_styles()
        self.setup_ui()
        self.load_source_file()

        self.root.bind("<Control-t>", lambda e: self.start_translation())
        self.root.bind("<Control-r>", lambda e: self.reroll_translations())
        self.root.bind("<Control-s>", lambda e: self.save_translated())
        self.root.bind("<Control-i>", lambda e: self.import_translated_txt())
        self.root.bind("<Escape>",    lambda e: self.stop_translation())
        self.root.bind("<F5>",        lambda e: self.reroll_translations())
        self.root.bind("<F2>",        lambda e: self.commit_entry())
        self.root.bind("<F3>",        lambda e: self.skip_entry())

    # ── Styles ────────────────────────────────────────────────────────────────
    def _apply_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure(".",            background=BG, foreground=FG, font=FONT_UI)
        s.configure("TFrame",       background=BG)
        s.configure("TLabel",       background=BG, foreground=FG)
        s.configure("TEntry",       fieldbackground=BG_LIGHT, foreground=FG,
                    bordercolor=BORDER, insertcolor=ACCENT, font=FONT_MONO_SM)
        s.configure("Treeview",     background=BG_LIGHT, foreground=FG,
                    fieldbackground=BG_LIGHT, font=FONT_MONO_SM, rowheight=26)
        s.configure("Treeview.Heading", background=BG_HIGHLIGHT, foreground=ACCENT,
                    font=FONT_UI_BOLD, relief="flat")
        s.map("Treeview",
              background=[("selected", ACCENT_DIM)],
              foreground=[("selected", ACCENT_BRIGHT)])
        s.configure("TPanedwindow", background=SEPARATOR_COLOR, sashwidth=4)
        s.configure("TProgressbar", background=ACCENT, troughcolor=BG_LIGHT,
                    thickness=3, borderwidth=0)
        s.configure("TScrollbar",   background=BG_LIGHT, troughcolor=BG,
                    arrowcolor=FG_DIM, borderwidth=0)
        s.map("TScrollbar",         background=[("active", BORDER_BRIGHT)])

    # ── UI ────────────────────────────────────────────────────────────────────
    def setup_ui(self):
        # ── STATUS BAR (pack first so it claims space before expand) ──────────
        sbar = tk.Frame(self.root, bg=BG_CARD, height=24)
        sbar.pack(fill=tk.X, side=tk.BOTTOM)
        sbar.pack_propagate(False)

        self.status_var    = tk.StringVar(value="Ready — open a source file to begin")
        self.entry_count_var   = tk.StringVar(value="0 entries")
        self.selected_count_var = tk.StringVar(value="0 selected")
        self.committed_var = tk.StringVar(value="Committed: 0")

        def _sl(var, fg=FG_MUTED, side=tk.LEFT, padx=10):
            tk.Label(sbar, textvariable=var, font=FONT_UI_SM,
                     fg=fg, bg=BG_CARD).pack(side=side, padx=padx)

        tk.Label(sbar, textvariable=self.status_var, font=FONT_UI_SM,
                 fg=CYAN, bg=BG_CARD, anchor="w").pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        _sl(self.committed_var,      fg=GREEN,   side=tk.RIGHT)
        _sl(self.selected_count_var, fg=FG_MUTED, side=tk.RIGHT)
        _sl(self.entry_count_var,    fg=ACCENT,  side=tk.RIGHT)
        lv = tk.StringVar(value=f"Pool: {len(ALL_LANG_CODES)} langs")
        _sl(lv, fg=FG_DIM, side=tk.RIGHT)

        # ── THIN PROGRESS BAR ─────────────────────────────────────────────────
        self._progress_val = tk.DoubleVar(value=0)
        self.progress_bar  = ttk.Progressbar(self.root, orient=tk.HORIZONTAL,
                                              mode="determinate",
                                              variable=self._progress_val)
        self.progress_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.progress_bar.pack_forget()

        # ── TOOLBAR ───────────────────────────────────────────────────────────
        toolbar = tk.Frame(self.root, bg=BG_CARD, height=38)
        toolbar.pack(fill=tk.X, side=tk.TOP)
        toolbar.pack_propagate(False)

        # Logo
        logo_f = tk.Frame(toolbar, bg=BG_CARD)
        logo_f.pack(side=tk.LEFT, padx=(10, 4), pady=4)
        tk.Label(logo_f, text="⟳", font=("Segoe UI", 13), fg=ACCENT,
                 bg=BG_CARD).pack(side=tk.LEFT)
        tk.Label(logo_f, text=" HyperTranslator", font=("Segoe UI", 10, "bold"),
                 fg=FG, bg=BG_CARD).pack(side=tk.LEFT)

        # Vertical divider
        tk.Frame(toolbar, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y,
                                                    padx=(6, 0), pady=6)

        self.file_path_var = tk.StringVar(value="No file loaded")
        tk.Label(toolbar, textvariable=self.file_path_var, font=FONT_UI_SM,
                 fg=FG_MUTED, bg=BG_CARD).pack(side=tk.LEFT, padx=8)

        # Right-side toolbar buttons
        tbr = tk.Frame(toolbar, bg=BG_CARD)
        tbr.pack(side=tk.RIGHT, padx=6, pady=5)

        # Keyboard hints (compact badge strip)
        hints_f = tk.Frame(tbr, bg=BG_CARD)
        hints_f.pack(side=tk.RIGHT, padx=(10, 0))
        for key_str, desc in [("Ctrl+T", "Translate"), ("F2", "Commit"),
                               ("F3", "Skip"), ("Esc", "Stop")]:
            hf = tk.Frame(hints_f, bg=BG_CARD)
            hf.pack(side=tk.LEFT, padx=3)
            tk.Label(hf, text=key_str, font=("Segoe UI", 7, "bold"), fg=ACCENT,
                     bg=BG_HIGHLIGHT, padx=3, pady=1).pack(side=tk.LEFT)
            tk.Label(hf, text=f" {desc}", font=("Segoe UI", 7),
                     fg=FG_DIM, bg=BG_CARD).pack(side=tk.LEFT)

        tk.Frame(tbr, bg=BORDER, width=1).pack(side=tk.RIGHT, fill=tk.Y,
                                                padx=(8, 0), pady=2)

        for btn_text, cmd, icon, col, tc in [
            ("Save",    self.save_translated,        "💾", GREEN,        BG),
            ("Import",  self.import_translated_txt,  "📤", CYAN,         BG),
            ("Cands",   self.browse_candidates_files,"📥", PURPLE,       BG),
            ("Open…",   self.browse_source_file,     "📂", BG_HIGHLIGHT, FG),
        ]:
            PillButton(tbr, btn_text, cmd, icon=icon, color=col,
                       text_color=tc, small=True, bg=BG_CARD).pack(
                           side=tk.RIGHT, padx=2)

        # ── MAIN HORIZONTAL PANED WINDOW ──────────────────────────────────────
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # ══════════════════ LEFT PANE (notebook) ══════════════════════════════
        left_outer = tk.Frame(paned, bg=BG)
        paned.add(left_outer, weight=3)

        # Search bar + filter (above the notebook)
        search_row = tk.Frame(left_outer, bg=BG)
        search_row.pack(fill=tk.X, padx=6, pady=(4, 2))

        sf = tk.Frame(search_row, bg=BG_LIGHT, highlightthickness=1,
                      highlightbackground=BORDER)
        sf.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(sf, text="🔍", font=FONT_UI, fg=FG_MUTED,
                 bg=BG_LIGHT, padx=5).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search)
        se = tk.Entry(sf, textvariable=self.search_var, font=FONT_MONO_SM,
                      bg=BG_LIGHT, fg=FG, insertbackground=ACCENT,
                      relief="flat", bd=0)
        se.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=4)
        clr = tk.Label(sf, text="✕", font=FONT_UI_SM, fg=FG_DIM,
                       bg=BG_LIGHT, padx=6, cursor="hand2")
        clr.pack(side=tk.RIGHT)
        clr.bind("<Button-1>", lambda e: self.search_var.set(""))

        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(search_row, textvariable=self.filter_var,
                                    values=["All", "Uncompleted", "Completed", "Skipped"],
                                    state="readonly", width=10, font=FONT_UI_SM)
        filter_combo.pack(side=tk.LEFT, padx=(4, 0))
        filter_combo.bind("<<ComboboxSelected>>", self.on_filter_change)

        # ── Left pane: vertical stack — tree (expands) → original text → candidates ──

        # Hidden stubs so logic methods that reference these still work
        self.key_label        = tk.Label(left_outer, text="—")
        self.cleaned_text_box = self._make_text(left_outer, height=1, fg=TEAL)

        # Tree
        tree_frame = tk.Frame(left_outer, bg=BG_LIGHT, highlightthickness=1,
                              highlightbackground=BORDER)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(4, 0))

        self.tree = ttk.Treeview(tree_frame,
                                  columns=("idx", "key", "text", "status"),
                                  show="headings", selectmode="extended")
        self.tree.heading("idx",    text="#")
        self.tree.heading("key",    text="Key")
        self.tree.heading("text",   text="Text")
        self.tree.heading("status", text="Status")
        self.tree.column("idx",    width=34,  minwidth=28,  stretch=False)
        self.tree.column("key",    width=110, minwidth=60)
        self.tree.column("text",   width=220, minwidth=80)
        self.tree.column("status", width=90,  minwidth=60,  stretch=False)

        ysb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=ysb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree.tag_configure("committed",     foreground=GREEN)
        self.tree.tag_configure("selected_best", foreground=YELLOW)
        self.tree.tag_configure("has_cands",     foreground=CYAN)
        self.tree.tag_configure("odd",           background=BG_CARD)
        self.tree.tag_configure("even",          background=BG_LIGHT)

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>",          self.on_tree_double_click)
        self.tree.bind("<MouseWheel>",  lambda e: self._on_tree_mousewheel(e))
        self.tree.bind("<Button-4>",    lambda e: self._on_tree_mousewheel(e))
        self.tree.bind("<Button-5>",    lambda e: self._on_tree_mousewheel(e))

        # Select All / None bar
        qa = tk.Frame(left_outer, bg=BG, pady=3)
        qa.pack(fill=tk.X, padx=4)
        tk.Label(qa, textvariable=self.selected_count_var, font=FONT_UI_SM,
                 fg=FG_MUTED, bg=BG).pack(side=tk.LEFT)
        PillButton(qa, "None", self.deselect_all, color=BG_HIGHLIGHT,
                   text_color=FG, small=True, bg=BG).pack(side=tk.RIGHT, padx=2)
        PillButton(qa, "All",  self.select_all,   color=BG_HIGHLIGHT,
                   text_color=FG, small=True, bg=BG).pack(side=tk.RIGHT, padx=2)

        # Original text panel (below tree)
        tk.Frame(left_outer, bg=BORDER, height=1).pack(fill=tk.X, padx=4, pady=(2, 0))
        orig_hdr = tk.Frame(left_outer, bg=BG)
        orig_hdr.pack(fill=tk.X, padx=6, pady=(3, 1))
        tk.Label(orig_hdr, text="ORIGINAL", font=FONT_LABEL,
                 fg=FG_MUTED, bg=BG).pack(side=tk.LEFT)
        self.original_text_box = self._make_text(left_outer, height=3, fg=FG)
        self.original_text_box.pack(fill=tk.X, padx=6, pady=(0, 2))

        # Candidates panel (below original)
        tk.Frame(left_outer, bg=BORDER, height=1).pack(fill=tk.X, padx=4, pady=(2, 0))
        cand_hdr = tk.Frame(left_outer, bg=BG, pady=4)
        cand_hdr.pack(fill=tk.X, padx=6)
        tk.Label(cand_hdr, text="CANDIDATES", font=FONT_LABEL,
                 fg=FG_MUTED, bg=BG).pack(side=tk.LEFT)
        PillButton(cand_hdr, "+ Load…", self.browse_candidates_files,
                   color=PURPLE, text_color=BG, small=True,
                   bg=BG).pack(side=tk.RIGHT)

        self.cand_list_frame = tk.Frame(left_outer, bg=BG)
        self.cand_list_frame.pack(fill=tk.X, padx=6, pady=(0, 4))

        self._no_cands_label = tk.Label(
            self.cand_list_frame,
            text="No candidates loaded.",
            font=FONT_UI_SM, fg=FG_DIM, bg=BG, justify="left")
        self._no_cands_label.pack(anchor=tk.W)

        # ══════════════════ RIGHT PANE (vertical pane: cards + editor) ════════
        right_outer = tk.Frame(paned, bg=BG)
        paned.add(right_outer, weight=5)

        right_vpane = ttk.PanedWindow(right_outer, orient=tk.VERTICAL)
        right_vpane.pack(fill=tk.BOTH, expand=True)

        # ── Top: translation cards ─────────────────────────────────────────────
        cards_pane = tk.Frame(right_vpane, bg=BG)
        right_vpane.add(cards_pane, weight=3)

        # Action bar
        action_bar = tk.Frame(cards_pane, bg=BG, pady=4)
        action_bar.pack(fill=tk.X, padx=6)

        self.translate_btn = PillButton(
            action_bar, "Translate", self.start_translation,
            icon="▶", color=ACCENT, text_color=BG, bg=BG)
        self.translate_btn.pack(side=tk.LEFT, padx=(0, 4))
        Tooltip(self.translate_btn, "Translate selected entries  (Ctrl+T)")

        self.reroll_btn = PillButton(
            action_bar, "Reroll", self.reroll_translations,
            icon="⟳", color=ORANGE, text_color=BG, bg=BG)
        self.reroll_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.stop_btn = PillButton(
            action_bar, "Stop", self.stop_translation,
            icon="■", color=RED, text_color=BG, bg=BG)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 4))
        self.stop_btn.set_state("disabled")

        tk.Frame(action_bar, bg=BORDER, width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=10, pady=2)

        PillButton(action_bar, "Auto-select Best", self.auto_select_all,
                   color=BG_HIGHLIGHT, text_color=TEAL,
                   small=True, bg=BG).pack(side=tk.LEFT, padx=2)

        self.ring = ProgressRing(action_bar, size=30)
        self.ring.pack(side=tk.RIGHT, padx=4)
        self.ring.pack_forget()

        self.progress_label = tk.Label(action_bar, text="",
                                        font=FONT_UI_SM, fg=ORANGE, bg=BG)
        self.progress_label.pack(side=tk.RIGHT, padx=4)

        # Batch notice
        self.batch_bar = tk.Frame(cards_pane, bg=YELLOW_DIM,
                                   highlightthickness=1,
                                   highlightbackground=YELLOW)
        self.batch_bar.pack(fill=tk.X, padx=6, pady=(0, 2))
        self.batch_bar.pack_forget()
        tk.Label(self.batch_bar,
                 text="⚡ Batch mode — entries joined by \\n, split back after translation.",
                 font=FONT_UI_SM, fg=YELLOW, bg=YELLOW_DIM,
                 padx=8, pady=3).pack(side=tk.LEFT)

        # Translation cards scroll area
        cards_outer = tk.Frame(cards_pane, bg=BG, padx=6)
        cards_outer.pack(fill=tk.BOTH, expand=True)

        self.trans_canvas = tk.Canvas(cards_outer, bg=BG, highlightthickness=0)
        trans_sb = ttk.Scrollbar(cards_outer, orient=tk.VERTICAL,
                                  command=self.trans_canvas.yview)
        self.trans_inner = tk.Frame(self.trans_canvas, bg=BG)
        self._trans_win  = self.trans_canvas.create_window(
            (0, 0), window=self.trans_inner, anchor="nw")
        self.trans_canvas.configure(yscrollcommand=trans_sb.set)
        self.trans_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        trans_sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.trans_canvas.bind("<Configure>",  self._on_canvas_resize)
        self.trans_inner.bind("<Configure>",   lambda e:
            self.trans_canvas.configure(
                scrollregion=self.trans_canvas.bbox("all")))
        self.trans_canvas.bind("<MouseWheel>", self._on_canvas_mousewheel)
        self.trans_canvas.bind("<Button-4>",   self._on_linux_scroll_up)
        self.trans_canvas.bind("<Button-5>",   self._on_linux_scroll_down)

        self._show_empty_state()

        # ── Bottom: editor ────────────────────────────────────────────────────
        editor_pane = tk.Frame(right_vpane, bg=BG_CARD,
                               highlightthickness=1, highlightbackground=BORDER)
        right_vpane.add(editor_pane, weight=2)

        ehdr = tk.Frame(editor_pane, bg=BG_CARD, pady=5)
        ehdr.pack(fill=tk.X, padx=10)
        tk.Label(ehdr, text="EDITOR", font=FONT_LABEL,
                 fg=FG_MUTED, bg=BG_CARD).pack(side=tk.LEFT)
        tk.Label(ehdr, text="Re-add GXT tags  (~w~, ~r~, ~VEACC~, …)",
                 font=FONT_UI_SM, fg=FG_DIM, bg=BG_CARD).pack(side=tk.LEFT, padx=8)
        self.edit_key_badge = tk.Label(ehdr, text="", font=FONT_MONO_SM,
                                        fg=CYAN, bg=BG_CARD)
        self.edit_key_badge.pack(side=tk.LEFT, padx=8)

        ebtns_top = tk.Frame(ehdr, bg=BG_CARD)
        ebtns_top.pack(side=tk.RIGHT)
        PillButton(ebtns_top, "Skip  F3", self.skip_entry,
                   icon="⏭", color=ORANGE, text_color=BG,
                   small=True, bg=BG_CARD).pack(side=tk.LEFT, padx=2)
        PillButton(ebtns_top, "Commit  F2", self.commit_entry,
                   icon="✓", color=GREEN, text_color=BG,
                   small=True, bg=BG_CARD).pack(side=tk.LEFT, padx=2)

        # GXT tag quick-insert bar
        self.gxt_tags_frame = tk.Frame(editor_pane, bg=BG_CARD)
        self.gxt_tags_frame.pack(fill=tk.X, padx=10, pady=(0, 4))

        self.edit_text_box = tk.Text(
            editor_pane, font=FONT_MONO, bg=BG_LIGHT, fg=FG,
            wrap=tk.WORD, bd=0, padx=8, pady=6, insertbackground=ACCENT,
            relief="flat", selectbackground=ACCENT_DIM,
            highlightthickness=1, highlightbackground=BORDER)
        self.edit_text_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _make_text(self, parent, height=2, fg=FG):
        return tk.Text(parent, height=height, font=FONT_MONO_SM,
                       bg=BG_LIGHT, fg=fg, wrap=tk.WORD, bd=0,
                       padx=6, pady=4, state=tk.DISABLED, relief="flat",
                       highlightthickness=1, highlightbackground=BORDER)

    def _set_text(self, widget, text):
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.config(state=tk.DISABLED)

    def _show_empty_state(self):
        for w in self.trans_inner.winfo_children():
            w.destroy()
        tk.Label(self.trans_inner,
                 text="Select entries then click  ▶ Translate\n\n"
                      "—  or  —\n\n"
                      "Load a candidates file produced by  hypertrans_cli.py\n"
                      "to import pre-computed translations.",
                 font=("Segoe UI", 11), fg=FG_DIM, bg=BG,
                 justify="center").pack(pady=80)

    def _on_canvas_resize(self, event):
        self.trans_canvas.itemconfig(self._trans_win, width=event.width)
        self.trans_canvas.configure(
            scrollregion=self.trans_canvas.bbox("all"))

    # Canvas mousewheel – used directly and via recursive binding on cards
    def _on_canvas_mousewheel(self, event):
        self.trans_canvas.yview_scroll(
            int(-1 * (event.delta / 120)), "units")

    def _on_linux_scroll_up(self, event):
        self.trans_canvas.yview_scroll(-1, "units")

    def _on_linux_scroll_down(self, event):
        self.trans_canvas.yview_scroll(1, "units")

    def _on_tree_mousewheel(self, event):
        if event.num == 4 or event.delta > 0:
            self.tree.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.tree.yview_scroll(1, "units")

    # Recursively bind canvas scroll to all widgets inside trans_inner
    def _bind_card_scrolling(self):
        def _recursive_bind(w):
            w.bind("<MouseWheel>", self._on_canvas_mousewheel)
            w.bind("<Button-4>",   self._on_linux_scroll_up)
            w.bind("<Button-5>",   self._on_linux_scroll_down)
            for child in w.winfo_children():
                _recursive_bind(child)
        _recursive_bind(self.trans_inner)

    # ── Source file ───────────────────────────────────────────────────────────
    def load_source_file(self, filepath=None):
        if not filepath:
            dir_path = os.path.dirname(os.path.abspath(__file__))
            for candidate in ["american.txt", "ENGLISH.txt", "american.gxt.txt", "english.txt"]:
                cp = os.path.join(dir_path, candidate)
                if os.path.exists(cp):
                    filepath = cp
                    break
        if not filepath or not os.path.exists(filepath):
            self.status_var.set("No source file — use Open Source File")
            return

        self._src_file_path  = filepath
        self.file_path_var.set(os.path.basename(filepath))
        self.entries         = []
        self.original_texts  = {}
        self.translation_results = {}
        self.best_selections = {}
        self.committed_keys  = set()
        self.skipped_keys    = set()
        self.current_edit_key = None

        try:
            with open(filepath, 'r', encoding='utf-16') as f:
                lines = f.readlines()
            
            if lines:
                lines[0] = lines[0].lstrip('\ufeff')
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith('[') and line.endswith(']'):
                    key  = line
                    text = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    self.entries.append((key, text))
                    self.original_texts[key] = text
                    i += 2 if text else 1
                else:
                    i += 1
            self.refresh_tree()
            self.entry_count_var.set(f"{len(self.entries)} entries")
            self.update_committed_count()
            self.status_var.set(
                f"Loaded {len(self.entries)} entries from "
                f"{os.path.basename(filepath)}")
            self._merge_all_candidates()
            self.load_session()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")

    def browse_source_file(self):
        fp = filedialog.askopenfilename(
            title="Open Source Localization File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if fp:
            self.load_source_file(fp)

    # ── Candidates files ──────────────────────────────────────────────────────
    def browse_candidates_files(self):
        fps = filedialog.askopenfilenames(
            title="Load Candidates File(s)",
            filetypes=[("Candidates JSON", "*.json"), ("All Files", "*.*")])
        for fp in fps:
            self._load_one_candidates_file(fp)

    def _load_one_candidates_file(self, path: str):
        if any(cf["path"] == path for cf in self._cand_files):
            self.status_var.set(f"Already loaded: {os.path.basename(path)}")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot read candidates file:\n{e}")
            return

        entries_in_file = data.get("entries", {})

        def make_remove(p=path):
            return lambda: self._remove_candidates_file(p)

        row = CandidatesFileRow(
            self.cand_list_frame,
            filename=os.path.basename(path),
            entry_count=len(entries_in_file),
            on_remove=make_remove())

        self._cand_files.append({"path": path, "data": data, "row": row})
        self._no_cands_label.pack_forget()
        self._merge_candidates_data(entries_in_file, os.path.basename(path))
        self.refresh_tree(self.search_var.get())
        self.save_session()
        self.status_var.set(
            f"Loaded {len(entries_in_file)} keys from {os.path.basename(path)}")

    def _remove_candidates_file(self, path: str):
        for cf in self._cand_files:
            if cf["path"] == path:
                cf["row"].destroy()
                break
        self._cand_files = [cf for cf in self._cand_files if cf["path"] != path]
        if not self._cand_files:
            self._no_cands_label.pack(anchor=tk.W)
        self.translation_results = {}
        self._merge_all_candidates()
        self.refresh_tree(self.search_var.get())
        self.render_translation_cards()
        self.save_session()
        self.status_var.set(f"Removed {os.path.basename(path)}")

    def _merge_all_candidates(self):
        self.translation_results = {}
        for cf in self._cand_files:
            filename = os.path.basename(cf["path"])
            self._merge_candidates_data(cf["data"].get("entries", {}), filename)

    def _merge_candidates_data(self, entries: dict, filename: str = ""):
        for key, hops in entries.items():
            if key not in self.translation_results:
                self.translation_results[key] = {}
            for hop_str, text in hops.items():
                if filename:
                    namespaced = f"{filename}·{hop_str}"
                else:
                    namespaced = hop_str
                self.translation_results[key][namespaced] = text

    # ── Tree ──────────────────────────────────────────────────────────────────
    def refresh_tree(self, filter_text=""):
        # Preserve selection across rebuilds so committed line stays visible
        selected_keys = set()
        for item in self.tree.selection():
            values = self.tree.item(item, "values")
            if values:
                selected_keys.add(values[1])

        for item in self.tree.get_children():
            self.tree.delete(item)

        status_filter = self.filter_var.get() if hasattr(self, 'filter_var') else "All"

        visible = 0
        for idx, (key, text) in enumerate(self.entries):
            cleaned = strip_gxt_tags(text)
            display = cleaned[:80] if len(cleaned) > 80 else cleaned
            if filter_text and filter_text.lower() not in key.lower() \
                    and filter_text.lower() not in text.lower():
                continue

            is_committed = key in self.committed_keys
            is_skipped   = key in self.skipped_keys
            if status_filter == "Completed" and not is_committed:
                if key not in selected_keys:
                    continue
            if status_filter == "Uncompleted":
                if (is_committed or is_skipped) and key not in selected_keys:
                    continue
            if status_filter == "Skipped" and not is_skipped:
                if key not in selected_keys:
                    continue

            status = ""
            tags   = ["odd" if visible % 2 == 0 else "even"]
            if is_committed:
                status = "✓ committed"
                tags.append("committed")
            elif is_skipped:
                status = "⏭ skipped"
                tags.append("selected_best")
            elif key in self.best_selections:
                status = "● selected"
                tags.append("selected_best")
            elif key in self.translation_results:
                status = "◆ has cands"
                tags.append("has_cands")

            self.tree.insert("", tk.END,
                             values=(str(idx + 1), key, display, status),
                             tags=tuple(tags))
            visible += 1

        self.entry_count_var.set(f"{len(self.entries)} entries")

        # Re-select previously selected keys
        for item in self.tree.get_children():
            item_key = self.tree.item(item, "values")[1]
            if item_key in selected_keys:
                self.tree.selection_add(item)

        sel = self.tree.selection()
        self.selected_count_var.set(
            f"{len(sel)} selected  ·  {visible} shown")

    def on_search(self, *args):
        self.refresh_tree(self.search_var.get())

    def on_filter_change(self, *args):
        self.refresh_tree(self.search_var.get())

    def on_tree_select(self, event):
        sel   = self.tree.selection()
        count = len(sel)
        self.selected_count_var.set(
            f"{count} selected  ·  {len(self.tree.get_children())} shown")
        if not sel:
            return

        key  = self.tree.item(sel[0], "values")[1]
        # Always show the original source text in the detail panel
        original = self.original_texts.get(key, "")
        self.key_label.config(text=key)
        self._set_text(self.original_text_box, original)
        self._set_text(self.cleaned_text_box, strip_gxt_tags(original))

        # If exactly one entry is selected, update editor
        if count == 1:
            self.current_edit_key = key
            # If this key is already committed, load the committed (final) text
            if key in self.committed_keys:
                committed_text = next((t for k, t in self.entries if k == key), "")
                self.edit_text_box.delete("1.0", tk.END)
                self.edit_text_box.insert("1.0", committed_text)
            # Else if there is a best_selection and the corresponding translation exists
            elif key in self.best_selections:
                hop_str = self.best_selections[key]
                if hop_str in self.translation_results.get(key, {}):
                    text = self.translation_results[key][hop_str]
                    self.edit_text_box.delete("1.0", tk.END)
                    self.edit_text_box.insert("1.0", text)
                    if "·" in str(hop_str):
                        _, num_part = str(hop_str).rsplit("·", 1)
                        badge_hop = f"{hop_str.rsplit('·',1)[0]}  ·  {num_part} hops"
                    else:
                        badge_hop = f"{hop_str} hops"

            # Update GXT tag buttons for the original source of this key
            self._update_gxt_tag_buttons(key)

        # Auto-show cards for single-entry selection that has candidates
        if count == 1 and key in self.translation_results:
            self._render_cards({key: self.translation_results[key]})

        self.batch_bar.pack_forget()
        if count > 1:
            self.batch_bar.pack(fill=tk.X, padx=6, pady=(0, 4))

    def on_tree_double_click(self, event):
        self.start_translation()

    # ── Selection ─────────────────────────────────────────────────────────────
    def get_selected_texts(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection",
                                   "Select one or more entries to translate.")
            return []
        results = []
        for item in sel:
            key = self.tree.item(item, "values")[1]
            for k, t in self.entries:
                if k == key:
                    cleaned = strip_gxt_tags(t)
                    if cleaned.strip():
                        results.append((key, cleaned))
                    break
        return results

    def select_all(self):
        for item in self.tree.get_children():
            self.tree.selection_add(item)

    def deselect_all(self):
        self.tree.selection_remove(self.tree.selection())
        self.selected_count_var.set("0 selected")

    def auto_select_all(self):
        changed = 0
        for key, results in self.translation_results.items():
            if results and key not in self.best_selections:
                self.best_selections[key] = next(iter(results))
                changed += 1
        if changed:
            self.render_translation_cards()
            self.status_var.set(f"Auto-selected {changed} translations")

    # ── Live translation ──────────────────────────────────────────────────────
    def _translate_text(self, text: str, iterations: int) -> str:
        current      = text
        current_lang = 'en'
        available    = [l for l in ALL_LANG_CODES if l != 'en']
        langs        = random.sample(available, min(iterations, len(available)))
        for lang in langs:
            try:
                r = GoogleTranslator(source=current_lang, target=lang).translate(current)
                if r:
                    current, current_lang = r, lang
            except Exception:
                pass
        try:
            r = GoogleTranslator(source=current_lang, target='en').translate(current)
            if r:
                current = r
        except Exception:
            pass
        return current

    def _translate_batch(self, entries: list, iterations: int) -> dict:
        if len(entries) == 1:
            key, text = entries[0]
            return {key: self._translate_text(text, iterations)}
        joined     = SEPARATOR.join(text for _, text in entries)
        translated = self._translate_text(joined, iterations)
        parts      = translated.split(SEPARATOR)
        return {key: (parts[i].strip() if i < len(parts) else translated.strip())
                for i, (key, _) in enumerate(entries)}

    def start_translation(self):
        if self.running:
            return
        selected = self.get_selected_texts()
        if not selected:
            return
        self._begin_translation(selected)

    def reroll_translations(self):
        if self.running:
            return
        if self.translation_results:
            selected = [(k, strip_gxt_tags(self.original_texts.get(k, "")))
                        for k in self.translation_results
                        if strip_gxt_tags(self.original_texts.get(k, ""))]
            if selected:
                self._begin_translation(selected)
                return
        self.start_translation()

    def _begin_translation(self, selected):
        self.running        = True
        self.stop_requested = False
        self.translate_btn.set_state("disabled")
        self.reroll_btn.set_state("disabled")
        self.stop_btn.set_state("normal")
        self.progress_bar.pack(fill=tk.X, side=tk.TOP)
        self.ring.pack(side=tk.RIGHT, padx=6)
        self._progress_val.set(0)
        threading.Thread(target=self._run_translation,
                         args=(selected,), daemon=True).start()

    def stop_translation(self):
        self.stop_requested = True
        self.status_var.set("Stopping…")

    def _run_translation(self, selected):
        iteration_counts = [3, 5, 20, 50, 100]
        total            = len(iteration_counts)
        for key, _ in selected:
            if key not in self.translation_results:
                self.translation_results[key] = {}

        for step, it in enumerate(iteration_counts):
            if self.stop_requested:
                break
            self.root.after(0, self.status_var.set,
                f"Translating — {it} hops ({step+1}/{total})")
            self.root.after(0, self.progress_label.config,
                            {"text": f"{it} hops"})
            try:
                for key, text in self._translate_batch(selected, it).items():
                    self.translation_results[key][str(it)] = text
            except Exception as e:
                for key, _ in selected:
                    self.translation_results[key][str(it)] = f"[Error: {e}]"
            self.root.after(0, self._update_progress, step + 1, total)
            time.sleep(0.05)

        self.running = False
        self.root.after(0, self.render_translation_cards)
        self.root.after(0, lambda: self.translate_btn.set_state("normal"))
        self.root.after(0, lambda: self.reroll_btn.set_state("normal"))
        self.root.after(0, lambda: self.stop_btn.set_state("disabled"))
        self.root.after(0, lambda: self._progress_val.set(100))
        self.root.after(0, lambda: self.ring.set(100))
        self.root.after(300, lambda: self.progress_bar.pack_forget())
        self.root.after(300, lambda: self.ring.pack_forget())
        self.root.after(0, lambda: self.progress_label.config({"text": ""}))
        n = len(selected)
        self.root.after(0, lambda: self.status_var.set(
            f"Done!  {n} entr{'y' if n == 1 else 'ies'} translated. "
            "Click a card to select."))

    def _update_progress(self, done, total):
        pct = (done / total * 100) if total else 0
        self._progress_val.set(pct)
        self.ring.set(pct)

    # ── Card rendering ────────────────────────────────────────────────────────
    def render_translation_cards(self):
        sel = self.tree.selection()
        results_to_render = {}
        
        # Limit to 50 items to prevent Tkinter from freezing on mass-selection
        for item in list(sel)[:50]:
            key = self.tree.item(item, "values")[1]
            if key in self.translation_results:
                results_to_render[key] = self.translation_results[key]
                
        self._render_cards(results_to_render)

    @staticmethod
    def _hop_sort_key(hop_str: str) -> int:
        """Extract a numeric hop count from strings like '5' or 'file·20'."""
        try:
            return int(hop_str.split("·")[-1])
        except (ValueError, IndexError):
            return 0

    def _render_cards(self, results: dict):
        for w in self.trans_inner.winfo_children():
            w.destroy()
        if not results:
            self._show_empty_state()
            # Even if empty, bind scroll to keep future cards ready
            self._bind_card_scrolling()
            return

        for key, hops in results.items():
            original = self.original_texts.get(key, "")

            hdr = tk.Frame(self.trans_inner, bg=BG_CARD,
                           highlightthickness=1, highlightbackground=BORDER)
            hdr.pack(fill=tk.X, padx=4, pady=(10, 0))

            hi = tk.Frame(hdr, bg=BG_CARD, pady=6)
            hi.pack(fill=tk.X, padx=10)
            tk.Label(hi, text=key, font=FONT_UI_BOLD,
                     fg=CYAN, bg=BG_CARD).pack(side=tk.LEFT)
            if key in self.committed_keys:
                tk.Label(hi, text=" ✓ COMMITTED", font=FONT_LABEL,
                         fg=GREEN, bg=BG_CARD).pack(side=tk.LEFT, padx=8)

            tk.Label(hdr, text=original, font=FONT_MONO_SM, fg=FG_DIM,
                     bg=BG_CARD, anchor="w",
                     wraplength=900).pack(fill=tk.X, padx=10, pady=(0, 6))

            cards_frame = tk.Frame(self.trans_inner, bg=BG)
            cards_frame.pack(fill=tk.X, padx=4, pady=(0, 4))

            # Sort hops numerically, robust against weird keys
            for hop_str, text in sorted(hops.items(), key=lambda kv: self._hop_sort_key(kv[0])):
                is_sel = (self.best_selections.get(key) == hop_str)

                def make_cb(k=key, h=hop_str):
                    return lambda: self._select_translation(k, h)

                TranslationCard(cards_frame, hop_str, text,
                                make_cb(), is_sel).pack(
                    fill=tk.X, expand=True, padx=2, pady=1)

        # After building all cards, rebind scrolling on every widget
        self._bind_card_scrolling()

    def _select_translation(self, key: str, hop_str: str):
        self.best_selections[key] = hop_str
        self.current_edit_key     = key
        text = self.translation_results[key][hop_str]
        self.edit_text_box.delete("1.0", tk.END)
        self.edit_text_box.insert("1.0", text)
        # Display hop label cleanly
        if "·" in str(hop_str):
            _, num_part = str(hop_str).rsplit("·", 1)
            badge_hop = f"{hop_str.rsplit('·',1)[0]}  ·  {num_part} hops"
        else:
            badge_hop = f"{hop_str} hops"
        self._update_gxt_tag_buttons(key)
        # Defer card rebuild so it runs after this click event fully unwinds
        self.root.after(0, self.render_translation_cards)
        self.status_var.set(
            f"Selected: {key}  ({hop_str} hops) — edit below, then Commit (F2)")

    # ── GXT tag insertion ─────────────────────────────────────────────────────
    def _update_gxt_tag_buttons(self, key: str):
        """Populate the gxt_tags_frame with buttons for each unique tag in the original text."""
        for w in self.gxt_tags_frame.winfo_children():
            w.destroy()
        if not key:
            return

        original = self.original_texts.get(key, "")
        if not original:
            return

        tags = list(dict.fromkeys(re.findall(r'~[a-zA-Z0-9_]+~', original)))
        if not tags:
            return

        for col, tag in enumerate(tags):
            btn = PillButton(
                self.gxt_tags_frame,
                text=tag,
                command=lambda t=tag: self._insert_gxt_tag(t),
                icon="",
                color=BG_HIGHLIGHT,
                text_color=ACCENT_BRIGHT,
                small=True,
                bg=BG_CARD
            )
            btn.grid(row=col // 5, column=col % 5, padx=2, pady=2, sticky="w")

    def _insert_gxt_tag(self, tag: str):
        """Insert a GXT tag at the current cursor position in the editor."""
        try:
            self.edit_text_box.insert(tk.INSERT, tag)
        except tk.TclError:
            pass

    # ── Skip / Commit ─────────────────────────────────────────────────────────
    def skip_entry(self):
        if not self.current_edit_key:
            return
        # Find the next uncommitted entry in the tree
        keys_shown = []
        for item in self.tree.get_children():
            k = self.tree.item(item, "values")[1]
            keys_shown.append(k)
        start = keys_shown.index(self.current_edit_key) + 1
        next_key = None
        for k in keys_shown[start:]:
            if k not in self.committed_keys:
                next_key = k
                break
        if next_key is None:
            for k in keys_shown:
                if k not in self.committed_keys and k != self.current_edit_key:
                    next_key = k
                    break

        self.skipped_keys.add(self.current_edit_key)
        self.current_edit_key = None
        self.edit_text_box.delete("1.0", tk.END)
        self.edit_key_badge.config(text="")

        # Deselect current, select next
        self.tree.selection_remove(self.tree.selection())
        if next_key:
            for item in self.tree.get_children():
                if self.tree.item(item, "values")[1] == next_key:
                    self.tree.selection_add(item)
                    self.tree.see(item)
                    # Trigger editor update for the new selection
                    self.on_tree_select(None)
                    break
        self.refresh_tree(self.search_var.get())
        self.status_var.set("Skipped")

    def commit_entry(self):
        if not self.current_edit_key:
            messagebox.showwarning("Nothing Selected",
                                   "Select an entry in the tree first.")
            return
        key   = self.current_edit_key
        final = self.edit_text_box.get("1.0", tk.END).strip()
        if not final:
            messagebox.showwarning("Empty", "Editor is empty.")
            return

        # Check for non-windows-1252 characters
        invalid_chars = []
        for char in final:
            try:
                char.encode("windows-1252")
            except UnicodeEncodeError:
                if char not in invalid_chars:
                    invalid_chars.append(char)

        if invalid_chars:
            chars_str = ", ".join(f"'{c}' (U+{ord(c):04X})" for c in invalid_chars[:10])
            messagebox.showerror(
                "Invalid Character Encoding",
                f"Cannot commit entry!\n\n"
                f"The text contains characters outside Windows-1252 encoding:\n"
                f"  {chars_str}\n\n"
                f"Please remove or replace these characters before committing."
            )
            return

        # Warn if original has GXT tags missing from the edit
        original = self.original_texts.get(key, "")
        orig_tags = set(re.findall(r'~[a-zA-Z0-9_]+~', original))
        if orig_tags:
            missing = [t for t in orig_tags if t not in final]
            if missing:
                msg = (f"This entry has GXT tags that are missing from your edit:\n"
                       f"  {' '.join(missing)}\n\n"
                       f"Commit anyway?")
                if not messagebox.askyesno("Missing GXT Tags", msg,
                                           icon="warning"):
                    return

        for i, (k, t) in enumerate(self.entries):
            if k == key:
                self.entries[i] = (k, final)
                break
        self.committed_keys.add(key)
        self.refresh_tree(self.search_var.get())
        self.update_committed_count()
        self.save_session()
        self.root.after(0, self.render_translation_cards)
        self.status_var.set(f"Committed  {key}  ✓")

    def update_committed_count(self):
        completed = len(self.committed_keys) + len(self.skipped_keys)
        self.committed_var.set(f"Committed: {completed} / {len(self.entries)} = %{round((completed/len(self.entries) * 100), 2)}")

    # ── Session persistence ───────────────────────────────────────────────────
    def _session_path(self):
        if not self._src_file_path:
            return None
        base = os.path.splitext(self._src_file_path)[0]
        return base + ".hypertrans_session"

    def save_session(self):
        sp = self._session_path()
        if not sp:
            return
        session = {
            "source_file":     self._src_file_path,
            "committed_keys":  list(self.committed_keys),
            "skipped_keys":    list(self.skipped_keys),
            "best_selections": self.best_selections,
            "committed_texts": {
                k: t for k, t in self.entries
                if k in self.committed_keys
            },
            "candidate_paths": [cf["path"] for cf in self._cand_files],
        }
        try:
            with open(sp, "w", encoding="utf-8") as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.status_var.set(f"Session save failed: {e}")

    def load_session(self):
        sp = self._session_path()
        if not sp or not os.path.exists(sp):
            return
        try:
            with open(sp, "r", encoding="utf-8") as f:
                session = json.load(f)
        except Exception:
            return

        committed_texts = session.get("committed_texts", {})
        for i, (k, _) in enumerate(self.entries):
            if k in committed_texts:
                self.entries[i] = (k, committed_texts[k])

        self.committed_keys  = set(session.get("committed_keys", []))
        self.skipped_keys    = set(session.get("skipped_keys", []))
        self.best_selections = session.get("best_selections", {})

        for path in session.get("candidate_paths", []):
            if os.path.exists(path):
                self._load_one_candidates_file(path)

        n = len(self.committed_keys)
        self.refresh_tree(self.search_var.get())
        self.update_committed_count()
        if n:
            self.status_var.set(
                f"Session restored — {n} committed entr{'y' if n == 1 else 'ies'} resumed.")

    # ── Save ──────────────────────────────────────────────────────────────────
    def save_translated(self):
        if not self.entries:
            messagebox.showwarning("Empty", "No entries to save.")
            return
        base_dir = os.path.dirname(
            os.path.abspath(self._src_file_path or __file__))
        src_name = os.path.splitext(os.path.basename(self._src_file_path))[0] if self._src_file_path else "translated"
        fp = filedialog.asksaveasfilename(
            title="Save Translated File",
            initialfile=f"{src_name}_translated.txt",
            initialdir=base_dir,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if not fp:
            return
        try:
            with open(fp, 'w', encoding='utf-16') as f:
                for key, text in self.entries:
                    f.write(f"{key}\n{text}\n\n")
            messagebox.showinfo("Saved",
                                f"Saved {len(self.entries)} entries to:\n{fp}")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed:\n{e}")
    
    # ── Import ────────────────────────────────────────────────────────────────
    def import_translated_txt(self):
        if not self.entries:
            messagebox.showwarning("No Source Loaded", "Please load a source file first.")
            return

        base_dir = os.path.dirname(os.path.abspath(self._src_file_path or __file__))
        fp = filedialog.askopenfilename(
            title="Import Translated Text File",
            initialdir=base_dir,
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if not fp:
            return

        try:
            # Try original utf-16-le first, fallback to utf-8 if user edited it externally
            try:
                with open(fp, 'r', encoding='utf-16') as f:
                    lines = f.readlines()
                
                if lines:
                    lines[0] = lines[0].lstrip('\ufeff')
            except UnicodeError:
                with open(fp, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

            imported_data = {}
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith('[') and line.endswith(']'):
                    key = line
                    text = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    imported_data[key] = text
                    i += 2 if text else 1
                else:
                    i += 1

            imported_count = 0
            skipped_encoding_count = 0
            for idx, (k, original_t) in enumerate(self.entries):
                if k in imported_data:
                    imported_text = imported_data[k]
                    # Only register if the imported text differs from the source original
                    if imported_text and imported_text != original_t:
                        try:
                            imported_text.encode("windows-1252")
                            self.entries[idx] = (k, imported_text)
                            self.committed_keys.add(k)
                            imported_count += 1
                        except UnicodeEncodeError:
                            skipped_encoding_count += 1

            if imported_count > 0:
                self.refresh_tree(self.search_var.get())
                self.update_committed_count()
                self.save_session()
                self.root.after(0, self.render_translation_cards)
                msg = f"Successfully imported {imported_count} translated entries."
                if skipped_encoding_count > 0:
                    msg += f"\n⚠️ Skipped {skipped_encoding_count} entries containing non-Windows-1252 characters."
                self.status_var.set(f"Imported {imported_count} entries from {os.path.basename(fp)}")
                messagebox.showinfo("Import Complete", msg)
            else:
                msg = "No new or matching translations found to import."
                if skipped_encoding_count > 0:
                    msg += f"\n⚠️ {skipped_encoding_count} entries were skipped due to non-Windows-1252 characters."
                messagebox.showinfo("Import Complete", msg)

        except Exception as e:
            messagebox.showerror("Error", f"Import failed:\n{e}")


def main():
    root = tk.Tk()
    HyperTranslationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()