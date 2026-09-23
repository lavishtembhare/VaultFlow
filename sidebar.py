import customtkinter as ctk

class SidebarView(ctk.CTkFrame):
    def __init__(self, parent, on_navigate):
        super().__init__(parent, width=230, corner_radius=0, fg_color="#080a11", border_width=0)
        self.on_navigate = on_navigate
        self.nav_buttons = {}

        self.grid_rowconfigure(5, weight=1)

        # VaultFlow Brand Header
        header_box = ctk.CTkFrame(self, fg_color="transparent")
        header_box.grid(row=0, column=0, padx=20, pady=(24, 25), sticky="w")

        ctk.CTkLabel(
            header_box, text="🏛️ VAULTFLOW",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color="#f59e0b"
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_box, text="// PRIVATE ASSET OS",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            text_color="#64748b"
        ).pack(anchor="w")

        # Nav Buttons with Banking Ledger Tags
        nav_items = [
            ("dashboard", "📊  Vault Dashboard"),
            ("add_entry", "💳  Log Transaction"),
            ("settings", "⚙️  Vault Parameters")
        ]

        for idx, (key, label) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self,
                text=label,
                anchor="w",
                height=42,
                font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                fg_color="transparent",
                hover_color="#141a29",
                text_color="#94a3b8",
                corner_radius=8,
                command=lambda k=key: self.select_nav(k)
            )
            btn.grid(row=idx, column=0, padx=14, pady=4, sticky="ew")
            self.nav_buttons[key] = btn

        self.set_active("dashboard")

        # Vault Security Status Box
        security_card = ctk.CTkFrame(self, fg_color="#0e121d", corner_radius=8, border_width=1, border_color="#1c2336")
        security_card.grid(row=6, column=0, padx=14, pady=16, sticky="ew")

        ctk.CTkLabel(
            security_card, text="● VAULT SECURED",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            text_color="#10b981"
        ).pack(anchor="w", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            security_card, text="AES-Safe Offline SQLite",
            font=ctk.CTkFont(size=9),
            text_color="#64748b"
        ).pack(anchor="w", padx=12, pady=(0, 8))

    def select_nav(self, key):
        self.set_active(key)
        self.on_navigate(key)

    def set_active(self, key):
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(
                    fg_color="#161c2d",
                    text_color="#f59e0b",
                    hover_color="#1c243a",
                    border_width=1,
                    border_color="#2c3752"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color="#94a3b8",
                    hover_color="#111625",
                    border_width=0
                )