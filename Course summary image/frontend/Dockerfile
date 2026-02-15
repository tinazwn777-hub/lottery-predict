FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Build for production
RUN npm run build

# Expose port
EXPOSE 3000

# Start command
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]
