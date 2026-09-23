<div align="center">

<!-- ANIMATED TYPING HEADER -->
<a href="https://github.com/yourusername/vaultflow">
  <img src="https://readme-typing-svg.demolab.com?font=Consolas&size=26&pause=1000&color=F59E0B&center=true&vCenter=true&width=680&lines=🏛️+VAULTFLOW+:+PRIVATE+ASSET+OS;ZERO-CLOUD+OFFLINE+FINANCIAL+ENGINE;EXECUTIVE+LEDGER+%26+REAL-TIME+ANALYTICS;ENCRYPTED+LOCAL+SQLITE+STORAGE" alt="VaultFlow Dynamic Typing Header" />
</a>

<p align="center">
  <strong>A high-performance, titanium-dark personal finance suite and ledger terminal built with Python, CustomTkinter, and Matplotlib.</strong>
</p>

<!-- DYNAMIC BADGES -->
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-080a11?style=for-the-badge&logo=python&logoColor=f59e0b" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/GUI-CustomTkinter-080a11?style=for-the-badge&logo=airplayvideo&logoColor=00f0ff" alt="CustomTkinter" />
  <img src="https://img.shields.io/badge/Database-SQLite3%20Local-080a11?style=for-the-badge&logo=sqlite&logoColor=00f5a0" alt="SQLite3" />
  <img src="https://img.shields.io/badge/Analytics-Matplotlib-080a11?style=for-the-badge&logo=chartdotjs&logoColor=c084fc" alt="Matplotlib" />
  <img src="https://img.shields.io/badge/Packaging-PyInstaller%20Ready-080a11?style=for-the-badge&logo=windows&logoColor=38bdf8" alt="PyInstaller" />
  <img src="https://img.shields.io/badge/License-MIT-080a11?style=for-the-badge&logo=open-source-initiative&logoColor=ffffff" alt="MIT License" />
</p>

<!-- INTERACTIVE NAVIGATION BAR -->
<p align="center">
  <a href="#-system-overview">Overview</a> •
  <a href="#-key-capabilities">Capabilities</a> •
  <a href="#-interactive-tour--deep-dive">Feature Tour</a> •
  <a href="#-keyboard-control-deck">Hotkeys</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-quickstart--installation">Quickstart</a> •
  <a href="#-compilation-to-exe">Build Executable</a>
</p>

---

</div>

## ⚡ System Overview

**VaultFlow** is engineered for individuals who reject cloud-hosted financial apps, surveillance banking telemetry, and clunky spreadsheets. Operating strictly offline on your local device, VaultFlow pairs the aesthetic of an **executive asset vault** with cryptographic-grade local data isolation.

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │  [🏛️ VAULTFLOW PRIVATE ASSET OS]                                      │
 │                                                                        │
 │  [// INFLOW LIQUIDITY]   [// OUTFLOW BURN]    [// NET ASSET RESERVE]   │
 │   $142,500.00             $38,210.00           $104,290.00             │
 │   ▲ +18.4% MoM            ▼ -4.2% MoM          ▲ Solvency 73.1%        │
 │                                                                        │
 │  [ANALYTICS ENGINE]                           [LEDGER AUDIT LOG]       │
 │   • Status Distribution (Donut)                • 2026-09-21: Retainer  │
 │   • Monthly Burn Velocity (Line Graph)         • 2026-09-18: Cloud HW  │
 │   • Channel Allocation (Funnel Bars)           • 2026-09-14: Dividend  │
 └────────────────────────────────────────────────────────────────────────┘

```

---

## 💎 Key Capabilities

---

## 🔍 Interactive Tour & Deep Dive

The central command dashboard aggregates all fiscal nodes into real-time visual streams:

* **Executive Metric Cards:** Real-time calculation of gross inflow, burn outflow, net balance, and transaction count.
* **Dual Visualization Engine:**
* **Interactive Donut & Pie Views:** Switch between Classic Pie, Modern Donut, or Exploded slices for category allocation.
* **Chrono Trend Line Charts:** Analyze 6-month burn rates vs. inflow reserves with gradient-filled vectors.
* **Conduit Funnel Analysis:** Track volume passing through UPI, Wire transfers, Corporate Cards, and Cash.



Data entry is organized into a dedicated full-screen workspace with intelligent validation:

* **Keystroke Guard:** Enforces strict numeric validation while allowing fluid shorthand notation (`k`, `m`, `b`, `cr`, `lakh`).
* **Directional Ledger Flow:** Segmented toggle dynamically updates account labels (`"Money Debited From"` vs `"Money Credited In"`).
* **Chrono-Picker Dialog:** Custom inline calendar and hour/minute selector for timestamp precision.
* **Inline Taxonomy Injection:** Add new expense or income categories on the fly without navigating away.

* **Pre-Decided Export Path:** Configure an immutable folder destination once (defaults to `./exports`).
* **Zero-Prompt 1-Click Export:** Clicking `⚡ Instant Export to Excel` bypasses repetitive save file dialogs and writes timestamped `.xlsx` files straight to disk.
* **Explorer Integration:** Includes an `Open Folder` trigger to reveal exported files in Windows Explorer immediately.
* **Ledger Purge Safeguard:** Two-step confirmation system for wiping transaction records while maintaining taxonomy rules.

---

## ⌨️ Keyboard Control Deck

VaultFlow features global hotkeys for keyboard-driven navigation:

| Key Binding | Function | Scope |
| --- | --- | --- |
| Ctrl + 1 | Jump to **Vault Dashboard** | Global Window |
| Ctrl + 2 | Open **Full-Screen Transaction Terminal** | Global Window |
| Ctrl + 3 | Open **Vault Parameters & Settings** | Global Window |
| F5 | Force Re-render & Refresh Analytics Telemetry | Dashboard |
| Esc | Dismiss Active Modal / Dropdown | Active Dialog |

---

## 🏗️ Architecture

```text
vaultflow/
├── app.py              # Root window controller, DPI-scaling & view router
├── database.py         # SQLite engine, shorthand math parser & migrations
├── metrics.py          # Top telemetry cards & financial notation formatters
├── analytics.py        # Embedded Matplotlib canvas (Donuts, Line & Funnel charts)
├── history.py          # High-density audited transaction ledger with badge pills
├── entry_view.py       # Full-screen asset ingestion terminal & keystroke filter
├── settings_view.py    # Predetermined export manager & taxonomy configurator
├── dialogs.py          # Inline category injectors & visual calendar picker
└── vaultflow_icon.ico  # High-resolution multi-size Windows icon

```

---

## 🚀 Quickstart & Installation

### Prerequisites

* Python `3.10` or higher
* Windows 10 / 11 (Per-Monitor DPI scaling supported)

### 1. Clone the Repository

```bash
git clone [https://github.com/yourusername/vaultflow.git](https://github.com/yourusername/vaultflow.git)
cd vaultflow

```

### 2. Configure Virtual Environment

```powershell
# Create virtual environment
python -m venv .venv

# Activate environment (PowerShell)
.\.venv\Scripts\Activate.ps1

```

### 3. Install Dependencies

```powershell
pip install customtkinter matplotlib pandas openpyxl pillow

```

### 4. Launch VaultFlow

```powershell
python app.py

```

---

## 📦 Compilation to Standalone .exe

Build a completely portable, single-file Windows executable with embedded assets and no external Python dependency:

```powershell
# Install compiler
pip install pyinstaller

# Build single-file production binary
pyinstaller --noconsole `
            --onefile `
            --icon="vaultflow_icon.ico" `
            --add-data "vaultflow_icon.ico;." `
            --collect-all customtkinter `
            --name "VaultFlow" `
            app.py

```

> **Build Output:** Your portable binary is generated at `dist/VaultFlow.exe`. Move it anywhere—it auto-initializes `vaultflow.db` and `./exports` in its directory.

---

### 🏛️ VaultFlow — Private Wealth & Asset Operating System

Designed with precision. Built for sovereign financial ownership.