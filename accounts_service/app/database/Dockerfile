FROM postgres:15-alpine

# Set environment variables (should be overridden in GitLab CI/CD)
ENV POSTGRES_DB=gdb_accounts_db
ENV POSTGRES_USER=user
ENV POSTGRES_PASSWORD=password

# Copy the schema file to the initialization directory
# The accounts_service/app/database/accounts_schema.sql will be copied here by GitLab CI/CD or docker context
COPY accounts_schema.sql /docker-entrypoint-initdb.d/

EXPOSE 5432
