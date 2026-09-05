# Copyright 2026 Gentoo Authors
# Distributed under the terms of the MIT License

EAPI=8

DISTUTILS_USE_PEP517=hatchling
PYTHON_COMPAT=( python3_{11..13} )

inherit distutils-r1 xdg

DESCRIPTION="A quiet, native PDF reader & warm paper styler for Linux"
HOMEPAGE="https://github.com/Refayatul/paperizer"
SRC_URI="https://github.com/Refayatul/paperizer/archive/refs/tags/v${PV}.tar.gz -> ${P}.tar.gz"

LICENSE="MIT"
SLOT="0"
KEYWORDS="~amd64 ~arm64 ~x86"

RDEPEND="
	>=dev-python/pyside6-6.6.0[${PYTHON_USEDEP}]
	>=dev-python/pikepdf-10.0.0[${PYTHON_USEDEP}]
	>=dev-python/pymupdf-1.24.0[${PYTHON_USEDEP}]
"
BDEPEND="
	dev-python/hatchling[${PYTHON_USEDEP}]
"

distutils_enable_tests pytest

src_install() {
	distutils-r1_src_install

	# Install desktop entry and icon
	domenu paperizer.desktop
	doicon -s scalable assets/icon.svg
}
