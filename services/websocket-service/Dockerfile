FROM golang:1.21-alpine AS builder

WORKDIR /app

# Paths must be relative to the build context (root of repo)
COPY services/websocket-service/go.mod ./
# Generating go.sum during build as it's missing from the repository
RUN go mod tidy

COPY services/websocket-service .
RUN go build -o main ./cmd/main.go

FROM alpine:latest
WORKDIR /root/
COPY --from=builder /app/main .

EXPOSE 8080
CMD ["./main"]
