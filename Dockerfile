# Use the official Rasa image
FROM rasa/rasa:latest

# Copy project files
COPY . /app

# Set the working directory
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir setuptools wheel
RUN pip install --no-cache-dir fire
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Train the model (optional, if not pre-trained)
RUN rasa train

# Expose the port
EXPOSE 5005

# Run the Rasa server
CMD ["rasa", "run", "--enable-api", "--cors", "*"]
