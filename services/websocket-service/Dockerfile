FROM golang:1.21-alpine AS builder

WORKDIR /app

# Paths must be relative to the build context (root of repo)
COPY services/websocket-service/go.mod ./
# COPY services/websocket-service/go.sum ./
RUN go mod download

COPY services/websocket-service .
RUN go build -o main ./cmd/main.go

FROM alpine:latest
WORKDIR /root/
COPY --from=builder /app/main .

EXPOSE 8080
CMD ["./main"]
