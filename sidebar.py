import customtkinter as ctk

class SidebarView(ctk.CTkFrame):
    def __init__(self, parent, on_navigate, icon_image=None):
        super().__init__(parent, width=260, corner_radius=0, fg_color="#090d16", border_width=0)
        self.on_navigate = on_navigate
        self.nav_buttons = {}
        self.ctk_icon = None

        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        # Brand Header with App Icon
        header_box = ctk.CTkFrame(self, fg_color="transparent")
        header_box.grid(row=0, column=0, padx=24, pady=(32, 28), sticky="ew")

        if icon_image is not None:
            self.ctk_icon = ctk.CTkImage(light_image=icon_image, dark_image=icon_image, size=(40, 40))
            icon_lbl = ctk.CTkLabel(header_box, text="", image=self.ctk_icon)
            icon_lbl.pack(side="left", padx=(0, 12))

        title_col = ctk.CTkFrame(header_box, fg_color="transparent")
        title_col.pack(side="left", fill="x")

        ctk.CTkLabel(
            title_col, text="VaultFlow",
            font=ctk.CTkFont(size=21, weight="bold"),
            text_color="#f8fafc"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col, text="Private Asset Suite",
            font=ctk.CTkFont(size=12),
            text_color="#64748b"
        ).pack(anchor="w")

        nav_items = [
            ("dashboard", "📊   Dashboard"),
            ("add_entry", "➕   New Transaction"),
            ("logs", "📋   Transaction Logs"),
            ("settings", "⚙️   Settings")
        ]

        for idx, (key, label) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self,
                text=label,
                anchor="w",
                height=48,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="transparent",
                hover_color="#131b2e",
                text_color="#94a3b8",
                corner_radius=10,
                command=lambda k=key: self.select_nav(k)
            )
            btn.grid(row=idx, column=0, padx=18, pady=5, sticky="ew")
            self.nav_buttons[key] = btn

        self.set_active("dashboard")

        # Minimal Offline Status Card
        security_card = ctk.CTkFrame(self, fg_color="#0f1523", corner_radius=12, border_width=1, border_color="#1e293b")
        security_card.grid(row=7, column=0, padx=18, pady=24, sticky="ew")

        ctk.CTkLabel(
            security_card, text="●  Local Vault Active",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#10b981"
        ).pack(anchor="w", padx=16, pady=(12, 2))

        ctk.CTkLabel(
            security_card, text="Offline SQLite Storage  •  F11 Fullscreen",
            font=ctk.CTkFont(size=11),
            text_color="#64748b"
        ).pack(anchor="w", padx=16, pady=(0, 12))

    def select_nav(self, key):
        self.set_active(key)
        self.on_navigate(key)

    def set_active(self, key):
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(
                    fg_color="#162035",
                    text_color="#38bdf8",
                    hover_color="#1c2842",
                    border_width=1,
                    border_color="#28385c"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color="#94a3b8",
                    hover_color="#111827",
                    border_width=0
                )