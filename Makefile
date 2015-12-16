all: build

build: clean
	python generate.py content build

watch:
	chokidar 'content/**/*' 'templates/**/*' 'public/**/*' generate.py -c "$(MAKE) build" --initial

run:
	cd build && http-server

clean:
	rm -rf build

deploy: build
	cd build && \
	git clone --bare git@github.com:oampo/oampo.github.io.git .git && \
	git config core.bare false && \
	git add . && \
	git commit -m "Deploy" && \
	git push origin master


.PHONY: all build watch run clean
