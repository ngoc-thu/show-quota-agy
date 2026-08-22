# Antigravity Quota Monitor 🚀

Native Ubuntu / GNOME desktop application and Top Bar indicator to monitor real-time Google Antigravity quota and rate limits.

---

## 🌟 Features

* **Real-time Antigravity Quota Tracking**: Fetches live percentage fractions and reset countdowns directly from active sessions.
* **Automatic Authentication**: Discovers active OAuth credentials via Linux GNOME Keyring / Secret Service (`service=gemini, username=antigravity`) without manual API key entry.
* **GNOME Top Bar Indicator**: Displays current quota status (e.g. `🚀 AG 79%`) with dynamic colored badge indicators.
* **Interactive Popup Menu**: Click the Top Bar indicator to view per-model progress bars, rate limit groups (5-hour and weekly limits), and quick actions.
* **GTK4 / Libadwaita Dashboard GUI**: Modern Ubuntu dark mode interface featuring:
  - 🏠 **Tổng quan (Overview)**: Model cards, smooth progress bars, thinking/recommended tags, and reset timers.
  - 📊 **Lịch sử (History)**: Cairo-rendered time-series timeline chart (1h, 6h, 24h, 7d, 30d).
  - ⚙ **Cài đặt (Settings)**: Autostart, refresh intervals, alert thresholds, display modes, and connection diagnostics.
  - ℹ **Giới thiệu (About)**: Version and system details.
* **Desktop Notifications**: Alerts when quota drops below warning threshold or replenishes.
* **SQLite Historical Persistence**: Local time-series database for offline tracking.
* **CLI Tool (`antigravity-quota`)**: Rich Unicode colored output, `--json`, `--debug`, `--refresh`.
* **Zero Credential Leaking**: Logs and diagnostics automatically scrub tokens and sensitive keys.

---

## 📋 Requirements

* **Ubuntu 22.04 LTS, 24.04 LTS**, or newer GNOME-based Linux distributions.
* **Python 3.10+**
* System dependencies:
  ```bash
  sudo apt install -y python3-gi python3-dbus python3-cairo gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-appindicator3-0.1
  ```

---

## 🚀 Quick Start & CLI Usage

### View Quota in Terminal
```bash
./antigravity-quota
```
Output:
```text
🚀 Antigravity Quota Monitor
────────────────────────────────────────────────────────────
  Claude Opus 4.6 (Thinking) [★]
  ███████████████░   95.9% (Reset: 4h 25m)

  Gemini 3.6 Flash (High)    [★]
  ███████████████░   95.7% (Reset: 4h 52m)

  GPT-OSS 120B (Medium)      [★]
  ███████████████░   95.9% (Reset: 4h 25m)

Hạn mức nhóm (Rate Limit Groups):
  • Gemini Models: weekly: 81.3% (reset: 3d 3h) | 5h: 95.7% (reset: 4h 52m)
  • Claude and GPT models: weekly: 88.1% (reset: 6d 7h) | 5h: 95.9% (reset: 4h 25m)

────────────────────────────────────────────────────────────
Trạng thái: 🟢 Live  |  Cập nhật: 17:14:32
```

### Additional CLI Commands
```bash
# Output JSON
./antigravity-quota --json

# Force live API reload
./antigravity-quota --refresh

# Run environment & auth diagnostics
./antigravity-quota --debug

# Launch GTK4 Dashboard GUI
./antigravity-quota --gui

# Launch GNOME Top Bar Indicator
./antigravity-quota --tray

# Print Version
./antigravity-quota --version
```

---

## 📦 Installation

### Option 1: Install Debian Package (.deb)
```bash
# Build package
./packaging/build_deb.sh

# Install package
sudo dpkg -i antigravity-quota-monitor_1.0.0_all.deb
```

After installation, the application is available in the Ubuntu Application Menu and `antigravity-quota` is in your `$PATH`.

### Option 2: Local User Installation
```bash
# Enable autostart
mkdir -p ~/.config/autostart
cp assets/antigravity-quota-monitor.desktop ~/.config/autostart/

# Desktop launcher
mkdir -p ~/.local/share/applications ~/.local/share/icons/hicolor/scalable/apps
cp assets/antigravity-quota-monitor.desktop ~/.local/share/applications/
cp assets/icons/antigravity-quota-monitor.svg ~/.local/share/icons/hicolor/scalable/apps/
```

---

## 🧪 Development & Testing

Run the automated test suite:
```bash
python3 -m unittest discover -s tests -v
```

---

## 📂 Project Architecture

```text
antigravity-quota-monitor/
├── src/
│   ├── core/
│   │   ├── models.py          # Data models & percentage calculations
│   │   ├── config.py          # Configuration & constants
│   │   ├── logger.py          # Token-sanitizing logger
│   │   └── service.py         # Central QuotaService & auto-refresh
│   ├── antigravity/
│   │   ├── auth.py            # Keyring & DBus Secret Service credential provider
│   │   ├── detector.py        # Process & environment detector
│   │   ├── client.py          # Google CloudCode PA HTTPS client
│   │   └── parser.py          # API response normalizer
│   ├── storage/
│   │   ├── db.py              # SQLite manager & migrations
│   │   ├── history_repo.py    # Time-series history repository
│   │   └── settings_repo.py   # Preferences repository
│   ├── notifications/
│   │   └── notifier.py        # Desktop notification manager
│   ├── autostart/
│   │   └── manager.py         # XDG autostart configuration
│   ├── tray/
│   │   ├── indicator.py       # GNOME Top Bar AppIndicator
│   │   └── menu.py            # Top Bar popup menu builder
│   ├── ui/
│   │   ├── app.py             # Libadwaita Application entrypoint
│   │   ├── window.py          # Main dashboard window with navigation sidebar
│   │   ├── style.py           # Custom CSS styling (dark, purple accent)
│   │   └── views/             # Overview, History, Settings, About views
│   └── cli/
│       └── main.py            # Command-line interface
├── assets/
│   ├── icons/                 # SVG vector application icon
│   └── antigravity-quota-monitor.desktop
├── docs/
│   └── ANTIGRAVITY_PROTOCOL.md # Reverse-engineered protocol specification
├── packaging/
│   └── build_deb.sh           # Debian package builder
├── tests/                     # Comprehensive test suite
├── antigravity-quota          # Executable launcher
├── README.md
└── LICENSE
```

---

## 🗑 Uninstallation

If installed via `.deb`:
```bash
sudo dpkg -r antigravity-quota-monitor
```

To remove local SQLite history and logs:
```bash
rm -rf ~/.local/share/antigravity-quota-monitor ~/.config/antigravity-quota-monitor ~/.config/autostart/antigravity-quota-monitor.desktop
```
