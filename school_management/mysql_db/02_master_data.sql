USE db_linkEd;

-- =========================================
-- CLASSES (1 to 10)
-- =========================================
INSERT INTO tbl_classes (class_name) VALUES
('Class 1'),
('Class 2'),
('Class 3'),
('Class 4'),
('Class 5'),
('Class 6'),
('Class 7'),
('Class 8'),
('Class 9'),
('Class 10');

-- =========================================
-- SECTIONS (A, B for each class)
-- =========================================
INSERT INTO tbl_sections (class_id, section_name) VALUES
(1,'A'),(1,'B'),
(2,'A'),(2,'B'),
(3,'A'),(3,'B'),
(4,'A'),(4,'B'),
(5,'A'),(5,'B'),
(6,'A'),(6,'B'),
(7,'A'),(7,'B'),
(8,'A'),(8,'B'),
(9,'A'),(9,'B'),
(10,'A'),(10,'B');

-- =========================================
-- SUBJECTS
-- =========================================
INSERT INTO tbl_subjects (subject_name) VALUES
('Mathematics'),
('Science'),
('English'),
('Hindi'),
('Social Studies'),
('Computer'),
('General Knowledge'),
('Drawing');