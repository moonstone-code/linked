USE db_linkEd;

-- =========================================================
-- RESET (safe re-run)
-- =========================================================
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE notifications;
TRUNCATE TABLE homework_student;
TRUNCATE TABLE homework_images;
TRUNCATE TABLE homework;
TRUNCATE TABLE tbl_fee_payments;
TRUNCATE TABLE tbl_student_fees;
TRUNCATE TABLE tbl_fee_structures;
TRUNCATE TABLE tbl_attendance;
TRUNCATE TABLE tbl_teacher_assignments;
TRUNCATE TABLE tbl_users;
TRUNCATE TABLE tbl_students;
TRUNCATE TABLE tbl_teachers;
TRUNCATE TABLE tbl_parents;
SET FOREIGN_KEY_CHECKS = 1;

-- =========================================================
-- TEACHERS (2)
-- =========================================================
INSERT INTO tbl_teachers (name, mobile, email) VALUES
('Mrs. Anjali Sharma', '9800000001', 'teacher1@school.edu'),
('Mr. Rakesh Mehta',  '9800000002', 'teacher2@school.edu');

-- =========================================================
-- PARENTS (2)
--   Parent 1  →  2 children  (ADM001, ADM002)
--   Parent 2  →  3 children  (ADM003, ADM004, ADM005)
-- =========================================================
INSERT INTO tbl_parents (father_name, mother_name, mobile, email, address) VALUES
('Rajesh Sharma',  'Sunita Sharma',  '9876500001', 'parent1@gmail.com', 'Mumbai'),
('Amit Patel',     'Neha Patel',     '9876500002', 'parent2@gmail.com', 'Pune');

-- =========================================================
-- STUDENTS (5)
--   Sections (from master data 02_master_data.sql):
--     Class 1 → section_id 1 (A), 2 (B)
--     Class 2 → section_id 3 (A), 4 (B)
--     Class 3 → section_id 5 (A), 6 (B)
--     Class 4 → section_id 7 (A), 8 (B)
--     Class 5 → section_id 9 (A), 10 (B)
-- =========================================================
INSERT INTO tbl_students
  (admission_no, first_name, last_name, dob, gender, class_id, section_id, parent_id, roll_no)
VALUES
  ('ADM001', 'Aarav',   'Sharma', '2018-06-15', 'Male',   1, 1,  1, '1'),  -- Parent 1, Teacher 1
  ('ADM002', 'Priya',   'Sharma', '2017-03-22', 'Female', 2, 3,  1, '1'),  -- Parent 1, Teacher 1 (sibling)
  ('ADM003', 'Arjun',   'Patel',  '2016-09-10', 'Male',   3, 5,  2, '1'),  -- Parent 2, Teacher 1
  ('ADM004', 'Anaya',   'Patel',  '2015-12-05', 'Female', 4, 7,  2, '1'),  -- Parent 2, Teacher 2 (sibling)
  ('ADM005', 'Vivaan',  'Patel',  '2014-07-30', 'Male',   5, 9,  2, '1');  -- Parent 2, Teacher 2 (sibling)

-- =========================================================
-- TEACHER ASSIGNMENTS
--   Teacher 1 → Classes 1, 2, 3  (Section A, Mathematics)
--   Teacher 2 → Classes 4, 5     (Section A, Mathematics)
-- =========================================================
INSERT INTO tbl_teacher_assignments (teacher_id, class_id, section_id, subject_id) VALUES
(1, 1, 1, 1),
(1, 2, 3, 1),
(1, 3, 5, 1),
(2, 4, 7, 1),
(2, 5, 9, 1);

-- =========================================================
-- FEE STRUCTURES (one per class the students are enrolled in)
-- =========================================================
INSERT INTO tbl_fee_structures
  (class_id, academic_year, tuition_fee, activity_fee, transport_fee, other_fee, total_fee)
VALUES
  (1, '2025-26', 50000, 5000, 8000, 2000, 65000),
  (2, '2025-26', 52000, 5000, 8000, 2000, 67000),
  (3, '2025-26', 54000, 5000, 8000, 2000, 69000),
  (4, '2025-26', 56000, 5000, 8000, 2000, 71000),
  (5, '2025-26', 58000, 5000, 8000, 2000, 73000);

-- =========================================================
-- STUDENT FEES (one record per student)
--   Student 1 → Paid     | Student 2 → Partial
--   Student 3 → Pending  | Student 4 → Paid
--   Student 5 → Partial
-- =========================================================
INSERT INTO tbl_student_fees
  (student_id, fee_structure_id, total_amount, paid_amount, pending_amount, status, last_payment_date)
VALUES
  (1, 1, 65000, 65000,     0, 'Paid',    '2025-04-10'),
  (2, 2, 67000, 33500, 33500, 'Partial', '2025-05-15'),
  (3, 3, 69000,     0, 69000, 'Pending',  NULL),
  (4, 4, 71000, 71000,     0, 'Paid',    '2025-04-20'),
  (5, 5, 73000, 36500, 36500, 'Partial', '2025-06-01');

-- =========================================================
-- FEE PAYMENTS (Paid + Partial students)
-- =========================================================
INSERT INTO tbl_fee_payments
  (student_fee_id, amount, payment_date, payment_method, transaction_ref)
VALUES
  (1, 65000, '2025-04-10', 'UPI',  'TXN0001'),
  (2, 33500, '2025-05-15', 'Cash', 'TXN0002'),
  (4, 71000, '2025-04-20', 'Card', 'TXN0003'),
  (5, 36500, '2025-06-01', 'UPI',  'TXN0004');

-- =========================================================
-- USERS  (1 Admin + 2 Teachers + 2 Parents + 5 Students)
-- =========================================================
-- Admin
INSERT INTO tbl_users (username, password_hash, role, reference_id) VALUES
('admin', 'Admin@123', 'Admin', NULL);

-- Teachers
INSERT INTO tbl_users (username, password_hash, role, reference_id) VALUES
('t1', 'Teacher@123', 'Teacher', 1),
('t2', 'Teacher@123', 'Teacher', 2);

-- Parents
INSERT INTO tbl_users (username, password_hash, role, reference_id) VALUES
('p1', 'Parent@123', 'Parent', 1),
('p2', 'Parent@123', 'Parent', 2);

-- Students
INSERT INTO tbl_users (username, password_hash, role, reference_id) VALUES
('s1', 'Student@123', 'Student', 1),
('s2', 'Student@123', 'Student', 2),
('s3', 'Student@123', 'Student', 3),
('s4', 'Student@123', 'Student', 4),
('s5', 'Student@123', 'Student', 5);
