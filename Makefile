.PHONY: install test experiments figures paper supplement checklist artifact clean

install:
	python -m pip install --no-build-isolation -e ".[dev]"

test:
	PYTHONPATH=src pytest -q

experiments:
	PYTHONPATH=src python experiments/run_all.py

figures:
	python experiments/plot_results.py

paper:
	bash scripts/build_paper.sh main

supplement:
	bash scripts/build_paper.sh supplement

checklist:
	bash scripts/build_paper.sh checklist

artifact:
	bash scripts/package_anonymous_artifact.sh

clean:
	rm -rf .pytest_cache src/epcoord/__pycache__ tests/__pycache__ experiments/__pycache__ scripts/__pycache__ _renders_* _preflight_*
	rm -f paper/*.aux paper/*.bbl paper/*.blg paper/*.fdb_latexmk paper/*.fls \
	      paper/*.log paper/*.out paper/*.synctex.gz paper/*.toc
