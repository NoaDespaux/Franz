# Mail Kummerkasten Service

The `mail-kummerkasten` service is a Python-based microservice that acts as an entry point for emails into the Franz Kafka architecture. It connects to an IMAP server, fetches unread emails, and transforms them into JSON payloads before publishing them to a Kafka topic.

This service is analogous to the `discord-kummerkasten` service but specifically handles email inputs, allowing the ticketing system to be multi-channel.

## Features

- **IMAP Polling:** Connects to an IMAP server (e.g., Gmail, Outlook, or a local mock server) using a secure SSL or standard connection.
- **Unread Email Fetching:** Periodically polls the `INBOX` for emails marked as `UNSEEN`.
- **Automatic Marking:** Marks emails as read (`Seen`) simply by fetching them, preventing duplicate processing.
- **Body Extraction:** Parses the multipart email structure to safely extract the plain text body while ignoring attachments or HTML parts.
- **JSON Transformation:** Converts the extracted email data (sender, subject, body, timestamp) into a structured JSON payload.
- **Kafka Producer:** Publishes the JSON payload to a configurable Kafka topic (`mailMSG` by default).

## Architecture

1.  **Source:** Any standard IMAP Email Server.
2.  **Service:** `mail-kummerkasten` (Python script using `imaplib` and `email` packages).
3.  **Target Topic:** `mailMSG` (Configurable via `TARGET_TOPIC`).

### Payload Example

When an email is received, it is transformed into the following JSON structure and pushed to Kafka:

```json
{
  "sender": "client@example.com",
  "subject": "[TICKET] Billing Issue",
  "message": "Hello,\n\nI have an issue with my latest invoice. Could you please help?\n\nThanks.",
  "timestamp": "2026-02-24T12:00:00.000Z"
}
```

## Configuration

The service is highly configurable via environment variables, typically set in the `docker-compose.yml` or via a `.env` file.

| Environment Variable | Description | Default Value |
| :--- | :--- | :--- |
| `IMAP_SERVER` | Address of the IMAP server (e.g., `imap.gmail.com` or `greenmail`). | `imap.gmail.com` |
| `IMAP_PORT` | Port number for IMAP connection (standard is 993 for SSL, 143/3143 for standard). | `993` |
| `IMAP_USER` | Email address or username for IMAP authentication. | `contact@my-project.com` |
| `IMAP_PASS` | Password or App Password for the email account. | `password_or_app_password` |
| `IMAP_SSL` | Enable or disable SSL connection. Set to `true` for public providers like Gmail, `false` for internal mocks. | `true` |
| `POLL_INTERVAL` | Time in seconds to wait between each IMAP polling cycle. | `10` |
| `KAFKA_BROKER` | Address of the Kafka broker. | `localhost:9092` |
| `TARGET_TOPIC` | Kafka topic where processed emails will be published. | `mailMSG` |

> **Note on Gmail:** If using a real Gmail account, Google requires you to generate an **App Password** for `IMAP_PASS`. Your standard account password will not work for security reasons.

## Local Development & Mocking

For local development or CI/CD pipelines, you may not want to hook up a real email address. The default `docker-compose.yml` configuration is set up to use **GreenMail**, a local sandboxed email server.

1.  **Start the stack:** `docker compose up -d` (Includes GreenMail and Mail Kummerkasten)
2.  **Send a test email:** We provide a utility script to send an email directly to the local GreenMail mock without needing a real mail client.
    ```bash
    python3 send_test_mail.py
    ```

You should see logs in the `mail-kummerkasten` container confirming the email was fetched and published to the Kafka topic.
