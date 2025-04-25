# University Python Web - Homework 12

## 📚 Lesson Resources

- [Lesson 11 Video](https://www.youtube.com/watch?v=mdn_MKntxUU)
- [Lesson 12 Video](https://www.youtube.com/watch?v=8aU_ILMz_Ak&t)

## 📚 GitHub Resources

- [Repo from text](https://github.com/goitacademy/FullStack-Web-Development-with-Python/tree/main/Chapter_12)
- [Repo from lesson!!!](https://github.com/Krabaton/FullStack-Web-Development-with-Python-Master-of-Science-Software-Engineering-1/tree/main/mcs10_12)

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

## 🛠 Redis Configuration

```bash
brew update
brew install redis
brew services start redis
```

_Note: Run \***\*`fastapi dev ./main.py`\*\*** only after starting Redis!_

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
```

## 🧪 Testing

### Running Tests
```bash
# Run repository tests
pytest tests/repositories/test_contacts_repository.py -v

# Run authentication tests
pytest tests/test_e2e_auth.py -v

# Generate coverage report (will be located in the htmlcov/index.html)
pytest --cov-report html --cov=src tests/
```

### Known Issues
- Issue with access token after refresh route:
  - Old access token doesn't revoke
  - New token works even after logout
  - Logout revokes old access token but doesn't affect new token from refresh route
  - Solution approach: Store access token in Redis after login, revoke it when refresh route is used, and store new token in Redis
- Issue with reset password email:
  - Basic template created but mail host blocks the logic
  - Works correctly in Postman
  - For proper functionality: Should link to front-end page with password reset form

## 📖 Documentation

### Sphinx Documentation
To create documentation with Sphinx:
1. Navigate to the docs folder
2. Run: `make html`
3. Custom styles in `_static/custom.css`
4. CSS connection in `docs/conf.py`: `html_css_files = ["custom.css"]`
5. To apply CSS changes: Run `make html` after each modification
