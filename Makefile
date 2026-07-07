VENV := .venv
PYTHON := $(VENV)/Scripts/python
DBT := $(VENV)/Scripts/dbt
DBT_DIR := dealership_analytics

.PHONY: setup generate seed run test build docs all

setup:
	python -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip -q
	$(PYTHON) -m pip install -r scripts/requirements.txt -q
	cd $(DBT_DIR) && DBT_PROFILES_DIR=. ../$(DBT) deps

generate:
	$(PYTHON) scripts/generate_raw_data.py --seed 42

seed:
	cd $(DBT_DIR) && DBT_PROFILES_DIR=. ../$(DBT) seed

run:
	cd $(DBT_DIR) && DBT_PROFILES_DIR=. ../$(DBT) run

test:
	cd $(DBT_DIR) && DBT_PROFILES_DIR=. ../$(DBT) test

build:
	cd $(DBT_DIR) && DBT_PROFILES_DIR=. ../$(DBT) build

docs:
	cd $(DBT_DIR) && DBT_PROFILES_DIR=. ../$(DBT) docs generate && ../$(DBT) docs serve

all: setup generate build
