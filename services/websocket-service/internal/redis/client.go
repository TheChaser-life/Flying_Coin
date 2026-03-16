package redis

import (
	"context"
	"log"

	"github.com/redis/go-redis/v9"
)

type RedisClient struct {
	Client *redis.Client
}

func NewRedisClient(url string) *RedisClient {
	opts, err := redis.ParseURL(url)
	if err != nil {
		log.Fatalf("Failed to parse Redis URL: %v", err)
	}
	client := redis.NewClient(opts)
	return &RedisClient{Client: client}
}

func (r *RedisClient) Subscribe(ctx context.Context, channels ...string) *redis.PubSub {
	return r.Client.Subscribe(ctx, channels...)
}

func (r *RedisClient) Listen(ctx context.Context, ps *redis.PubSub, msgChan chan<- []byte) {
	defer ps.Close()
	ch := ps.Channel()

	for {
		select {
		case msg := <-ch:
			if msg == nil {
				return
			}
			msgChan <- []byte(msg.Payload)
		case <-ctx.Done():
			return
		}
	}
}
