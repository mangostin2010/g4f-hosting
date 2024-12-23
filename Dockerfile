# Use the official Python image as the base image
FROM python:3.11

# Set the working directory in the container
WORKDIR /

# Copy the application files into the working directory
COPY . /

# Install the application dependencies
RUN pip install -r requirements.txt

# Expose the port your application listens on
EXPOSE 80

# Define the entry point for the container
CMD ["python", "chat.py"]
