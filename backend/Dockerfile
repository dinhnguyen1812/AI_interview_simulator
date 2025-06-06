FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    ninja-build \
    ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install latest CMake (for x86_64 platform)
ENV CMAKE_VERSION=3.27.9
RUN mkdir -p /opt && \
    curl -LO https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz && \
    tar -xzf cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz -C /opt && \
    ln -s /opt/cmake-${CMAKE_VERSION}-linux-x86_64/bin/* /usr/local/bin/ && \
    rm cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz

ENV PATH="/opt/cmake-${CMAKE_VERSION}-linux-x86_64/bin:${PATH}"

# Set working directory inside container
WORKDIR /app

# Copy backend folder contents into container's /app
COPY backend/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app

# Start the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

