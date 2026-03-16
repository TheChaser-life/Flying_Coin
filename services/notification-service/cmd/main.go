package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"

	"github.com/gin-gonic/gin"
	"github.com/thechaser-life/flying-coin/notification-service/internal/email"
	"github.com/thechaser-life/flying-coin/notification-service/internal/redis"
)

type EmailPayload struct {
	To      string      `json:"to"`
	Subject string      `json:"subject"`
	Body    string      `json:"body"`
	Data    interface{} `json:"data"`
}

func main() {
	redisURL := getEnv("REDIS_URL", "redis://localhost:6379/0")
	smtpHost := getEnv("SMTP_HOST", "smtp.gmail.com")
	smtpPort, _ := strconv.Atoi(getEnv("SMTP_PORT", "587"))
	smtpUser := getEnv("SMTP_USER", "")
	smtpPass := getEnv("SMTP_PASS", "")
	fromEmail := getEnv("FROM_EMAIL", "alerts@thinhopsops.win")

	redisClient := redis.NewClient(redisURL)
	mailer := email.NewMailer(smtpHost, smtpPort, smtpUser, smtpPass, fromEmail)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Sub loop
	go func() {
		pubsub := redisClient.Subscribe(ctx, "notifications:email")
		defer pubsub.Close()
		ch := pubsub.Channel()

		log.Println("Notification Service listening on notifications:email ...")
		for msg := range ch {
			var payload EmailPayload
			if err := json.Unmarshal([]byte(msg.Payload), &payload); err != nil {
				log.Printf("Failed to unmarshal email payload: %v", err)
				continue
			}

			log.Printf("Sending email to %s: %s", payload.To, payload.Subject)
			if err := mailer.Send(payload.To, payload.Subject, payload.Body); err != nil {
				log.Printf("Error sending email: %v", err)
			}
		}
	}()

	// Health check API
	r := gin.Default()
	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "ok"})
	})

	srv := &http.Server{
		Addr:    ":8080",
		Handler: r,
	}

	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("listen: %s\n", err)
		}
	}()

	// Wait for interrupt
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	log.Println("Shutting down Notification Service...")
	cancel()
}

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}
