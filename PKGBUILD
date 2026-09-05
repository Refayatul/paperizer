# Maintainer: Refayatul <https://github.com/Refayatul>
# Contributor: Humanitas Labs (Paperize core)

pkgname=paperizer-git
_pkgname=paperizer
pkgver=0.1.0.r10.355232b
pkgrel=1
pkgdesc="A quiet, native PDF reader & warm paper styler for Linux"
arch=('any')
url="https://github.com/Refayatul/paperizer"
license=('MIT')
depends=(
    'python>=3.11'
    'pyside6'
    'python-pikepdf'
    'python-pymupdf'
)
makedepends=(
    'git'
    'python-build'
    'python-installer'
    'python-wheel'
    'python-hatchling'
)
checkdepends=(
    'python-pytest'
    'python-pytest-qt'
)
provides=('paperizer' 'paperize-gui')
conflicts=('paperizer' 'paperize-gui')
source=("git+https://github.com/Refayatul/paperizer.git")
sha256sums=('SKIP')

pkgver() {
    cd "${srcdir}/${_pkgname}"
    printf "0.1.0.r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

build() {
    cd "${srcdir}/${_pkgname}"
    python -m build --wheel --no-isolation
}

check() {
    cd "${srcdir}/${_pkgname}"
    QT_QPA_PLATFORM=offscreen pytest tests/
}

package() {
    cd "${srcdir}/${_pkgname}"
    python -m installer --destdir="${pkgdir}" dist/*.whl

    # Desktop entry & Icons
    install -Dm644 paperizer.desktop "${pkgdir}/usr/share/applications/paperizer.desktop"
    install -Dm644 assets/icon.svg "${pkgdir}/usr/share/icons/hicolor/scalable/apps/paperizer.svg"
    install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}

