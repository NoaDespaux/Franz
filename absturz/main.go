package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"hash/fnv"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"sync"
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
	KafkaTopics    []string
	ConsumerGroup  string
	DiscordWebhook string
}

func loadConfig() (*Config, error) {
	// Load .env file if it exists
	_ = godotenv.Load()

	topicsStr := getEnv("KAFKA_TOPICS", "dlq")
	topics := strings.Split(topicsStr, ",")
	// Trim whitespace from each topic
	for i := range topics {
		topics[i] = strings.TrimSpace(topics[i])
	}

	config := &Config{
		KafkaBrokers:   strings.Split(getEnv("KAFKA_BROKERS", "localhost:9092"), ","),
		KafkaTopics:    topics,
		ConsumerGroup:  getEnv("CONSUMER_GROUP", "absturz"),
		DiscordWebhook: getEnv("DISCORD_WEBHOOK_URL", ""),
	}

	if config.DiscordWebhook == "" {
		return nil, fmt.Errorf("DISCORD_WEBHOOK_URL environment variable is required")
	}

	if len(config.KafkaTopics) == 0 {
		return nil, fmt.Errorf("at least one Kafka topic must be specified")
	}

	return config, nil
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func sendToDiscord(webhookURL string, topic string, message string) error {
	// Format message as JSON if possible
	formattedMsg := formatJSONMessage(message)

	// Create embed with error information
	embed := DiscordEmbed{
		Title: fmt.Sprintf("⚠️ Processing Failed - %s", topic),
		Color: getColorForTopic(topic),
		Fields: []DiscordEmbedField{
			{
				Name:   "DLQ Topic",
				Value:  "`" + topic + "`",
				Inline: true,
			},
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

// getColorForTopic generates a consistent color for a topic name
func getColorForTopic(topic string) int {
	h := fnv.New32a()
	h.Write([]byte(topic))
	hash := h.Sum32()

	// Generate a color that's vibrant and visible
	// Use the hash to generate RGB values, avoiding too dark colors
	r := int((hash>>16)&0xFF)>>1 + 64 // 64-191
	g := int((hash>>8)&0xFF)>>1 + 64  // 64-191
	b := int(hash&0xFF)>>1 + 64       // 64-191

	return (r << 16) | (g << 8) | b
}

func waitForKafka(brokers []string, topics []string, maxRetries int) error {
	log.Printf("Waiting for Kafka to be ready and topics %v to exist...", topics)

	for i := 0; i < maxRetries; i++ {
		allReady := true
		for _, topic := range topics {
			conn, err := kafka.DialLeader(context.Background(), "tcp", brokers[0], topic, 0)
			if err != nil {
				allReady = false
				log.Printf("Topic '%s' not ready yet: %v", topic, err)
				break
			}
			conn.Close()
		}

		if allReady {
			log.Println("Kafka is ready and all topics exist!")
			return nil
		}

		waitTime := time.Duration(i+1) * 2 * time.Second
		log.Printf("Kafka not ready yet (attempt %d/%d), waiting %v...", i+1, maxRetries, waitTime)
		time.Sleep(waitTime)
	}

	return fmt.Errorf("failed to connect to Kafka after %d attempts", maxRetries)
}

func consumeTopic(ctx context.Context, wg *sync.WaitGroup, config *Config, topic string) {
	defer wg.Done()

	log.Printf("Starting consumer for topic: %s", topic)

	// Create Kafka reader for this topic
	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:     config.KafkaBrokers,
		GroupID:     config.ConsumerGroup,
		Topic:       topic,
		MinBytes:    10e3,              // 10KB
		MaxBytes:    10e6,              // 10MB
		StartOffset: kafka.FirstOffset, // Read from beginning if no offset stored
	})
	defer reader.Close()

	log.Printf("Consumer ready for topic: %s", topic)

	// Start consuming
	for {
		msg, err := reader.ReadMessage(ctx)
		if err != nil {
			if ctx.Err() != nil {
				// Context cancelled, shutting down
				log.Printf("Consumer for topic %s shutting down", topic)
				return
			}
			log.Printf("Error reading message from %s: %v", topic, err)
			continue
		}

		log.Printf("Message received: topic=%s partition=%d offset=%d",
			msg.Topic, msg.Partition, msg.Offset)

		// Send to Discord
		err = sendToDiscord(config.DiscordWebhook, topic, string(msg.Value))
		if err != nil {
			log.Printf("Error sending to Discord from %s: %v", topic, err)
		} else {
			log.Printf("Successfully sent message from %s to Discord", topic)
		}
	}
}

func main() {
	log.Println("Starting absturz - Kafka to Discord error reporter")

	// Load configuration
	config, err := loadConfig()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	log.Printf("Connecting to Kafka brokers: %v", config.KafkaBrokers)
	log.Printf("Monitoring topics: %v", config.KafkaTopics)
	log.Printf("Consumer Group: %s", config.ConsumerGroup)

	// Wait for Kafka to be ready
	if err := waitForKafka(config.KafkaBrokers, config.KafkaTopics, 10); err != nil {
		log.Fatalf("Failed to connect to Kafka: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle shutdown signals
	sigterm := make(chan os.Signal, 1)
	signal.Notify(sigterm, syscall.SIGINT, syscall.SIGTERM)

	// WaitGroup to track all consumer goroutines
	var wg sync.WaitGroup

	// Start a consumer goroutine for each topic
	for _, topic := range config.KafkaTopics {
		wg.Add(1)
		go consumeTopic(ctx, &wg, config, topic)
	}

	log.Printf("All consumers started, monitoring %d DLQ topics...", len(config.KafkaTopics))

	// Wait for interrupt signal
	<-sigterm
	log.Println("Shutting down gracefully...")
	cancel()

	// Wait for all consumers to finish
	wg.Wait()
	log.Println("All consumers stopped. Shutdown complete.")
}
