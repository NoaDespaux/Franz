package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"log"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/joho/godotenv"
	_ "github.com/lib/pq"
	"github.com/segmentio/kafka-go"
)

// FormattedTicket holds the inner ticket data from Kafka
type FormattedTicket struct {
	Contact string `json:"contact"`
	Origin  string `json:"origin"`
	Date    int64  `json:"date"`
	Body    string `json:"body"`
}

// LabeledTicket represents the full Kafka message payload
type LabeledTicket struct {
	FormattedTicket FormattedTicket `json:"formattedTicket"`
	Category        string          `json:"category"`
	Priority        string          `json:"priority"`
	Type            string          `json:"type"`
}

// Config holds the application configuration
type Config struct {
	KafkaBrokers  []string
	KafkaTopic    string
	ConsumerGroup string
	PostgresDSN   string
}

func loadConfig() *Config {
	_ = godotenv.Load()

	brokersRaw := getEnv("KAFKA_BROKERS", "localhost:9092")
	brokers := strings.Split(brokersRaw, ",")
	for i := range brokers {
		brokers[i] = strings.TrimSpace(brokers[i])
	}

	return &Config{
		KafkaBrokers:  brokers,
		KafkaTopic:    getEnv("KAFKA_TOPIC", "tickets-labeled"),
		ConsumerGroup: getEnv("CONSUMER_GROUP", "exportdienst"),
		PostgresDSN:   getEnv("POSTGRES_DSN", "postgres://postgres:postgres@localhost:5432/tickets?sslmode=disable"),
	}
}

func getEnv(key, defaultValue string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return defaultValue
}

func initDB(dsn string) (*sql.DB, error) {
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		return nil, err
	}

	if err = db.Ping(); err != nil {
		return nil, err
	}

	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS tickets (
			id       SERIAL PRIMARY KEY,
			contact  TEXT        NOT NULL,
			origin   TEXT        NOT NULL,
			date     TIMESTAMPTZ NOT NULL,
			body     TEXT        NOT NULL,
			category TEXT        NOT NULL,
			priority TEXT        NOT NULL,
			type     TEXT        NOT NULL
		)
	`)
	return db, err
}

func insertTicket(db *sql.DB, t LabeledTicket) error {
	date := time.UnixMilli(t.FormattedTicket.Date).UTC()
	_, err := db.Exec(
		`INSERT INTO tickets (contact, origin, date, body, category, priority, type)
		 VALUES ($1, $2, $3, $4, $5, $6, $7)`,
		t.FormattedTicket.Contact,
		t.FormattedTicket.Origin,
		date,
		t.FormattedTicket.Body,
		t.Category,
		t.Priority,
		t.Type,
	)
	return err
}

func main() {
	cfg := loadConfig()

	log.Println("connecting to postgres...")
	db, err := initDB(cfg.PostgresDSN)
	if err != nil {
		log.Fatalf("failed to initialize database: %v", err)
	}
	defer db.Close()
	log.Println("postgres connected and table ready")

	// Wait a bit to avoid race condition with topic creation
	// This ensures producers have time to create topics with initial data
	log.Println("waiting for upstream services to initialize...")
	time.Sleep(10 * time.Second)

	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:     cfg.KafkaBrokers,
		Topic:       cfg.KafkaTopic,
		GroupID:     cfg.ConsumerGroup,
		StartOffset: kafka.FirstOffset,
		MinBytes:    1,        // fetch as soon as any data is available
		MaxBytes:    10e6,     // 10 MB
		MaxWait:     5 * time.Second,
	})
	defer reader.Close()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigCh
		log.Println("shutting down...")
		cancel()
	}()

	log.Printf("consuming from topic %q with group %q", cfg.KafkaTopic, cfg.ConsumerGroup)
	for {
		msg, err := reader.ReadMessage(ctx)
		if err != nil {
			if ctx.Err() != nil {
				break
			}
			log.Printf("error reading message: %v", err)
			continue
		}

		var ticket LabeledTicket
		if err := json.Unmarshal(msg.Value, &ticket); err != nil {
			log.Printf("error unmarshaling message (offset %d): %v", msg.Offset, err)
			continue
		}

		if err := insertTicket(db, ticket); err != nil {
			log.Printf("error inserting ticket (offset %d): %v", msg.Offset, err)
			continue
		}

		log.Printf("inserted ticket: contact=%s category=%s priority=%s type=%s",
			ticket.FormattedTicket.Contact, ticket.Category, ticket.Priority, ticket.Type)
	}

	log.Println("exportdienst stopped")
}
