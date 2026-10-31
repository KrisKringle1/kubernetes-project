# 1. Base Image: Start from an official, lightweight Python 3.12 Linux image
#    (Spring Boot equivalent: eclipse-temurin:21-jre-alpine)
FROM python:3.12-slim

# 2. Working Directory: Create and cd into /app inside the container
WORKDIR /app

# 3. Layer Caching Trick: Copy ONLY requirements.txt first and install dependencies.
#    Docker caches each step ("layer"). As long as requirements.txt doesn't change,
#    Docker will skip reinstalling packages when you edit app.py!
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy Application Code: Now copy the rest of our project into /app
COPY app.py .

# 5. Document the Port: Informs developers/tools that the container listens on 8080
#    (Just like Spring Boot's default server.port=8080)
EXPOSE 8080

# 6. Startup Command: What runs when the container starts
#    (Spring Boot equivalent: CMD ["java", "-jar", "app.jar"])
CMD ["python", "app.py"]
