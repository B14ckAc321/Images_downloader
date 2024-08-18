# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /usr/app/src
# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /usr/app/src
COPY . .

# Run the image scraper script when the container launches
ENTRYPOINT ["python3", "scout_site_scraper.py"]
