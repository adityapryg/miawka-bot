# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Set environment variables (these should be overridden at runtime)
ENV DISCORD_TOKEN="MTI4NjI1NTYxMjcxOTY2MTA4OQ.GQItvb.MqaWOQnNYGFyEctUdHRG7uQruDVIsAyM1wzMwk"
ENV OPENAI_API_KEY=""
ENV PERPLEXITY_API_KEY="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"
ENV LLM_PROVIDER="openai"

# Run the bot
CMD ["python", "bot.py"]