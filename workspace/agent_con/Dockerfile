FROM nvidia/cuda:12.1.0-runtime-ubuntu20.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/app/models/cache
ENV TORCH_HOME=/app/models/torch
ENV CUDA_VISIBLE_DEVICES=0
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

WORKDIR /app

# Install system dependencies and Python 3.9
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y \
    python3.9 \
    python3.9-dev \
    python3.9-distutils \
    build-essential \
    git \
    curl \
    && curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
    && python3.9 get-pip.py \
    && rm get-pip.py \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic links
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1 \
    && update-alternatives --set python3 /usr/bin/python3.9 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1

# Create cache directories with proper permissions
RUN mkdir -p /app/models/cache /app/models/torch /app/models/offload && \
    chmod -R 777 /app/models && \
    chmod -R 777 /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt && \
    pip3 install --no-cache-dir bitsandbytes --upgrade && \
    pip3 install --no-cache-dir triton==2.1.0

# Copy source code
COPY . .

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the service with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120", "agent.entrypoint:app"] 