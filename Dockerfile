# Use a lightweight Python base image
FROM python:3.12-slim

# Install uv for fast, reliable package installations
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory inside the container
WORKDIR /app

# Copy dependency definition files first for optimal build caching
COPY pyproject.toml uv.lock ./

# Install project dependencies (excluding the editable package itself)
RUN uv sync --frozen --no-install-project

# Copy your project's source code
COPY src/ ./src
COPY README.md ./

# Sync again to install your project in editable/local mode inside the image
RUN uv sync --frozen

# Expose ports: 8000 for FastAPI backend, 8501 for Streamlit UI
EXPOSE 8000 8501

# Place virtual environment binaries directly in the execution PATH
ENV PATH="/app/.venv/bin:$PATH"