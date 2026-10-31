import os
import socket
import datetime
from flask import Flask, jsonify

app = Flask(__name__)

# In Spring Boot, these would be in application.yml (e.g., ${APP_ENV:local-docker})
# and injected via @Value("${app.env}") or @ConfigurationProperties.
APP_ENV = os.getenv("APP_ENV", "local-docker")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
REDIS_HOST = os.getenv("REDIS_HOST", "")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Optional Redis connection (used starting in Stage 2: Docker Compose & Stage 3: Kubernetes)
redis_client = None
if REDIS_HOST:
    import redis
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        socket_connect_timeout=1,
    )

# Simple in-memory counter for Stage 1 (resets when container stops/restarts!)
local_hits = 0


def get_hit_count():
    """
    Stage 1: Counts hits in container memory (demonstrating why containers are stateless).
    Stage 2+: If REDIS_HOST is configured, stores hits in a shared Redis container.
    """
    global local_hits
    if redis_client:
        try:
            return f"{redis_client.incr('hits')} (stored in Redis @ {REDIS_HOST}:{REDIS_PORT})"
        except Exception as e:
            return f"Redis error: {e}"
    local_hits += 1
    return f"{local_hits} (in-memory only — resets if container restarts!)"


@app.route("/")
def index():
    # Inside Docker/Kubernetes, socket.gethostname() returns the Container ID or Pod Name!
    container_id = socket.gethostname()
    hits = get_hit_count()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Docker & K8s Learning Lab</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 680px; margin: 40px auto; padding: 0 20px; background: #f8fafc; color: #1e293b; }}
            .card {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); border: 1px solid #e2e8f0; }}
            .badge {{ display: inline-block; background: #dbeafe; color: #1e40af; padding: 4px 10px; border-radius: 9999px; font-size: 0.85rem; font-weight: 600; }}
            .pod-box {{ background: #0f172a; color: #38bdf8; padding: 14px 18px; border-radius: 8px; font-family: monospace; font-size: 1.2rem; margin: 16px 0; }}
            .meta {{ color: #64748b; font-size: 0.9rem; margin-top: 16px; }}
            a {{ color: #2563eb; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="card">
            <span class="badge">Environment: {APP_ENV} | v{APP_VERSION}</span>
            <h2>🐳 Container / Pod Responder</h2>
            <p>Your request was handled by container hostname (Pod ID):</p>
            <div class="pod-box">{container_id}</div>
            <p><strong>Hit Counter:</strong> {hits}</p>
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <p><strong>Spring Boot Equivalent Endpoints:</strong></p>
            <ul>
                <li><a href="/actuator/health">/actuator/health</a> (Overall Health)</li>
                <li><a href="/actuator/health/liveness">/actuator/health/liveness</a> (K8s Liveness Probe)</li>
                <li><a href="/actuator/health/readiness">/actuator/health/readiness</a> (K8s Readiness Probe)</li>
                <li><a href="/api/info">/api/info</a> (JSON API response)</li>
            </ul>
            <div class="meta">Timestamp: {now}</div>
        </div>
    </body>
    </html>
    """


@app.route("/api/info")
def api_info():
    """JSON endpoint similar to a @RestController in Spring Boot."""
    return jsonify({
        "containerId": socket.gethostname(),
        "environment": APP_ENV,
        "version": APP_VERSION,
        "hits": get_hit_count(),
        "timestamp": datetime.datetime.now().isoformat()
    })


# =====================================================================
# Spring Boot Actuator Equivalent Health Endpoints for Kubernetes Probes
# =====================================================================

@app.route("/actuator/health")
def health():
    return jsonify({
        "status": "UP",
        "components": {
            "livenessState": {"status": "UP"},
            "readinessState": {"status": "UP"}
        }
    }), 200


@app.route("/actuator/health/liveness")
def liveness():
    """
    Kubernetes 'livenessProbe' checks this endpoint.
    If this returns 500 or times out, Kubernetes kills and restarts the container.
    """
    return jsonify({"status": "UP"}), 200


@app.route("/actuator/health/readiness")
def readiness():
    """
    Kubernetes 'readinessProbe' checks this endpoint.
    If this returns 503, Kubernetes stops sending traffic to this Pod until it recovers.
    """
    if redis_client:
        try:
            redis_client.ping()
        except Exception as e:
            return jsonify({"status": "DOWN", "reason": str(e)}), 503
    return jsonify({"status": "UP"}), 200


if __name__ == "__main__":
    # In Spring Boot, server.port defaults to 8080. Let's use 8080 here too!
    # IMPORTANT for Docker: host="0.0.0.0" tells the server to listen on all network
    # interfaces inside the container, not just 127.0.0.1 (localhost).
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
