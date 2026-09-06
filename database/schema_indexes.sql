-- Custom Index Builder - Database Schema Extension
-- FuFu Index Platform for Indian Stock Market (NSE/BSE)
-- Run this in MySQL Workbench after the base schema

USE stock_app;

-- ============================================================
-- Custom indexes created by users
-- ============================================================
CREATE TABLE IF NOT EXISTS custom_indexes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sector VARCHAR(50),
    theme VARCHAR(50),
    universe_size INT NOT NULL,
    top_n INT NOT NULL,
    weight_strategy ENUM('EQUAL', 'MARKET_CAP', 'CUSTOM', 'PERFORMANCE') DEFAULT 'EQUAL',
    rebalance_frequency ENUM('SEMI_ANNUAL') DEFAULT 'SEMI_ANNUAL',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_theme (theme),
    INDEX idx_sector (sector)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Companies in a custom index's universe (the pool)
-- User selects N companies, system picks top_n from these
-- ============================================================
CREATE TABLE IF NOT EXISTS index_constituents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    index_id INT NOT NULL,
    stock_id INT NOT NULL,
    custom_weight DECIMAL(5,2) DEFAULT NULL,
    is_active_in_index BOOLEAN DEFAULT TRUE,
    rank_position INT DEFAULT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (index_id) REFERENCES custom_indexes(id) ON DELETE CASCADE,
    FOREIGN KEY (stock_id) REFERENCES stocks(id),
    UNIQUE KEY unique_index_stock (index_id, stock_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Investment positions in custom indexes
-- Like mutual fund units with NAV tracking
-- ============================================================
CREATE TABLE IF NOT EXISTS index_investments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    index_id INT NOT NULL,
    total_invested DECIMAL(15,2) DEFAULT 0.00,
    current_value DECIMAL(15,2) DEFAULT 0.00,
    units DECIMAL(15,6) DEFAULT 0.000000,
    nav DECIMAL(15,4) DEFAULT 100.0000,
    status ENUM('ACTIVE', 'REDEEMED') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (index_id) REFERENCES custom_indexes(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_index (user_id, index_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Individual stock allocations within an index investment
-- ============================================================
CREATE TABLE IF NOT EXISTS index_holdings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    investment_id INT NOT NULL,
    stock_id INT NOT NULL,
    quantity INT DEFAULT 0,
    allocated_amount DECIMAL(15,2) DEFAULT 0.00,
    weight_percent DECIMAL(5,2) DEFAULT 0.00,
    avg_buy_price DECIMAL(15,2) DEFAULT 0.00,
    FOREIGN KEY (investment_id) REFERENCES index_investments(id) ON DELETE CASCADE,
    FOREIGN KEY (stock_id) REFERENCES stocks(id),
    UNIQUE KEY unique_investment_stock (investment_id, stock_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Index NAV value history (for performance charts)
-- ============================================================
CREATE TABLE IF NOT EXISTS index_value_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    index_id INT NOT NULL,
    nav DECIMAL(15,4) NOT NULL,
    total_value DECIMAL(15,2) DEFAULT 0.00,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (index_id) REFERENCES custom_indexes(id) ON DELETE CASCADE,
    INDEX idx_index_date (index_id, recorded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Rebalance execution log
-- Records every buy/sell during rebalancing
-- ============================================================
CREATE TABLE IF NOT EXISTS rebalance_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    index_id INT NOT NULL,
    investment_id INT NOT NULL,
    rebalance_type ENUM('SEMI_ANNUAL', 'MANUAL') DEFAULT 'SEMI_ANNUAL',
    action VARCHAR(20),
    stock_symbol VARCHAR(20),
    old_weight DECIMAL(5,2),
    new_weight DECIMAL(5,2),
    quantity_change INT DEFAULT 0,
    price_at_rebalance DECIMAL(15,2) DEFAULT 0.00,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (index_id) REFERENCES custom_indexes(id) ON DELETE CASCADE,
    FOREIGN KEY (investment_id) REFERENCES index_investments(id) ON DELETE CASCADE,
    INDEX idx_index_date (index_id, executed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- AI advisor interaction log
-- Records all AI-powered trade advice
-- ============================================================
CREATE TABLE IF NOT EXISTS ai_advisor_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    context_type ENUM('INDEX_BUY', 'INDEX_SELL', 'STOCK_BUY', 'STOCK_SELL', 'REBALANCE') NOT NULL,
    stock_symbol VARCHAR(20),
    index_id INT,
    query TEXT,
    ai_response TEXT,
    sentiment VARCHAR(20),
    confidence DECIMAL(5,2),
    news_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
