from django import forms
from decimal import Decimal
from django.contrib.auth.hashers import make_password
from django.db.models import Sum
from django.utils import timezone

from .models import (
    TblAttendance,
    TblClass,
    TblFeePayment,
    TblFeeStructure,
    TblHomework,
    TblHomeworkStudent,
    TblParent,
    TblNotification,
    TblSection,
    TblStudent,
    TblStudentFee,
    TblSubject,
    TblTeacher,
    TblTeacherAssignment,
    TblUser,
)


class UserForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Enter password"}
        ),
        help_text="Required while creating a user.",
    )

    class Meta:
        model = TblUser
        fields = ["username", "password", "role", "reference_id", "is_active"]
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Unique username"}
            ),
            "role": forms.Select(attrs={"class": "form-select"}),
            "reference_id": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "e.g. Teacher/Parent/Student ID"}
            ),
            "is_active": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "username": "Username",
            "password": "Password",
            "role": "Role",
            "reference_id": "Reference ID",
            "is_active": "Active",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].widget.choices = [
            ("Admin", "Admin"),
            ("Teacher", "Teacher"),
            ("Parent", "Parent"),
            ("Student", "Student"),
        ]
        self.fields["is_active"].widget.choices = [
            (True, "Yes"),
            (False, "No"),
        ]

        if self.instance and self.instance.pk:
            self.fields["password"].help_text = "Leave blank to keep current password."

    def clean_username(self):
        value = (self.cleaned_data.get("username") or "").strip()
        if not value:
            raise forms.ValidationError("Username is required.")

        qs = TblUser.objects.filter(username__iexact=value)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This username is already in use.")
        return value

    def clean_password(self):
        value = self.cleaned_data.get("password") or ""
        if not self.instance.pk and not value:
            raise forms.ValidationError("Password is required while creating a user.")
        return value

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        reference_id = cleaned_data.get("reference_id")

        if role == "Admin":
            cleaned_data["reference_id"] = None
        elif role in {"Teacher", "Parent", "Student"} and not reference_id:
            self.add_error("reference_id", "Reference ID is required for this role.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw_password = self.cleaned_data.get("password")
        if raw_password:
            instance.password_hash = make_password(raw_password)

        if commit:
            instance.save()
        return instance


class ClassForm(forms.ModelForm):
    class Meta:
        model = TblClass
        fields = ["class_name"]
        widgets = {
            "class_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Class 1",
                    "autofocus": True,
                }
            )
        }
        labels = {"class_name": "Class Name"}

    def clean_class_name(self):
        value = self.cleaned_data.get("class_name", "").strip()
        if not value:
            raise forms.ValidationError("Class name is required.")
        qs = TblClass.objects.filter(class_name__iexact=value)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A class with this name already exists.")
        return value


class SectionForm(forms.ModelForm):
    class Meta:
        model = TblSection
        fields = ["class_field", "section_name"]
        widgets = {
            "class_field": forms.Select(attrs={"class": "form-select"}),
            "section_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. A"}
            ),
        }
        labels = {
            "class_field": "Class",
            "section_name": "Section Name",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_field"].queryset = TblClass.objects.all()
        self.fields["class_field"].empty_label = "— Select Class —"

    def clean(self):
        cleaned_data = super().clean()
        class_field = cleaned_data.get("class_field")
        section_name = cleaned_data.get("section_name", "").strip().upper()
        if class_field and section_name:
            qs = TblSection.objects.filter(
                class_field=class_field,
                section_name__iexact=section_name,
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f"Section '{section_name}' already exists for {class_field.class_name}."
                )
        if section_name:
            cleaned_data["section_name"] = section_name
        return cleaned_data


class SubjectForm(forms.ModelForm):
    class Meta:
        model = TblSubject
        fields = ["subject_name"]
        widgets = {
            "subject_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Mathematics",
                    "autofocus": True,
                }
            )
        }
        labels = {"subject_name": "Subject Name"}

    def clean_subject_name(self):
        value = self.cleaned_data.get("subject_name", "").strip()
        if not value:
            raise forms.ValidationError("Subject name is required.")
        qs = TblSubject.objects.filter(subject_name__iexact=value)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A subject with this name already exists.")
        return value


class ParentForm(forms.ModelForm):
    class Meta:
        model = TblParent
        fields = ["father_name", "mother_name", "mobile", "email", "address"]
        widgets = {
            "father_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Father's name"}),
            "mother_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Mother's name"}),
            "mobile": forms.TextInput(attrs={"class": "form-control", "placeholder": "Mobile number", "required": True}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email address"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Address"}),
        }
        labels = {
            "father_name": "Father Name",
            "mother_name": "Mother Name",
            "mobile": "Mobile Number",
            "email": "Email",
            "address": "Address",
        }

    def clean_mobile(self):
        value = self.cleaned_data.get("mobile", "").strip()
        if not value:
            raise forms.ValidationError("Mobile number is required.")
        return value


class ParentProfileForm(forms.ModelForm):
    class Meta:
        model = TblParent
        fields = ["father_name", "mother_name", "mobile", "email", "address"]
        widgets = {
            "father_name": forms.TextInput(attrs={"class": "form-control"}),
            "mother_name": forms.TextInput(attrs={"class": "form-control"}),
            "mobile": forms.TextInput(attrs={"class": "form-control", "required": True}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        labels = {
            "father_name": "Father Name",
            "mother_name": "Mother Name",
            "mobile": "Mobile Number",
            "email": "Email",
            "address": "Address",
        }

    def clean_mobile(self):
        value = (self.cleaned_data.get("mobile") or "").strip()
        if not value:
            raise forms.ValidationError("Mobile number is required.")
        return value


class TeacherForm(forms.ModelForm):
    class Meta:
        model = TblTeacher
        fields = ["name", "mobile", "email"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full name", "required": True}),
            "mobile": forms.TextInput(attrs={"class": "form-control", "placeholder": "Mobile number"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email address"}),
        }
        labels = {
            "name": "Name",
            "mobile": "Mobile Number",
            "email": "Email",
        }

    def clean_name(self):
        value = self.cleaned_data.get("name", "").strip()
        if not value:
            raise forms.ValidationError("Name is required.")
        return value

    def clean_email(self):
        value = self.cleaned_data.get("email", "").strip()
        if value:
            qs = TblTeacher.objects.filter(email__iexact=value)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("A teacher with this email already exists.")
        return value


class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = TblTeacher
        fields = ["name", "mobile", "email"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "required": True}),
            "mobile": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }
        labels = {
            "name": "Full Name",
            "mobile": "Mobile Number",
            "email": "Email Address",
        }

    def clean_name(self):
        value = (self.cleaned_data.get("name") or "").strip()
        if not value:
            raise forms.ValidationError("Name is required.")
        return value

    def clean_email(self):
        value = (self.cleaned_data.get("email") or "").strip()
        if value:
            qs = TblTeacher.objects.filter(email__iexact=value)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Another teacher is already using this email.")
        return value


class AttendanceMarkForm(forms.Form):
    assignment_id = forms.IntegerField(widget=forms.HiddenInput())
    attendance_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )

    def clean_attendance_date(self):
        value = self.cleaned_data.get("attendance_date")
        if value and value > timezone.localdate():
            raise forms.ValidationError("Attendance date cannot be in the future.")
        return value


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"class": "form-control", "multiple": True}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if data in self.empty_values:
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        cleaned_files = []
        base_clean = super(MultipleFileField, self).clean
        for item in data:
            cleaned_files.append(base_clean(item, initial))
        return cleaned_files


class HomeworkForm(forms.ModelForm):
    images = MultipleFileField(required=False, label="Homework Images")

    class Meta:
        model = TblHomework
        fields = ["title", "description", "class_field", "subject_field", "due_date", "status"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Homework title"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Homework description"}),
            "class_field": forms.Select(attrs={"class": "form-select"}),
            "subject_field": forms.Select(attrs={"class": "form-select"}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "title": "Homework Title",
            "description": "Description",
            "class_field": "Class",
            "subject_field": "Subject",
            "due_date": "Due Date",
            "status": "Status",
        }

    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop("teacher", None)
        super().__init__(*args, **kwargs)
        self._allowed_class_ids = []
        self._allowed_subject_ids = []

        if self.teacher is not None:
            assignments = TblTeacherAssignment.objects.filter(teacher_field=self.teacher)
            self._allowed_class_ids = list(assignments.values_list("class_field_id", flat=True).distinct())
            self._allowed_subject_ids = list(assignments.values_list("subject_field_id", flat=True).distinct())

            class_qs = TblClass.objects.filter(class_id__in=self._allowed_class_ids)
            subject_qs = TblSubject.objects.filter(subject_id__in=self._allowed_subject_ids)

            selected_class_id = None
            if self.is_bound:
                selected_class_id = self.data.get("class_field")
            elif self.instance and self.instance.pk:
                selected_class_id = self.instance.class_field_id

            if selected_class_id:
                subject_ids_for_class = assignments.filter(class_field_id=selected_class_id).values_list("subject_field_id", flat=True).distinct()
                subject_qs = subject_qs.filter(subject_id__in=subject_ids_for_class)

            self.fields["class_field"].queryset = class_qs
            self.fields["subject_field"].queryset = subject_qs
        else:
            self.fields["class_field"].queryset = TblClass.objects.all()
            self.fields["subject_field"].queryset = TblSubject.objects.all()

        self.fields["class_field"].empty_label = "— Select Class —"
        self.fields["subject_field"].required = False
        self.fields["subject_field"].empty_label = "— Optional Subject —"

    def clean_title(self):
        value = (self.cleaned_data.get("title") or "").strip()
        if not value:
            raise forms.ValidationError("Homework title is required.")
        return value

    def clean_description(self):
        value = (self.cleaned_data.get("description") or "").strip()
        if not value:
            raise forms.ValidationError("Description is required.")
        return value

    def clean(self):
        cleaned_data = super().clean()
        class_field = cleaned_data.get("class_field")
        subject_field = cleaned_data.get("subject_field")

        if self.teacher is None:
            return cleaned_data

        if class_field and class_field.class_id not in self._allowed_class_ids:
            self.add_error("class_field", "You can assign homework only to your assigned classes.")

        if subject_field and subject_field.subject_id not in self._allowed_subject_ids:
            self.add_error("subject_field", "You can select only your assigned subjects.")

        if class_field and subject_field:
            assignment_exists = TblTeacherAssignment.objects.filter(
                teacher_field=self.teacher,
                class_field=class_field,
                subject_field=subject_field,
            ).exists()
            if not assignment_exists:
                self.add_error("subject_field", "Selected subject is not assigned to you for this class.")

        return cleaned_data


class HomeworkCompletionForm(forms.Form):
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Optional comment"}),
        label="Comment",
    )


class HomeworkFilterForm(forms.Form):
    class_field = forms.ModelChoiceField(
        queryset=TblClass.objects.all(),
        required=False,
        empty_label="All Classes",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    subject_field = forms.ModelChoiceField(
        queryset=TblSubject.objects.all(),
        required=False,
        empty_label="All Subjects",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All Status"), ("Active", "Active"), ("Inactive", "Inactive")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop("teacher", None)
        super().__init__(*args, **kwargs)

        if self.teacher is None:
            return

        assignments = TblTeacherAssignment.objects.filter(teacher_field=self.teacher)
        class_ids = assignments.values_list("class_field_id", flat=True).distinct()
        subject_ids = assignments.values_list("subject_field_id", flat=True).distinct()

        class_qs = TblClass.objects.filter(class_id__in=class_ids)
        subject_qs = TblSubject.objects.filter(subject_id__in=subject_ids)

        selected_class_id = None
        if self.is_bound:
            selected_class_id = self.data.get("class_field")

        if selected_class_id:
            subject_ids_for_class = assignments.filter(class_field_id=selected_class_id).values_list("subject_field_id", flat=True).distinct()
            subject_qs = subject_qs.filter(subject_id__in=subject_ids_for_class)

        self.fields["class_field"].queryset = class_qs
        self.fields["subject_field"].queryset = subject_qs


class StudentForm(forms.ModelForm):
    class Meta:
        model = TblStudent
        fields = ["admission_no", "first_name", "last_name", "dob", "gender", "class_field", "section_field", "parent_field", "roll_no", "status"]
        widgets = {
            "admission_no": forms.TextInput(attrs={"class": "form-control", "placeholder": "Unique admission number", "required": True}),
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "First name"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Last name"}),
            "dob": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "class_field": forms.Select(attrs={"class": "form-select", "required": True}),
            "section_field": forms.Select(attrs={"class": "form-select", "required": True}),
            "parent_field": forms.Select(attrs={"class": "form-select", "required": True}),
            "roll_no": forms.TextInput(attrs={"class": "form-control", "placeholder": "Roll number"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "admission_no": "Admission Number",
            "first_name": "First Name",
            "last_name": "Last Name",
            "dob": "Date of Birth",
            "gender": "Gender",
            "class_field": "Class",
            "section_field": "Section",
            "parent_field": "Parent",
            "roll_no": "Roll Number",
            "status": "Status",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_field"].queryset = TblClass.objects.all()
        self.fields["class_field"].empty_label = "— Select Class —"
        self.fields["section_field"].queryset = TblSection.objects.select_related("class_field").all()
        self.fields["section_field"].empty_label = "— Select Section —"
        self.fields["parent_field"].queryset = TblParent.objects.all()
        self.fields["parent_field"].empty_label = "— Select Parent —"

    def clean_admission_no(self):
        value = self.cleaned_data.get("admission_no", "").strip()
        if not value:
            raise forms.ValidationError("Admission number is required.")
        qs = TblStudent.objects.filter(admission_no__iexact=value)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A student with this admission number already exists.")
        return value


class TeacherAssignmentForm(forms.ModelForm):
    class Meta:
        model = TblTeacherAssignment
        fields = ["teacher_field", "class_field", "section_field", "subject_field"]
        widgets = {
            "teacher_field": forms.Select(attrs={"class": "form-select"}),
            "class_field": forms.Select(attrs={"class": "form-select"}),
            "section_field": forms.Select(attrs={"class": "form-select"}),
            "subject_field": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "teacher_field": "Teacher",
            "class_field": "Class",
            "section_field": "Section",
            "subject_field": "Subject",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["teacher_field"].queryset = TblTeacher.objects.all()
        self.fields["teacher_field"].empty_label = "— Select Teacher —"
        self.fields["class_field"].queryset = TblClass.objects.all()
        self.fields["class_field"].empty_label = "— Select Class —"
        self.fields["section_field"].queryset = TblSection.objects.select_related("class_field").all()
        self.fields["section_field"].empty_label = "— Select Section —"
        self.fields["subject_field"].queryset = TblSubject.objects.all()
        self.fields["subject_field"].empty_label = "— Select Subject —"

    def clean(self):
        cleaned_data = super().clean()
        teacher = cleaned_data.get("teacher_field")
        cls = cleaned_data.get("class_field")
        section = cleaned_data.get("section_field")
        subject = cleaned_data.get("subject_field")

        if teacher and cls and section and subject:
            qs = TblTeacherAssignment.objects.filter(
                teacher_field=teacher,
                class_field=cls,
                section_field=section,
                subject_field=subject,
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f"This assignment already exists for {teacher.name}."
                )
        return cleaned_data




class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = TblFeeStructure
        fields = ["class_field", "academic_year", "tuition_fee", "activity_fee", "transport_fee", "other_fee", "total_fee"]
        widgets = {
            "class_field": forms.Select(attrs={"class": "form-select"}),
            "academic_year": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., 2024-2025"}),
            "tuition_fee": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "activity_fee": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "transport_fee": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "other_fee": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "total_fee": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "readonly": "readonly"}),
        }
        labels = {
            "class_field": "Class",
            "academic_year": "Academic Year",
            "tuition_fee": "Tuition Fee",
            "activity_fee": "Activity Fee",
            "transport_fee": "Transport Fee",
            "other_fee": "Other Fee",
            "total_fee": "Total Fee",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_field"].queryset = TblClass.objects.all()
        self.fields["class_field"].empty_label = "— Select Class —"

    def clean(self):
        cleaned_data = super().clean()
        class_field = cleaned_data.get("class_field")
        academic_year = (cleaned_data.get("academic_year") or "").strip()
        tuition_fee = cleaned_data.get("tuition_fee") or Decimal("0")
        activity_fee = cleaned_data.get("activity_fee") or Decimal("0")
        transport_fee = cleaned_data.get("transport_fee") or Decimal("0")
        other_fee = cleaned_data.get("other_fee") or Decimal("0")

        if academic_year:
            cleaned_data["academic_year"] = academic_year

        # Always compute total server-side to avoid manual/incorrect values.
        computed_total = tuition_fee + activity_fee + transport_fee + other_fee
        cleaned_data["total_fee"] = computed_total

        if class_field and academic_year:
            qs = TblFeeStructure.objects.filter(
                class_field=class_field,
                academic_year__iexact=academic_year,
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    "Fee structure already exists for this class and academic year."
                )

        return cleaned_data


class StudentFeeForm(forms.ModelForm):
    payment_reference_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
        label="Payment Reference File",
    )
    payment_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        label="Payment Date",
    )
    payment_month = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "month"}),
        label="Payment Month",
    )
    payment_method = forms.ChoiceField(
        required=False,
        choices=[("", "— Select Method —")] + list(TblFeePayment.PAYMENT_METHOD_CHOICES),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Payment Method",
    )
    transaction_ref = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Transaction reference (optional)"}),
        label="Transaction Reference",
    )

    class Meta:
        model = TblStudentFee
        fields = ["student_field", "fee_structure_field", "total_amount", "paid_amount", "status"]
        widgets = {
            "student_field": forms.Select(attrs={"class": "form-select"}),
            "fee_structure_field": forms.Select(attrs={"class": "form-select"}),
            "total_amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "readonly": "readonly"}),
            "paid_amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "student_field": "Student",
            "fee_structure_field": "Fee Structure",
            "total_amount": "Total Amount",
            "paid_amount": "Paid Amount",
            "status": "Status",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student_field"].queryset = TblStudent.objects.select_related("class_field", "section_field")
        self.fields["student_field"].empty_label = "— Select Student —"
        self.fields["fee_structure_field"].queryset = TblFeeStructure.objects.select_related("class_field")
        self.fields["fee_structure_field"].empty_label = "— Select Fee Structure —"
        if not self.is_bound:
            self.fields["payment_date"].initial = timezone.localdate()

    def clean(self):
        cleaned_data = super().clean()
        fee_structure = cleaned_data.get("fee_structure_field")
        student = cleaned_data.get("student_field")
        paid_amount = cleaned_data.get("paid_amount") or Decimal("0")
        payment_date = cleaned_data.get("payment_date")
        payment_method = cleaned_data.get("payment_method")
        payment_reference_file = cleaned_data.get("payment_reference_file")

        if paid_amount < 0:
            raise forms.ValidationError("Paid amount cannot be negative.")

        # If uploaded, payment reference file must not exceed 1 MB.
        if payment_reference_file and payment_reference_file.size >= 1024 * 1024:
            self.add_error("payment_reference_file", "Reference file must not exceed 1 MB.")

        # For new Student Fee entries, payment details are required when amount is paid.
        if not self.instance.pk and paid_amount > 0:
            if not payment_date:
                self.add_error("payment_date", "Payment date is required when paid amount is greater than 0.")
            if not payment_method:
                self.add_error("payment_method", "Payment method is required when paid amount is greater than 0.")

        if fee_structure:
            # Always take total from selected fee structure to avoid null/manual mismatch.
            cleaned_data["total_amount"] = fee_structure.total_fee

        if fee_structure and student:
            qs = TblStudentFee.objects.filter(
                student_field=student,
                fee_structure_field=fee_structure,
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            existing_paid = qs.aggregate(total=Sum("paid_amount"))["total"] or Decimal("0")
            allowed_total = fee_structure.total_fee or Decimal("0")
            next_total_paid = existing_paid + paid_amount

            # If full fee is already covered by earlier records, block new entries.
            if existing_paid >= allowed_total and not (self.instance and self.instance.pk):
                raise forms.ValidationError(
                    "This student fee is already fully paid. No additional record is allowed."
                )

            # Block any record that makes cumulative paid amount exceed fee total.
            if next_total_paid > allowed_total:
                remaining = allowed_total - existing_paid
                raise forms.ValidationError(
                    f"Paid amount exceeds total fee. Remaining allowed amount is {remaining}."
                )

            # Keep each record consistent with cumulative payment progression.
            cleaned_data["pending_amount"] = allowed_total - next_total_paid
            if next_total_paid == allowed_total:
                cleaned_data["status"] = "Paid"
            elif next_total_paid > 0:
                cleaned_data["status"] = "Partial"
            else:
                cleaned_data["status"] = "Pending"

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        fee_structure = self.cleaned_data.get("fee_structure_field")
        student = self.cleaned_data.get("student_field")
        paid_amount = self.cleaned_data.get("paid_amount") or Decimal("0")
        payment_date = self.cleaned_data.get("payment_date")

        if fee_structure and student:
            qs = TblStudentFee.objects.filter(
                student_field=student,
                fee_structure_field=fee_structure,
            )
            if instance.pk:
                qs = qs.exclude(pk=instance.pk)

            existing_paid = qs.aggregate(total=Sum("paid_amount"))["total"] or Decimal("0")
            allowed_total = fee_structure.total_fee or Decimal("0")
            next_total_paid = existing_paid + paid_amount

            instance.total_amount = allowed_total
            instance.pending_amount = allowed_total - next_total_paid
            if next_total_paid == allowed_total:
                instance.status = "Paid"
            elif next_total_paid > 0:
                instance.status = "Partial"
            else:
                instance.status = "Pending"

        if paid_amount > 0 and payment_date:
            instance.last_payment_date = payment_date

        if commit:
            instance.save()
        return instance


# COMMENTED OUT - Fee Payments now managed through StudentFeeForm with monthly tracking
# class FeePaymentForm(forms.ModelForm):
#     class Meta:
#         model = TblFeePayment
#         fields = ["student_fee_field", "amount", "payment_date", "payment_method", "transaction_ref"]
#         widgets = {
#             "student_fee_field": forms.Select(attrs={"class": "form-select"}),
#             "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
#             "payment_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
#             "payment_method": forms.Select(attrs={"class": "form-select"}),
#             "transaction_ref": forms.TextInput(attrs={"class": "form-control", "placeholder": "Transaction reference (optional)"}),
#         }
#         labels = {
#             "student_fee_field": "Student Fee",
#             "amount": "Amount",
#             "payment_date": "Payment Date",
#             "payment_method": "Payment Method",
#             "transaction_ref": "Transaction Reference",
#         }
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields["student_fee_field"].queryset = TblStudentFee.objects.select_related("student_field", "fee_structure_field")
#         self.fields["student_fee_field"].empty_label = "— Select Student Fee —"
#         if not self.is_bound:
#             self.fields["payment_date"].initial = timezone.localdate()


