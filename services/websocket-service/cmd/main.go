package main

import (
	"context"
	"log"
	"net/http"
	"os"

	"github.com/gorilla/websocket"
	"github.com/thechaser-life/flying-coin/websocket-service/internal/hub"
	"github.com/thechaser-life/flying-coin/websocket-service/internal/redis"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true // Allow all origins for dev
	},
}

func serveWs(h *hub.Hub, w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("Upgrade error: %v", err)
		return
	}
	client := &hub.Client{Conn: conn, Send: make(chan []byte, 256)}
	h.Register(client)

	// Read/Write pumps
	go func() {
		defer func() {
			h.Unregister(client)
			conn.Close()
		}()
		for {
			_, _, err := conn.ReadMessage()
			if err != nil {
				break
			}
		}
	}()

	go func() {
		for msg := range client.Send {
			err := conn.WriteMessage(websocket.TextMessage, msg)
			if err != nil {
				break
			}
		}
	}()
}

func main() {
	redisURL := os.Getenv("REDIS_URL")
	if redisURL == "" {
		redisURL = "redis://localhost:6379/0"
	}

	h := hub.NewHub()
	go h.Run()

	rClient := redis.NewRedisClient(redisURL)
	ctx := context.Background()

	// Subscribe to relevant channels
	ps := rClient.Subscribe(ctx, "price:*", "sentiment:*", "forecast:*")
	msgChan := make(chan []byte)

	go rClient.Listen(ctx, ps, msgChan)

	// Broadcast Redis messages to all WS clients
	go func() {
		for msg := range msgChan {
			h.Broadcast(msg)
		}
	}()

	http.HandleFunc("/ws", func(w http.ResponseWriter, r *http.Request) {
		serveWs(h, w, r)
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("WebSocket Service starting on :%s", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatalf("ListenAndServe: %v", err)
	}
}
