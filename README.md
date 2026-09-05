# Paperizer 📜✨

> **A quiet, native PDF reader & warm paper styler for Linux.**  
> Inspired by the distraction-free philosophy of [Humanitas Labs' Paper](https://github.com/humanitas-labs/paper) and built on [Paperize](https://github.com/humanitas-labs/paperize).

![Paperizer Banner](assets/icon.svg)

---

## Design Philosophy: Radical Minimalism

Most PDF readers are covered in bulky toolbars, side panels, and menus that invite you to do everything other than read.

**Paperizer puts the document first.**
- **Full-Bleed Quiet Canvas**: Nothing between you and the reading material.
- **Default to Warm Paper**: Opens directly in peaceful, eye-friendly paper mode.
- **Auto-Fading Capsule**: A subtle glass pill dock floats quietly at the bottom and gently hides after 3 seconds of reading.
- **Non-Destructive Vector Warmth**: Text, vector graphics, and links are never rasterized or degraded. White glare becomes soft paper.
- 🎨 **Aesthetic Reading Presets**:
  - **Parchment**: Soft golden-warm antique paper with subtle radial falloff.
  - **Cream**: Gentle off-white/ivory ideal for prolonged night reading.
  - **Sepia**: Classic library vintage aesthetic.
- 🛠️ **Real-Time Fine-Tuning**: Sliders for Warmth/Strength, Paper Texture grain, and Vignette falloff.
- ⚡ **Zero-Freeze Multithreading**: Background rendering workers (`QThread`) ensure the UI stays responsive even when rendering high-DPI document previews.
- 📂 **Batch Processing**: Queue entire directories of books, whitepapers, or planners and convert them with one click.
- 🐧 **Native KDE Plasma & Linux Integration**: Automatically follows system color palettes (Breeze Light / Dark) and runs natively on Wayland and X11.

---

## Architecture & Technology Stack

```mermaid
graph TD
    A[Input PDF] --> B[PyMuPDF Page Extractor]
    B --> C[Background Preview Worker]
    C --> D[Paperize Stream Transformation Engine]
    D --> E[Interactive Split Curtain Canvas]
    E --> F[KDE Plasma Qt6 GUI]
    D --> G[Batch Export Pipeline]
    G --> H[Final Vector-Preserved PDF]
```

- **Frontend**: PySide6 (Qt 6.11+)
- **Rendering & Preview**: PyMuPDF (`fitz`)
- **PDF Manipulation Engine**: `pikepdf` + `paperize-pdf`
- **Target OS**: Linux (CachyOS / Arch Linux / KDE Plasma / Wayland)

---

## Installation

### 1. Arch Linux / CachyOS / Manjaro

**Direct native install (1-liner):**
```bash
sudo pacman -U https://github.com/Refayatul/paperizer/releases/download/v0.1.0/paperizer-0.1.0-1-any.pkg.tar.zst
```

**Or via AUR:**
```bash
yay -S paperizer
# or for git master:
yay -S paperizer-git
```

### 2. Debian / Ubuntu / Linux Mint / Pop!_OS

Download and install the native `.deb`:
```bash
curl -LO https://github.com/Refayatul/paperizer/releases/download/v0.1.0/paperizer_0.1.0-1_all.deb
sudo apt install ./paperizer_0.1.0-1_all.deb
```

### 3. Fedora / RHEL / openSUSE

Direct RPM install:
```bash
sudo dnf install https://github.com/Refayatul/paperizer/releases/download/v0.1.0/paperizer-0.1.0-1.noarch.rpm
```

### 4. Developer / From Source

```bash
# Clone the repository
git clone https://github.com/Refayatul/paperizer.git
cd paperizer

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies and package
pip install -e .

# Run the app
paperizer
```

---

## Usage

```bash
# Launch GUI directly
paperizer

# Open a specific PDF immediately on launch
paperizer path/to/document.pdf
```

### Keyboard & Reading Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **`0`** or **`R`** | **Fit to Reading** (life-size book reading width) |
| **`W`** | **Fit Width** |
| **`P`** | **Fit Page** (full-page overview) |
| **`+`** / **`-`** (or `Ctrl` + Scroll) | Zoom in / Zoom out |
| **`Up`** / **`Down`** (or Mouse Scroll) | Smooth vertical reading pan |
| **`PageUp`** / **`PageDown`** | Fast scroll jump |
| **`Space`** / **`→`** / **`←`** | Next / Previous page |
| **`1`** / **`2`** / **`3`** | Parchment / Cream / Sepia presets |
| **`Tab`** | Toggle Split Curtain ↔ Full Paper |
| **`F`** / **`F11`** | Distraction-free Fullscreen |
| **`Ctrl + O`** | Open PDF document |
| **`Ctrl + S`** | Export paperized PDF |

---

## License

MIT License. Core PDF stream transformation algorithm courtesy of [Humanitas Labs / Paperize](https://github.com/humanitas-labs/paperize).

