VERSION := "0.1"
test:
	docker-compose -f nginx/docker-compose.yml up -d
	export LD_PRELOAD=${LD_PRELOAD}:/usr/lib/arm-linux-gnueabihf/libatomic.so.1 && python3 LapCounterByCamCV.py
ui: nginx/index.html
	cd nginx && make
pkg:
	./crt-pkg.sh VERSION=${VERSION}
install:
	sudo dpkg -i backyard-surv-${VERSION}-armhf.deb
