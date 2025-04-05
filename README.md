# University Python Web - Homework 12


## 📚 Lesson Resources

- [Lesson 9 Video](https://www.youtube.com/watch?v=w-xbSutnP0Q\&t=1s)
- [Lesson 10 Video](https://www.youtube.com/watch?v=r3xDHqpTOSo\&t=1s)

## 🚀 Quick Start

### Local PostgreSQL Setup

```bash
docker run --name some-postgres -p 5432:5432 -e POSTGRES_PASSWORD=mysecretpassword -d postgres
```

### 🔧 Development Setup

```bash
# Initialize async Alembic
alembic init -t async migrations

# Add development tools
poetry add black -G dev

# Create and apply migrations
alembic revision --autogenerate -m "Init"
alembic upgrade head

# Start development server
fastapi dev ./main.py
```

## 📖 Pagination Reference

[FastAPI Pagination Guide](https://uriyyo-fastapi-pagination.netlify.app/)

## 🛠 Redis Configuration

```bash
brew update
brew install redis
brew services start redis
```

*Note: Run ****`fastapi dev ./main.py`**** only after starting Redis!*

## 🐳 Docker Compose Commands

```bash
# Start containers in detached mode
docker-compose up -d

# Rebuild and start containers
docker-compose up -d --build

# Stop containers without deleting
docker-compose stop

# Stop and delete containers
docker-compose down -v

# Sync databases
docker-compose exec app python -m sync_databases save
```

## ⚠️ Common Issues

### SMTP Certificate Error

If you encounter:

```
Error connecting to smtp.meta.ua on port 465: [SSL: CERTIFICATE_VERIFY_FAILED]
```

Follow this solution:\
[SSL Certificate Fix](https://stackoverflow.com/questions/52805115/certificate-verify-failed-unable-to-get-local-issuer-certificate)

### PostgreSQL Version Check

```bash
# Check pg_dump versions
docker-compose exec app pg_dump --version
docker-compose exec postgres pg_dump --version
```

### Known Issues

- Issue with password hard-coding in `docker-compose.yml` (not resolved)
