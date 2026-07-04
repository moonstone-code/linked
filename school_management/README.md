# LinkEd — School Management System

A full-stack web application built with **Django 5** and **MySQL** for managing school operations including students, teachers, parents, fee tracking, and user accounts.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Folder Structure](#folder-structure)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Running the Project](#running-the-project)
- [Default Login Credentials](#default-login-credentials)
- [URL Reference](#url-reference)

---

## Features

| Module | Description |
|--------|-------------|
| **Admin Dashboard** | Live KPI cards, fee collection progress bars, recent payments, user-by-role breakdown |
| **Student Management** | Full CRUD — admission no, class, section, parent linkage, status |
| **Teacher Management** | Full CRUD — name, mobile, email |
| **Parent Management** | Full CRUD — father/mother name, mobile, address |
| **Class Management** | Full CRUD — class names (Class 1–10) |
| **Section Management** | Full CRUD — sections per class (A/B/C) |
| **Subject Management** | Full CRUD — subject catalog |
| **Teacher Assignment** | Assign teacher → class + section + subject |
| **Fee Structure** | Define fees per class per academic year |
| **Student Fees** | Track total / paid / pending amounts, payment method, file upload |
| **Homework Management** | Teacher publish flow, multiple images, student/parent completion tracking, notifications |
| **User Management** | Admin-only CRUD for `tbl_users` with role & password management |
| **Role-based Auth** | Four roles: Admin · Teacher · Parent · Student — each with own dashboard & sidebar |

---

## Tech Stack

- **Backend:** Python 3.10+, Django 5
- **Database:** MySQL 8 (via `mysqlclient` / `PyMySQL`)
- **Frontend:** Bootstrap 5.3, Bootstrap Icons 1.11
- **Auth:** Custom `TblUsersBackend` authenticating against `tbl_users`
- **Config:** `python-dotenv` for environment variable management

---

## Folder Structure

```
linkEd_Mysql/
│
├── README.md                         ← This file
│
├── mysql_db/                         ← Raw SQL scripts
│   ├── 01_schema.sql                 ← Create all tables
│   ├── 02_master_data.sql            ← Seed master/lookup data
│   ├── 03_dummy_data.sql             ← Sample records (students, fees, users)
│   ├── ER-Diagram-Mermaid.txt        ← ER diagram in Mermaid syntax
│   └── ER-Diagram.png                ← ER diagram image
│
└── school_management/                ← Django project root
    │
    ├── manage.py
    ├── requirements.txt
    ├── .env                          ← Create this file (see below)
    │
    ├── school_management/            ← Django settings package
    │   ├── settings.py
    │   ├── urls.py
    │   ├── wsgi.py
    │   └── asgi.py
    │
    ├── accounts/                     ← Main application
    │   ├── models.py                 ← All ORM models (managed=False, maps to tbl_*)
    │   ├── views.py                  ← All CRUD views + dashboards
    │   ├── forms.py                  ← ModelForms with validation
    │   ├── urls.py                   ← All URL patterns
    │   ├── auth_backends.py          ← Custom auth against tbl_users
    │   ├── context_processors.py     ← Role-based sidebar menu
    │   ├── decorators.py             ← @role_required decorator
    │   └── templates/
    │       └── accounts/
    │           ├── login.html
    │           ├── admin_dashboard.html
    │           ├── teacher_dashboard.html
    │           ├── parent_dashboard.html
    │           ├── student_dashboard.html
    │           ├── class_master.html
    │           ├── section_master.html
    │           ├── subject_master.html
    │           ├── parent_master.html
    │           ├── teacher_master.html
    │           ├── teacher_assignment_master.html
    │           ├── student_master.html
    │           ├── fee_structure_master.html
    │           ├── student_fee_master.html
    │           ├── fee_payment_master.html
    │           ├── teacher_homework_dashboard.html
    │           ├── teacher_homework_list.html
    │           ├── teacher_homework_form.html
    │           ├── teacher_homework_report.html
    │           ├── student_homework_list.html
    │           ├── student_homework_detail.html
    │           └── user_master.html
    │
    ├── templates/
    │   ├── base.html                 ← Shared layout (navbar + sidebar + content block)
    │   └── partials/                 ← Reusable template partials
    │
    └── media/
        └── fee_payment_refs/         ← Uploaded payment reference files
```

---

## Prerequisites

Make sure the following are installed on your machine:

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| MySQL Server | 8.0+ | [mysql.com](https://dev.mysql.com/downloads/) |
| pip | latest | Comes with Python |
| virtualenv (optional) | any | Recommended |

> **Windows users:** If `mysqlclient` installation fails, install the MySQL C connector first or use PyMySQL as the fallback (already included in requirements).

---

## Installation & Setup

### 1. Clone or Download the Repository

```bash
git clone <repository-url>
cd linkEd_Mysql
```

### 2. Create and Activate a Virtual Environment

```bash
# Create
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
cd school_management
pip install -r requirements.txt
```

The `requirements.txt` installs:

```
Django>=5.0,<6.0
mysqlclient>=2.2.0
PyMySQL>=1.1.0
python-dotenv>=1.0.1
```

> If `mysqlclient` fails to install on Windows, run:
> ```bash
> pip install PyMySQL
> ```
> Then add the following at the top of `school_management/settings.py`:
> ```python
> import pymysql
> pymysql.install_as_MySQLdb()
> ```

---

## Environment Variables

Create a `.env` file inside `school_management/` (alongside `manage.py`):

```
# school_management/.env

DJANGO_SECRET_KEY=your-very-secret-key-here
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=db_linkEd
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

> **Never commit `.env` to version control.** Add it to `.gitignore`.

---

## Database Setup

### 1. Create the Database and Tables

Open your MySQL client and run the SQL scripts in order:

```sql
-- Step 1: Create schema (tables)
SOURCE /path/to/linkEd_Mysql/mysql_db/01_schema.sql;

-- Step 2: Insert master/lookup data
SOURCE /path/to/linkEd_Mysql/mysql_db/02_master_data.sql;

-- Step 3: (Optional) Insert sample dummy data
SOURCE /path/to/linkEd_Mysql/mysql_db/03_dummy_data.sql;
```

Or using the MySQL CLI directly:

```bash
mysql -u root -p < mysql_db/01_schema.sql
mysql -u root -p < mysql_db/02_master_data.sql
mysql -u root -p < mysql_db/03_dummy_data.sql   # optional
```

### 2. Run Django Migrations (Session + Auth tables only)

> **Note:** All `tbl_*` tables are `managed = False` in Django — they are managed entirely by the SQL scripts above. Django migrations only create internal framework tables (sessions, auth, etc.).

```bash
cd school_management
python manage.py migrate
```

### 3. Create a Django Superuser (optional)

```bash
python manage.py createsuperuser
```

---

## Running the Project

From the repository root:

```bash
cd school_management
python manage.py runserver 127.0.0.1:8000
```

If you are already inside the `school_management/` folder, run:

```bash
python manage.py runserver 127.0.0.1:8000
```

The app will be available at: **http://127.0.0.1:8000/**

To bind to all interfaces (e.g., for LAN access):

```bash
python manage.py runserver 0.0.0.0:8000
```

---

## Default Login Credentials

> These are loaded by `03_dummy_data.sql`. Passwords are stored as plain text in the dummy data and validated by `TblUsersBackend`.

| Username | Password | Role |
|----------|----------|------|
| `admin` | `hash123` | Admin |
| `t1` – `t10` | `hash` | Teacher |
| `p1` – `p10` | `hash` | Parent |
| `s1` – `s10` | `hash` | Student |

> In production, use hashed passwords (Django's `make_password`). The custom auth backend supports both plain text (dev) and `pbkdf2_/bcrypt/argon2` hashed passwords.

---

## URL Reference

| URL | Name | Role | Description |
|-----|------|------|-------------|
| `/` or `/login/` | `login` | All | Login page |
| `/logout/` | `logout` | All | POST to log out |
| `/admin/dashboard/` | `admin_dashboard` | Admin | Progress status dashboard |
| `/teacher/dashboard/` | `teacher_dashboard` | Teacher | Teacher home |
| `/teacher/homework/` | `teacher_homework_dashboard` | Teacher | Homework dashboard |
| `/teacher/homework/list/` | `teacher_homework_list` | Teacher | Homework list and filters |
| `/parent/dashboard/` | `parent_dashboard` | Parent | Parent home |
| `/parent/homework/` | `parent_homework_list` | Parent | Child homework list |
| `/student/dashboard/` | `student_dashboard` | Student | Student home |
| `/student/homework/` | `student_homework_list` | Student | Own homework list |
| `/admin/students/` | `student_list` | Admin | Student CRUD |
| `/admin/teachers/` | `teacher_list` | Admin | Teacher CRUD |
| `/admin/parents/` | `parent_list` | Admin | Parent CRUD |
| `/admin/classes/` | `class_list` | Admin | Class CRUD |
| `/admin/sections/` | `section_list` | Admin | Section CRUD |
| `/admin/subjects/` | `subject_list` | Admin | Subject CRUD |
| `/admin/assignments/` | `teacher_assignment_list` | Admin | Teacher Assignments CRUD |
| `/admin/fee-structures/` | `fee_structure_list` | Admin | Fee Structure CRUD |
| `/admin/student-fees/` | `student_fee_list` | Admin | Student Fee CRUD |
| `/admin/users/` | `user_list` | Admin | User Management CRUD |

---

## ER Diagram

The full entity-relationship diagram is available at:

- **Image:** `mysql_db/ER-Diagram.png`
- **Mermaid source:** `mysql_db/ER-Diagram-Mermaid.txt`
