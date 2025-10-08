#!/bin/bash
# Deployment script for Test Results Archive System

set -e  # Exit on error

echo "======================================"
echo "Test Results Archive - Deployment"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Parse arguments
COMMAND=${1:-"start"}

case "$COMMAND" in
    start)
        echo "Starting services..."
        docker-compose up -d
        echo ""
        echo "Services started successfully!"
        echo ""
        echo "Access the application at:"
        echo "  - Web UI: http://localhost:80"
        echo "  - API: http://localhost:80/api"
        echo "  - API Docs: http://localhost:80/docs"
        echo ""
        echo "Direct service access (without nginx):"
        echo "  - Web: http://localhost:8080"
        echo "  - API: http://localhost:8000"
        echo ""
        ;;

    stop)
        echo "Stopping services..."
        docker-compose stop
        echo "Services stopped."
        ;;

    restart)
        echo "Restarting services..."
        docker-compose restart
        echo "Services restarted."
        ;;

    down)
        echo "Stopping and removing containers..."
        docker-compose down
        echo "Containers removed."
        ;;

    logs)
        SERVICE=${2:-""}
        if [ -z "$SERVICE" ]; then
            docker-compose logs -f
        else
            docker-compose logs -f "$SERVICE"
        fi
        ;;

    build)
        echo "Building Docker images..."
        docker-compose build --no-cache
        echo "Build complete."
        ;;

    rebuild)
        echo "Rebuilding and restarting services..."
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
        echo "Rebuild complete."
        ;;

    status)
        echo "Service status:"
        docker-compose ps
        ;;

    import)
        echo "Running data import..."
        docker-compose exec api python sql_importer.py --scan output
        echo "Import complete."
        ;;

    backup)
        echo "Creating backup..."
        BACKUP_DIR="backups"
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).tar.gz"

        mkdir -p "$BACKUP_DIR"

        echo "Backing up database and configuration..."
        tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
            test_results.db \
            docker-compose.yml \
            nginx/ \
            --exclude='*.log'

        echo "Backup created: $BACKUP_DIR/$BACKUP_FILE"
        ;;

    restore)
        BACKUP_FILE=${2}
        if [ -z "$BACKUP_FILE" ]; then
            echo "Error: Please specify backup file to restore."
            echo "Usage: $0 restore <backup_file>"
            exit 1
        fi

        if [ ! -f "$BACKUP_FILE" ]; then
            echo "Error: Backup file not found: $BACKUP_FILE"
            exit 1
        fi

        echo "Warning: This will overwrite existing data!"
        read -p "Are you sure you want to continue? (yes/no): " CONFIRM

        if [ "$CONFIRM" = "yes" ]; then
            echo "Stopping services..."
            docker-compose stop

            echo "Restoring from backup..."
            tar -xzf "$BACKUP_FILE"

            echo "Starting services..."
            docker-compose start

            echo "Restore complete."
        else
            echo "Restore cancelled."
        fi
        ;;

    ssl)
        echo "Generating self-signed SSL certificate for testing..."
        mkdir -p nginx/ssl

        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/privkey.pem \
            -out nginx/ssl/fullchain.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

        echo "Self-signed certificate created."
        echo "Warning: This is for testing only. Use proper certificates in production."
        ;;

    clean)
        echo "Warning: This will remove all containers, volumes, and data!"
        read -p "Are you sure you want to continue? (yes/no): " CONFIRM

        if [ "$CONFIRM" = "yes" ]; then
            docker-compose down -v
            echo "Cleanup complete."
        else
            echo "Cleanup cancelled."
        fi
        ;;

    *)
        echo "Usage: $0 {start|stop|restart|down|logs|build|rebuild|status|import|backup|restore|ssl|clean}"
        echo ""
        echo "Commands:"
        echo "  start     - Start all services"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  down      - Stop and remove containers"
        echo "  logs      - View logs (optionally specify service: logs api)"
        echo "  build     - Build Docker images"
        echo "  rebuild   - Rebuild images and restart services"
        echo "  status    - Show service status"
        echo "  import    - Run data import from output directory"
        echo "  backup    - Create backup of database and config"
        echo "  restore   - Restore from backup (requires backup file)"
        echo "  ssl       - Generate self-signed SSL certificate"
        echo "  clean     - Remove all containers and volumes (WARNING: deletes data)"
        exit 1
        ;;
esac
