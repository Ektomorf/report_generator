-- SQL Schema for Test Results Archive System
-- SQLite compatible schema

-- Campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_name VARCHAR(255) UNIQUE NOT NULL,
    campaign_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_campaign_date ON campaigns(campaign_date);
CREATE INDEX IF NOT EXISTS idx_campaign_name ON campaigns(campaign_name);

-- Tests table
CREATE TABLE IF NOT EXISTS tests (
    test_id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL,
    test_name VARCHAR(255) NOT NULL,
    test_path VARCHAR(500),
    status VARCHAR(20) CHECK(status IN ('passed', 'failed', 'unknown')),
    start_time DATETIME,
    start_timestamp BIGINT,
    docstring TEXT,
    analyzer_html_path VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_campaign_test ON tests(campaign_id, test_name);
CREATE INDEX IF NOT EXISTS idx_status ON tests(status);
CREATE INDEX IF NOT EXISTS idx_start_time ON tests(start_time);

-- Test parameters table
CREATE TABLE IF NOT EXISTS test_params (
    param_id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id INTEGER NOT NULL,
    param_name VARCHAR(255) NOT NULL,
    param_value TEXT,
    FOREIGN KEY (test_id) REFERENCES tests(test_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_test_params ON test_params(test_id);

-- Test results table (stores result rows from combined CSV)
CREATE TABLE IF NOT EXISTS test_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id INTEGER NOT NULL,
    row_index INTEGER,
    timestamp BIGINT,
    timestamp_formatted VARCHAR(50),
    pass BOOLEAN,
    command_method VARCHAR(255),
    command_str TEXT,
    raw_response TEXT,
    peak_frequency FLOAT,
    peak_amplitude FLOAT,
    failure_messages TEXT,
    is_result_row BOOLEAN DEFAULT 1,
    row_class VARCHAR(50),
    full_data_json TEXT,
    FOREIGN KEY (test_id) REFERENCES tests(test_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_test_results ON test_results(test_id, row_index);
CREATE INDEX IF NOT EXISTS idx_pass ON test_results(pass);
CREATE INDEX IF NOT EXISTS idx_timestamp ON test_results(timestamp);

-- Test logs table (stores log rows from combined CSV)
CREATE TABLE IF NOT EXISTS test_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id INTEGER NOT NULL,
    row_index INTEGER,
    timestamp BIGINT,
    timestamp_formatted VARCHAR(50),
    level VARCHAR(20),
    message TEXT,
    log_type VARCHAR(50),
    line_number INTEGER,
    full_data_json TEXT,
    FOREIGN KEY (test_id) REFERENCES tests(test_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_test_logs ON test_logs(test_id, row_index);
CREATE INDEX IF NOT EXISTS idx_level ON test_logs(level);
CREATE INDEX IF NOT EXISTS idx_log_timestamp ON test_logs(timestamp);

-- Failure messages table
CREATE TABLE IF NOT EXISTS failure_messages (
    failure_id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id INTEGER NOT NULL,
    message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (test_id) REFERENCES tests(test_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_test_failures ON failure_messages(test_id);

-- Artefacts table
CREATE TABLE IF NOT EXISTS artefacts (
    artefact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id INTEGER,
    artefact_type VARCHAR(20) CHECK(artefact_type IN ('csv', 'analyzer_html', 'log', 'json', 'screenshot')),
    file_path VARCHAR(500) NOT NULL UNIQUE,
    file_hash VARCHAR(64),
    processed BOOLEAN DEFAULT 0,
    processed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (test_id) REFERENCES tests(test_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_test_artefacts ON artefacts(test_id, artefact_type);
CREATE INDEX IF NOT EXISTS idx_processed ON artefacts(processed);
CREATE INDEX IF NOT EXISTS idx_file_hash ON artefacts(file_hash);

-- Processing log table
CREATE TABLE IF NOT EXISTS processing_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    artefact_id INTEGER,
    processing_status VARCHAR(20) CHECK(processing_status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    started_at DATETIME,
    completed_at DATETIME,
    FOREIGN KEY (artefact_id) REFERENCES artefacts(artefact_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_processing_status ON processing_log(processing_status);
