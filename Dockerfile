# # Use a lightweight Python image
# FROM python:3.9-slim-buster

# # Set the working directory in the container
# WORKDIR /app

# # Copy the requirements file before running pip install
# COPY requirements.txt .

# # Install dependencies
# RUN python3 -m venv venv && \
#     venv/bin/pip install --upgrade pip && \
#     venv/bin/pip install -r requirements.txt

# # Copy the rest of the application files
# COPY . .

# # Expose the application port
# EXPOSE 5000

# # Run the application
# CMD ["venv/bin/gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]

# Use the Python 3 official image
# https://hub.docker.com/_/python
FROM python:3

# Run in unbuffered mode
ENV PYTHONUNBUFFERED=1 

# Create and change to the app directory.
WORKDIR /app

# Copy local code to the container image.
COPY . ./

# Install project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the web service on container startup.
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]