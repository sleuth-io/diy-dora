.PHONY: help lint format check-format dist

# Help system from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.DEFAULT_GOAL := help

include .env
export $(shell sed 's/=.*//' .env)

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

pyenv: ## Install and setup local py env
	python3.90 -m venv venv
	venv/bin/pip install -r requirements.txt


clean: pyenv ## Cleans and rebuilds
	rm -rf media


run: ## Builds video
	manim -pql deployment-frequency.py DeployFrequencyChart


