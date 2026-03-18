FROM golang:1.21-alpine AS builder

# Install git for fetching dependencies
RUN apk add --no-cache git

WORKDIR /app

# Copy the service source code
COPY services/websocket-service/ .

# Disable CGO for static binary and ensure dependencies are tidied/downloaded in one go
ENV CGO_ENABLED=0
RUN go mod tidy && \
    go mod download && \
    go build -v -o main ./cmd/main.go

FROM alpine:latest
WORKDIR /root/
COPY --from=builder /app/main .

EXPOSE 8080
CMD ["./main"]
