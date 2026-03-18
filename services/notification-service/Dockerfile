FROM golang:1.21-alpine AS builder

WORKDIR /app
# Copy the service source code
COPY services/notification-service/ .

# Download dependencies and build
RUN go mod tidy && \
    go mod download && \
    CGO_ENABLED=0 GOOS=linux go build -o notification-service ./cmd/main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates

WORKDIR /root/
COPY --from=builder /app/notification-service .

EXPOSE 8080
CMD ["./notification-service"]
