CREATE DATABASE IF NOT EXISTS db_linkEd;
USE db_linkEd;

-- =========================================
-- DROP TABLES (SAFE RE-RUN)
-- =========================================
DROP TABLE IF EXISTS tbl_fee_payments;
DROP TABLE IF EXISTS tbl_student_fees;
DROP TABLE IF EXISTS tbl_fee_structures;
DROP TABLE IF EXISTS tbl_attendance;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS homework_student;
DROP TABLE IF EXISTS homework_images;
DROP TABLE IF EXISTS homework;
DROP TABLE IF EXISTS tbl_teacher_assignments;
DROP TABLE IF EXISTS tbl_students;
DROP TABLE IF EXISTS tbl_users;
DROP TABLE IF EXISTS tbl_teachers;
DROP TABLE IF EXISTS tbl_subjects;
DROP TABLE IF EXISTS tbl_sections;
DROP TABLE IF EXISTS tbl_parents;
DROP TABLE IF EXISTS tbl_classes;

-- =========================================
-- TABLE: CLASSES
-- =========================================
CREATE TABLE tbl_classes (
    class_id INT AUTO_INCREMENT PRIMARY KEY,
    class_name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =========================================
-- TABLE: SECTIONS
-- =========================================
CREATE TABLE tbl_sections (
    section_id INT AUTO_INCREMENT PRIMARY KEY,
    class_id INT NOT NULL,
    section_name VARCHAR(10) NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (class_id) REFERENCES tbl_classes(class_id) ON DELETE CASCADE,
    UNIQUE(class_id, section_name)
);

-- =========================================
-- TABLE: SUBJECTS
-- =========================================
CREATE TABLE tbl_subjects (
    subject_id INT AUTO_INCREMENT PRIMARY KEY,
    subject_name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =========================================
-- TABLE: PARENTS
-- =========================================
CREATE TABLE tbl_parents (
    parent_id INT AUTO_INCREMENT PRIMARY KEY,
    father_name VARCHAR(150),
    mother_name VARCHAR(150),
    mobile VARCHAR(20) NOT NULL,
    email VARCHAR(150),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =========================================
-- TABLE: TEACHERS
-- =========================================
CREATE TABLE tbl_teachers (
    teacher_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    mobile VARCHAR(20),
    email VARCHAR(150) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =========================================
-- TABLE: STUDENTS
-- =========================================
CREATE TABLE tbl_students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    admission_no VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    dob DATE,
    gender ENUM('Male','Female','Other'),

    class_id INT NOT NULL,
    section_id INT NOT NULL,
    parent_id INT NOT NULL,

    roll_no VARCHAR(20),
    status ENUM('Active','Inactive') DEFAULT 'Active',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (class_id) REFERENCES tbl_classes(class_id),
    FOREIGN KEY (section_id) REFERENCES tbl_sections(section_id),
    FOREIGN KEY (parent_id) REFERENCES tbl_parents(parent_id)
);

-- =========================================
-- TABLE: TEACHER ASSIGNMENTS
-- =========================================
CREATE TABLE tbl_teacher_assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT NOT NULL,
    class_id INT NOT NULL,
    section_id INT NOT NULL,
    subject_id INT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (teacher_id) REFERENCES tbl_teachers(teacher_id),
    FOREIGN KEY (class_id) REFERENCES tbl_classes(class_id),
    FOREIGN KEY (section_id) REFERENCES tbl_sections(section_id),
    FOREIGN KEY (subject_id) REFERENCES tbl_subjects(subject_id)
);

-- =========================================
-- TABLE: ATTENDANCE
-- =========================================
CREATE TABLE tbl_attendance (
    attendance_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status ENUM('Present','Absent','Leave') NOT NULL,
    remarks VARCHAR(255),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id) REFERENCES tbl_students(student_id),
    UNIQUE(student_id, attendance_date)
);

-- =========================================
-- TABLE: FEE STRUCTURE
-- =========================================
CREATE TABLE tbl_fee_structures (
    fee_structure_id INT AUTO_INCREMENT PRIMARY KEY,
    class_id INT NOT NULL,
    academic_year VARCHAR(20) NOT NULL,

    tuition_fee DECIMAL(10,2) DEFAULT 0,
    activity_fee DECIMAL(10,2) DEFAULT 0,
    transport_fee DECIMAL(10,2) DEFAULT 0,
    other_fee DECIMAL(10,2) DEFAULT 0,

    total_fee DECIMAL(10,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (class_id) REFERENCES tbl_classes(class_id)
);

-- =========================================
-- TABLE: STUDENT FEES
-- =========================================
CREATE TABLE tbl_student_fees (
    student_fee_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    fee_structure_id INT NOT NULL,

    total_amount DECIMAL(10,2),
    paid_amount DECIMAL(10,2) DEFAULT 0,
    pending_amount DECIMAL(10,2) DEFAULT 0,

    status ENUM('Paid','Pending','Partial') DEFAULT 'Pending',
    last_payment_date DATE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id) REFERENCES tbl_students(student_id),
    FOREIGN KEY (fee_structure_id) REFERENCES tbl_fee_structures(fee_structure_id)
);

-- =========================================
-- TABLE: FEE PAYMENTS
-- =========================================
CREATE TABLE tbl_fee_payments (
    payment_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    student_fee_id BIGINT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_date DATE NOT NULL,

    payment_method ENUM('Cash','UPI','Card','Bank'),
    transaction_ref VARCHAR(100),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_fee_id) REFERENCES tbl_student_fees(student_fee_id)
);

-- =========================================
-- TABLE: HOMEWORK
-- =========================================
CREATE TABLE homework (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    class_id INT NOT NULL,
    subject_id INT NULL,
    teacher_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    due_date DATE,
    status ENUM('Active','Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES tbl_classes(class_id),
    FOREIGN KEY (subject_id) REFERENCES tbl_subjects(subject_id) ON DELETE SET NULL,
    FOREIGN KEY (teacher_id) REFERENCES tbl_teachers(teacher_id)
);

-- =========================================
-- TABLE: HOMEWORK IMAGES
-- =========================================
CREATE TABLE homework_images (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    homework_id BIGINT NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (homework_id) REFERENCES homework(id) ON DELETE CASCADE
);

-- =========================================
-- TABLE: HOMEWORK STUDENT
-- =========================================
CREATE TABLE homework_student (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    homework_id BIGINT NOT NULL,
    student_id INT NOT NULL,
    status ENUM('Pending','Completed') DEFAULT 'Pending',
    completed_by ENUM('Student','Parent') NULL,
    completed_at DATETIME NULL,
    student_comment TEXT NULL,
    parent_comment TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (homework_id) REFERENCES homework(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES tbl_students(student_id) ON DELETE CASCADE,
    UNIQUE(homework_id, student_id)
);

-- =========================================
-- TABLE: NOTIFICATIONS
-- =========================================
CREATE TABLE notifications (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_type ENUM('Teacher','Student','Parent') NOT NULL,
    user_id INT NOT NULL,
    homework_id BIGINT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (homework_id) REFERENCES homework(id) ON DELETE CASCADE
);

-- =========================================
-- TABLE: USERS (LOGIN SYSTEM)
-- =========================================
CREATE TABLE tbl_users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,

    role ENUM('Admin','Teacher','Parent','Student') NOT NULL,
    reference_id INT NULL,

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);