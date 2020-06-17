include common.mk

MODULES=herzog tests

test: lint mypy tests

lint:
	flake8 $(MODULES) *.py

mypy:
	mypy --ignore-missing-imports --no-strict-optional $(MODULES)

tests:
	PYTHONWARNINGS=ignore:ResourceWarning coverage run --source=herzog \
		-m unittest discover --start-directory tests --top-level-directory . --verbose

version: herzog/version.py

herzog/version.py: setup.py
	echo "__version__ = '$$(python setup.py --version)'" > $@

clean:
	git clean -dfx

sdist: clean version
	python setup.py sdist

build: clean version
	-rm -rf dist
	python setup.py bdist_wheel

install: build
	pip install --upgrade dist/*.whl

.PHONY: test lint mypy tests clean sdist build install package_samtools
