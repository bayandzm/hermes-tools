FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn mcp

# Copy server
COPY api_server.py .
COPY mcp_server.py .

# Expose port
EXPOSE 8765

# Run API server
CMD ["python", "api_server.py", "8765"]
