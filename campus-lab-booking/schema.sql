CREATE DATABASE IF NOT EXISTS campus_lab_booking;
USE campus_lab_booking;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    college_id VARCHAR(30) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('STUDENT','FACULTY','STAFF','INCHARGE','ADMIN') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS students (
    user_id INT PRIMARY KEY,
    programme VARCHAR(100) NULL,
    year_of_study INT NULL,
    contact_number VARCHAR(15) NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS faculty (
    user_id INT PRIMARY KEY,
    department VARCHAR(100) NULL,
    designation VARCHAR(100) NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS staff (
    user_id INT PRIMARY KEY,
    department VARCHAR(100) NULL,
    designation VARCHAR(100) NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- A lab stores its physical identity. Its assigned in-charge is stored
-- once in lab_incharges.lab_id (unique), avoiding duplicate relationships.
CREATE TABLE IF NOT EXISTS labs (
    lab_id INT AUTO_INCREMENT PRIMARY KEY,
    lab_name VARCHAR(100) NOT NULL UNIQUE,
    floor_number INT NOT NULL
);

CREATE TABLE IF NOT EXISTS lab_incharges (
    user_id INT PRIMARY KEY,
    department VARCHAR(100) NOT NULL,
    designation VARCHAR(100) NOT NULL,
    lab_id INT NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (lab_id) REFERENCES labs(lab_id)
);

CREATE TABLE IF NOT EXISTS computers (
    computer_id INT AUTO_INCREMENT PRIMARY KEY,
    computer_code VARCHAR(30) NOT NULL UNIQUE,
    lab_id INT NOT NULL,
    health_status ENUM('HEALTHY','UNHEALTHY') NOT NULL DEFAULT 'HEALTHY',
    health_updated_by INT,
    health_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (lab_id) REFERENCES labs(lab_id),
    FOREIGN KEY (health_updated_by) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS timetable_slots (
    slot_id INT AUTO_INCREMENT PRIMARY KEY,
    day_of_week ENUM('MON','TUE','WED','THU','FRI','SAT','SUN') NOT NULL,
    slot_code VARCHAR(20) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    display_label VARCHAR(100),
    UNIQUE(day_of_week, slot_code)
);

CREATE TABLE IF NOT EXISTS bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    booking_date DATE NOT NULL,
    purpose VARCHAR(255),
    status ENUM('CONFIRMED','CANCELLED') NOT NULL DEFAULT 'CONFIRMED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS booking_items (
    booking_item_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    computer_id INT NOT NULL,
    slot_id INT NOT NULL,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
    FOREIGN KEY (computer_id) REFERENCES computers(computer_id),
    FOREIGN KEY (slot_id) REFERENCES timetable_slots(slot_id),
    UNIQUE(booking_id, computer_id, slot_id)
);

CREATE TABLE IF NOT EXISTS maintenance (
    maintenance_id INT AUTO_INCREMENT PRIMARY KEY,
    computer_id INT NOT NULL,
    reported_by INT,
    description TEXT NOT NULL,
    status ENUM('OPEN','IN_PROGRESS','RESOLVED') NOT NULL DEFAULT 'OPEN',
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (computer_id) REFERENCES computers(computer_id),
    FOREIGN KEY (reported_by) REFERENCES users(user_id) ON DELETE SET NULL
);
