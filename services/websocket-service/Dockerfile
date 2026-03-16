FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy the entire service directory first so go mod tidy can scan the source code
COPY services/websocket-service .

# Generate go.sum and download dependencies
RUN go mod tidy

# Build the binary
RUN go build -o main ./cmd/main.go

FROM alpine:latest
WORKDIR /root/
COPY --from=builder /app/main .

EXPOSE 8080
CMD ["./main"]
