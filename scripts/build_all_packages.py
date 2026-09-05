#!/usr/bin/env python3
"""Build universal .whl, Arch .pkg.tar.zst, Debian .deb, and Fedora .rpm packages."""

import os
import shutil
import subprocess
import zipfile
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"
DIST_DIR.mkdir(exist_ok=True)

VERSION = "0.1.0"
PKG_NAME = "paperizer"
WHEEL_NAME = f"{PKG_NAME}-{VERSION}-py3-none-any.whl"
WHEEL_PATH = DIST_DIR / WHEEL_NAME
PY_VER = f"python{sys.version_info.major}.{sys.version_info.minor}"


def build_wheel() -> Path:
    print("[1/4] Building Python wheel...")
    python_bin = sys.executable
    venv_py = ROOT_DIR / ".venv/bin/python"
    try:
        subprocess.check_call([python_bin, "-c", "import build"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        if venv_py.exists():
            python_bin = str(venv_py)

    subprocess.check_call([
        python_bin, "-m", "build", "--wheel", "--outdir", str(DIST_DIR)
    ], cwd=str(ROOT_DIR))
    print("✓ Wheel ready:", WHEEL_PATH)
    return WHEEL_PATH


def build_arch_pkg() -> Path:
    print("[2/4] Building Arch Linux (.pkg.tar.zst)...")
    build_dir = Path("/tmp/paperizer_arch_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)

    # 1. Unpack wheel into site-packages
    site_packages = build_dir / f"usr/lib/{PY_VER}/site-packages"
    site_packages.mkdir(parents=True)
    with zipfile.ZipFile(WHEEL_PATH, "r") as z:
        z.extractall(site_packages)

    # 2. Add bin scripts
    bin_dir = build_dir / "usr/bin"
    bin_dir.mkdir(parents=True)
    paperizer_bin = bin_dir / "paperizer"
    paperizer_bin.write_text("""#!/usr/bin/env python3
import sys
from paperize_gui.app import main
if __name__ == "__main__":
    sys.exit(main())
""")
    paperizer_bin.chmod(0o755)

    (bin_dir / "paperize-gui").symlink_to("paperizer")

    # 3. Add desktop file & icon & license
    app_dir = build_dir / "usr/share/applications"
    app_dir.mkdir(parents=True)
    shutil.copy(ROOT_DIR / "paperizer.desktop", app_dir / "paperizer.desktop")

    icon_dir = build_dir / "usr/share/icons/hicolor/scalable/apps"
    icon_dir.mkdir(parents=True)
    shutil.copy(ROOT_DIR / "assets/icon.svg", icon_dir / "paperizer.svg")

    lic_dir = build_dir / "usr/share/licenses/paperizer"
    lic_dir.mkdir(parents=True)
    shutil.copy(ROOT_DIR / "LICENSE", lic_dir / "LICENSE")

    # 4. Generate .PKGINFO
    pkginfo = f"""pkgname = {PKG_NAME}
pkgver = {VERSION}-1
pkgdesc = A quiet, native PDF reader & warm paper styler for Linux
url = https://github.com/Refayatul/paperizer
builddate = 1788590000
packager = Refayatul <https://github.com/Refayatul>
size = 220000
arch = any
license = MIT
depend = python>=3.11
depend = pyside6
depend = python-pikepdf
depend = python-pymupdf
provides = paperizer
provides = paperize-gui
conflict = paperizer-git
conflict = paperize-gui
"""
    (build_dir / ".PKGINFO").write_text(pkginfo)

    out_pkg = DIST_DIR / f"{PKG_NAME}-{VERSION}-1-any.pkg.tar.zst"
    subprocess.check_call([
        "bsdtar", "-cf", str(out_pkg),
        "--zstd",
        "-C", str(build_dir),
        ".PKGINFO", "usr"
    ])
    print("✓ Arch package ready:", out_pkg, f"({out_pkg.stat().st_size} bytes)")
    return out_pkg


def build_deb_pkg() -> Path:
    print("[3/4] Building Debian/Ubuntu (.deb)...")
    staging_dir = Path("/tmp/paperizer_deb_staging")
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True)

    # 1. Staging files
    dist_packages = staging_dir / "usr/lib/python3/dist-packages"
    dist_packages.mkdir(parents=True)
    with zipfile.ZipFile(WHEEL_PATH, "r") as z:
        z.extractall(dist_packages)

    bin_dir = staging_dir / "usr/bin"
    bin_dir.mkdir(parents=True)
    bin_script = bin_dir / "paperizer"
    bin_script.write_text("""#!/usr/bin/env python3
import sys
from paperize_gui.app import main
if __name__ == "__main__":
    sys.exit(main())
""")
    bin_script.chmod(0o755)
    (bin_dir / "paperize-gui").symlink_to("paperizer")

    app_dir = staging_dir / "usr/share/applications"
    app_dir.mkdir(parents=True)
    shutil.copy(ROOT_DIR / "paperizer.desktop", app_dir / "paperizer.desktop")

    icon_dir = staging_dir / "usr/share/icons/hicolor/scalable/apps"
    icon_dir.mkdir(parents=True)
    shutil.copy(ROOT_DIR / "assets/icon.svg", icon_dir / "paperizer.svg")

    doc_dir = staging_dir / "usr/share/doc/paperizer"
    doc_dir.mkdir(parents=True)
    shutil.copy(ROOT_DIR / "LICENSE", doc_dir / "copyright")

    # 2. DEBIAN/control
    debian_meta = staging_dir / "DEBIAN"
    debian_meta.mkdir()
    control_content = f"""Package: {PKG_NAME}
Version: {VERSION}-1
Architecture: all
Maintainer: Refayatul <https://github.com/Refayatul>
Installed-Size: 220
Depends: python3 (>= 3.11), python3-pyside6 | python3-pyqt6, python3-pikepdf, python3-fitz
Section: graphics
Priority: optional
Homepage: https://github.com/Refayatul/paperizer
Description: A quiet, native PDF reader & warm paper styler for Linux
 Paperizer transforms harsh white PDF content streams into soothing,
 eye-comfort paper tones (Parchment, Cream, Sepia) while preserving 100%
 vector graphics and searchable text.
"""
    (debian_meta / "control").write_text(control_content)

    out_deb = DIST_DIR / f"{PKG_NAME}_{VERSION}-1_all.deb"
    subprocess.check_call([
        "dpkg-deb", "--root-owner-group", "--build", str(staging_dir), str(out_deb)
    ])
    print("✓ Debian package ready:", out_deb, f"({out_deb.stat().st_size} bytes)")
    return out_deb


def build_rpm_pkg() -> Path:
    print("[4/4] Building Fedora/RHEL (.rpm)...")
    rpm_root = Path("/tmp/paperizer_rpm_build")
    if rpm_root.exists():
        shutil.rmtree(rpm_root)

    for sub in ["BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS", "db"]:
        (rpm_root / sub).mkdir(parents=True)

    source_stage = rpm_root / "stage"
    source_stage.mkdir(parents=True)

    # 1. Populate source_stage
    py_dir = source_stage / f"usr/lib/{PY_VER}/site-packages"
    py_dir.mkdir(parents=True)
    with zipfile.ZipFile(WHEEL_PATH, "r") as z:
        z.extractall(py_dir)

    bin_dir = source_stage / "usr/bin"
    bin_dir.mkdir(parents=True)
    bin_script = bin_dir / "paperizer"
    bin_script.write_text("""#!/usr/bin/env python3
import sys
from paperize_gui.app import main
if __name__ == "__main__":
    sys.exit(main())
""")
    bin_script.chmod(0o755)
    (bin_dir / "paperize-gui").symlink_to("paperizer")

    app_dir = source_stage / "usr/share/applications"
    app_dir.mkdir(parents=True)
    shutil.copy(ROOT_DIR / "paperizer.desktop", app_dir / "paperizer.desktop")

    icon_dir = source_stage / "usr/share/icons/hicolor/scalable/apps"
    icon_dir.mkdir(parents=True)
    shutil.copy(ROOT_DIR / "assets/icon.svg", icon_dir / "paperizer.svg")

    lic_dir = source_stage / "usr/share/licenses/paperizer"
    lic_dir.mkdir(parents=True)
    shutil.copy(ROOT_DIR / "LICENSE", lic_dir / "LICENSE")

    # 2. Create RPM Spec
    spec_path = rpm_root / "SPECS" / "paperizer.spec"
    spec_content = f"""Name:           {PKG_NAME}
Version:        {VERSION}
Release:        1
Summary:        A quiet, native PDF reader & warm paper styler for Linux
License:        MIT
URL:            https://github.com/Refayatul/paperizer
BuildArch:      noarch
Requires:       python3 >= 3.11, python3-pyside6, python3-pikepdf, python3-pymupdf
AutoReqProv:    no

%description
Paperizer transforms harsh white PDF content streams into soothing,
eye-comfort paper tones (Parchment, Cream, Sepia) while preserving 100%
vector graphics and searchable text.

%install
cp -r {source_stage}/* %{{buildroot}}/

%files
/usr/bin/paperizer
/usr/bin/paperize-gui
/usr/lib/python*/*-packages/*
/usr/share/applications/paperizer.desktop
/usr/share/icons/hicolor/scalable/apps/paperizer.svg
/usr/share/licenses/paperizer/LICENSE

%changelog
* Sat Sep 05 2026 Refayatul <https://github.com/Refayatul> - {VERSION}-1
- Initial public release of Paperizer
"""
    spec_path.write_text(spec_content)

    # 3. Build RPM using rpmbuild
    subprocess.check_call([
        "rpmbuild",
        "--define", f"_topdir {rpm_root}",
        "--define", f"_dbpath {rpm_root}/db",
        "-bb",
        str(spec_path)
    ])

    generated_rpms = list((rpm_root / "RPMS/noarch").glob("*.rpm"))
    if not generated_rpms:
        raise RuntimeError("RPM file was not generated by rpmbuild")

    out_rpm = DIST_DIR / f"{PKG_NAME}-{VERSION}-1.noarch.rpm"
    shutil.copy(generated_rpms[0], out_rpm)
    print("✓ RPM package ready:", out_rpm, f"({out_rpm.stat().st_size} bytes)")
    return out_rpm


if __name__ == "__main__":
    build_wheel()
    build_arch_pkg()
    build_deb_pkg()
    build_rpm_pkg()
    print("\n🎉 ALL PACKAGES SUCCESSFULLY CREATED IN dist/:")
    for f in DIST_DIR.iterdir():
        print(f" - {f.name} ({f.stat().st_size / 1024:.1f} KB)")
