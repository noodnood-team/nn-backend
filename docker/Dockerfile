FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/program

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY docker ./docker
COPY app ./app
COPY sagemaker ./sagemaker

RUN chmod +x /opt/program/sagemaker/serve
RUN chmod +x /opt/program/docker/entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/opt/program/docker/entrypoint.sh"]
CMD ["/opt/program/sagemaker/serve"]

