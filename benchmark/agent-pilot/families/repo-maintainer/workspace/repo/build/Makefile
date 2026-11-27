.PHONY: test lint release docs

test:
	python3 -m pytest tests

lint:
	python3 -m pyflakes src

release:
	./build/tag-release.sh

docs:
	echo "build docs"
