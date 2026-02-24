import smtplib
from email.message import EmailMessage

def send_mock_email():
    msg = EmailMessage()
    msg.set_content("Hello,\n\nThis is a simulated test email for the Franz Kafka system!\nI have an access issue.\n\nBest regards.")
    msg['Subject'] = '[TICKET] Access issue'
    msg['From'] = 'dilhan@test.local'
    msg['To'] = 'test@franz.local'

    try:
        print("Sending email to GreenMail on localhost:3025...")
        with smtplib.SMTP('localhost', 3025) as server:
            server.send_message(msg)
        print("✅ Email sent successfully!\nOpen the 'mail-kummerkasten' logs or the Kafka topic to see the result.")
    except Exception as e:
        print(f"❌ SMTP sending error: {e}")

if __name__ == '__main__':
    send_mock_email()
