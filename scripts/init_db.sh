#!/bin/bash

# Script to initialize the database tables for the first time
# Run this from the root directory: bash scripts/init_db.sh

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        Database Initialization Script                      ║"
echo "╚════════════════════════════════════════════════════════════╝"

# Check if database is running
if ! docker-compose exec -T mysql mysqladmin ping -h localhost > /dev/null 2>&1; then
    echo "ERROR: MySQL is not running. Please start Docker containers first."
    echo "Run: docker-compose up -d"
    exit 1
fi

echo "✓ Database connection established"
echo ""

# Create initial tables
echo "Creating initial database tables..."

# Create users table
docker-compose exec -T mysql mysql -u root -p"${DB_PASSWORD}" "${DB_NAME}" << 'EOF'
SET FOREIGN_KEY_CHECKS = 0;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(500) NOT NULL,
    phone VARCHAR(20),
    profile_picture VARCHAR(500),
    bio TEXT,
    status ENUM('pending', 'active', 'suspended', 'banned') DEFAULT 'pending',
    role VARCHAR(50) DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_username (username),
    INDEX idx_status (status)
);

-- Audit trail table
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id INT,
    details JSON,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);

SET FOREIGN_KEY_CHECKS = 1;
EOF

echo "✓ Tables created successfully"
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║        Database initialization completed!                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
