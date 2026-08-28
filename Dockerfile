FROM python:3.10-slim

# Install system utilities and Ollama
RUN apt-get update && apt-get install -y curl procps && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app

# Copy application files
COPY . /app

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Hugging Face Spaces default port
EXPOSE 7860

# Launch Ollama in background, pull model, and run Streamlit app
CMD ollama serve & sleep 5 && ollama pull llama3.2:1b && streamlit run app.py --server.port 7860 --server.address 0.0.0.0
