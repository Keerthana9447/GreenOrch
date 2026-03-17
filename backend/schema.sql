-- GreenOrch Database Schema

CREATE TABLE IF NOT EXISTS carbon_regions (
    region_id VARCHAR(50) PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL,
    provider VARCHAR(50),
    carbon_intensity DECIMAL(6,4) NOT NULL,
    renewable_pct INTEGER,
    pue DECIMAL(4,2),
    lat DECIMAL(8,5),
    lng DECIMAL(8,5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workloads (
    id SERIAL PRIMARY KEY,
    workload_id VARCHAR(50) UNIQUE NOT NULL,
    cpu_load DECIMAL(5,3) NOT NULL,
    execution_time DECIMAL(8,2) NOT NULL,
    memory_usage DECIMAL(5,3),
    workload_type VARCHAR(50),
    selected_region VARCHAR(50) REFERENCES carbon_regions(region_id),
    energy_consumed DECIMAL(10,6),
    carbon_emission DECIMAL(10,6),
    baseline_emission DECIMAL(10,6),
    reduction_pct DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    recorded_at DATE NOT NULL,
    baseline_emission DECIMAL(10,4),
    optimized_emission DECIMAL(10,4),
    reduction_percentage DECIMAL(5,2),
    workloads_processed INTEGER,
    carbon_saved_kg DECIMAL(10,4)
);

CREATE TABLE IF NOT EXISTS ml_predictions (
    id SERIAL PRIMARY KEY,
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hour_of_day INTEGER,
    predicted_cpu DECIMAL(5,3),
    actual_cpu DECIMAL(5,3),
    model_version VARCHAR(50)
);

-- Seed carbon regions
INSERT INTO carbon_regions (region_id, region_name, provider, carbon_intensity, renewable_pct, pue, lat, lng)
VALUES
    ('us-east',     'US East (N. Virginia)',   'AWS',   0.386, 42, 1.20, 37.77, -78.17),
    ('eu-west',     'EU West (Ireland)',        'AWS',   0.198, 71, 1.15, 53.35,  -6.26),
    ('asia-south',  'Asia South (Mumbai)',      'GCP',   0.708, 18, 1.35, 19.08,  72.88),
    ('us-west',     'US West (Oregon)',         'AWS',   0.091, 89, 1.10, 45.52,-122.68),
    ('eu-north',    'EU North (Stockholm)',     'Azure', 0.013, 98, 1.08, 59.33,  18.07),
    ('ap-southeast','AP Southeast (Singapore)', 'GCP',   0.431, 35, 1.25,  1.35, 103.82),
    ('eu-central',  'EU Central (Frankfurt)',   'Azure', 0.233, 65, 1.18, 50.11,   8.68),
    ('us-central',  'US Central (Iowa)',        'GCP',   0.147, 79, 1.12, 41.88, -93.10)
ON CONFLICT DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_workloads_created ON workloads(created_at);
CREATE INDEX IF NOT EXISTS idx_workloads_region ON workloads(selected_region);
CREATE INDEX IF NOT EXISTS idx_metrics_date ON metrics(recorded_at);
