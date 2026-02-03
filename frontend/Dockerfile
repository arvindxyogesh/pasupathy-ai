FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --silent

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Health check - use 127.0.0.1 explicitly for IPv4
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:3000 || exit 1

# Start the application
CMD ["npm", "start"]