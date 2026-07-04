from django.db import models


class TblClass(models.Model):
    class_id = models.AutoField(primary_key=True)
    class_name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "tbl_classes"
        ordering = ["class_name"]

    def __str__(self):
        return self.class_name


class TblSection(models.Model):
    section_id = models.AutoField(primary_key=True)
    class_field = models.ForeignKey(
        TblClass,
        on_delete=models.CASCADE,
        db_column="class_id",
        related_name="sections",
    )
    section_name = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "tbl_sections"
        ordering = ["class_field__class_name", "section_name"]
        unique_together = [("class_field", "section_name")]

    def __str__(self):
        return f"{self.class_field.class_name} – {self.section_name}"


class TblSubject(models.Model):
    subject_id = models.AutoField(primary_key=True)
    subject_name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "tbl_subjects"
        ordering = ["subject_name"]

    def __str__(self):
        return self.subject_name


class TblParent(models.Model):
    parent_id = models.AutoField(primary_key=True)
    father_name = models.CharField(max_length=150, blank=True, null=True)
    mother_name = models.CharField(max_length=150, blank=True, null=True)
    mobile = models.CharField(max_length=20)
    email = models.CharField(max_length=150, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "tbl_parents"
        ordering = ["father_name", "mother_name"]

    def __str__(self):
        return f"{self.father_name or ''} / {self.mother_name or ''} ({self.mobile})".strip()


class TblTeacher(models.Model):
    teacher_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=150, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "tbl_teachers"
        ordering = ["name"]

    def __str__(self):
        return self.name


class TblStudent(models.Model):
    student_id = models.AutoField(primary_key=True)
    admission_no = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ], blank=True, null=True)
    class_field = models.ForeignKey(
        TblClass,
        on_delete=models.CASCADE,
        db_column="class_id",
        related_name="students",
    )
    section_field = models.ForeignKey(
        TblSection,
        on_delete=models.CASCADE,
        db_column="section_id",
        related_name="students",
    )
    parent_field = models.ForeignKey(
        TblParent,
        on_delete=models.CASCADE,
        db_column="parent_id",
        related_name="children",
    )
    roll_no = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=10, choices=[
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ], default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "tbl_students"
        ordering = ["class_field", "section_field", "roll_no"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}" if self.first_name else self.admission_no


class TblTeacherAssignment(models.Model):
    assignment_id = models.AutoField(primary_key=True)
    teacher_field = models.ForeignKey(
        TblTeacher,
        on_delete=models.CASCADE,
        db_column="teacher_id",
        related_name="assignments",
    )
    class_field = models.ForeignKey(
        TblClass,
        on_delete=models.CASCADE,
        db_column="class_id",
        related_name="teacher_assignments",
    )
    section_field = models.ForeignKey(
        TblSection,
        on_delete=models.CASCADE,
        db_column="section_id",
        related_name="teacher_assignments",
    )
    subject_field = models.ForeignKey(
        TblSubject,
        on_delete=models.CASCADE,
        db_column="subject_id",
        related_name="teacher_assignments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "tbl_teacher_assignments"
        ordering = ["teacher_field", "class_field", "section_field", "subject_field"]
        unique_together = [("teacher_field", "class_field", "section_field", "subject_field")]

    def __str__(self):
        return f"{self.teacher_field.name} – {self.class_field.class_name} {self.section_field.section_name} ({self.subject_field.subject_name})"


class TblAttendance(models.Model):
    STATUS_CHOICES = [
        ("Present", "Present"),
        ("Absent", "Absent"),
        ("Leave", "Leave"),
    ]

    attendance_id = models.BigAutoField(primary_key=True)
    student_field = models.ForeignKey(
        TblStudent,
        on_delete=models.CASCADE,
        db_column="student_id",
        related_name="attendances",
    )
    attendance_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    remarks = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "tbl_attendance"
        ordering = ["-attendance_date", "student_field"]
        unique_together = [("student_field", "attendance_date")]

    def __str__(self):
        return f"{self.student_field} - {self.attendance_date} ({self.status})"


class TblFeeStructure(models.Model):
    fee_structure_id = models.AutoField(primary_key=True)
    class_field = models.ForeignKey(
        TblClass,
        on_delete=models.CASCADE,
        db_column="class_id",
        related_name="fee_structures",
    )
    academic_year = models.CharField(max_length=20)
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    activity_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_fee = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "tbl_fee_structures"
        ordering = ["-academic_year", "class_field"]

    def __str__(self):
        return f"{self.class_field.class_name} – {self.academic_year} (₹{self.total_fee})"


class TblStudentFee(models.Model):
    STATUS_CHOICES = [
        ("Paid", "Paid"),
        ("Pending", "Pending"),
        ("Partial", "Partial"),
    ]
    
    student_fee_id = models.BigAutoField(primary_key=True)
    student_field = models.ForeignKey(
        TblStudent,
        on_delete=models.CASCADE,
        db_column="student_id",
        related_name="fees",
    )
    fee_structure_field = models.ForeignKey(
        TblFeeStructure,
        on_delete=models.CASCADE,
        db_column="fee_structure_id",
        related_name="student_fees",
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pending_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Pending")
    last_payment_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "tbl_student_fees"
        ordering = ["status", "student_field"]

    def __str__(self):
        return f"{self.student_field} – {self.fee_structure_field.academic_year} ({self.status})"


class TblFeePayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ("Cash", "Cash"),
        ("UPI", "UPI"),
        ("Card", "Card"),
        ("Bank", "Bank"),
    ]
    
    payment_id = models.BigAutoField(primary_key=True)
    student_fee_field = models.ForeignKey(
        TblStudentFee,
        on_delete=models.CASCADE,
        db_column="student_fee_id",
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    transaction_ref = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "tbl_fee_payments"
        ordering = ["-payment_date"]

    def __str__(self):
        return f"₹{self.amount} – {self.student_fee_field.student_field.first_name} ({self.payment_date})"


class TblHomework(models.Model):
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Inactive", "Inactive"),
    ]

    homework_id = models.BigAutoField(primary_key=True, db_column="id")
    class_field = models.ForeignKey(
        TblClass,
        on_delete=models.CASCADE,
        db_column="class_id",
        related_name="homework_items",
    )
    subject_field = models.ForeignKey(
        TblSubject,
        on_delete=models.SET_NULL,
        db_column="subject_id",
        related_name="homework_items",
        blank=True,
        null=True,
    )
    teacher_field = models.ForeignKey(
        TblTeacher,
        on_delete=models.CASCADE,
        db_column="teacher_id",
        related_name="homework_items",
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "homework"
        ordering = ["-created_at", "title"]

    def __str__(self):
        return self.title


class TblHomeworkImage(models.Model):
    homework_image_id = models.BigAutoField(primary_key=True, db_column="id")
    homework_field = models.ForeignKey(
        TblHomework,
        on_delete=models.CASCADE,
        db_column="homework_id",
        related_name="images",
    )
    image_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "homework_images"
        ordering = ["homework_field", "homework_image_id"]

    def __str__(self):
        return self.image_path


class TblHomeworkStudent(models.Model):
    COMPLETED_BY_CHOICES = [
        ("Student", "Student"),
        ("Parent", "Parent"),
    ]
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Completed", "Completed"),
    ]

    homework_student_id = models.BigAutoField(primary_key=True, db_column="id")
    homework_field = models.ForeignKey(
        TblHomework,
        on_delete=models.CASCADE,
        db_column="homework_id",
        related_name="student_records",
    )
    student_field = models.ForeignKey(
        TblStudent,
        on_delete=models.CASCADE,
        db_column="student_id",
        related_name="homework_records",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Pending")
    completed_by = models.CharField(max_length=10, choices=COMPLETED_BY_CHOICES, blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    student_comment = models.TextField(blank=True, null=True)
    parent_comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "homework_student"
        ordering = ["status", "student_field"]
        unique_together = [("homework_field", "student_field")]

    def __str__(self):
        return f"{self.homework_field.title} - {self.student_field} ({self.status})"


class TblNotification(models.Model):
    USER_TYPE_CHOICES = [
        ("Teacher", "Teacher"),
        ("Student", "Student"),
        ("Parent", "Parent"),
    ]

    notification_id = models.BigAutoField(primary_key=True, db_column="id")
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    user_id = models.IntegerField()
    homework_field = models.ForeignKey(
        TblHomework,
        on_delete=models.CASCADE,
        db_column="homework_id",
        related_name="notifications",
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_type} - {self.title}"
class TblUser(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=20)
    reference_id = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "tbl_users"
