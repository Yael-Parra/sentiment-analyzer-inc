# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependencies
COPY server/requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy backend code
COPY server/ /app/server

# Copy model folder
COPY models/bilstm_advanced /app/models/bilstm_advanced
COPY etl/ /app/etl
COPY .env /app/.env

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"] 