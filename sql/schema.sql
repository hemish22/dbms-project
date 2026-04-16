-- Cloud Resource Usage & Cost Optimization System
-- Chapter 2: Schema

CREATE DATABASE IF NOT EXISTS Cloud_Cost_Optimization;
USE Cloud_Cost_Optimization;

-- Table 1: User
CREATE TABLE IF NOT EXISTS User (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    organization VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: Cloud_Resource
CREATE TABLE IF NOT EXISTS Cloud_Resource (
    resource_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    resource_type ENUM('VM', 'Storage', 'Database', 'Network') NOT NULL,
    instance_type VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL,
    status ENUM('Running', 'Stopped', 'Idle') DEFAULT 'Running',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- Table 3: Usage_Log
CREATE TABLE IF NOT EXISTS Usage_Log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    resource_id INT NOT NULL,
    cpu_usage DECIMAL(5,2) NOT NULL CHECK (cpu_usage >= 0 AND cpu_usage <= 100),
    memory_usage DECIMAL(5,2) NOT NULL CHECK (memory_usage >= 0 AND memory_usage <= 100),
    storage_used DECIMAL(10,2) NOT NULL CHECK (storage_used >= 0),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resource_id) REFERENCES Cloud_Resource(resource_id) ON DELETE CASCADE
);

-- Table 4: Billing
CREATE TABLE IF NOT EXISTS Billing (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    resource_id INT NOT NULL,
    usage_hours DECIMAL(8,2) NOT NULL,
    cost_per_hour DECIMAL(8,4) NOT NULL,
    total_cost DECIMAL(10,2) DEFAULT 0.00,
    billing_date DATE NOT NULL DEFAULT (CURDATE()),
    FOREIGN KEY (resource_id) REFERENCES Cloud_Resource(resource_id) ON DELETE CASCADE
);

-- Table 5: Optimization_Suggestion
CREATE TABLE IF NOT EXISTS Optimization_Suggestion (
    suggestion_id INT AUTO_INCREMENT PRIMARY KEY,
    resource_id INT NOT NULL,
    suggestion_type ENUM('Stop', 'Resize', 'Schedule', 'Migrate') NOT NULL,
    reason TEXT NOT NULL,
    estimated_savings DECIMAL(8,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ai_recommendation TEXT NULL,
    ai_generated_at TIMESTAMP NULL,
    FOREIGN KEY (resource_id) REFERENCES Cloud_Resource(resource_id) ON DELETE CASCADE
);

-- Table 6: Chat_History
CREATE TABLE IF NOT EXISTS Chat_History (
    chat_id INT AUTO_INCREMENT PRIMARY KEY,
    user_question TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
