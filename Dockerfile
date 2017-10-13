# Use an official Python runtime as a parent image
FROM frolvlad/alpine-python3:latest

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip3 install -r requirements.txt

# Define environment variable
ENV NAME magic-judge-telegram-bot

# Run app.py when the container launches
CMD ["python3", "magic-judge-telegram-bot.py"]
