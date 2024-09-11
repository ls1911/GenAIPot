# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port 25 (SMTP) and port 110 (POP3) available to the world outside this container
EXPOSE 25 110

# Run main.py when the container launches
CMD ["/app/start.sh"]