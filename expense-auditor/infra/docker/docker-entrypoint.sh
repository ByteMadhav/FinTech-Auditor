#!/bin/sh
set -e

# Function to wait for a service to be ready
wait_for_service() {
    host="$1"
    port="$2"
    service_name="$3"
    timeout="${4:-30}"
    
    echo "Waiting for $service_name to be ready..."
    for i in $(seq 1 $timeout); do
        if nc -z "$host" "$port"; then
            echo "$service_name is ready!"
            return 0
        fi
        echo "Waiting for $service_name... $i/$timeout"
        sleep 1
    done
    echo "Timeout reached waiting for $service_name"
    return 1
}

# Wait for dependent services based on environment variables
if [ -n "$DATABASE_URL" ] && echo "$DATABASE_URL" | grep -q "postgresql"; then
    # Extract host and port from DATABASE_URL
    db_host=$(echo "$DATABASE_URL" | sed -E 's/.*@([^:]+):.*/\1/')
    db_port=$(echo "$DATABASE_URL" | sed -E 's/.*:([0-9]+).*/\1/')
    wait_for_service "$db_host" "$db_port" "PostgreSQL"
fi

if [ -n "$DATABASE_URL" ] && echo "$DATABASE_URL" | grep -q "mongodb"; then
    # Extract host and port from DATABASE_URL
    db_host=$(echo "$DATABASE_URL" | sed -E 's/.*@([^:]+):.*/\1/')
    db_port=$(echo "$DATABASE_URL" | sed -E 's/.*:([0-9]+).*/\1/')
    wait_for_service "$db_host" "$db_port" "MongoDB"
fi

if [ -n "$CELERY_BROKER_URL" ] && echo "$CELERY_BROKER_URL" | grep -q "redis"; then
    # Extract host and port from CELERY_BROKER_URL
    redis_host=$(echo "$CELERY_BROKER_URL" | sed -E 's/.*@([^:]+):.*/\1/')
    redis_port=$(echo "$CELERY_BROKER_URL" | sed -E 's/.*:([0-9]+).*/\1/')
    wait_for_service "$redis_host" "$redis_port" "Redis"
fi

if [ -n "$CELERY_BROKER_URL" ] && echo "$CELERY_BROKER_URL" | grep -q "amqp"; then
    # Extract host and port from CELERY_BROKER_URL
    rabbitmq_host=$(echo "$CELERY_BROKER_URL" | sed -E 's/.*@([^:]+):.*/\1/')
    rabbitmq_port=$(echo "$CELERY_BROKER_URL" | sed -E 's/.*:([0-9]+).*/\1/')
    wait_for_service "$rabbitmq_host" "$rabbitmq_port" "RabbitMQ"
fi

# Run database migrations if needed
if [ "$1" = "uvicorn" ] || [ "$1" = "gunicorn" ]; then
    echo "Running database migrations..."
    if [ -f "/app/alembic.ini" ]; then
        alembic upgrade head
    fi
fi

# Execute the command
exec "$@"
