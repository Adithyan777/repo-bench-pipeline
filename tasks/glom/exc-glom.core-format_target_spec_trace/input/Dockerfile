FROM python@sha256:2c941e860699f878900b0edc2403613c234d4b32eda3cc9fa7036991a2a63c4a
WORKDIR /repo
ENV PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY requirements.lock.txt .
RUN pip install --no-deps --require-hashes -r requirements.lock.txt
COPY . .
RUN pip install --no-deps -e .
CMD ["python", "-m", "pytest", "-q"]
