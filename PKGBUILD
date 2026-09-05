# Maintainer: Kai <kai@example.com>
# Contributor: Humanitas Labs (Paperize core)
pkgname=paperize-gui-git
pkgver=0.1.0.r1
pkgrel=1
pkgdesc="Modern Qt6 GUI for paperize - turn glaring white PDFs into comfortable, warm paper"
arch=('any')
url="https://github.com/kai/paperize-gui"
license=('MIT')
depends=(
    'python>=3.12'
    'pyside6'
    'python-pikepdf'
    'python-pymupdf'
    'python-click'
)
makedepends=(
    'git'
    'python-build'
    'python-installer'
    'python-wheel'
    'python-hatchling'
)
provides=('paperize-gui')
conflicts=('paperize-gui')
source=("${pkgname}::git+https://github.com/kai/paperize-gui.git")
sha256sums=('SKIP')

pkgver() {
    cd "${srcdir}/${pkgname}"
    printf "0.1.0.r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

build() {
    cd "${srcdir}/${pkgname}"
    python -m build --wheel --no-isolation
}

package() {
    cd "${srcdir}/${pkgname}"
    python -m installer --destdir="${pkgdir}" dist/*.whl

    # Desktop entry & Icons
    install -Dm644 paperize-gui.desktop "${pkgdir}/usr/share/applications/paperize-gui.desktop"
    install -Dm644 assets/icon.svg "${pkgdir}/usr/share/icons/hicolor/scalable/apps/paperize-gui.svg"
}
