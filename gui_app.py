import tkinter as tk
from tkinter import ttk, messagebox

import customtkinter as ctk

import storage
import monitor

STATUS_REFRESH_MS = 3000
WATCHLIST_REFRESH_MS = 8000

BG = "#17181c"
CARD = "#212227"
BORDER = "#34363c"
TEXT = "#e7e8ea"
MUTED = "#9aa0aa"
ACCENT = "#6366f1"
ACCENT_HOVER = "#818cf8"
DANGER = "#ef4444"
DANGER_HOVER = "#dc2626"
OK = "#4ade80"
OFF = "#6b7280"
ROW_ALT = "#26272d"

FONT_FAMILY = "Segoe UI Variable"
FONT_SIZE_TITLE = 26
FONT_SIZE_SECTION = 18
FONT_SIZE_BODY = 15
FONT_SIZE_META = 14

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def ui_font(size, weight="normal"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def card(parent, title=None):
    frame = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12, border_width=1, border_color=BORDER)
    if title:
        ctk.CTkLabel(frame, text=title, font=ui_font(FONT_SIZE_SECTION, "bold"), text_color=TEXT).pack(
            anchor="w", padx=18, pady=(14, 8)
        )
    return frame


def _setup_treeview_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Dark.Treeview",
        background=CARD,
        fieldbackground=CARD,
        foreground=TEXT,
        rowheight=36,
        borderwidth=0,
        font=(FONT_FAMILY, FONT_SIZE_META),
    )
    style.configure(
        "Dark.Treeview.Heading",
        background=BG,
        foreground=MUTED,
        relief="flat",
        font=(FONT_FAMILY, FONT_SIZE_META, "bold"),
    )
    style.map(
        "Dark.Treeview",
        background=[("selected", ACCENT)],
        foreground=[("selected", "#ffffff")],
    )
    style.map("Dark.Treeview.Heading", background=[("active", BORDER)])
    style.layout("Dark.Treeview", [("Dark.Treeview.treearea", {"sticky": "nswe"})])

    style.configure(
        "Dark.Vertical.TScrollbar",
        background=CARD,
        troughcolor=BG,
        bordercolor=BG,
        arrowcolor=MUTED,
    )


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YT 直播留言監控")
        self.geometry("920x920")
        self.minsize(760, 680)
        self.configure(fg_color=BG)

        _setup_treeview_style()

        self.watchlist_cache = []
        self.sort_key = "last_seen"
        self.sort_reverse = True
        self.column_headings = {
            "enabled": "啟用",
            "name": "名稱",
            "channel_id": "Channel ID",
            "note": "備註",
            "count": "留言次數",
            "last_seen": "最後留言",
        }

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=BG)
        self.scroll.pack(fill="both", expand=True, padx=14, pady=14)
        self.scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.scroll,
            text="YT 直播留言監控",
            font=ui_font(FONT_SIZE_TITLE, "bold"),
            text_color=TEXT,
        ).pack(
            anchor="w", pady=(0, 2)
        )
        ctk.CTkLabel(
            self.scroll,
            text="自動偵測指定頻道開播，比對名單內帳號的留言，符合就推送到 Discord",
            font=ui_font(FONT_SIZE_META),
            text_color=MUTED,
        ).pack(anchor="w", pady=(0, 14))

        self._build_status_card()
        self._build_settings_card()
        self._build_watchlist_card()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._load_settings()
        self._refresh_status()
        self._refresh_watchlist()

    # ---------- status ----------
    def _build_status_card(self):
        frame = card(self.scroll, "目前狀態")
        frame.pack(fill="x", pady=(0, 12))

        grid = ctk.CTkFrame(frame, fg_color="transparent")
        grid.pack(fill="x", padx=18, pady=(0, 6))

        self.status_dot = ctk.CTkLabel(grid, text="", width=10, height=10, corner_radius=5, fg_color=OFF)
        self.status_dot.grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.status_labels = {}
        fields = [
            ("is_live", "直播狀態"),
            ("video_id", "影片 ID"),
            ("last_checked", "上次檢查"),
            ("last_message_at", "最後收到留言"),
            ("matched_count", "已通知次數"),
        ]
        col = 1
        for key, label in fields:
            box = ctk.CTkFrame(grid, fg_color="transparent")
            box.grid(row=0, column=col, sticky="w", padx=(0, 22))
            ctk.CTkLabel(box, text=label, font=ui_font(FONT_SIZE_META), text_color=MUTED).pack(anchor="w")
            val = ctk.CTkLabel(box, text="-", font=ui_font(FONT_SIZE_BODY, "bold"), text_color=TEXT)
            val.pack(anchor="w")
            self.status_labels[key] = val
            col += 1

        self.error_label = ctk.CTkLabel(frame, text="", font=ui_font(FONT_SIZE_META), text_color=DANGER)
        self.error_label.pack(anchor="w", padx=18, pady=(0, 12))

    def _refresh_status(self):
        s = monitor.get_status()
        self.status_dot.configure(fg_color=OK if s["is_live"] else OFF)
        self.status_labels["is_live"].configure(text="直播中" if s["is_live"] else "未偵測到直播")
        self.status_labels["video_id"].configure(text=s["video_id"] or "-")
        self.status_labels["last_checked"].configure(text=s["last_checked"] or "-")
        self.status_labels["last_message_at"].configure(text=s["last_message_at"] or "-")
        self.status_labels["matched_count"].configure(text=str(s["matched_count"]))
        self.error_label.configure(text=("錯誤：" + s["last_error"]) if s.get("last_error") else "")
        self.after(STATUS_REFRESH_MS, self._refresh_status)

    # ---------- settings ----------
    def _build_settings_card(self):
        frame = card(self.scroll, "監控設定")
        frame.pack(fill="x", pady=(0, 12))

        row1 = ctk.CTkFrame(frame, fg_color="transparent")
        row1.pack(fill="x", padx=18)
        row1.grid_columnconfigure((0, 1, 2), weight=1)

        col1 = ctk.CTkFrame(row1, fg_color="transparent")
        col1.grid(row=0, column=0, sticky="we", padx=(0, 10))
        ctk.CTkLabel(
            col1,
            text="要監控的頻道 Channel ID",
            font=ui_font(FONT_SIZE_META),
            text_color=MUTED,
        ).pack(anchor="w")
        self.var_channel_id = ctk.StringVar()
        ctk.CTkEntry(
            col1,
            textvariable=self.var_channel_id,
            font=ui_font(FONT_SIZE_BODY),
            fg_color=BG,
            border_color=BORDER,
            text_color=TEXT,
        ).pack(
            fill="x", pady=(2, 0)
        )

        col2 = ctk.CTkFrame(row1, fg_color="transparent")
        col2.grid(row=0, column=1, sticky="we", padx=10)
        ctk.CTkLabel(
            col2,
            text="頻道名稱（僅供顯示）",
            font=ui_font(FONT_SIZE_META),
            text_color=MUTED,
        ).pack(anchor="w")
        self.var_channel_name = ctk.StringVar()
        ctk.CTkEntry(
            col2,
            textvariable=self.var_channel_name,
            font=ui_font(FONT_SIZE_BODY),
            fg_color=BG,
            border_color=BORDER,
            text_color=TEXT,
        ).pack(
            fill="x", pady=(2, 0)
        )

        col3 = ctk.CTkFrame(row1, fg_color="transparent")
        col3.grid(row=0, column=2, sticky="we", padx=(10, 0))
        ctk.CTkLabel(
            col3,
            text="偵測間隔（秒）",
            font=ui_font(FONT_SIZE_META),
            text_color=MUTED,
        ).pack(anchor="w")
        self.var_interval = ctk.StringVar()
        ctk.CTkEntry(
            col3,
            textvariable=self.var_interval,
            font=ui_font(FONT_SIZE_BODY),
            fg_color=BG,
            border_color=BORDER,
            text_color=TEXT,
        ).pack(
            fill="x", pady=(2, 0)
        )

        ctk.CTkLabel(
            frame,
            text="Discord Webhook 網址",
            font=ui_font(FONT_SIZE_META),
            text_color=MUTED,
        ).pack(
            anchor="w", padx=18, pady=(12, 0)
        )
        self.var_webhook = ctk.StringVar()
        ctk.CTkEntry(
            frame,
            textvariable=self.var_webhook,
            font=ui_font(FONT_SIZE_BODY),
            fg_color=BG,
            border_color=BORDER,
            text_color=TEXT,
        ).pack(
            fill="x", padx=18, pady=(2, 0)
        )

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(anchor="w", padx=18, pady=14)
        ctk.CTkButton(
            btn_row,
            text="儲存設定",
            font=ui_font(FONT_SIZE_BODY),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._save_settings,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_row,
            text="測試 Discord 通知",
            font=ui_font(FONT_SIZE_BODY),
            fg_color="transparent",
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            hover_color=ROW_ALT,
            command=self._test_webhook,
        ).pack(side="left")

    def _load_settings(self):
        s = storage.load_settings()
        self.var_channel_id.set(s.get("channel_id", ""))
        self.var_channel_name.set(s.get("channel_name", ""))
        self.var_interval.set(str(s.get("live_check_interval_sec", 60)))
        self.var_webhook.set(s.get("discord_webhook_url", ""))

    def _save_settings(self):
        try:
            interval = int(self.var_interval.get() or "60")
        except ValueError:
            messagebox.showerror("錯誤", "偵測間隔請輸入數字")
            return
        storage.save_settings({
            "channel_id": self.var_channel_id.get().strip(),
            "channel_name": self.var_channel_name.get().strip(),
            "live_check_interval_sec": interval,
            "discord_webhook_url": self.var_webhook.get().strip(),
        })
        messagebox.showinfo("已儲存", "設定已儲存")

    def _test_webhook(self):
        webhook_url = self.var_webhook.get().strip()
        if not webhook_url:
            messagebox.showerror("錯誤", "請先填寫 Discord Webhook 網址")
            return
        import requests
        try:
            r = requests.post(webhook_url, json={"content": "✅ 測試通知：YT 留言監控已連接成功"}, timeout=10)
            r.raise_for_status()
        except Exception as exc:
            messagebox.showerror("失敗", str(exc))
            return
        messagebox.showinfo("成功", "已送出測試通知，請檢查 Discord")

    # ---------- watchlist ----------
    def _build_watchlist_card(self):
        frame = card(self.scroll, "追蹤名單")
        frame.pack(fill="both", expand=True, pady=(0, 12))

        ctk.CTkLabel(
            frame,
            text="留言過的人會自動出現在下方（預設關閉），找到大哥後點兩下「啟用」欄打勾",
            font=ui_font(FONT_SIZE_META),
            text_color=MUTED,
        ).pack(anchor="w", padx=18)

        top_row = ctk.CTkFrame(frame, fg_color="transparent")
        top_row.pack(fill="x", padx=18, pady=(8, 8))
        ctk.CTkLabel(
            top_row,
            text="搜尋名稱",
            font=ui_font(FONT_SIZE_META),
            text_color=MUTED,
        ).pack(side="left")
        self.var_filter = ctk.StringVar()
        self.var_filter.trace_add("write", lambda *a: self._render_watchlist())
        ctk.CTkEntry(
            top_row,
            textvariable=self.var_filter,
            font=ui_font(FONT_SIZE_BODY),
            width=200,
            fg_color=BG,
            border_color=BORDER,
            text_color=TEXT,
        ).pack(side="left", padx=(6, 0))
        ctk.CTkButton(
            top_row,
            text="重新整理",
            font=ui_font(FONT_SIZE_BODY),
            width=80,
            fg_color="transparent",
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            hover_color=ROW_ALT,
            command=self._refresh_watchlist,
        ).pack(side="right")
        ctk.CTkButton(
            top_row,
            text="刪除選取",
            font=ui_font(FONT_SIZE_BODY),
            width=80,
            fg_color="transparent",
            border_width=1,
            border_color=DANGER,
            text_color=DANGER,
            hover_color=ROW_ALT,
            command=self._delete_selected,
        ).pack(side="right", padx=(0, 8))

        add_frame = ctk.CTkFrame(frame, fg_color=BG, corner_radius=10, border_width=1, border_color=BORDER)
        add_frame.pack(fill="x", padx=18, pady=(0, 10))
        inner = ctk.CTkFrame(add_frame, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=10)
        self.var_new_name = ctk.StringVar()
        self.var_new_channel_id = ctk.StringVar()
        self.var_new_note = ctk.StringVar()
        ctk.CTkEntry(
            inner, textvariable=self.var_new_name, placeholder_text="名稱", font=ui_font(FONT_SIZE_BODY), width=140,
            fg_color=CARD, border_color=BORDER, text_color=TEXT,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkEntry(
            inner,
            textvariable=self.var_new_channel_id,
            placeholder_text="Channel ID（選填）",
            font=ui_font(FONT_SIZE_BODY),
            width=200,
            fg_color=CARD, border_color=BORDER, text_color=TEXT,
        ).pack(side="left", padx=6)
        ctk.CTkEntry(
            inner,
            textvariable=self.var_new_note,
            placeholder_text="備註（選填）",
            font=ui_font(FONT_SIZE_BODY),
            width=120,
            fg_color=CARD, border_color=BORDER, text_color=TEXT,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            inner,
            text="新增",
            font=ui_font(FONT_SIZE_BODY),
            width=60,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._add_entry,
        ).pack(side="left", padx=(6, 0))

        tree_wrap = tk.Frame(frame, background=CARD)
        tree_wrap.pack(fill="both", expand=True, padx=18, pady=(0, 16))

        columns = ("enabled", "name", "channel_id", "note", "count", "last_seen")
        self.tree = ttk.Treeview(tree_wrap, columns=columns, show="headings", height=14, style="Dark.Treeview")
        widths = {"enabled": 55, "name": 140, "channel_id": 190, "note": 90, "count": 80, "last_seen": 150}
        for col in columns:
            self.tree.heading(col, text=self.column_headings[col], command=lambda c=col: self._on_sort_click(c))
            self.tree.column(col, width=widths[col], anchor="center" if col in ("enabled", "count") else "w")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Button-1>", self._on_tree_click)
        self.tree.tag_configure("odd", background=ROW_ALT)
        self.tree.tag_configure("even", background=CARD)

        scrollbar = ttk.Scrollbar(
            tree_wrap, orient="vertical", command=self.tree.yview, style="Dark.Vertical.TScrollbar"
        )
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self._update_heading_labels()

    def _on_tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        row_id = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not row_id or col != "#1":
            return
        entry = next((e for e in self.watchlist_cache if e["id"] == row_id), None)
        if entry is None:
            return
        new_enabled = not entry.get("enabled", False)
        storage.update_watchlist_entry(row_id, {"enabled": new_enabled})
        entry["enabled"] = new_enabled
        self._render_watchlist()

    def _on_sort_click(self, col):
        if self.sort_key == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_key = col
            self.sort_reverse = col in ("count", "last_seen", "enabled")
        self._update_heading_labels()
        self._render_watchlist()

    def _update_heading_labels(self):
        for col, label in self.column_headings.items():
            if col == self.sort_key:
                arrow = " ▼" if self.sort_reverse else " ▲"
                self.tree.heading(col, text=label + arrow)
            else:
                self.tree.heading(col, text=label)

    _SORT_GETTERS = {
        "enabled": lambda e: bool(e.get("enabled")),
        "name": lambda e: (e.get("name") or "").lower(),
        "channel_id": lambda e: e.get("channel_id") or "",
        "note": lambda e: e.get("note") or "",
        "count": lambda e: e.get("message_count", 0),
        "last_seen": lambda e: e.get("last_seen") or "",
    }

    def _refresh_watchlist(self):
        self.watchlist_cache = storage.load_watchlist()
        self._render_watchlist()
        self.after(WATCHLIST_REFRESH_MS, self._refresh_watchlist)

    def _render_watchlist(self):
        filt = self.var_filter.get().strip().lower()
        rows = self.watchlist_cache
        if filt:
            rows = [e for e in rows if filt in (e.get("name") or "").lower()]
        getter = self._SORT_GETTERS[self.sort_key]
        rows = sorted(rows, key=getter, reverse=self.sort_reverse)

        selected = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for i, e in enumerate(rows):
            self.tree.insert(
                "", "end", iid=e["id"],
                values=(
                    "✅" if e.get("enabled") else "⬜",
                    e.get("name", ""),
                    e.get("channel_id", "") or "-",
                    e.get("note", ""),
                    e.get("message_count", 0),
                    e.get("last_seen", "-") or "-",
                ),
                tags=("odd" if i % 2 else "even",),
            )
        still_present = [i for i in selected if self.tree.exists(i)]
        if still_present:
            self.tree.selection_set(still_present)

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("提示", "請先在清單中選取要刪除的項目")
            return
        if not messagebox.askyesno("確認刪除", f"確定要刪除選取的 {len(sel)} 筆追蹤對象嗎？"):
            return
        for entry_id in sel:
            storage.delete_watchlist_entry(entry_id)
        self.watchlist_cache = storage.load_watchlist()
        self._render_watchlist()

    def _add_entry(self):
        name = self.var_new_name.get().strip()
        if not name:
            messagebox.showerror("錯誤", "請輸入名稱")
            return
        storage.add_watchlist_entry(name, self.var_new_channel_id.get().strip(), self.var_new_note.get().strip())
        self.var_new_name.set("")
        self.var_new_channel_id.set("")
        self.var_new_note.set("")
        self.watchlist_cache = storage.load_watchlist()
        self._render_watchlist()

    def _on_close(self):
        self.destroy()


if __name__ == "__main__":
    monitor.start_background_thread()
    App().mainloop()
