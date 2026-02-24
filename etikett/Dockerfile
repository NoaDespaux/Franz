# Build stage
FROM maven:3.9.6-eclipse-temurin-21 AS builder

WORKDIR /app

# Copy pom.xml and other maven config files
COPY pom.xml .
COPY mvnw .
COPY mvnw.cmd .
COPY .mvn .mvn

# Download dependencies
RUN mvn dependency:resolve

# Copy source code
COPY src ./src

# Build the application
RUN mvn clean package -DskipTests

# Final stage
FROM eclipse-temurin:21-jre-alpine

WORKDIR /root/

# Copy the JAR file from builder
COPY --from=builder /app/target/*.jar app.jar

# Expose port (adjust if needed)
EXPOSE 8080

# Run the application
CMD ["java", "-jar", "app.jar"]
