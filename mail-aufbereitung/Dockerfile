# Utilisation de l'image officielle Python en version allégée
FROM python:3.11-slim

# Emplacement du projet dans le conteneur
WORKDIR /app

# Utilitaires de compilation requis par 'confluent-kafka' car c'est une extension C
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer le fichier requirements.txt localement
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le script python et autres fichiers annexes
COPY main.py .

# Lancement du micro-service
CMD ["python", "main.py"]
