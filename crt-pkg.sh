#!/bin/bash
eval $1
PKG_NAME=lap-counter-${VERSION}-armhf.deb
DEB_PKG_BUILD_DIR=./pkg-build-dir
PKG_ROOT=/usr/local/bin/backyard/lap-counter
SYSTEMD_DIR=/etc/systemd/system

mkdir -p $DEB_PKG_BUILD_DIR/$PKG_ROOT $DEB_PKG_BUILD_DIR/$SYSTEMD_DIR
cp CamMotionCV.py $DEB_PKG_BUILD_DIR/$PKG_ROOT
cp LapCounterByCamCV.py $DEB_PKG_BUILD_DIR/$PKG_ROOT
cp lap-counter.sh $DEB_PKG_BUILD_DIR/$PKG_ROOT
cp lap-counter.conf $DEB_PKG_BUILD_DIR/$PKG_ROOT
cp lap-counter.service $DEB_PKG_BUILD_DIR/$SYSTEMD_DIR
cp nginx/index.html $DEB_PKG_BUILD_DIR/$PKG_ROOT
sed -E -e "/(build|context|dockerfile):/d" nginx/docker-compose.yml > $DEB_PKG_BUILD_DIR/$PKG_ROOT/docker-compose.yml
cp nginx/Cheer.wav $DEB_PKG_BUILD_DIR/$PKG_ROOT
cp -r DEBIAN $DEB_PKG_BUILD_DIR

echo "Version: ${VERSION}" >> ${DEB_PKG_BUILD_DIR}/DEBIAN/control
echo "Architecture: armhf" >> ${DEB_PKG_BUILD_DIR}/DEBIAN/control
echo "Maintainer: Jingbo Ni (jnistargazer@gmail.com)" >> ${DEB_PKG_BUILD_DIR}/DEBIAN/control
echo "Description: built at $(date +'%H:%M:%S %m/%d/%Y')" >> ${DEB_PKG_BUILD_DIR}/DEBIAN/control

sudo dpkg -b ${DEB_PKG_BUILD_DIR} ./${PKG_NAME}
echo $PKG_NAME
