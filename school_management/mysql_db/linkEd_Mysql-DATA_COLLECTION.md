Create File

The file creation tool is currently disabled. Copy the content below and save it as `DATA_COLLECTION.md` in `linkEd_Mysql/`:

````markdown
# LinkEd — School Data Collection Form

Please fill in all the sections below and return this document.  
Fields marked **\*** are mandatory.

---

## Section 1 — School Information

| Field | Your Answer |
|-------|-------------|
| School Name * | |
| School Address * | |
| Contact Number * | |
| Email Address * | |
| Academic Year * (e.g. 2024-2025) | |
| Principal / Admin Name * | |

---

## Section 2 — Classes & Sections

| Class Name * | Sections * (comma separated) |
|---|---|
| e.g. Class 1 | A, B |
| e.g. Class 2 | A, B, C |
| | |
| | |

---

## Section 3 — Subjects

| # | Subject Name * |
|---|---|
| 1 | |
| 2 | |
| 3 | |

---

## Section 4 — Teachers

| # | Full Name * | Mobile * | Email | Assigned Class * | Assigned Section * | Subject Taught * |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |

*(If a teacher teaches multiple classes, add one row per class/section/subject)*

---

## Section 5 — Parents

| # | Father's Name | Mother's Name | Mobile * | Email | Address |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |

---

## Section 6 — Students

| # | Admission No * | First Name * | Last Name * | DOB (DD-MM-YYYY) | Gender | Class * | Section * | Roll No | Parent Name * | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | | | Active |
| 2 | | | | | | | | | | Active |

---

## Section 7 — Fee Structure (amounts in ₹)

| Class * | Academic Year * | Tuition Fee * | Activity Fee | Transport Fee | Other Fee |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |

> Total fee is calculated automatically as the sum of all components.

---

## Section 8 — Portal Login Credentials

### Admin Account

| Username * | Password * |
|---|---|
| | |

### Teacher Logins

| # | Teacher Name * | Username * | Initial Password * |
|---|---|---|---|
| 1 | | | |

### Parent Logins

| # | Parent Name * | Username * | Initial Password * |
|---|---|---|---|
| 1 | | | |

### Student Logins

| # | Student Name * | Username * | Initial Password * |
|---|---|---|---|
| 1 | | | |

---

## Submission Checklist

- [ ] All classes and sections listed
- [ ] All subjects listed
- [ ] Every teacher has a class/section/subject assignment
- [ ] Every student has a matching parent in Section 5
- [ ] Fee structure filled for every class
- [ ] All usernames are unique
- [ ] All mandatory `*` fields are filled

---
*Return this completed document to your LinkEd setup team.*
````
 