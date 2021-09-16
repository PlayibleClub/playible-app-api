# fantasy-app-api

## Creating Virtual Env
pip install virtualenv

python3 -m venv env

source env/bin/activate

## Create requirements.txt
pip3 freeze > requirements.txt

## Install requirements.txt
pip install -r requirements.txt

## build docker compose
docker compose build

## run docker compose
docker compose up

## Run commands on docker
docker compose run app sh -c "insert command here"