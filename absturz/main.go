package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/joho/godotenv"
	"github.com/segmentio/kafka-go"
)

// DiscordWebhook represents the payload structure for Discord webhooks
type DiscordWebhook struct {
	Content string         `json:"content,omitempty"`
	Embeds  []DiscordEmbed `json:"embeds,omitempty"`
}

// DiscordEmbed represents an embed in a Discord message
type DiscordEmbed struct {
	Title       string              `json:"title,omitempty"`
	Description string              `json:"description,omitempty"`
	Color       int                 `json:"color,omitempty"`
	Fields      []DiscordEmbedField `json:"fields,omitempty"`
	Timestamp   string              `json:"timestamp,omitempty"`
}

// DiscordEmbedField represents a field in a Discord embed
type DiscordEmbedField struct {
	Name   string `json:"name"`
	Value  string `json:"value"`
	Inline bool   `json:"inline,omitempty"`
}

// Config holds the application configuration
type Config struct {
	KafkaBrokers   []string
	KafkaTopic     string
	ConsumerGroup  string
	DiscordWebhook string
}

func loadConfig() (*Config, error) {
	// Load .env file if it exists
	_ = godotenv.Load()

	config := &Config{
		KafkaBrokers:   strings.Split(getEnv("KAFKA_BROKERS", "localhost:9092"), ","),
		KafkaTopic:     getEnv("KAFKA_TOPIC", "errors"),
		ConsumerGroup:  getEnv("CONSUMER_GROUP", "absturz"),
		DiscordWebhook: getEnv("DISCORD_WEBHOOK_URL", ""),
	}

	if config.DiscordWebhook == "" {
		return nil, fmt.Errorf("DISCORD_WEBHOOK_URL environment variable is required")
	}

	return config, nil
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func sendToDiscord(webhookURL string, message string) error {
	// Format message as JSON if possible
	formattedMsg := formatJSONMessage(message)

	// Create embed with error information
	embed := DiscordEmbed{
		Title: "⚠️ Processing Failed",
		Color: 15158332, // Red color
		Fields: []DiscordEmbedField{
			{
				Name:   "Content",
				Value:  truncateString(formattedMsg, 1024),
				Inline: false,
			},
		},
		Timestamp: time.Now().UTC().Format(time.RFC3339),
	}

	webhook := DiscordWebhook{
		Embeds: []DiscordEmbed{embed},
	}

	jsonData, err := json.Marshal(webhook)
	if err != nil {
		return fmt.Errorf("failed to marshal Discord webhook: %w", err)
	}

	resp, err := http.Post(webhookURL, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return fmt.Errorf("failed to send Discord webhook: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusNoContent && resp.StatusCode != http.StatusOK {
		return fmt.Errorf("Discord webhook returned status: %d", resp.StatusCode)
	}

	return nil
}

func formatJSONMessage(message string) string {
	var obj interface{}
	if err := json.Unmarshal([]byte(message), &obj); err == nil {
		// Valid JSON - format with indentation
		if formatted, err := json.MarshalIndent(obj, "", "  "); err == nil {
			return "```json\n" + string(formatted) + "\n```"
		}
	}
	// Not JSON or formatting failed - return as-is in code block
	return "```\n" + message + "\n```"
}

func truncateString(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}

func main() {
	log.Println("Starting absturz - Kafka to Discord error reporter")

	// Load configuration
	config, err := loadConfig()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	log.Printf("Connecting to Kafka brokers: %v", config.KafkaBrokers)
	log.Printf("Topic: %s", config.KafkaTopic)
	log.Printf("Consumer Group: %s", config.ConsumerGroup)

	// Create Kafka reader
	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:     config.KafkaBrokers,
		GroupID:     config.ConsumerGroup,
		Topic:       config.KafkaTopic,
		MinBytes:    10e3,              // 10KB
		MaxBytes:    10e6,              // 10MB
		StartOffset: kafka.FirstOffset, // Read from beginning if no offset stored
	})
	defer reader.Close()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle shutdown signals
	sigterm := make(chan os.Signal, 1)
	signal.Notify(sigterm, syscall.SIGINT, syscall.SIGTERM)

	log.Println("Consumer started, waiting for messages...")

	// Start consuming
	go func() {
		for {
			msg, err := reader.ReadMessage(ctx)
			if err != nil {
				if ctx.Err() != nil {
					// Context cancelled, shutting down
					return
				}
				log.Printf("Error reading message: %v", err)
				continue
			}

			log.Printf("Message received: topic=%s partition=%d offset=%d",
				msg.Topic, msg.Partition, msg.Offset)

			// Send to Discord
			err = sendToDiscord(config.DiscordWebhook, string(msg.Value))
			if err != nil {
				log.Printf("Error sending to Discord: %v", err)
			} else {
				log.Printf("Successfully sent message to Discord")
			}
		}
	}()

	// Wait for interrupt signal
	<-sigterm
	log.Println("Shutting down gracefully...")
	cancel()

	// Give some time for graceful shutdown
	time.Sleep(time.Second)
}
