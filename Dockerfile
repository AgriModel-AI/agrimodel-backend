# Use a lightweight Python image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file before running pip install
COPY requirements.txt .

# Install dependencies
RUN python3 -m venv venv && \
    venv/bin/pip install --upgrade pip && \
    venv/bin/pip install -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose the application port
EXPOSE 5000

# Run the application
CMD ["venv/bin/gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
