import customtkinter as ctk

class SidebarView(ctk.CTkFrame):
    def __init__(self, parent, on_navigate, icon_image=None):
        super().__init__(parent, width=235, corner_radius=0, fg_color="#090d16", border_width=0)
        self.on_navigate = on_navigate
        self.nav_buttons = {}
        self.ctk_icon = None

        self.grid_rowconfigure(6, weight=1)

        # Brand Header with App Icon
        header_box = ctk.CTkFrame(self, fg_color="transparent")
        header_box.grid(row=0, column=0, padx=20, pady=(26, 24), sticky="ew")

        if icon_image is not None:
            self.ctk_icon = ctk.CTkImage(light_image=icon_image, dark_image=icon_image, size=(34, 34))
            icon_lbl = ctk.CTkLabel(header_box, text="", image=self.ctk_icon)
            icon_lbl.pack(side="left", padx=(0, 10))

        title_col = ctk.CTkFrame(header_box, fg_color="transparent")
        title_col.pack(side="left", fill="x")

        ctk.CTkLabel(
            title_col, text="VaultFlow",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#f8fafc"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col, text="Private Asset Suite",
            font=ctk.CTkFont(size=11),
            text_color="#64748b"
        ).pack(anchor="w")

        # Navigation Tabs (Added Separate Transaction Logs Tab)
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
                height=42,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="transparent",
                hover_color="#131b2e",
                text_color="#94a3b8",
                corner_radius=10,
                command=lambda k=key: self.select_nav(k)
            )
            btn.grid(row=idx, column=0, padx=16, pady=4, sticky="ew")
            self.nav_buttons[key] = btn

        self.set_active("dashboard")

        # Minimal Offline Status Card
        security_card = ctk.CTkFrame(self, fg_color="#0f1523", corner_radius=10, border_width=1, border_color="#1e293b")
        security_card.grid(row=7, column=0, padx=16, pady=18, sticky="ew")

        ctk.CTkLabel(
            security_card, text="●  Local Vault Active",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#10b981"
        ).pack(anchor="w", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            security_card, text="Offline SQLite Storage",
            font=ctk.CTkFont(size=10),
            text_color="#64748b"
        ).pack(anchor="w", padx=14, pady=(0, 10))

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