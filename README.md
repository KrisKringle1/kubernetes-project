# 🐳 Docker & Kubernetes Hands-On Learning Lab (with Spring Boot Comparisons)

A 3-stage hands-on project demonstrating how an application evolves from a **single stateless Docker container** (Stage 1), to a **multi-container network with Redis** (Stage 2), to a **load-balanced, self-healing Kubernetes cluster** (Stage 3).

---

## 🏗️ Final Architecture (Stage 3: Kubernetes)

```text
                   [ Browser: http://localhost:8080 ]
                                   │
                                   ▼
          ┌─────────────────────────────────────────────────┐
          │  Kubernetes Service (k8s-lab-app-service)       │
          │  Type: LoadBalancer (Port 8080 -> 8080)         │
          └───────────┬────────────┬────────────┬───────────┘
                      │            │            │  (Splits traffic across READY Pods)
                      ▼            ▼            ▼
               ┌────────────┐┌────────────┐┌────────────┐
               │ Web Pod #1 ││ Web Pod #2 ││ Web Pod #3 │  ◄── Kubernetes Deployment
               │ (Replica)  ││ (Replica)  ││ (Replica)  │      (Maintains replicas: 3)
               └──────┬─────┘└──────┬─────┘└──────┬─────┘
                      │             │             │
                      └─────────────┼─────────────┘
                                    ▼
                     ┌─────────────────────────────┐
                     │  Redis Service (ClusterIP)  │
                     │  DNS: redis-cache:6379      │
                     │        [ Redis Pod ]        │  ◄── Shared Hit Counter in RAM
                     └─────────────────────────────┘
```

---

## 🔄 Python (Flask) ↔ Java (Spring Boot) Cheat Sheet

Containers are **language-agnostic**. Once packaged into an image, Kubernetes manages a Python container and a Spring Boot container identically:

| Concept | In This Repo (Python / Flask) | In Java / Spring Boot at Work |
| :--- | :--- | :--- |
| **Dependency File** | [`requirements.txt`](./requirements.txt) | `pom.xml` (Maven) or `build.gradle` (Gradle) |
| **Dockerfile** | [`Dockerfile`](./Dockerfile) (`python:3.12-slim`) | [`Dockerfile.spring-example`](./Dockerfile.spring-example) (Maven build → `eclipse-temurin:21-jre-alpine`) |
| **Startup CMD** | `CMD ["python", "app.py"]` | `CMD ["java", "-jar", "app.jar"]` |
| **Config / Env Vars** | `os.getenv("REDIS_HOST")` in [`app.py`](./app.py) | `application.yml` (`${SPRING_DATA_REDIS_HOST}`) |
| **Liveness Probe** | `/actuator/health/liveness` | `spring-boot-starter-actuator` (`/actuator/health/liveness`) |
| **Readiness Probe** | `/actuator/health/readiness` (pings Redis) | `spring-boot-starter-actuator` (`/actuator/health/readiness`) |
| **K8s Manifests** | [`k8s/deployment.yaml`](./k8s/deployment.yaml) & [`k8s/service.yaml`](./k8s/service.yaml) | **100% identical** (only the `image:` name changes!) |

---

## 🧠 Core Engineering Takeaways

1. **Image vs. Container = Class vs. Object Instance**
   - **`Dockerfile`**: Source code instructions for building the environment.
   - **Docker Image (`k8s-lab-app:1.0`)**: The compiled, read-only snapshot produced by `docker build`.
   - **Docker Container / Pod**: A live, isolated Linux process running in memory.
2. **Dockerfile Layer Caching**
   - Docker caches each step in a `Dockerfile`. Always `COPY` dependency manifests (`requirements.txt` / `pom.xml`) and install dependencies **before** copying application source code (`COPY app.py .`) so code edits rebuild in under a second.
3. **One Immutable Image Across Environments**
   - Never rebuild different images for `dev`, `staging`, and `prod`. Build once (`k8s-lab-app:1.0`) and inject environment variables (`APP_ENV`, `REDIS_HOST`) at runtime.
4. **Stateless Apps ("Cattle, Not Pets") & Redis**
   - App containers are disposable. If state lives in local container memory, it is lost on restart and isn't shared across replicas. Storing shared state/cache in **Redis** (an in-memory network key-value store) lets any web Pod die or scale horizontally without losing data.
5. **Liveness vs. Readiness Probes (`/actuator/health/*`)**
   - **Liveness (`/actuator/health/liveness`)**: *"Is my process deadlocked/frozen?"* If this fails, Kubernetes **kills and restarts** the container.
   - **Readiness (`/actuator/health/readiness`)**: *"Can this Pod serve traffic right now (e.g., is Redis reachable)?"* If this returns `503 DOWN`, Kubernetes **does not kill** the Pod—it simply stops routing user requests to it until it recovers.
6. **Declarative Control Loop & Rolling Updates**
   - In Kubernetes, you declare **Desired State** (`replicas: 3`). If a Pod is deleted, the ReplicaSet controller immediately spawns a replacement Pod.
   - During a version upgrade (`v1.0.0` → `v2.0.0`), Kubernetes performs a **Rolling Update**: it boots a new Pod first, waits for `/actuator/health/readiness` to return `200 UP`, and only then terminates an old Pod—achieving zero downtime.

---

## 🛠️ Command Cheat Sheet (Replay Any Stage Anytime)

### Stage 1: Single Docker Container (In-Memory Counter)
```bash
# 1. Build the image and tag it as k8s-lab-app:1.0
docker build -t k8s-lab-app:1.0 .

# 2. Run a single container in the background (-d), mapping Mac port 8080 -> Container port 8080
docker run -d -p 8080:8080 --name my-first-container k8s-lab-app:1.0

# 3. View running containers and logs
docker ps
docker logs my-first-container

# 4. Stop and remove the container
docker rm -f my-first-container
```

### Stage 2: Multi-Container with Docker Compose (Web App + Redis)
```bash
# 1. Start both web-app and redis-cache on a private virtual network
docker compose up -d

# 2. Test recreating the web container (Hit counter persists in Redis!)
docker compose up -d --force-recreate web-app

# 3. Tear down the Docker Compose stack
docker compose down
```

### Stage 3: Kubernetes Cluster (3 Load-Balanced Replicas + Self-Healing)
```bash
# 1. Apply all manifests in the k8s/ directory (Redis + Web Deployment + LoadBalancer Service)
kubectl apply -f k8s/

# 2. View running Pods, Services, and Deployments
kubectl get pods
kubectl get svc
kubectl get deployments

# 3. Watch Pods in real time (press Ctrl+C to stop watching)
kubectl get pods -w

# 4. Test Self-Healing: Delete any Pod and watch Kubernetes immediately spawn a replacement
kubectl delete pod <pod-name>

# 5. Scale up to 5 replicas (or back down to 3) instantly
kubectl scale deployment k8s-lab-app --replicas=5
kubectl scale deployment k8s-lab-app --replicas=3

# 6. Check rollout status or undo a deployment (instant rollback!)
kubectl rollout status deployment/k8s-lab-app
kubectl rollout undo deployment/k8s-lab-app

# 7. View logs from all Pods in the deployment
kubectl logs -l app=k8s-lab-app --tail=50

# 8. Pause/Clean up the Kubernetes resources when you're done practicing (frees up RAM)
kubectl delete -f k8s/
```
