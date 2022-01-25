# fantasy-app-api

## Creating Virtual Env
pip install virtualenv

windows: python3 -m venv env | ubuntu: virtualenv venv

source env/bin/activate

## Create requirements.txt
pip3 freeze > requirements.txt

## Install requirements.txt
pip install -r requirements.txt

## build docker compose
docker compose build

## run docker compose
docker compose up

## run docker-compose with local settings
docker-compose -f docker-compose.yml -f docker-compose.local.yml up -d

## Run commands on docker
docker-compose exec app sh -c "insert command here"

## Load initial data
python manage.py loaddata initial_data.json