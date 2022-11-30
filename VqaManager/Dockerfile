FROM python:3.7-slim-buster
WORKDIR /app

RUN pip3 --no-cache-dir install --index-url https://mirror-python.t-idc.net/simple/ websocket
RUN pip3 --no-cache-dir install --index-url https://mirror-python.t-idc.net/simple/ cached_property
RUN pip3 --no-cache-dir install --index-url https://mirror-python.t-idc.net/simple/ websocket-client==0.56.0
RUN pip3 --no-cache-dir install --index-url https://mirror-python.t-idc.net/simple/ fastapi_health
RUN pip3 --no-cache-dir install --index-url https://mirror-python.t-idc.net/simple/ fastapi_utils
RUN pip3 --no-cache-dir install --index-url https://mirror-python.t-idc.net/simple/ install unidecode
RUN pip3 --no-cache-dir install --index-url https://mirror-python.t-idc.net/simple/ install gunicorn
RUN pip3 --no-cache-dir install --index-url https://mirror-python.t-idc.net/simple/ install dnspython

COPY . .

RUN cd lib && pip3 --no-cache-dir install --index-url https://mirror-python.t-idc.net/simple/ *.whl && cd ../ && rm -r lib

RUN export PYTHONPATH=./

ENTRYPOINT ["gunicorn", "app:app", "--workers", "5", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "--preload", "--timeout", "600"]