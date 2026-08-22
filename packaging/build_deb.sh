#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PKG_NAME="antigravity-quota-monitor"
PKG_VER="1.0.0"
BUILD_DIR="${SCRIPT_DIR}/build/${PKG_NAME}_${PKG_VER}_all"

echo "==> Building ${PKG_NAME}_${PKG_VER}_all.deb..."

# Clean old build
rm -rf "${BUILD_DIR}" "${SCRIPT_DIR}/build/${PKG_NAME}_${PKG_VER}_all.deb"
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/usr/bin"
mkdir -p "${BUILD_DIR}/usr/lib/${PKG_NAME}"
mkdir -p "${BUILD_DIR}/usr/share/applications"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps"
mkdir -p "${BUILD_DIR}/etc/xdg/autostart"

# Copy DEBIAN control scripts
cp "${SCRIPT_DIR}/debian/control" "${BUILD_DIR}/DEBIAN/"
cp "${SCRIPT_DIR}/debian/postinst" "${BUILD_DIR}/DEBIAN/"
cp "${SCRIPT_DIR}/debian/prerm" "${BUILD_DIR}/DEBIAN/"
chmod 755 "${BUILD_DIR}/DEBIAN/postinst" "${BUILD_DIR}/DEBIAN/prerm"

# Copy application source code
cp -r "${ROOT_DIR}/src" "${BUILD_DIR}/usr/lib/${PKG_NAME}/"
cp "${ROOT_DIR}/antigravity-quota" "${BUILD_DIR}/usr/lib/${PKG_NAME}/"
chmod +x "${BUILD_DIR}/usr/lib/${PKG_NAME}/antigravity-quota"

# Symlink to /usr/bin/antigravity-quota
ln -sf "/usr/lib/${PKG_NAME}/antigravity-quota" "${BUILD_DIR}/usr/bin/antigravity-quota"

# Copy Desktop Entry & Icons
cp "${ROOT_DIR}/assets/antigravity-quota-monitor.desktop" "${BUILD_DIR}/usr/share/applications/"
cp "${ROOT_DIR}/assets/antigravity-quota-monitor.desktop" "${BUILD_DIR}/etc/xdg/autostart/"
cp "${ROOT_DIR}/assets/icons/antigravity-quota-monitor.svg" "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps/"

# Build .deb package
dpkg-deb --build --root-owner-group "${BUILD_DIR}" "${ROOT_DIR}/antigravity-quota-monitor_${PKG_VER}_all.deb"

echo "==> Package built successfully at ${ROOT_DIR}/antigravity-quota-monitor_${PKG_VER}_all.deb"
