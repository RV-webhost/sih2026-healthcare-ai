import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Securely grab the Neon connection string
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing. Please check your .env file.")

# ---------------------------------------------------------
# 1. THE SCHEMA (Creating the Tables)
# ---------------------------------------------------------
SCHEMA_SQL = """
-- Drop tables if they exist so we can run this script multiple times safely
DROP TABLE IF EXISTS beds CASCADE;
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS doctors CASCADE;

CREATE TABLE doctors (
    doctor_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    is_available BOOLEAN DEFAULT TRUE
);

CREATE TABLE patients (
    patient_id VARCHAR(50) PRIMARY KEY,
    patient_name VARCHAR(100) NOT NULL,
    contact_number VARCHAR(15) NOT NULL,
    department_required VARCHAR(50) NOT NULL,
    symptoms TEXT,
    token_number VARCHAR(50),
    queue_position INT,
    estimated_wait_time_mins INT
);

CREATE TABLE beds (
    bed_id VARCHAR(50) PRIMARY KEY,
    department VARCHAR(50) NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    patient_id VARCHAR(50) REFERENCES patients(patient_id) ON DELETE SET NULL
);
"""

# ---------------------------------------------------------
# 2. THE RAW DATA (Injecting Dummy Data)
# ---------------------------------------------------------
SEED_DATA_SQL = """
-- Insert Mock Doctors
INSERT INTO doctors (doctor_id, name, department, is_available) VALUES
('DOC-001', 'Dr. Sharma', 'Cardiology', TRUE),
('DOC-002', 'Dr. Gupta', 'Neurology', TRUE),
('DOC-003', 'Dr. Patel', 'General', FALSE);

-- Insert Mock Patients
INSERT INTO patients (patient_id, patient_name, contact_number, department_required, symptoms, token_number, queue_position, estimated_wait_time_mins) VALUES
('P-8847', 'Rahul Sharma', '9876543210', 'General', 'High fever', 'T-01', 1, 15),
('P-8848', 'Priya Singh', '9123456789', 'Cardiology', 'Severe chest pain', 'T-42', 5, 45);

-- Insert Mock Beds (Matching the API Contract)
INSERT INTO beds (bed_id, department, is_available, patient_id) VALUES
('B-101', 'ICU', TRUE, NULL),
('B-102', 'General', FALSE, 'P-8847'),
('B-103', 'Cardiology', TRUE, NULL),
('B-104', 'Neurology', TRUE, NULL);
"""

def run_seed():
    print("🌱 Connecting to Neon Cloud Database...")
    try:
        # Connect to your Neon PostgreSQL database
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        print("⚠️  Wiping old data and building fresh tables...")
        cur.execute(SCHEMA_SQL)

        print("💉 Injecting raw hackathon data...")
        cur.execute(SEED_DATA_SQL)

        # Commit the changes and close the connection
        conn.commit()
        cur.close()
        conn.close()
        
        print("✅ Success! The database is seeded and ready for the team.")
        
    except Exception as e:
        print(f"❌ Error seeding the database: {e}")

if __name__ == "__main__":
    run_seed()