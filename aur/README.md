# 📦 AUR Packaging for Paperizer

This directory contains the ready-to-push PKGBUILDs and `.SRCINFO` files for the Arch User Repository (AUR).

## Package Options

1. **`aur/paperizer/` (Recommended Default)**:
   - Pre-built binary package.
   - Installs the official release wheel (`.whl`) from GitHub Releases via `python -m installer`.
   - Takes 1 second to install via `yay -S paperizer` with zero compilation and zero extra build dependencies.

2. **`aur/paperizer-git/`**:
   - Development package.
   - Clones directly from `git+https://github.com/Refayatul/paperizer.git` and builds from the latest source.

## How to Submit to AUR

### Prerequisites:
1. An active AUR account on [aur.archlinux.org](https://aur.archlinux.org/).
2. Your public SSH key uploaded to your AUR account:
   ```text
   ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGIK5MpBRNbbrz7oKbUzzYLcb8L/sbJiCa6coue2mVsA aur-refayatul
   ```

### Push `paperizer` (Default):
```bash
git clone ssh://aur@aur.archlinux.org/paperizer.git /tmp/aur-paperizer
cp aur/paperizer/* /tmp/aur-paperizer/
cd /tmp/aur-paperizer
git add PKGBUILD .SRCINFO
git commit -m "feat: initial release of paperizer 0.1.0"
git push origin master
```

### Push `paperizer-git`:
```bash
git clone ssh://aur@aur.archlinux.org/paperizer-git.git /tmp/aur-paperizer-git
cp aur/paperizer-git/* /tmp/aur-paperizer-git/
cd /tmp/aur-paperizer-git
git add PKGBUILD .SRCINFO
git commit -m "feat: initial release of paperizer-git"
git push origin master
```
