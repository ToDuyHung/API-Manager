
build:
	sudo docker-compose --env-file .env up -d --build --remove-orphans

stop:
	sudo docker-compose down

start:
	sudo docker-compose --env-file .env up -d

start_debug:
	PYTHONPATH=./ python app_dev.py

start_dev:
	gunicorn app:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080 --preload
