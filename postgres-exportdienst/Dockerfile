# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy source and module files
COPY . .

# Generate go.sum and download dependencies
RUN go mod tidy

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o postgres-exportdienst .

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

# Copy the binary from builder
COPY --from=builder /app/postgres-exportdienst .

# Run the binary
CMD ["./postgres-exportdienst"]
