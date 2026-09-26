PYTHON ?= python3

.PHONY: test compile render-runtime smoke-local docker-build

test:
	$(PYTHON) -m pytest -q

compile:
	$(PYTHON) -m compileall -q scripts tests

render-runtime:
	$(PYTHON) scripts/render_runtime_preview.py

smoke-local:
	./scripts/smoke_appliance.sh

docker-build:
	docker build -t rss-publisher-agent:dev .
