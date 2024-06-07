# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set environment variables
ENV FLASK_APP=app.py

# Install git and other dependencies
RUN apt-get update && apt-get install -y git

# Set the working directory in the container
WORKDIR /app

# Clone the GitHub repository
RUN git clone https://github.com/franfrancisco9/Museums_and_Restaurants_Board.git .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run the application
CMD ["flask", "run", "--host=0.0.0.0"]
