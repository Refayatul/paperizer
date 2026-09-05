# 📜 Paperizer — Project Directives & AI Agent Knowledge Base

> **Notice for AI Assistants**: This repository is **Paperizer** — a quiet, native Linux PDF eye-comfort reader and warm paper styler. This file contains persistent architecture rules, repository details, multi-distro packaging blueprints, and the complete AUR publishing roadmap.

---

## 1. Project & Repository Identity

- **Name**: Paperizer (executable: `paperizer`, alias: `paperize-gui`)
- **Repository**: [https://github.com/Refayatul/paperizer](https://github.com/Refayatul/paperizer)
- **Author / Maintainer**: Refayatul (`refayatul`)
- **License**: MIT (`LICENSE`)
- **Design Philosophy**: Radical minimalism inspired by Humanitas Labs' [Paper](https://github.com/humanitas-labs/paper) and [Paperize](https://github.com/humanitas-labs/paperize).
- **Core Technology Stack**:
  - Python 3.11+
  - PySide6 (Qt 6.11+)
  - PyMuPDF (`fitz`) for 240 DPI retina rendering
  - `pikepdf` for vector stream transformation
  - Vendored fallback engine in `src/paperize_gui/vendor/paperize/` (zero missing Arch dependencies)

---

## 2. Arch User Repository (AUR) Publishing Blueprint

### Architecture
We maintain two AUR package specifications in `aur/`:
1. **`aur/paperizer/` (Default Recommended Package)**:
   - Pre-built binary/wheel package (`paperizer`).
   - Downloads the release wheel from GitHub and installs via `python -m installer`.
   - **Why**: Installs in under 1 second on Arch/CachyOS with zero compiling, zero build dependencies, and zero chance of environment breakage.
2. **`aur/paperizer-git/`**:
   - Bleeding-edge VCS package tracking the `main` git branch from source.

### SSH Authentication for AUR
When registering on the AUR, use the configured SSH key:
- **Public Key**:
  ```text
  ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGIK5MpBRNbbrz7oKbUzzYLcb8L/sbJiCa6coue2mVsA aur-refayatul
  ```
- **Local SSH Config (`~/.ssh/config`)**:
  ```ssh-config
  Host aur.archlinux.org
    User aur
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new
  ```

### AUR Registration Status & Publishing Instructions
- **Current Status**: AUR account registration was temporarily closed by Arch Infrastructure (HTTP 503) due to an automated spam bot attack.
- **Action as soon as Arch reopens registration**:
  1. Open [https://aur.archlinux.org/register](https://aur.archlinux.org/register), create account with username `refayatul`, and paste the SSH public key above.
  2. Clone the AUR repository:
     ```bash
     git clone ssh://aur@aur.archlinux.org/paperizer.git /tmp/aur-paperizer
     ```
  3. Copy the prepared files from this repository:
     ```bash
     cp /path/to/paperizer/aur/paperizer/* /tmp/aur-paperizer/
     cd /tmp/aur-paperizer
     git add PKGBUILD .SRCINFO
     git commit -m "feat: initial release of paperizer 0.1.0"
     git push origin master
     ```
  4. (Optional) Repeat for `paperizer-git`:
     ```bash
     git clone ssh://aur@aur.archlinux.org/paperizer-git.git /tmp/aur-paperizer-git
     cp /path/to/paperizer/aur/paperizer-git/* /tmp/aur-paperizer-git/
     cd /tmp/aur-paperizer-git
     git add PKGBUILD .SRCINFO
     git commit -m "feat: initial release of paperizer-git"
     git push origin master
     ```

---

## 3. Multi-Distro Packaging Pipeline

Paperizer produces native packages for all major Linux distributions:
- **Arch Linux / CachyOS**: `.pkg.tar.zst` (installable via `sudo pacman -U`)
- **Debian / Ubuntu / Mint**: `.deb` (installable via `sudo apt install`)
- **Fedora / RHEL / openSUSE**: `.rpm` (installable via `sudo dnf install`)
- **Universal Python**: `.whl` (installable via `pip install`)

### Packaging Automation
- **GitHub Actions (`.github/workflows/release.yml`)**:
  Automatically runs on every release tag (`v*`) or manual `workflow_dispatch`, compiles all 4 packages, and attaches them to the GitHub release.
- **Local Build Script (`scripts/build_all_packages.py`)**:
  Can be run on any Linux system to compile all packages locally into `dist/`:
  ```bash
  python3 scripts/build_all_packages.py
  ```

---

## 4. Key UI & Functional Conventions

1. **Default Reading Fit (`fit_to_reading`)**:
   - Documents must always open at life-size book width (~58% of viewport, clamped between 640px and 860px) aligned to the top (`y = 24px`).
   - Window resizing must never violently reset or shrink the user's zoom factor.
2. **Quiet Distraction-Free Dock**:
   - Floating glass pill dock with 3.2s idle fade timer.
   - Visible controls: Open, Presets (Parchment, Cream, Sepia), Mode (Paper, Split), Warmth slider, Zoom cluster (`[−]`, `slider 40–250%`, `[+]`, `[ 100% ]` reset badge), Page navigation, Export.
3. **Wayland Portal Logging**:
   - `app.py` sets `QT_LOGGING_RULES="qt.qpa.services=false"` to silence internal DBus host portal registration warnings on Wayland/KDE.
