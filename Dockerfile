# Use the official Ubuntu 22.04 base image
FROM ubuntu:22.04

# Set environment variables to avoid prompts during package installations
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies (Python 3.11, pip, LibreOffice, curl, Redis, supervisor, etc.)
RUN apt-get update && \
    apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-distutils \
    curl \
    libreoffice-common \
    libreoffice \
    build-essential \
    gcc \
    g++ \
    supervisor \
    && apt-get clean

# Install pip for Python 3.11
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3.11 get-pip.py && \
    rm get-pip.py

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies from the requirements.txt file
RUN pip3.11 install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# Expose the port that FastAPI will run on
EXPOSE 7002

# Copy the supervisord.conf file
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start Supervisor to manage Redis and FastAPI
CMD ["/usr/bin/supervisord"]
