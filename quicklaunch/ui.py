"""Tkinter UI — Revitalised assets (black + orange) + map card grid."""
from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageDraw, ImageTk

from discovery import (
    LevelInfo,
    ScanCache,
    VehicleInfo,
    cache_is_fresh,
    load_cache,
    save_cache,
    scan_all,
)
from handoff import ensure_steam
from launch import DEFAULT_GFX, LaunchRequest, launch
from paths import app_dir, console_log_path, find_exe, find_game_install, find_userfolder
from settings import SettingsStore
from versioning import version_status

# Revitalised palette (from extracted assets / BeamNG orange)
BG = "#000000"
PANEL = "#0d0d0d"
CARD = "#141414"
CARD_SEL = "#1a1208"
FG = "#ffffff"
MUTED = "#a7a7a7"
ORANGE = "#ff6600"
ORANGE_HOT = "#ff8c00"
BORDER = "#2a2a2a"

ASSETS = app_dir() / "assets"
CARD_W, CARD_H = 168, 110
MAP_COLS = 4


def _load_pil(name: str) -> Image.Image | None:
    p = ASSETS / name
    if not p.is_file():
        return None
    try:
        return Image.open(p).convert("RGBA")
    except OSError:
        return None


def _thumb(path: str | Path, size: tuple[int, int], placeholder: str = "?") -> Image.Image:
    try:
        im = Image.open(path).convert("RGB")
        im = im.copy()
        im.thumbnail(size, Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", size, (20, 20, 20))
        x = (size[0] - im.width) // 2
        y = (size[1] - im.height) // 2
        canvas.paste(im, (x, y))
        return canvas
    except OSError:
        canvas = Image.new("RGB", size, (20, 20, 20))
        d = ImageDraw.Draw(canvas)
        d.text((12, size[1] // 2 - 8), placeholder[:18], fill=(180, 180, 180))
        return canvas


def _fit_asset(name: str, max_w: int, max_h: int) -> ImageTk.PhotoImage | None:
    im = _load_pil(name)
    if im is None:
        return None
    im = im.copy()
    im.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(im)


class QuickLaunchApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("BeamNG QuickLaunch")
        self.geometry("1100x780")
        self.minsize(960, 680)
        self.configure(bg=BG)

        self.settings = SettingsStore()
        self.cache_path = app_dir() / "cache" / "scan.json"
        self.cache = load_cache(self.cache_path) or ScanCache()
        self._levels: list[LevelInfo] = list(self.cache.levels)
        self._vehicles: list[VehicleInfo] = list(self.cache.vehicles)
        self._scan_thread: threading.Thread | None = None
        self._photo_keep: list[ImageTk.PhotoImage] = []
        self._map_cards: dict[str, tk.Frame] = {}
        self._thumb_cache: dict[str, ImageTk.PhotoImage] = {}
        self._selected_level: str | None = None
        self._selected_veh: str | None = None
        self._level_ids: list[str] = []
        self._veh_ids: list[str] = []
        self._bg_photo: ImageTk.PhotoImage | None = None
        self._filter_job: str | None = None
        self._bg_job: str | None = None
        self._last_bg_size: tuple[int, int] = (0, 0)

        self._setup_style()
        self._build()
        self._load_selection()
        self._refresh_lists()
        self.bind("<Return>", lambda e: self.on_spawn())
        self.bind("<Control-f>", lambda e: self._focus_search())
        self.bind("<Control-F>", lambda e: self._focus_search())
        self.bind("<Configure>", self._on_resize_bg)

        # Prefer fingerprint-fresh cache — no auto full-rescan on every open
        install = Path(self.settings.get("game_install") or "") if self.settings.get("game_install") else find_game_install()
        user = Path(self.settings.get("userfolder") or "") if self.settings.get("userfolder") else find_userfolder()
        fresh = None
        if install and user:
            fresh = cache_is_fresh(self.cache_path, Path(install), Path(user))
        if fresh:
            self.cache = fresh
            self._levels = list(fresh.levels)
            self._vehicles = list(fresh.vehicles)
            self._refresh_lists()
            self._set_status(f"Cache hot: {len(self._levels)} maps, {len(self._vehicles)} vehicles (skip scan)")
        elif not self._levels or not self._vehicles:
            self.after(200, self.on_refresh_scan)
        else:
            self._set_status(f"Loaded cache: {len(self._levels)} maps, {len(self._vehicles)} vehicles")

        # Prewarm Steam in background (ticket warm) — don't block first paint
        if bool(self.settings.get("prewarm_steam", True)):
            self.after(100, self._bg_prewarm_steam)

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", background=BG, foreground=FG, fieldbackground=CARD)
        style.configure("TFrame", background=BG)
        style.configure("Dark.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("TButton", background=CARD, foreground=FG, padding=8)
        style.configure("TCheckbutton", background=BG, foreground=FG)
        style.configure("TEntry", fieldbackground=CARD, foreground=FG, insertcolor=FG)
        style.configure("TRadiobutton", background=BG, foreground=FG)
        style.configure("Horizontal.TProgressbar", troughcolor=CARD, background=ORANGE, bordercolor=BG)
        style.map("TButton", background=[("active", "#222")])

    def _build(self) -> None:
        # wallpaper layer
        self.bg_label = tk.Label(self, bg=BG, borderwidth=0)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        root = tk.Frame(self, bg=BG)
        root.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.content = root

        # header — real Revitalised / BeamNG logo assets
        header = tk.Frame(root, bg=BG)
        header.pack(fill=tk.X, padx=16, pady=(12, 6))

        self._logo_drive = _fit_asset("logo_drive.png", 220, 40)
        self._logo_mark = _fit_asset("logo_mark.png", 48, 42)
        if self._logo_mark:
            tk.Label(header, image=self._logo_mark, bg=BG).pack(side=tk.LEFT, padx=(0, 8))
        if self._logo_drive:
            tk.Label(header, image=self._logo_drive, bg=BG).pack(side=tk.LEFT)
        else:
            tk.Label(header, text=".drive", bg=BG, fg=ORANGE, font=("Segoe UI", 22, "bold italic")).pack(side=tk.LEFT)
        tk.Label(
            header,
            text="  QUICKLAUNCH",
            bg=BG,
            fg=FG,
            font=("Segoe UI", 16, "bold"),
        ).pack(side=tk.LEFT, padx=(10, 0))

        ver = version_status(self.settings.get("game_install"), self.settings.get("userfolder"))
        ver_fg = ORANGE if not ver.get("update_pending") else "#ff4444"
        tk.Label(
            header,
            text=f"  {ver.get('summary', '')}  ·  GFX {self.settings.get('gfx_mode') or DEFAULT_GFX}".upper(),
            bg=BG,
            fg=ver_fg,
            font=("Segoe UI", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(8, 0))

        # side asset buttons (same tiles as Revitalised)
        side = tk.Frame(header, bg=BG)
        side.pack(side=tk.RIGHT)
        self._btn_settings_img = _fit_asset("btn_settings.png", 140, 36)
        self._btn_more_img = _fit_asset("btn_more_features.png", 120, 36)
        if self._btn_settings_img:
            tk.Button(
                side,
                image=self._btn_settings_img,
                command=self.on_settings,
                bg=BG,
                activebackground=BG,
                bd=0,
                highlightthickness=0,
                cursor="hand2",
            ).pack(side=tk.RIGHT, padx=4)
        else:
            tk.Button(side, text="SETTINGS", command=self.on_settings, bg=CARD, fg=FG, bd=0).pack(side=tk.RIGHT)

        # search
        sf = tk.Frame(root, bg=BG)
        sf.pack(fill=tk.X, padx=16, pady=(0, 8))
        tk.Label(sf, text="FILTER", bg=BG, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._debounce_filter())
        self.search_entry = tk.Entry(
            sf,
            textvariable=self.search_var,
            bg=CARD,
            fg=FG,
            insertbackground=FG,
            relief=tk.FLAT,
            font=("Segoe UI", 11),
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, ipady=6)

        # main split: map grid | vehicle+config
        body = tk.Frame(root, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)

        # MAP grid (Revitalised-style cards)
        map_col = tk.Frame(body, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        map_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        tk.Label(map_col, text="MAP SELECT", bg=PANEL, fg=FG, font=("Segoe UI", 12, "bold")).pack(
            anchor="w", padx=10, pady=(8, 4)
        )

        map_wrap = tk.Frame(map_col, bg=PANEL)
        map_wrap.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))
        self.map_canvas = tk.Canvas(map_wrap, bg=PANEL, highlightthickness=0, bd=0)
        self.map_scroll = ttk.Scrollbar(map_wrap, orient=tk.VERTICAL, command=self.map_canvas.yview)
        self.map_inner = tk.Frame(self.map_canvas, bg=PANEL)
        self.map_inner.bind(
            "<Configure>",
            lambda e: self.map_canvas.configure(scrollregion=self.map_canvas.bbox("all")),
        )
        self._map_window = self.map_canvas.create_window((0, 0), window=self.map_inner, anchor="nw")
        self.map_canvas.configure(yscrollcommand=self.map_scroll.set)
        self.map_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.map_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.map_canvas.bind("<Configure>", self._on_map_canvas_cfg)
        self.map_canvas.bind("<Enter>", lambda e: self.map_canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.map_canvas.bind("<Leave>", lambda e: self.map_canvas.unbind_all("<MouseWheel>"))

        # right: vehicle + config
        right = tk.Frame(body, bg=BG, width=340)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)

        veh_box = tk.Frame(right, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        veh_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        tk.Label(veh_box, text="VEHICLE", bg=PANEL, fg=FG, font=("Segoe UI", 12, "bold")).pack(
            anchor="w", padx=10, pady=(8, 4)
        )
        self.veh_list = tk.Listbox(
            veh_box,
            bg=CARD,
            fg=FG,
            selectbackground=ORANGE,
            selectforeground="#000000",
            activestyle="none",
            exportselection=False,
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            highlightthickness=0,
            bd=0,
        )
        vsb = ttk.Scrollbar(veh_box, orient=tk.VERTICAL, command=self.veh_list.yview)
        self.veh_list.configure(yscrollcommand=vsb.set)
        self.veh_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=(0, 8))
        vsb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 8), pady=(0, 8))
        self.veh_list.bind("<<ListboxSelect>>", lambda e: self._on_veh_pick())

        cfg_box = tk.Frame(right, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        cfg_box.pack(fill=tk.BOTH, expand=True)
        tk.Label(cfg_box, text="CONFIG", bg=PANEL, fg=FG, font=("Segoe UI", 12, "bold")).pack(
            anchor="w", padx=10, pady=(8, 4)
        )
        self.cfg_list = tk.Listbox(
            cfg_box,
            bg=CARD,
            fg=FG,
            selectbackground=ORANGE,
            selectforeground="#000000",
            activestyle="none",
            exportselection=False,
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            highlightthickness=0,
            bd=0,
            height=8,
        )
        csb = ttk.Scrollbar(cfg_box, orient=tk.VERTICAL, command=self.cfg_list.yview)
        self.cfg_list.configure(yscrollcommand=csb.set)
        self.cfg_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=(0, 8))
        csb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 8), pady=(0, 8))

        # options row
        opts = tk.Frame(root, bg=BG)
        opts.pack(fill=tk.X, padx=16, pady=6)
        tk.Label(opts, text="SPAWN POINT", bg=BG, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
        self.spawn_var = tk.StringVar(value=self.settings.get("spawn_point", ""))
        tk.Entry(opts, textvariable=self.spawn_var, bg=CARD, fg=FG, insertbackground=FG, relief=tk.FLAT, width=18).pack(
            side=tk.LEFT, padx=6, ipady=4
        )
        self.launch_mode = tk.StringVar(value=self.settings.get("launch_mode", "direct"))
        tk.Radiobutton(
            opts, text="Direct exe", variable=self.launch_mode, value="direct", bg=BG, fg=FG, selectcolor=CARD, activebackground=BG
        ).pack(side=tk.LEFT, padx=8)
        tk.Radiobutton(
            opts, text="Steam", variable=self.launch_mode, value="steam", bg=BG, fg=FG, selectcolor=CARD, activebackground=BG
        ).pack(side=tk.LEFT)
        self.tod_var = tk.StringVar(value=self.settings.get("time_of_day", ""))

        # favorites
        fav_frame = tk.Frame(root, bg=BG)
        fav_frame.pack(fill=tk.X, padx=16)
        tk.Label(fav_frame, text="FAVORITES", bg=BG, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.fav_bar = tk.Frame(fav_frame, bg=BG)
        self.fav_bar.pack(fill=tk.X, pady=4)
        self._rebuild_favorites()

        # launch bar — real LAUNCH asset button
        bar = tk.Frame(root, bg=BG)
        bar.pack(fill=tk.X, padx=16, pady=8)

        self._launch_img = _fit_asset("btn_launch_play.png", 160, 160)
        self._launch_wide = _fit_asset("btn_launch.png", 200, 48)
        launch_holder = tk.Frame(bar, bg=BG)
        launch_holder.pack(side=tk.LEFT)
        if self._launch_img:
            tk.Button(
                launch_holder,
                image=self._launch_img,
                command=self.on_spawn,
                bg=BG,
                activebackground=BG,
                bd=0,
                highlightthickness=0,
                cursor="hand2",
            ).pack(side=tk.LEFT)
        elif self._launch_wide:
            tk.Button(
                launch_holder,
                image=self._launch_wide,
                command=self.on_spawn,
                bg=BG,
                activebackground=BG,
                bd=0,
                cursor="hand2",
            ).pack(side=tk.LEFT)
        else:
            tk.Button(
                launch_holder,
                text="LAUNCH",
                command=self.on_spawn,
                bg=ORANGE,
                fg="#000",
                font=("Segoe UI", 16, "bold"),
                bd=0,
                padx=28,
                pady=12,
            ).pack(side=tk.LEFT)

        tools = tk.Frame(bar, bg=BG)
        tools.pack(side=tk.LEFT, padx=16)
        for text, cmd in (
            ("REFRESH SCAN", self.on_refresh_scan),
            ("★ FAVORITE", self.on_add_favorite),
            ("EDIT LUA", self.on_edit_lua),
        ):
            tk.Button(
                tools,
                text=text,
                command=cmd,
                bg=CARD,
                fg=FG,
                activebackground="#222",
                activeforeground=ORANGE,
                bd=0,
                font=("Segoe UI", 9, "bold"),
                padx=12,
                pady=8,
                cursor="hand2",
            ).pack(side=tk.LEFT, padx=4)

        self.progress = ttk.Progressbar(root, mode="determinate")
        self.progress.pack(fill=tk.X, padx=16, pady=(0, 4))

        logf = tk.Frame(root, bg=BG)
        logf.pack(fill=tk.X, padx=16, pady=(0, 4))
        tk.Label(logf, text="LAUNCH COMMAND", bg=BG, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        row = tk.Frame(logf, bg=BG)
        row.pack(fill=tk.X)
        self.log_var = tk.StringVar(value="(not launched yet)")
        tk.Entry(row, textvariable=self.log_var, bg=CARD, fg=MUTED, relief=tk.FLAT, font=("Consolas", 9)).pack(
            side=tk.LEFT, fill=tk.X, expand=True, ipady=4
        )
        tk.Button(row, text="COPY", command=self.on_copy_cmd, bg=CARD, fg=FG, bd=0, padx=10, pady=4).pack(
            side=tk.LEFT, padx=6
        )

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(root, textvariable=self.status_var, bg=BG, fg=MUTED, anchor="w", font=("Segoe UI", 9)).pack(
            fill=tk.X, padx=16, pady=(0, 10)
        )

        # Wallpaper after first paint — hides launcher load behind UI
        self.after(400, self._paint_bg)

    def _bg_prewarm_steam(self) -> None:
        def work() -> None:
            ready, started = ensure_steam(wait_s=2.0)
            msg = "Steam warm" if ready else "Steam cold"
            if started:
                msg = "Steam prewarmed"
            self.after(0, lambda: self._set_status(f"{self.status_var.get()} · {msg}"))

        threading.Thread(target=work, daemon=True).start()

    def _paint_bg(self) -> None:
        wp = ASSETS / "bg_wallpaper.png"
        if not wp.is_file():
            return
        try:
            w = max(self.winfo_width(), 1100)
            h = max(self.winfo_height(), 780)
            # only repaint when size jumped meaningfully
            if abs(w - self._last_bg_size[0]) < 40 and abs(h - self._last_bg_size[1]) < 40 and self._bg_photo:
                return
            self._last_bg_size = (w, h)
            # downscale source first (wallpaper is 1080p+) — faster than full LANCZOS to window
            im = Image.open(wp).convert("RGB")
            im.thumbnail((max(w, 1280), max(h, 720)), Image.Resampling.BILINEAR)
            im = im.resize((w, h), Image.Resampling.BILINEAR)
            dark = Image.new("RGB", im.size, (0, 0, 0))
            im = Image.blend(im, dark, 0.72)
            self._bg_photo = ImageTk.PhotoImage(im)
            self.bg_label.configure(image=self._bg_photo)
        except OSError:
            pass

    def _on_resize_bg(self, event: tk.Event) -> None:
        if event.widget is self:
            if self._bg_job:
                self.after_cancel(self._bg_job)
            self._bg_job = self.after(350, self._paint_bg)

    def _debounce_filter(self) -> None:
        if self._filter_job:
            self.after_cancel(self._filter_job)
        self._filter_job = self.after(120, self._refresh_lists)

    def _on_map_canvas_cfg(self, event: tk.Event) -> None:
        self.map_canvas.itemconfigure(self._map_window, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> None:
        if self.map_canvas.winfo_containing(event.x_root, event.y_root):
            self.map_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _focus_search(self) -> None:
        self.search_entry.focus_set()
        self.search_entry.selection_range(0, tk.END)

    def _set_status(self, msg: str) -> None:
        self.status_var.set(msg)

    def _filter(self, text: str) -> bool:
        q = self.search_var.get().strip().lower()
        return (not q) or q in text.lower()

    def _load_selection(self) -> None:
        last = self.settings.get("last_selection") or {}
        self._pending_level = last.get("level_id")
        self._pending_veh = last.get("vehicle_id")
        self._pending_cfg = last.get("config_name", "Default")

    def _selected_level_id(self) -> str | None:
        return self._selected_level

    def _selected_vehicle_id(self) -> str | None:
        sel = self.veh_list.curselection()
        if not sel:
            return self._selected_veh
        return self._veh_ids[sel[0]]

    def _selected_config(self) -> str:
        sel = self.cfg_list.curselection()
        if not sel:
            return "Default"
        return self.cfg_list.get(sel[0])

    def _vehicle_by_id(self, vid: str | None) -> VehicleInfo | None:
        if not vid:
            return None
        for v in self._vehicles:
            if v.id == vid:
                return v
        return None

    def _level_by_id(self, lid: str | None) -> LevelInfo | None:
        if not lid:
            return None
        for lv in self._levels:
            if lv.id == lid:
                return lv
        return None

    def _select_level(self, level_id: str) -> None:
        self._selected_level = level_id
        for lid, fr in self._map_cards.items():
            selected = lid == level_id
            fr.configure(
                highlightbackground=ORANGE if selected else BORDER,
                highlightthickness=2 if selected else 1,
                bg=CARD_SEL if selected else CARD,
            )
            for child in fr.winfo_children():
                try:
                    child.configure(bg=CARD_SEL if selected else CARD)  # type: ignore[call-arg]
                except tk.TclError:
                    pass

    def _card_photo(self, lv: LevelInfo) -> ImageTk.PhotoImage:
        cached = self._thumb_cache.get(lv.id)
        if cached is not None:
            return cached
        thumb = _thumb(lv.preview, (CARD_W, CARD_H), lv.name)
        draw = ImageDraw.Draw(thumb)
        draw.rectangle([0, CARD_H - 3, CARD_W, CARD_H], fill=ORANGE)
        photo = ImageTk.PhotoImage(thumb)
        self._thumb_cache[lv.id] = photo
        return photo

    def _build_map_cards(self, level_ids: list[str], prefer: str | None) -> None:
        for w in self.map_inner.winfo_children():
            w.destroy()
        self._map_cards.clear()
        self._photo_keep.clear()

        for i, lid in enumerate(level_ids):
            lv = self._level_by_id(lid)
            if not lv:
                continue
            r, c = divmod(i, MAP_COLS)
            fr = tk.Frame(
                self.map_inner,
                bg=CARD,
                highlightbackground=BORDER,
                highlightthickness=1,
                cursor="hand2",
                width=CARD_W + 8,
                height=CARD_H + 36,
            )
            fr.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
            fr.grid_propagate(False)

            photo = self._card_photo(lv)
            self._photo_keep.append(photo)

            img_lbl = tk.Label(fr, image=photo, bg=CARD, bd=0)
            img_lbl.pack(padx=4, pady=(4, 0))
            name_lbl = tk.Label(
                fr,
                text=lv.name.upper()[:22],
                bg=CARD,
                fg=FG,
                font=("Segoe UI", 8, "bold"),
                wraplength=CARD_W,
            )
            name_lbl.pack(padx=4, pady=(2, 4))

            def bind_all(widget: tk.Widget, lid_=lid) -> None:
                widget.bind("<Button-1>", lambda e, x=lid_: self._select_level(x))

            bind_all(fr)
            bind_all(img_lbl)
            bind_all(name_lbl)
            self._map_cards[lid] = fr

        if prefer and prefer in level_ids:
            self._select_level(prefer)
        elif level_ids:
            self._select_level(level_ids[0])

    def _on_veh_pick(self) -> None:
        self._selected_veh = self._selected_vehicle_id()
        self._reload_configs()

    def _reload_configs(self, prefer: str | None = None) -> None:
        self.cfg_list.delete(0, tk.END)
        v = self._vehicle_by_id(self._selected_vehicle_id())
        configs = v.configs if v else ["Default"]
        for c in configs:
            self.cfg_list.insert(tk.END, c)
        if prefer and prefer in configs:
            self.cfg_list.selection_set(configs.index(prefer))
        else:
            self.cfg_list.selection_set(0)

    def _select_id(self, lb: tk.Listbox, ids: list[str], want: str | None) -> None:
        if want and want in ids:
            idx = ids.index(want)
            lb.selection_clear(0, tk.END)
            lb.selection_set(idx)
            lb.see(idx)
        elif ids:
            lb.selection_set(0)

    def _refresh_lists(self) -> None:
        cur_level = getattr(self, "_pending_level", None) or self._selected_level_id()
        cur_veh = getattr(self, "_pending_veh", None) or self._selected_vehicle_id()
        cur_cfg = getattr(self, "_pending_cfg", None) or self._selected_config()
        self._pending_level = None
        self._pending_veh = None
        self._pending_cfg = None

        self._level_ids = []
        for lv in self._levels:
            label = f"{lv.name} {lv.id}"
            if self._filter(label):
                self._level_ids.append(lv.id)
        self._build_map_cards(self._level_ids, cur_level)

        self.veh_list.delete(0, tk.END)
        self._veh_ids = []
        for v in self._vehicles:
            label = f"{v.name}  [{v.id}]"
            if self._filter(label):
                self.veh_list.insert(tk.END, label)
                self._veh_ids.append(v.id)
        self._select_id(self.veh_list, self._veh_ids, cur_veh)
        self._selected_veh = self._selected_vehicle_id()
        self._reload_configs(prefer=cur_cfg)

    def _persist_selection(self) -> None:
        self.settings.set(
            "last_selection",
            {
                "level_id": self._selected_level_id() or "",
                "vehicle_id": self._selected_vehicle_id() or "",
                "config_name": self._selected_config(),
            },
        )
        self.settings.set("spawn_point", self.spawn_var.get())
        self.settings.set("time_of_day", self.tod_var.get())
        self.settings.set("launch_mode", self.launch_mode.get())
        self.settings.save()

    def _rebuild_favorites(self) -> None:
        for w in self.fav_bar.winfo_children():
            w.destroy()
        favs = self.settings.get("favorites") or []
        if not favs:
            tk.Label(self.fav_bar, text="(none yet)", bg=BG, fg=MUTED).pack(side=tk.LEFT)
            return
        for fav in favs[:12]:
            label = f"{fav.get('level_id','?')} · {fav.get('vehicle_id','?')}"
            tk.Button(
                self.fav_bar,
                text=label,
                command=lambda f=fav: self._apply_favorite(f),
                bg=CARD,
                fg=FG,
                activebackground=ORANGE,
                activeforeground="#000",
                relief=tk.FLAT,
                padx=8,
                pady=4,
                font=("Segoe UI", 8, "bold"),
                cursor="hand2",
            ).pack(side=tk.LEFT, padx=3)

    def _apply_favorite(self, fav: dict) -> None:
        self._pending_level = fav.get("level_id")
        self._pending_veh = fav.get("vehicle_id")
        self._pending_cfg = fav.get("config_name", "Default")
        self.search_var.set("")
        self._refresh_lists()

    def on_add_favorite(self) -> None:
        fav = {
            "level_id": self._selected_level_id(),
            "vehicle_id": self._selected_vehicle_id(),
            "config_name": self._selected_config(),
        }
        if not fav["level_id"] or not fav["vehicle_id"]:
            messagebox.showwarning("Favorite", "Pick a map and vehicle first.")
            return
        favs = list(self.settings.get("favorites") or [])
        if fav not in favs:
            favs.insert(0, fav)
        self.settings.set("favorites", favs[:20])
        self.settings.save()
        self._rebuild_favorites()

    def on_refresh_scan(self) -> None:
        if self._scan_thread and self._scan_thread.is_alive():
            self._set_status("Scan already running…")
            return
        install_s = (self.settings.get("game_install") or "").strip()
        user_s = (self.settings.get("userfolder") or "").strip()
        install = Path(install_s) if install_s else find_game_install()
        user = Path(user_s) if user_s else find_userfolder()
        if not install or not Path(install).is_dir():
            messagebox.showerror("Scan", "Game install not found. Set it in Settings.")
            return
        if not user or not Path(user).is_dir():
            messagebox.showerror("Scan", "Userfolder not found. Set it in Settings.")
            return

        self.progress["value"] = 0
        self._set_status("Scanning…")

        def progress(msg: str, frac: float) -> None:
            self.after(0, lambda: (self.progress.configure(value=frac * 100), self._set_status(msg)))

        scan_mod_zips = bool(self.settings.get("scan_mod_zips", False))

        def work() -> None:
            try:
                cache = scan_all(
                    Path(install),
                    Path(user),
                    progress,
                    scan_mod_zips=scan_mod_zips,
                )
                save_cache(self.cache_path, cache)

                def done() -> None:
                    self.cache = cache
                    self._levels = list(cache.levels)
                    self._vehicles = list(cache.vehicles)
                    self._thumb_cache.clear()
                    self._refresh_lists()
                    self.progress["value"] = 100
                    mode = " + top mod zips" if scan_mod_zips else " (fast)"
                    self._set_status(
                        f"Scan done{mode}: {len(self._levels)} maps, {len(self._vehicles)} vehicles"
                    )

                self.after(0, done)
            except Exception as ex:  # noqa: BLE001
                self.after(0, lambda: messagebox.showerror("Scan failed", str(ex)))

        self._scan_thread = threading.Thread(target=work, daemon=True)
        self._scan_thread.start()

    def _active_lua_template(self) -> str:
        custom = (self.settings.get("custom_lua") or "").strip()
        if custom:
            return custom
        return self.settings.get("lua_template") or ""

    def on_spawn(self) -> None:
        level = self._selected_level_id()
        veh = self._selected_vehicle_id()
        cfg = self._selected_config()
        if not level or not veh:
            messagebox.showwarning("Spawn", "Pick a map and vehicle.")
            return
        self._persist_selection()

        use_level = bool(self.settings.get("use_level_flag", True))
        if (self.settings.get("custom_lua") or "").strip():
            lua_t = self.settings.get("custom_lua")
        elif use_level:
            lua_t = self.settings.get("lua_template")
        else:
            lua_t = self.settings.get("lua_template_full") or self.settings.get("lua_template")

        gfx = self.settings.get("gfx_mode") or DEFAULT_GFX
        vmode = self.settings.get("vehicle_spawn_mode") or "native"
        self._set_status(f"HANDOFF → {gfx.upper()} · {level} · {veh} · spawn={vmode}…")
        self.update_idletasks()

        req = LaunchRequest(
            level_id=level,
            vehicle_id=veh,
            config_name=cfg,
            lua_template=lua_t or "",
            use_level_flag=use_level,
            extra_args=self.settings.get("extra_args") or "",
            spawn_point=self.spawn_var.get(),
            time_of_day=self.tod_var.get(),
            userfolder=self.settings.get("userfolder") or "",
            exe_path=self.settings.get("exe_path") or "",
            launch_mode=self.launch_mode.get(),
            gfx_mode=gfx,
            vehicle_spawn_mode=vmode,
            prewarm_steam=bool(self.settings.get("prewarm_steam", True)),
            check_injectors=bool(self.settings.get("check_injectors", True)),
        )
        try:
            plan = launch(req)
        except Exception as ex:  # noqa: BLE001
            clog = console_log_path(Path(req.userfolder) if req.userfolder else None)
            messagebox.showerror(
                "Launch failed",
                f"{ex}\n\nIf the game opens to the menu, check console:\n{clog}",
            )
            return
        self.log_var.set(plan.display)
        hs = plan.handoff.summary()
        warn = ""
        if plan.handoff.injector_warnings:
            warn = " | INJECTOR WARN — see status / keep SpecialK parked"
            messagebox.showwarning(
                "Injector warning (D3D12)",
                "\n".join(plan.handoff.injector_warnings[:6])
                + "\n\nGame still launched. Remove/park proxy DLLs if D3D12 fails.",
            )
        self._set_status(f"Launched ({hs}){warn}. Log: {plan.console_log}")

    def on_copy_cmd(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.log_var.get())
        self._set_status("Command copied.")

    def on_edit_lua(self) -> None:
        win = tk.Toplevel(self)
        win.title("Startup Lua")
        win.geometry("780x420")
        win.configure(bg=BG)
        tk.Label(
            win,
            text="Placeholders: {LEVEL_ID} {VEHICLE_MODEL} {CONFIG_PATH}",
            bg=BG,
            fg=MUTED,
            justify=tk.LEFT,
        ).pack(anchor="w", padx=10, pady=8)
        text = tk.Text(win, bg=CARD, fg=FG, insertbackground=FG, wrap=tk.WORD, font=("Consolas", 10), relief=tk.FLAT)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        text.insert("1.0", self._active_lua_template())

        bf = tk.Frame(win, bg=BG)
        bf.pack(fill=tk.X, padx=10, pady=8)

        def save() -> None:
            self.settings.set("custom_lua", text.get("1.0", tk.END).strip())
            self.settings.save()
            self._set_status("Custom startup Lua saved.")
            win.destroy()

        def reset() -> None:
            self.settings.set("custom_lua", "")
            self.settings.save()
            text.delete("1.0", tk.END)
            text.insert("1.0", self.settings.get("lua_template") or "")

        tk.Button(bf, text="SAVE", command=save, bg=ORANGE, fg="#000", bd=0, padx=12, pady=6).pack(side=tk.LEFT)
        tk.Button(bf, text="RESET", command=reset, bg=CARD, fg=FG, bd=0, padx=12, pady=6).pack(side=tk.LEFT, padx=6)
        tk.Button(bf, text="CLOSE", command=win.destroy, bg=CARD, fg=FG, bd=0, padx=12, pady=6).pack(side=tk.RIGHT)

    def on_settings(self) -> None:
        win = tk.Toplevel(self)
        win.title("Settings")
        win.geometry("640x480")
        win.configure(bg=BG)

        gear = _fit_asset("icon_gear.png", 48, 48)
        if gear:
            self._settings_gear = gear
            tk.Label(win, image=self._settings_gear, bg=BG).pack(pady=(12, 0))
        tk.Label(win, text="SETTINGS", bg=BG, fg=FG, font=("Segoe UI", 14, "bold")).pack()

        fields = [
            ("game_install", "Game install"),
            ("exe_path", "Exe path"),
            ("userfolder", "Userfolder"),
            ("extra_args", "Extra args"),
        ]
        vars_: dict[str, tk.StringVar] = {}
        for key, label in fields:
            fr = tk.Frame(win, bg=BG)
            fr.pack(fill=tk.X, padx=12, pady=4)
            tk.Label(fr, text=label, width=14, anchor="w", bg=BG, fg=MUTED).pack(side=tk.LEFT)
            var = tk.StringVar(value=str(self.settings.get(key) or ""))
            vars_[key] = var
            tk.Entry(fr, textvariable=var, bg=CARD, fg=FG, insertbackground=FG, relief=tk.FLAT).pack(
                side=tk.LEFT, fill=tk.X, expand=True, ipady=4
            )

            def browse(k=key, v=var) -> None:
                if k == "exe_path":
                    p = filedialog.askopenfilename(filetypes=[("Exe", "*.exe"), ("All", "*.*")])
                else:
                    p = filedialog.askdirectory()
                if p:
                    v.set(p)

            tk.Button(fr, text="…", width=3, command=browse, bg=CARD, fg=FG, bd=0).pack(side=tk.LEFT, padx=4)

        gfx_fr = tk.Frame(win, bg=BG)
        gfx_fr.pack(fill=tk.X, padx=12, pady=8)
        tk.Label(gfx_fr, text="Graphics API", width=14, anchor="w", bg=BG, fg=MUTED).pack(side=tk.LEFT)
        gfx_var = tk.StringVar(value=str(self.settings.get("gfx_mode") or DEFAULT_GFX))
        for label, val in (("D3D12", "d3d12"), ("D3D11", "d3d11"), ("Vulkan", "vulkan")):
            tk.Radiobutton(
                gfx_fr,
                text=label,
                variable=gfx_var,
                value=val,
                bg=BG,
                fg=FG,
                selectcolor=CARD,
                activebackground=BG,
            ).pack(side=tk.LEFT, padx=6)

        veh_fr = tk.Frame(win, bg=BG)
        veh_fr.pack(fill=tk.X, padx=12, pady=4)
        tk.Label(veh_fr, text="Vehicle spawn", width=14, anchor="w", bg=BG, fg=MUTED).pack(side=tk.LEFT)
        vmode_var = tk.StringVar(value=str(self.settings.get("vehicle_spawn_mode") or "native"))
        for label, val in (("Native CLI", "native"), ("Lua hook", "lua"), ("Both", "both")):
            tk.Radiobutton(
                veh_fr,
                text=label,
                variable=vmode_var,
                value=val,
                bg=BG,
                fg=FG,
                selectcolor=CARD,
                activebackground=BG,
            ).pack(side=tk.LEFT, padx=6)

        use_level = tk.BooleanVar(value=bool(self.settings.get("use_level_flag", True)))
        tk.Checkbutton(
            win,
            text="Use -level for map (recommended on 0.39)",
            variable=use_level,
            bg=BG,
            fg=FG,
            selectcolor=CARD,
            activebackground=BG,
        ).pack(anchor="w", padx=12, pady=4)

        prewarm = tk.BooleanVar(value=bool(self.settings.get("prewarm_steam", True)))
        tk.Checkbutton(
            win,
            text="Prewarm Steam on launcher open + before SPAWN",
            variable=prewarm,
            bg=BG,
            fg=FG,
            selectcolor=CARD,
            activebackground=BG,
        ).pack(anchor="w", padx=12)

        check_inj = tk.BooleanVar(value=bool(self.settings.get("check_injectors", True)))
        tk.Checkbutton(
            win,
            text="Warn on Bin64 proxy injectors (dxgi/SpecialK — breaks D3D12)",
            variable=check_inj,
            bg=BG,
            fg=FG,
            selectcolor=CARD,
            activebackground=BG,
        ).pack(anchor="w", padx=12)

        scan_zips = tk.BooleanVar(value=bool(self.settings.get("scan_mod_zips", True)))
        tk.Checkbutton(
            win,
            text="Scan top-level mods/*.zip (never repo/_parked rglob)",
            variable=scan_zips,
            bg=BG,
            fg=FG,
            selectcolor=CARD,
            activebackground=BG,
        ).pack(anchor="w", padx=12)

        tech = tk.BooleanVar(value=bool(self.settings.get("tech_mode", False)))
        tk.Checkbutton(
            win,
            text="Tech mode / BeamNGpy (off by default)",
            variable=tech,
            bg=BG,
            fg=FG,
            selectcolor=CARD,
            activebackground=BG,
        ).pack(anchor="w", padx=12)

        ver = version_status(self.settings.get("game_install"), self.settings.get("userfolder"))
        tk.Label(
            win,
            text=ver.get("summary", ""),
            bg=BG,
            fg=ORANGE,
            font=("Segoe UI", 9),
            wraplength=580,
            justify=tk.LEFT,
        ).pack(anchor="w", padx=12, pady=8)

        def autodect() -> None:
            inst = find_game_install()
            exe = find_exe(inst)
            uf = find_userfolder()
            if inst:
                vars_["game_install"].set(str(inst))
            if exe:
                vars_["exe_path"].set(str(exe))
            if uf:
                vars_["userfolder"].set(str(uf))

        def save() -> None:
            for k, v in vars_.items():
                self.settings.set(k, v.get().strip())
            self.settings.set("use_level_flag", use_level.get())
            self.settings.set("tech_mode", tech.get())
            self.settings.set("scan_mod_zips", scan_zips.get())
            self.settings.set("gfx_mode", gfx_var.get())
            self.settings.set("vehicle_spawn_mode", vmode_var.get())
            self.settings.set("prewarm_steam", prewarm.get())
            self.settings.set("check_injectors", check_inj.get())
            self.settings.set("launch_mode", self.launch_mode.get())
            self.settings.save()
            self._set_status(f"Settings saved. GFX={gfx_var.get()} spawn={vmode_var.get()}")
            win.destroy()

        bf = tk.Frame(win, bg=BG)
        bf.pack(fill=tk.X, padx=12, pady=16)
        tk.Button(bf, text="AUTO-DETECT", command=autodect, bg=CARD, fg=FG, bd=0, padx=12, pady=6).pack(side=tk.LEFT)
        tk.Button(bf, text="SAVE", command=save, bg=ORANGE, fg="#000", bd=0, padx=12, pady=6).pack(side=tk.RIGHT)
        tk.Button(bf, text="CANCEL", command=win.destroy, bg=CARD, fg=FG, bd=0, padx=12, pady=6).pack(
            side=tk.RIGHT, padx=6
        )


def run_app() -> None:
    app = QuickLaunchApp()
    app.mainloop()
