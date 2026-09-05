# Paperizer 📜✨

> **A quiet, native PDF reader & warm paper styler for Linux, Windows & macOS.**  
> Inspired by the distraction-free philosophy of [Humanitas Labs' Paper](https://github.com/humanitas-labs/paper) and built on [Paperize](https://github.com/humanitas-labs/paperize).

[![GitHub Release](https://img.shields.io/github/v/release/Refayatul/paperizer?color=emerald&label=Release&logo=github)](https://github.com/Refayatul/paperizer/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-blue.svg)](#installation-guide)
[![Nix](https://img.shields.io/badge/NixFlake-Ready-5277C3.svg?logo=nixos)](flake.nix)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![GUI: Qt6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt6-41CD52.svg?logo=qt)](https://www.qt.io/)

<p align="center">
  <img src="assets/icon.svg" width="128" height="128" alt="Paperizer Icon" />
</p>

---

## Quick Downloads (v0.1.1)

| Platform | Format | Package | Install Command / Action |
| :--- | :--- | :--- | :--- |
| **Windows 10 / 11** | Setup Wizard | [**`Paperizer-0.1.1-Setup-x64.exe`**](https://github.com/Refayatul/paperizer/releases/download/v0.1.1/Paperizer-0.1.1-Setup-x64.exe) | Double-click to install (Desktop, Start Menu, Explorer context menu) |
| **Windows 10 / 11** | Portable ZIP | [**`Paperizer-0.1.1-Windows-Portable.zip`**](https://github.com/Refayatul/paperizer/releases/download/v0.1.1/Paperizer-0.1.1-Windows-Portable.zip) | Extract anywhere & run `Paperizer.exe` (Zero install needed) |
| **Arch / CachyOS** | Native Package | [**`paperizer-0.1.1-1-any.pkg.tar.zst`**](https://github.com/Refayatul/paperizer/releases/download/v0.1.1/paperizer-0.1.1-1-any.pkg.tar.zst) | `sudo pacman -U <url>` or `yay -S paperizer` |
| **Debian / Ubuntu** | `.deb` | [**`paperizer_0.1.1-1_all.deb`**](https://github.com/Refayatul/paperizer/releases/download/v0.1.1/paperizer_0.1.1-1_all.deb) | `sudo apt install ./paperizer_0.1.1-1_all.deb` |
| **Fedora / RHEL** | `.rpm` | [**`paperizer-0.1.1-1.noarch.rpm`**](https://github.com/Refayatul/paperizer/releases/download/v0.1.1/paperizer-0.1.1-1.noarch.rpm) | `sudo dnf install <url>` |
| **NixOS** | Flake | `github:Refayatul/paperizer` | `nix run github:Refayatul/paperizer` |
| **Gentoo** | Ebuild | [`packaging/gentoo/`](packaging/gentoo/) | Copy to local overlay or run via `pipx` |
| **macOS & Other Linux** | Universal Python | [**`paperizer-0.1.1-py3-none-any.whl`**](https://github.com/Refayatul/paperizer/releases/download/v0.1.1/paperizer-0.1.1-py3-none-any.whl) | `pipx install <url>` |

---

## Design Philosophy: Radical Minimalism

Most PDF readers are covered in bulky toolbars, side panels, and menus that invite you to do everything other than read.

**Paperizer puts the document first.**
- **Full-Bleed Quiet Canvas**: Nothing between you and the reading material.
- **Default to Warm Paper**: Opens directly in peaceful, eye-friendly paper mode.
- **Auto-Fading Capsule**: A subtle glass pill dock floats quietly at the bottom and gently hides after 3.2 seconds of reading.
- **Non-Destructive Vector Warmth**: Text, vector graphics, and links are never rasterized or degraded. Harsh white glare is transformed into soft organic paper.
- 🎨 **Aesthetic Reading Presets**:
  - **Parchment**: Soft golden-warm antique paper with subtle radial falloff.
  - **Cream**: Gentle off-white/ivory ideal for prolonged night reading.
  - **Sepia**: Classic library vintage aesthetic.
- 🛠️ **Real-Time Fine-Tuning**: Sliders for Warmth/Strength, Paper Texture grain, and Vignette falloff.
- ⚡ **Zero-Freeze Multithreading**: Background rendering workers (`QThread`) ensure the UI stays responsive even when rendering high-DPI document previews.
- 📂 **Batch Processing**: Queue entire directories of books, whitepapers, or planners and convert them with one click.
- 🖥️ **Cross-Platform System Integration**:
  - **Linux (KDE / GNOME)**: Native Wayland and X11 rendering; automatically mirrors system color palettes (Breeze Light / Dark).
  - **Windows (10 / 11)**: Native taskbar grouping (`AppUserModelID`), crisp high-DPI scaling, and right-click Explorer context menu integration.
  - **macOS**: Native Cocoa window frames and dark/light system appearance.

---

## Architecture & Technology Stack

```mermaid
graph TD
    A[Input PDF] --> B[PyMuPDF Page Extractor]
    B --> C[Background Preview Worker]
    C --> D[Paperize Stream Transformation Engine]
    D --> E[Interactive Split Curtain Canvas]
    E --> F[Qt6 Native GUI - PySide6]
    D --> G[Batch Export Pipeline]
    G --> H[Final Vector-Preserved PDF]
```

- **Frontend**: PySide6 (Qt 6.6+)
- **Retina Preview Engine**: PyMuPDF (`fitz`) with supersampled rendering
- **PDF Manipulation Engine**: `pikepdf` + `paperize-pdf`
- **Supported Operating Systems**:
  - **Linux**: Arch Linux / CachyOS, Debian / Ubuntu, Fedora / RHEL, NixOS, Gentoo, Void, Alpine, openSUSE
  - **Windows**: Windows 10 & 11 (64-bit)
  - **macOS**: Apple Silicon (M-series) & Intel

---

## Installation Guide

### 1. Windows 10 & 11

- **Setup Installer (`.exe`)**:
  Download [**`Paperizer-0.1.1-Setup-x64.exe`**](https://github.com/Refayatul/paperizer/releases/download/v0.1.1/Paperizer-0.1.1-Setup-x64.exe) and run the wizard. Adds Desktop & Start Menu shortcuts, an uninstaller in Windows Settings, and right-click *"Open with Paperizer"* for `.pdf` files.
- **Portable Standalone (`.zip`)**:
  Download [**`Paperizer-0.1.1-Windows-Portable.zip`**](https://github.com/Refayatul/paperizer/releases/download/v0.1.1/Paperizer-0.1.1-Windows-Portable.zip), unzip anywhere, and run `Paperizer.exe`. No admin rights or installation required.

### 2. Arch Linux / CachyOS / Manjaro

```bash
# 1-line native install:
sudo pacman -U https://github.com/Refayatul/paperizer/releases/download/v0.1.1/paperizer-0.1.1-1-any.pkg.tar.zst

# Or via AUR helper (instant wheel, 0 compilation):
yay -S paperizer

# Or tracking git master:
yay -S paperizer-git
```

### 3. Debian / Ubuntu / Linux Mint / Pop!_OS

```bash
curl -LO https://github.com/Refayatul/paperizer/releases/download/v0.1.1/paperizer_0.1.1-1_all.deb
sudo apt install ./paperizer_0.1.1-1_all.deb
```

### 4. Fedora / RHEL / openSUSE

```bash
sudo dnf install https://github.com/Refayatul/paperizer/releases/download/v0.1.1/paperizer-0.1.1-1.noarch.rpm
```

### 5. NixOS (Flake)

Run Paperizer instantly without installation:
```bash
nix run github:Refayatul/paperizer
```

Or add to your NixOS configuration:
```nix
# flake.nix
inputs.paperizer.url = "github:Refayatul/paperizer";

# In your environment.systemPackages:
environment.systemPackages = [
  inputs.paperizer.packages.${system}.default
];
```

### 6. Gentoo Linux

- **Via `pipx`**:
  ```bash
  emerge --ask dev-python/pipx
  pipx install https://github.com/Refayatul/paperizer/releases/download/v0.1.1/paperizer-0.1.1-py3-none-any.whl
  ```
- **Via Portage Ebuild**:
  An ebuild is included in [`packaging/gentoo/paperizer-0.1.1.ebuild`](packaging/gentoo/paperizer-0.1.1.ebuild). Copy it into your local overlay (e.g. `/var/db/repos/local/gui-apps/paperizer/`) and run `ebuild paperizer-0.1.1.ebuild digest && emerge gui-apps/paperizer`.

### 7. Universal Linux (Void, Alpine, Solus, Slackware) & macOS

Any OS with Python 3.11+ can install Paperizer cleanly in an isolated sandbox using [`pipx`](https://pypa.github.io/pipx/):

```bash
# Install pipx (if not already installed)
# macOS: brew install pipx
# Void: xbps-install -S python3-pipx
# Alpine: apk add pipx

# Install Paperizer
pipx install https://github.com/Refayatul/paperizer/releases/download/v0.1.1/paperizer-0.1.1-py3-none-any.whl

# Run anywhere:
paperizer
```

### 8. Developer / From Source

```bash
git clone https://github.com/Refayatul/paperizer.git
cd paperizer

python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

pip install -e .
paperizer
```

---

## Usage & Controls

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
