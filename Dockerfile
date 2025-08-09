# Use official Python slim image
FROM python:3.11-slim-bullseye

# Update system and install dependencies (converted from Ubuntu 18.04)
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    curl \
    git \
    gcc \
    g++ \
    gnupg \
    apt-transport-https \
    unixodbc-dev \
    freetds-dev \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Add SQL Server ODBC Driver 17 for Debian 11 (bullseye) - converted from Ubuntu 18.04
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && ACCEPT_EULA=Y apt-get install -y mssql-tools \
    && echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bash_profile \
    && echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies from requirements (includes pyodbc)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Environment variables
# Azure SQL Configuration (for production) - MUST be provided at runtime
ENV DB_TYPE=azure
ENV FLASK_ENV=production
ENV DEBUG=False

# CORS Configuration for React frontend
ENV FRONTEND_URL=http://localhost:3000
# ENV CORS_ORIGINS=https://your-production-domain.com,https://your-staging-domain.com

# Azure SQL credentials - UNCOMMENT and set these OR pass at runtime:
# ENV AZURE_SQL_SERVER=your-server.database.windows.net
# ENV AZURE_SQL_DATABASE=your-database-name
# ENV AZURE_SQL_USERNAME=your-username
# ENV AZURE_SQL_PASSWORD=your-password

# Optional: Force specific driver (auto-detects pymssql for production)
# ENV AZURE_SQL_DRIVER_TYPE=pymssql


# Expose the port your app runs on
EXPOSE 8000

# Start Gunicorn (using existing database)
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:8000 app:app"]