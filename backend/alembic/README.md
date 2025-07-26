# Database Migrations

This directory contains database migrations managed by Alembic.

## Running Migrations

### Apply all migrations

```bash
cd backend
alembic upgrade head
```

### Create a new migration

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

### Rollback one migration

```bash
cd backend
alembic downgrade -1
```

### View migration history

```bash
cd backend
alembic history
```

## Seed Data

To populate the database with sample data for development:

```bash
cd backend
python -m app.scripts.seed_data
```

This will create:

- Sample users with different roles (admin, collaborator, viewer)
- Sample projects
- Sample application assessments with realistic data

## Migration Files

- `001_initial_schema.py` - Creates the initial database schema including:
  - Users table with RBAC support
  - Projects and project members tables
  - Application assessments table with 22 critical attributes
  - Legacy tables (applications, collection_flows)
