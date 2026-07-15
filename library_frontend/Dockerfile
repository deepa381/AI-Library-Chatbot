# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Serve stage
FROM node:18-alpine

WORKDIR /app

# Install serve to run the application
RUN npm install -g serve

# Copy the build output from the builder stage
COPY --from=builder /app/dist ./dist

EXPOSE 5173

# Start the server on port 5173
CMD ["serve", "-s", "dist", "-l", "5173"]
