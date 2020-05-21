VERSION := "0.1"
run:
	python3 LapCounterByCamCV.py
ui: nginx/index.html
	cd nginx && make
pkg:
	./crt-pkg.sh VERSION=${VERSION}
install:
	sudo dpkg -i lap-counter-${VERSION}-armhf.deb
