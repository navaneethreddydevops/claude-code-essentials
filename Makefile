.PHONY: install lint format test synth-dev synth-staging synth-prod \
        deploy-dev deploy-staging deploy-prod diff-dev diff-staging diff-prod bootstrap

# uv — install from https://docs.astral.sh/uv/
UV ?= uv

install:
	$(UV) sync --all-extras

lint:
	$(UV) run ruff check infra tests app.py
	$(UV) run black --check infra tests app.py

format:
	$(UV) run ruff check --fix infra tests app.py
	$(UV) run black infra tests app.py

test:
	$(UV) run pytest --cov=infra --cov-report=term-missing

synth-dev:
	CDK_ENV=dev $(UV) run cdk synth

synth-staging:
	CDK_ENV=staging $(UV) run cdk synth

synth-prod:
	CDK_ENV=prod $(UV) run cdk synth

deploy-dev:
	CDK_ENV=dev $(UV) run cdk deploy --all --profile dev --require-approval never

deploy-staging:
	CDK_ENV=staging $(UV) run cdk deploy --all --profile staging

deploy-prod:
	CDK_ENV=prod $(UV) run cdk deploy --all --profile prod

diff-dev:
	CDK_ENV=dev $(UV) run cdk diff --all --profile dev

diff-staging:
	CDK_ENV=staging $(UV) run cdk diff --all --profile staging

diff-prod:
	CDK_ENV=prod $(UV) run cdk diff --all --profile prod

bootstrap:
	bash scripts/bootstrap.sh
