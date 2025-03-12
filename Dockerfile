# Use the official Rasa image
FROM rasa/rasa:latest

# Copy project files
COPY . /app

# Set the working directory
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Train the model (optional, if not pre-trained)
RUN rasa train

# Expose the port
EXPOSE 5005

# Run the Rasa server
CMD ["rasa", "run", "--enable-api", "--cors", "*"]