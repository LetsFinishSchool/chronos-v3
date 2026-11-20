FROM python:3.13-slim
RUN pip install --no-cache-dir "psycopg[binary]" "pyjwt[crypto]" python-dateutil
RUN useradd -u 10001 app
COPY ref_server.py /app/ref_server.py
USER app
ENTRYPOINT ["python", "/app/ref_server.py"]
CMD ["web"]
