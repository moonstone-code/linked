import os
import re
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db import models, transaction
from django.db.models import Count, Prefetch, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from uuid import uuid4

from .decorators import role_required
from .forms import (
    AttendanceMarkForm,
    ClassForm,
    FeeStructureForm,
    HomeworkCompletionForm,
    HomeworkFilterForm,
    HomeworkForm,
    ParentForm,
    ParentProfileForm,
    SectionForm,
    StudentFeeForm,
    StudentForm,
    SubjectForm,
    TeacherAssignmentForm,
    TeacherForm,
    TeacherProfileForm,
    UserForm,
)
from .models import (
    TblAttendance,
    TblClass,
    TblFeePayment,
    TblFeeStructure,
    TblHomework,
    TblHomeworkImage,
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

ROLE_TO_DASHBOARD_NAME = {
    "Admin": "admin_dashboard",
    "Teacher": "teacher_dashboard",
    "Parent": "parent_dashboard",
    "Student": "student_dashboard",
}


def get_user_role(user):
    """Return the first matching business role for the user."""
    if not user.is_authenticated:
        return None

    if user.is_superuser:
        return "Admin"

    for role in ROLE_TO_DASHBOARD_NAME.keys():
        if user.groups.filter(name=role).exists():
            return role

    return None


def _redirect_user_by_role(user):
    role = get_user_role(user)
    dashboard_name = ROLE_TO_DASHBOARD_NAME.get(role)
    if dashboard_name:
        return redirect(dashboard_name)
    return redirect("login")


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_user_by_role(request.user)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Invalid username or password.")
            return render(request, "accounts/login.html", status=401)

        if not user.is_active:
            messages.error(request, "Your account is disabled. Contact admin.")
            return render(request, "accounts/login.html", status=403)

        login(request, user)
        return _redirect_user_by_role(user)

    return render(request, "accounts/login.html")


@login_required
def logout_view(request):
    if request.method != "POST":
        return _redirect_user_by_role(request.user)

    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")


@login_required
@role_required("Admin")
def admin_dashboard(request):
    from django.db.models import Count

    # ── KPI counts ────────────────────────────────────────────────────────────
    total_students  = TblStudent.objects.count()
    total_teachers  = TblTeacher.objects.count()
    total_parents   = TblParent.objects.count()
    total_users     = TblUser.objects.count()
    active_users    = TblUser.objects.filter(is_active=True).count()

    fee_totals = TblStudentFee.objects.aggregate(
        grand_total=Sum("total_amount"),
        grand_paid=Sum("paid_amount"),
        grand_pending=Sum("pending_amount"),
    )
    grand_total   = fee_totals["grand_total"]   or 0
    grand_paid    = fee_totals["grand_paid"]    or 0
    grand_pending = fee_totals["grand_pending"] or 0
    collection_pct = int((grand_paid / grand_total * 100)) if grand_total else 0

    # ── Fee status breakdown ────────────────────────────────────────────
    fee_status_counts = (
        TblStudentFee.objects
        .values("status")
        .annotate(count=Count("student_fee_id"))
        .order_by("status")
    )
    status_map = {r["status"]: r["count"] for r in fee_status_counts}
    total_fee_records = sum(status_map.values()) or 1  # avoid zero-div
    paid_count    = status_map.get("Paid", 0)
    partial_count = status_map.get("Partial", 0)
    pending_count = status_map.get("Pending", 0)

    # ── Recent fee payments (latest 5) ────────────────────────────────────────────
    recent_payments = (
        TblFeePayment.objects
        .select_related(
            "student_fee_field__student_field",
            "student_fee_field__fee_structure_field",
        )
        .order_by("-payment_date", "-payment_id")[:5]
    )

    # ── User role distribution ─────────────────────────────────────────────────────
    role_counts = (
        TblUser.objects
        .values("role")
        .annotate(count=Count("user_id"))
        .order_by("role")
    )

    return render(request, "accounts/admin_dashboard.html", {
        # KPI
        "total_students":  total_students,
        "total_teachers":  total_teachers,
        "total_parents":   total_parents,
        "total_users":     total_users,
        "active_users":    active_users,
        # Fee summary
        "grand_total":     grand_total,
        "grand_paid":      grand_paid,
        "grand_pending":   grand_pending,
        "collection_pct":  collection_pct,
        # Fee status breakdown
        "paid_count":      paid_count,
        "partial_count":   partial_count,
        "pending_count":   pending_count,
        "total_fee_records": total_fee_records,
        # Recent activity
        "recent_payments": recent_payments,
        # User role distribution
        "role_counts": role_counts,
    })


def _get_current_student(request):
    """Resolve current student via tbl_users.reference_id; return None if invalid."""
    tbl_user = TblUser.objects.filter(
        username=request.user.username,
        role="Student",
        is_active=True,
    ).first()
    if not tbl_user or not tbl_user.reference_id:
        return None

    return TblStudent.objects.select_related("class_field", "section_field", "parent_field").filter(pk=tbl_user.reference_id).first()


def _student_fee_qs(student):
    return TblStudentFee.objects.select_related(
        "fee_structure_field", "student_field", "student_field__class_field", "student_field__section_field"
    ).filter(student_field=student)


def _student_attendance_qs(student):
    return TblAttendance.objects.select_related(
        "student_field", "student_field__class_field", "student_field__section_field"
    ).filter(student_field=student)


def _student_payment_qs(student):
    return TblFeePayment.objects.select_related(
        "student_fee_field__student_field",
        "student_fee_field__fee_structure_field",
    ).filter(student_fee_field__student_field=student)


@login_required
@role_required("Student")
def student_profile(request):
    student = _get_current_student(request)
    if not student:
        messages.error(request, "Student profile mapping is missing. Contact admin.")
        return redirect("login")

    fee_qs = _student_fee_qs(student)
    payment_qs = _student_payment_qs(student)

    return render(request, "accounts/student_profile.html", {
        "student": student,
        "fee_records": fee_qs,
        "recent_payments": payment_qs.order_by("-payment_date", "-payment_id")[:3],
    })


@login_required
@role_required("Student")
def student_attendance(request):
    student = _get_current_student(request)
    if not student:
        messages.error(request, "Student profile mapping is missing. Contact admin.")
        return redirect("login")

    search_q = request.GET.get("q", "").strip()
    attendance_qs = _student_attendance_qs(student)
    if search_q:
        attendance_qs = attendance_qs.filter(
            models.Q(attendance_date__icontains=search_q)
            | models.Q(status__icontains=search_q)
            | models.Q(remarks__icontains=search_q)
        )

    paginator = Paginator(attendance_qs, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/student_attendance.html", {
        "student": student,
        "page_obj": page_obj,
        "search_q": search_q,
    })


@login_required
@role_required("Student")
def student_fee_status(request):
    student = _get_current_student(request)
    if not student:
        messages.error(request, "Student profile mapping is missing. Contact admin.")
        return redirect("login")

    search_q = request.GET.get("q", "").strip()
    fee_qs = _student_fee_qs(student)
    if search_q:
        fee_qs = fee_qs.filter(
            models.Q(fee_structure_field__academic_year__icontains=search_q)
            | models.Q(status__icontains=search_q)
        )

    paginator = Paginator(fee_qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/student_fee_status.html", {
        "student": student,
        "page_obj": page_obj,
        "search_q": search_q,
    })


@login_required
@role_required("Student")
def student_receipts(request):
    student = _get_current_student(request)
    if not student:
        messages.error(request, "Student profile mapping is missing. Contact admin.")
        return redirect("login")

    search_q = request.GET.get("q", "").strip()
    payment_qs = _student_payment_qs(student)
    if search_q:
        payment_qs = payment_qs.filter(
            models.Q(payment_method__icontains=search_q)
            | models.Q(transaction_ref__icontains=search_q)
            | models.Q(payment_date__icontains=search_q)
            | models.Q(student_fee_field__fee_structure_field__academic_year__icontains=search_q)
        )

    paginator = Paginator(payment_qs, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/student_receipts.html", {
        "student": student,
        "page_obj": page_obj,
        "search_q": search_q,
    })


def _get_current_teacher(request):
    """Resolve current teacher via tbl_users.reference_id; return None if invalid."""
    tbl_user = TblUser.objects.filter(
        username=request.user.username,
        role="Teacher",
        is_active=True,
    ).first()
    if not tbl_user or not tbl_user.reference_id:
        return None

    return TblTeacher.objects.filter(pk=tbl_user.reference_id).first()


def _teacher_assignments_qs(teacher):
    return TblTeacherAssignment.objects.select_related(
        "teacher_field", "class_field", "section_field", "subject_field"
    ).filter(teacher_field=teacher)


def _teacher_students_qs(teacher):
    assignments = list(
        _teacher_assignments_qs(teacher)
        .values_list("class_field_id", "section_field_id")
        .distinct()
    )
    if not assignments:
        return TblStudent.objects.none()

    scope_q = models.Q(pk__in=[])
    for class_id, section_id in assignments:
        scope_q |= models.Q(class_field_id=class_id, section_field_id=section_id)

    return TblStudent.objects.select_related(
        "class_field", "section_field", "parent_field"
    ).filter(scope_q)


@login_required
@role_required("Teacher")
def teacher_dashboard(request):
    teacher = _get_current_teacher(request)
    if not teacher:
        messages.error(request, "Teacher profile mapping is missing. Contact admin.")
        return redirect("login")

    assignments_qs = _teacher_assignments_qs(teacher)
    students_qs = _teacher_students_qs(teacher)
    today = timezone.localdate()

    todays_attendance = TblAttendance.objects.filter(
        student_field_id__in=students_qs.values_list("student_id", flat=True),
        attendance_date=today,
    )
    attendance_counts = todays_attendance.values("status").annotate(count=Count("attendance_id"))
    status_map = {row["status"]: row["count"] for row in attendance_counts}

    context = {
        "teacher": teacher,
        "assignments_count": assignments_qs.count(),
        "students_count": students_qs.count(),
        "today_attendance_count": todays_attendance.count(),
        "present_count": status_map.get("Present", 0),
        "absent_count": status_map.get("Absent", 0),
        "leave_count": status_map.get("Leave", 0),
    }
    return render(request, "accounts/teacher_dashboard.html", context)


@login_required
@role_required("Teacher")
def teacher_my_assignments(request):
    teacher = _get_current_teacher(request)
    if not teacher:
        messages.error(request, "Teacher profile mapping is missing. Contact admin.")
        return redirect("login")

    search_q = request.GET.get("q", "").strip()
    qs = _teacher_assignments_qs(teacher)
    if search_q:
        qs = qs.filter(
            models.Q(class_field__class_name__icontains=search_q)
            | models.Q(section_field__section_name__icontains=search_q)
            | models.Q(subject_field__subject_name__icontains=search_q)
        )

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/teacher_my_assignments.html", {
        "teacher": teacher,
        "page_obj": page_obj,
        "search_q": search_q,
    })


@login_required
@role_required("Teacher")
def teacher_my_students(request):
    teacher = _get_current_teacher(request)
    if not teacher:
        messages.error(request, "Teacher profile mapping is missing. Contact admin.")
        return redirect("login")

    search_q  = request.GET.get("q", "").strip()
    class_id  = request.GET.get("class_id", "").strip()

    qs = _teacher_students_qs(teacher)

    # Classes this teacher is assigned to (for filter tabs)
    assigned_classes = TblClass.objects.filter(
        pk__in=_teacher_assignments_qs(teacher).values_list("class_field_id", flat=True)
    ).distinct().order_by("class_id")

    if class_id:
        qs = qs.filter(class_field_id=class_id)

    if search_q:
        qs = qs.filter(
            models.Q(first_name__icontains=search_q)
            | models.Q(last_name__icontains=search_q)
            | models.Q(admission_no__icontains=search_q)
            | models.Q(roll_no__icontains=search_q)
            | models.Q(class_field__class_name__icontains=search_q)
            | models.Q(section_field__section_name__icontains=search_q)
        )

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/teacher_my_students.html", {
        "teacher": teacher,
        "page_obj": page_obj,
        "search_q": search_q,
        "assigned_classes": assigned_classes,
        "selected_class_id": class_id,
    })


@login_required
@role_required("Teacher")
def teacher_attendance_manage(request):
    teacher = _get_current_teacher(request)
    if not teacher:
        messages.error(request, "Teacher profile mapping is missing. Contact admin.")
        return redirect("login")

    assignments = _teacher_assignments_qs(teacher)
    selected_assignment = None
    students = TblStudent.objects.none()
    existing_map = {}

    selected_assignment_id = request.GET.get("assignment_id") or request.POST.get("assignment_id")
    selected_date = request.GET.get("attendance_date") or request.POST.get("attendance_date") or str(timezone.localdate())

    if selected_assignment_id:
        selected_assignment = assignments.filter(pk=selected_assignment_id).first()
        if selected_assignment:
            students = TblStudent.objects.select_related("class_field", "section_field").filter(
                class_field=selected_assignment.class_field,
                section_field=selected_assignment.section_field,
            )
            existing_rows = TblAttendance.objects.filter(
                student_field_id__in=students.values_list("student_id", flat=True),
                attendance_date=selected_date,
            )
            existing_map = {
                row.student_field_id: {"status": row.status, "remarks": row.remarks or ""}
                for row in existing_rows
            }

    if request.method == "POST":
        form = AttendanceMarkForm(request.POST)
        if form.is_valid():
            assignment_id = form.cleaned_data["assignment_id"]
            attendance_date = form.cleaned_data["attendance_date"]
            assignment = assignments.filter(pk=assignment_id).first()

            if not assignment:
                messages.error(request, "Invalid assignment selected.")
                return redirect("teacher_attendance_manage")

            scoped_students = TblStudent.objects.filter(
                class_field=assignment.class_field,
                section_field=assignment.section_field,
            )

            updated_count = 0
            for student in scoped_students:
                status = request.POST.get(f"status_{student.student_id}", "").strip()
                remarks = (request.POST.get(f"remarks_{student.student_id}", "") or "").strip()[:255]
                if status not in {"Present", "Absent", "Leave"}:
                    continue

                TblAttendance.objects.update_or_create(
                    student_field=student,
                    attendance_date=attendance_date,
                    defaults={"status": status, "remarks": remarks or None},
                )
                updated_count += 1

            messages.success(request, f"Attendance saved for {updated_count} students.")
            return redirect("teacher_attendance_manage")
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)

    mark_form = AttendanceMarkForm(initial={
        "assignment_id": selected_assignment.assignment_id if selected_assignment else None,
        "attendance_date": selected_date,
    })

    for student in students:
        row = existing_map.get(student.student_id, {})
        student.current_status = row.get("status", "")
        student.current_remarks = row.get("remarks", "")

    return render(request, "accounts/teacher_attendance_manage.html", {
        "teacher": teacher,
        "assignments": assignments,
        "selected_assignment": selected_assignment,
        "selected_date": selected_date,
        "students": students,
        "existing_map": existing_map,
        "mark_form": mark_form,
    })


@login_required
@role_required("Teacher")
def teacher_attendance_history(request):
    teacher = _get_current_teacher(request)
    if not teacher:
        messages.error(request, "Teacher profile mapping is missing. Contact admin.")
        return redirect("login")

    search_q = request.GET.get("q", "").strip()
    students_qs = _teacher_students_qs(teacher)

    attendance_qs = TblAttendance.objects.select_related(
        "student_field", "student_field__class_field", "student_field__section_field"
    ).filter(student_field_id__in=students_qs.values_list("student_id", flat=True))

    if search_q:
        attendance_qs = attendance_qs.filter(
            models.Q(student_field__first_name__icontains=search_q)
            | models.Q(student_field__last_name__icontains=search_q)
            | models.Q(student_field__admission_no__icontains=search_q)
            | models.Q(status__icontains=search_q)
            | models.Q(attendance_date__icontains=search_q)
        )

    paginator = Paginator(attendance_qs, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/teacher_attendance_history.html", {
        "teacher": teacher,
        "page_obj": page_obj,
        "search_q": search_q,
    })


@login_required
@role_required("Teacher")
def teacher_profile(request):
    teacher = _get_current_teacher(request)
    if not teacher:
        messages.error(request, "Teacher profile mapping is missing. Contact admin.")
        return redirect("login")

    if request.method == "POST":
        form = TeacherProfileForm(request.POST, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("teacher_profile")
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(request, error)
    else:
        form = TeacherProfileForm(instance=teacher)

    assignments_qs = _teacher_assignments_qs(teacher)
    return render(request, "accounts/teacher_profile.html", {
        "teacher": teacher,
        "form": form,
        "assignments": assignments_qs,
    })


@login_required
@role_required("Parent")
def parent_dashboard(request):
    parent = _get_current_parent(request)
    if not parent:
        messages.error(request, "Parent profile mapping is missing. Contact admin.")
        return redirect("login")

    children_qs = _parent_children_qs(parent)
    total_children = children_qs.count()

    attendance_qs = TblAttendance.objects.filter(
        student_field_id__in=children_qs.values_list("student_id", flat=True)
    )
    attendance_counts = attendance_qs.values("status").annotate(count=Count("attendance_id"))
    status_map = {row["status"]: row["count"] for row in attendance_counts}

    student_fee_qs = TblStudentFee.objects.filter(
        student_field_id__in=children_qs.values_list("student_id", flat=True)
    )
    fee_totals = student_fee_qs.aggregate(
        total=Sum("total_amount"),
        paid=Sum("paid_amount"),
        pending=Sum("pending_amount"),
    )

    recent_payments = TblFeePayment.objects.select_related(
        "student_fee_field__student_field",
        "student_fee_field__fee_structure_field",
    ).filter(
        student_fee_field__student_field_id__in=children_qs.values_list("student_id", flat=True)
    ).order_by("-payment_date", "-payment_id")[:5]

    return render(request, "accounts/parent_dashboard.html", {
        "parent": parent,
        "children_count": total_children,
        "present_count": status_map.get("Present", 0),
        "absent_count": status_map.get("Absent", 0),
        "leave_count": status_map.get("Leave", 0),
        "fee_total": fee_totals.get("total") or 0,
        "fee_paid": fee_totals.get("paid") or 0,
        "fee_pending": fee_totals.get("pending") or 0,
        "recent_payments": recent_payments,
    })


def _get_current_parent(request):
    """Resolve current parent via tbl_users.reference_id; return None if invalid."""
    tbl_user = TblUser.objects.filter(
        username=request.user.username,
        role="Parent",
        is_active=True,
    ).first()
    if not tbl_user or not tbl_user.reference_id:
        return None

    return TblParent.objects.filter(pk=tbl_user.reference_id).first()


def _parent_children_qs(parent):
    return TblStudent.objects.select_related(
        "class_field", "section_field", "parent_field"
    ).filter(parent_field=parent)


@login_required
@role_required("Parent")
def parent_my_child(request):
    parent = _get_current_parent(request)
    if not parent:
        messages.error(request, "Parent profile mapping is missing. Contact admin.")
        return redirect("login")

    search_q = request.GET.get("q", "").strip()
    children_qs = _parent_children_qs(parent)
    if search_q:
        children_qs = children_qs.filter(
            models.Q(first_name__icontains=search_q)
            | models.Q(last_name__icontains=search_q)
            | models.Q(admission_no__icontains=search_q)
            | models.Q(roll_no__icontains=search_q)
            | models.Q(class_field__class_name__icontains=search_q)
            | models.Q(section_field__section_name__icontains=search_q)
        )

    paginator = Paginator(children_qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/parent_my_child.html", {
        "parent": parent,
        "page_obj": page_obj,
        "search_q": search_q,
    })


@login_required
@role_required("Parent")
def parent_attendance(request):
    parent = _get_current_parent(request)
    if not parent:
        messages.error(request, "Parent profile mapping is missing. Contact admin.")
        return redirect("login")

    search_q = request.GET.get("q", "").strip()
    children_qs = _parent_children_qs(parent)

    attendance_qs = TblAttendance.objects.select_related(
        "student_field", "student_field__class_field", "student_field__section_field"
    ).filter(student_field_id__in=children_qs.values_list("student_id", flat=True))

    if search_q:
        attendance_qs = attendance_qs.filter(
            models.Q(student_field__first_name__icontains=search_q)
            | models.Q(student_field__last_name__icontains=search_q)
            | models.Q(student_field__admission_no__icontains=search_q)
            | models.Q(status__icontains=search_q)
            | models.Q(attendance_date__icontains=search_q)
        )

    paginator = Paginator(attendance_qs, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/parent_attendance.html", {
        "parent": parent,
        "page_obj": page_obj,
        "search_q": search_q,
    })


@login_required
@role_required("Parent")
def parent_fee_status(request):
    parent = _get_current_parent(request)
    if not parent:
        messages.error(request, "Parent profile mapping is missing. Contact admin.")
        return redirect("login")

    search_q = request.GET.get("q", "").strip()
    children_qs = _parent_children_qs(parent)

    fee_qs = TblStudentFee.objects.select_related(
        "student_field", "fee_structure_field", "student_field__class_field", "student_field__section_field"
    ).filter(student_field_id__in=children_qs.values_list("student_id", flat=True))

    if search_q:
        fee_qs = fee_qs.filter(
            models.Q(student_field__first_name__icontains=search_q)
            | models.Q(student_field__last_name__icontains=search_q)
            | models.Q(student_field__admission_no__icontains=search_q)
            | models.Q(fee_structure_field__academic_year__icontains=search_q)
            | models.Q(status__icontains=search_q)
        )

    paginator = Paginator(fee_qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/parent_fee_status.html", {
        "parent": parent,
        "page_obj": page_obj,
        "search_q": search_q,
    })


@login_required
@role_required("Parent")
def parent_payment_history(request):
    parent = _get_current_parent(request)
    if not parent:
        messages.error(request, "Parent profile mapping is missing. Contact admin.")
        return redirect("login")

    search_q = request.GET.get("q", "").strip()
    children_qs = _parent_children_qs(parent)

    payment_qs = TblFeePayment.objects.select_related(
        "student_fee_field__student_field",
        "student_fee_field__fee_structure_field",
    ).filter(
        student_fee_field__student_field_id__in=children_qs.values_list("student_id", flat=True)
    )

    if search_q:
        payment_qs = payment_qs.filter(
            models.Q(student_fee_field__student_field__first_name__icontains=search_q)
            | models.Q(student_fee_field__student_field__last_name__icontains=search_q)
            | models.Q(transaction_ref__icontains=search_q)
            | models.Q(payment_method__icontains=search_q)
            | models.Q(payment_date__icontains=search_q)
        )

    paginator = Paginator(payment_qs, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/parent_payment_history.html", {
        "parent": parent,
        "page_obj": page_obj,
        "search_q": search_q,
    })


@login_required
@role_required("Parent")
def parent_profile(request):
    parent = _get_current_parent(request)
    if not parent:
        messages.error(request, "Parent profile mapping is missing. Contact admin.")
        return redirect("login")

    if request.method == "POST":
        form = ParentProfileForm(request.POST, instance=parent)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("parent_profile")
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(request, error)
    else:
        form = ParentProfileForm(instance=parent)

    children_qs = _parent_children_qs(parent)
    return render(request, "accounts/parent_profile.html", {
        "parent": parent,
        "form": form,
        "children": children_qs,
    })


def _get_current_student(request):
    """Resolve current student via tbl_users.reference_id; return None if invalid."""
    tbl_user = TblUser.objects.filter(
        username=request.user.username,
        role="Student",
        is_active=True,
    ).first()
    if not tbl_user or not tbl_user.reference_id:
        return None

    return TblStudent.objects.select_related("class_field", "section_field", "parent_field").filter(pk=tbl_user.reference_id).first()


def _get_homework_owner_user(role, reference_id):
    return TblUser.objects.filter(role=role, reference_id=reference_id, is_active=True).first()


def _teacher_homework_qs(teacher):
    return TblHomework.objects.select_related("class_field", "subject_field", "teacher_field").prefetch_related("images", "student_records__student_field", "student_records__student_field__parent_field").filter(teacher_field=teacher)


def _teacher_homework_records(homework):
    return homework.student_records.select_related("student_field", "student_field__parent_field").all()


def _student_homework_qs(student):
    return TblHomeworkStudent.objects.select_related(
        "homework_field",
        "homework_field__class_field",
        "homework_field__subject_field",
        "homework_field__teacher_field",
        "student_field",
    ).prefetch_related("homework_field__images").filter(student_field=student)


def _parent_homework_qs(parent):
    return TblHomeworkStudent.objects.select_related(
        "homework_field",
        "homework_field__class_field",
        "homework_field__subject_field",
        "homework_field__teacher_field",
        "student_field",
    ).prefetch_related("homework_field__images").filter(student_field__parent_field=parent)


def _save_homework_images(homework, uploaded_files):
    saved_images = []
    for uploaded_file in uploaded_files or []:
        extension = os.path.splitext(uploaded_file.name)[1].lower()
        unique_name = f"homework/{homework.homework_id}/{uuid4().hex}{extension}"
        stored_path = default_storage.save(unique_name, uploaded_file)
        saved_images.append(TblHomeworkImage.objects.create(homework_field=homework, image_path=stored_path))
    return saved_images


def _create_homework_notification(user_type, user_id, homework, title, message):
    if not user_id:
        return

    today = timezone.localdate()
    if TblNotification.objects.filter(
        user_type=user_type,
        user_id=user_id,
        homework_field=homework,
        title=title,
        message=message,
        created_at__date=today,
    ).exists():
        return

    TblNotification.objects.create(
        user_type=user_type,
        user_id=user_id,
        homework_field=homework,
        title=title,
        message=message,
    )


def _notify_homework_publish(homework):
    students = TblStudent.objects.select_related("parent_field").filter(class_field=homework.class_field, status="Active")
    for student in students:
        student_user = _get_homework_owner_user("Student", student.student_id)
        if student_user:
            _create_homework_notification("Student", student_user.user_id, homework, "New Homework", "New homework has been assigned.")

        parent_user = _get_homework_owner_user("Parent", student.parent_field_id)
        if parent_user:
            _create_homework_notification("Parent", parent_user.user_id, homework, "New Homework", "Homework has been assigned to your child.")


def _notify_homework_completion(homework_record):
    teacher_user = _get_homework_owner_user("Teacher", homework_record.homework_field.teacher_field_id)
    if not teacher_user:
        return

    student_name = homework_record.student_field.first_name or homework_record.student_field.admission_no
    _create_homework_notification(
        "Teacher",
        teacher_user.user_id,
        homework_record.homework_field,
        "Homework Completed",
        f"{student_name} has completed Homework: {homework_record.homework_field.title}.",
    )


def _sync_homework_due_notifications(homework_records):
    today = timezone.localdate()
    due_tomorrow = today + timedelta(days=1)

    for record in homework_records:
        homework = record.homework_field
        if record.status == "Completed" or not homework.due_date:
            continue

        if homework.due_date == due_tomorrow:
            title = "Homework Due Tomorrow"
            message = "Homework is due tomorrow."
        elif homework.due_date < today:
            title = "Homework Overdue"
            message = "Homework is overdue."
        else:
            continue

        student_user = _get_homework_owner_user("Student", record.student_field_id)
        if student_user:
            _create_homework_notification("Student", student_user.user_id, homework, title, message)

        parent_user = _get_homework_owner_user("Parent", record.student_field.parent_field_id)
        if parent_user:
            _create_homework_notification("Parent", parent_user.user_id, homework, title, message)


def _homework_accessible_record(user_role, user_obj, homework_id):
    if user_role == "Student":
        return TblHomeworkStudent.objects.select_related(
            "homework_field",
            "homework_field__class_field",
            "homework_field__subject_field",
            "homework_field__teacher_field",
            "student_field",
        ).prefetch_related("homework_field__images").filter(student_field=user_obj, homework_field_id=homework_id).first()

    if user_role == "Parent":
        return TblHomeworkStudent.objects.select_related(
            "homework_field",
            "homework_field__class_field",
            "homework_field__subject_field",
            "homework_field__teacher_field",
            "student_field",
        ).prefetch_related("homework_field__images").filter(student_field__parent_field=user_obj, homework_field_id=homework_id).first()

    return None


def _render_homework_row(row):
    for image in row.homework_field.images.all():
        image.image_url = default_storage.url(image.image_path)
    return row


def _mark_homework_completed(record, completed_by, comment):
    if record.status == "Completed":
        return False

    now = timezone.now()
    update_kwargs = {
        "status": "Completed",
        "completed_by": completed_by,
        "completed_at": now,
    }
    if completed_by == "Student":
        update_kwargs["student_comment"] = comment or None
    else:
        update_kwargs["parent_comment"] = comment or None

    TblHomeworkStudent.objects.filter(pk=record.pk).update(**update_kwargs)
    record.status = "Completed"
    record.completed_by = completed_by
    record.completed_at = now
    if completed_by == "Student":
        record.student_comment = comment or None
    else:
        record.parent_comment = comment or None

    _notify_homework_completion(record)
    return True


@login_required
@role_required("Teacher")
def teacher_homework_dashboard(request):
    teacher = _get_current_teacher(request)
    if not teacher:
        messages.error(request, "Teacher profile mapping is missing. Contact admin.")
        return redirect("login")

    homework_qs = _teacher_homework_qs(teacher)
    all_records = TblHomeworkStudent.objects.select_related("homework_field", "student_field", "student_field__parent_field").filter(homework_field__teacher_field=teacher)
    _sync_homework_due_notifications(all_records)

    homework_cards = []
    assigned_students = 0
    completed_students = 0
    completion_durations = []

    for homework in homework_qs:
        records = list(_teacher_homework_records(homework))
        assigned_count = len(records)
        completed_count = sum(1 for record in records if record.status == "Completed")
        pending_count = max(assigned_count - completed_count, 0)
        completion_pct = int((completed_count / assigned_count) * 100) if assigned_count else 0
        for record in records:
            if record.status == "Completed" and record.completed_at:
                completion_durations.append((record.completed_at - homework.created_at).total_seconds() / 3600)

        assigned_students += assigned_count
        completed_students += completed_count
        homework_cards.append({
            "homework": homework,
            "assigned_count": assigned_count,
            "completed_count": completed_count,
            "pending_count": pending_count,
            "completion_pct": completion_pct,
        })

    avg_completion_hours = round(sum(completion_durations) / len(completion_durations), 2) if completion_durations else 0
    completion_pct = int((completed_students / assigned_students) * 100) if assigned_students else 0

    return render(request, "accounts/teacher_homework_dashboard.html", {
        "teacher": teacher,
        "homework_cards": homework_cards[:5],
        "homework_count": homework_qs.count(),
        "assigned_students": assigned_students,
        "completed_students": completed_students,
        "pending_students": max(assigned_students - completed_students, 0),
        "completion_pct": completion_pct,
        "avg_completion_hours": avg_completion_hours,
    })


@login_required
@role_required("Teacher")
def teacher_homework_list(request):
    teacher = _get_current_teacher(request)
    if not teacher:
        messages.error(request, "Teacher profile mapping is missing. Contact admin.")
        return redirect("login")

    filter_form = HomeworkFilterForm(request.GET or None, teacher=teacher)
    search_q = (request.GET.get("q") or "").strip()
    qs = _teacher_homework_qs(teacher)

    if search_q:
        qs = qs.filter(models.Q(title__icontains=search_q) | models.Q(description__icontains=search_q))
    if filter_form.is_valid():
        if filter_form.cleaned_data.get("class_field"):
            qs = qs.filter(class_field=filter_form.cleaned_data["class_field"])
        if filter_form.cleaned_data.get("subject_field"):
            qs = qs.filter(subject_field=filter_form.cleaned_data["subject_field"])
        if filter_form.cleaned_data.get("status"):
            qs = qs.filter(status=filter_form.cleaned_data["status"])

    homework_rows = []
    for homework in qs:
        records = list(_teacher_homework_records(homework))
        completed_count = sum(1 for record in records if record.status == "Completed")
        homework_rows.append({
            "homework": homework,
            "assigned_count": len(records),
            "completed_count": completed_count,
            "pending_count": max(len(records) - completed_count, 0),
            "completion_pct": int((completed_count / len(records)) * 100) if records else 0,
        })

    paginator = Paginator(homework_rows, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/teacher_homework_list.html", {
        "teacher": teacher,
        "page_obj": page_obj,
        "search_q": search_q,
        "filter_form": filter_form,
    })


@login_required
@role_required("Teacher")
def teacher_homework_create(request):
    teacher = _get_current_teacher(request)
    if not teacher:
        messages.error(request, "Teacher profile mapping is missing. Contact admin.")
        return redirect("login")

    if request.method == "POST":
        form = HomeworkForm(request.POST, request.FILES, teacher=teacher)
        if form.is_valid():
            with transaction.atomic():
                homework = form.save(commit=False)
                homework.teacher_field = teacher
                homework.save()
                _save_homework_images(homework, request.FILES.getlist("images"))
                students = TblStudent.objects.filter(class_field=homework.class_field, status="Active")
                TblHomeworkStudent.objects.bulk_create([
                    TblHomeworkStudent(homework_field=homework, student_field=student) for student in students
                ])
                _notify_homework_publish(homework)
            messages.success(request, "Homework published successfully.")
            return redirect("teacher_homework_list")
    else:
        form = HomeworkForm(initial={"status": "Active"}, teacher=teacher)

    return render(request, "accounts/teacher_homework_form.html", {
        "teacher": teacher,
        "form": form,
        "mode": "Create",
    })


@login_required
@role_required("Teacher")
def teacher_homework_edit(request, pk):
    teacher = _get_current_teacher(request)
    if not teacher:
        messages.error(request, "Teacher profile mapping is missing. Contact admin.")
        return redirect("login")

    homework = get_object_or_404(TblHomework.objects.select_related("class_field", "subject_field", "teacher_field"), pk=pk, teacher_field=teacher)
    if homework.student_records.filter(status="Completed").exists():
        messages.error(request, "Completed homework cannot be edited.")
        return redirect("teacher_homework_report", pk=homework.homework_id)

    if request.method == "POST":
        form = HomeworkForm(request.POST, request.FILES, instance=homework, teacher=teacher)
        if form.is_valid():
            with transaction.atomic():
                previous_class_id = homework.class_field_id
                homework = form.save()
                if request.FILES.getlist("images"):
                    _save_homework_images(homework, request.FILES.getlist("images"))
                if homework.class_field_id != previous_class_id:
                    homework.student_records.all().delete()
                    students = TblStudent.objects.filter(class_field=homework.class_field, status="Active")
                    TblHomeworkStudent.objects.bulk_create([
                        TblHomeworkStudent(homework_field=homework, student_field=student) for student in students
                    ])
                    _notify_homework_publish(homework)
            messages.success(request, "Homework updated successfully.")
            return redirect("teacher_homework_report", pk=homework.homework_id)
    else:
        form = HomeworkForm(instance=homework, teacher=teacher)

    homework_images = list(homework.images.all())
    for image in homework_images:
        image.image_url = default_storage.url(image.image_path)

    return render(request, "accounts/teacher_homework_form.html", {
        "teacher": teacher,
        "form": form,
        "homework": homework,
        "homework_images": homework_images,
        "mode": "Edit",
    })


@login_required
@role_required("Teacher")
def teacher_homework_delete(request, pk):
    teacher = _get_current_teacher(request)
    if not teacher:
        messages.error(request, "Teacher profile mapping is missing. Contact admin.")
        return redirect("login")

    homework = get_object_or_404(TblHomework, pk=pk, teacher_field=teacher)
    if homework.student_records.filter(status="Completed").exists():
        messages.error(request, "Homework with completed records cannot be deleted.")
        return redirect("teacher_homework_report", pk=homework.homework_id)

    if request.method == "POST":
        homework.student_records.all().delete()
        homework.images.all().delete()
        homework.delete()
        messages.success(request, "Homework deleted successfully.")
    return redirect("teacher_homework_list")


@login_required
@role_required("Teacher")
def teacher_homework_report(request, pk):
    teacher = _get_current_teacher(request)
    if not teacher:
        messages.error(request, "Teacher profile mapping is missing. Contact admin.")
        return redirect("login")

    homework = get_object_or_404(
        TblHomework.objects.select_related("class_field", "subject_field", "teacher_field").prefetch_related("images", "student_records__student_field", "student_records__student_field__parent_field"),
        pk=pk,
        teacher_field=teacher,
    )
    records = list(_teacher_homework_records(homework))
    completed_count = sum(1 for record in records if record.status == "Completed")
    pending_count = max(len(records) - completed_count, 0)
    completion_pct = int((completed_count / len(records)) * 100) if records else 0

    homework_images = list(homework.images.all())
    for image in homework_images:
        image.image_url = default_storage.url(image.image_path)

    return render(request, "accounts/teacher_homework_report.html", {
        "teacher": teacher,
        "homework": homework,
        "records": records,
        "homework_images": homework_images,
        "completed_count": completed_count,
        "pending_count": pending_count,
        "completion_pct": completion_pct,
        "can_edit": not homework.student_records.filter(status="Completed").exists(),
    })


@login_required
@role_required("Student")
def student_dashboard(request):
    student = _get_current_student(request)
    if not student:
        messages.error(request, "Student profile mapping is missing. Contact admin.")
        return redirect("login")

    homework_qs = _student_homework_qs(student)
    _sync_homework_due_notifications(homework_qs)
    attendance_qs = TblAttendance.objects.filter(student_field=student)
    fee_qs = TblStudentFee.objects.filter(student_field=student)
    payment_qs = TblFeePayment.objects.select_related("student_fee_field__fee_structure_field").filter(student_fee_field__student_field=student)

    attendance_counts = attendance_qs.values("status").annotate(count=Count("attendance_id"))
    status_map = {row["status"]: row["count"] for row in attendance_counts}
    fee_totals = fee_qs.aggregate(total=Sum("total_amount"), paid=Sum("paid_amount"), pending=Sum("pending_amount"))

    recent_attendance = list(attendance_qs.order_by("-attendance_date")[:5])
    recent_payments = list(payment_qs.order_by("-payment_date", "-payment_id")[:5])
    for row in homework_qs[:5]:
        _render_homework_row(row)

    return render(request, "accounts/student_dashboard.html", {
        "student": student,
        "present_count": status_map.get("Present", 0),
        "absent_count": status_map.get("Absent", 0),
        "leave_count": status_map.get("Leave", 0),
        "fee_total": fee_totals.get("total") or 0,
        "fee_paid": fee_totals.get("paid") or 0,
        "fee_pending": fee_totals.get("pending") or 0,
        "recent_attendance": recent_attendance,
        "recent_payments": recent_payments,
        "recent_homework": homework_qs.order_by("-homework_field__created_at")[:5],
    })


@login_required
@role_required("Student")
def student_homework_list(request):
    student = _get_current_student(request)
    if not student:
        messages.error(request, "Student profile mapping is missing. Contact admin.")
        return redirect("login")

    search_q = (request.GET.get("q") or "").strip()
    qs = _student_homework_qs(student)
    _sync_homework_due_notifications(qs)
    if search_q:
        qs = qs.filter(
            models.Q(homework_field__title__icontains=search_q)
            | models.Q(homework_field__description__icontains=search_q)
            | models.Q(homework_field__class_field__class_name__icontains=search_q)
            | models.Q(homework_field__subject_field__subject_name__icontains=search_q)
            | models.Q(status__icontains=search_q)
        )

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    for row in page_obj:
        _render_homework_row(row)

    return render(request, "accounts/student_homework_list.html", {
        "student": student,
        "page_obj": page_obj,
        "search_q": search_q,
        "role_label": "Student",
    })


@login_required
@role_required("Parent")
def parent_homework_list(request):
    parent = _get_current_parent(request)
    if not parent:
        messages.error(request, "Parent profile mapping is missing. Contact admin.")
        return redirect("login")

    search_q = (request.GET.get("q") or "").strip()
    qs = _parent_homework_qs(parent)
    _sync_homework_due_notifications(qs)
    if search_q:
        qs = qs.filter(
            models.Q(homework_field__title__icontains=search_q)
            | models.Q(homework_field__description__icontains=search_q)
            | models.Q(student_field__first_name__icontains=search_q)
            | models.Q(student_field__last_name__icontains=search_q)
            | models.Q(homework_field__class_field__class_name__icontains=search_q)
            | models.Q(homework_field__subject_field__subject_name__icontains=search_q)
            | models.Q(status__icontains=search_q)
        )

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    for row in page_obj:
        _render_homework_row(row)

    return render(request, "accounts/student_homework_list.html", {
        "parent": parent,
        "page_obj": page_obj,
        "search_q": search_q,
        "role_label": "Parent",
    })


@login_required
@role_required("Student")
def student_homework_detail(request, pk):
    student = _get_current_student(request)
    if not student:
        messages.error(request, "Student profile mapping is missing. Contact admin.")
        return redirect("login")

    record = _homework_accessible_record("Student", student, pk)
    if not record:
        messages.error(request, "Homework not found.")
        return redirect("student_homework_list")

    _sync_homework_due_notifications([record])
    _render_homework_row(record)

    return render(request, "accounts/student_homework_detail.html", {
        "student": student,
        "record": record,
        "completion_form": HomeworkCompletionForm(),
        "completion_url_name": "student_homework_complete",
        "role_label": "Student",
    })


@login_required
@role_required("Parent")
def parent_homework_detail(request, pk):
    parent = _get_current_parent(request)
    if not parent:
        messages.error(request, "Parent profile mapping is missing. Contact admin.")
        return redirect("login")

    record = _homework_accessible_record("Parent", parent, pk)
    if not record:
        messages.error(request, "Homework not found.")
        return redirect("parent_homework_list")

    _sync_homework_due_notifications([record])
    _render_homework_row(record)

    return render(request, "accounts/student_homework_detail.html", {
        "parent": parent,
        "record": record,
        "completion_form": HomeworkCompletionForm(),
        "completion_url_name": "parent_homework_complete",
        "role_label": "Parent",
    })


@login_required
@role_required("Student")
def student_homework_complete(request, pk):
    student = _get_current_student(request)
    if not student:
        messages.error(request, "Student profile mapping is missing. Contact admin.")
        return redirect("login")

    record = _homework_accessible_record("Student", student, pk)
    if not record:
        messages.error(request, "Homework not found.")
        return redirect("student_homework_list")

    if request.method == "POST":
        form = HomeworkCompletionForm(request.POST)
        if form.is_valid():
            if _mark_homework_completed(record, "Student", form.cleaned_data.get("comment", "").strip()):
                messages.success(request, "Homework marked as completed.")
            else:
                messages.error(request, "Only the first completion is recorded.")
    return redirect("student_homework_detail", pk=pk)


@login_required
@role_required("Parent")
def parent_homework_complete(request, pk):
    parent = _get_current_parent(request)
    if not parent:
        messages.error(request, "Parent profile mapping is missing. Contact admin.")
        return redirect("login")

    record = _homework_accessible_record("Parent", parent, pk)
    if not record:
        messages.error(request, "Homework not found.")
        return redirect("parent_homework_list")

    if request.method == "POST":
        form = HomeworkCompletionForm(request.POST)
        if form.is_valid():
            if _mark_homework_completed(record, "Parent", form.cleaned_data.get("comment", "").strip()):
                messages.success(request, "Homework marked as completed.")
            else:
                messages.error(request, "Only the first completion is recorded.")
    return redirect("parent_homework_detail", pk=pk)


# ---------------------------------------------------------------------------
# User Management CRUD (Admin only)
# ---------------------------------------------------------------------------

@login_required
@role_required("Admin")
def user_list(request):
    add_form = UserForm(initial={"is_active": True})

    if request.method == "POST" and request.POST.get("action") == "add":
        add_form = UserForm(request.POST)
        if add_form.is_valid():
            add_form.save()
            messages.success(request, "User created successfully.")
            return redirect("user_list")

    search_q = request.GET.get("q", "").strip()
    qs = TblUser.objects.all().order_by("username")
    if search_q:
        filters = models.Q(username__icontains=search_q) | models.Q(role__icontains=search_q)
        if search_q.isdigit():
            filters = filters | models.Q(reference_id=int(search_q))
        qs = qs.filter(filters)

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "accounts/user_master.html",
        {
            "page_obj": page_obj,
            "search_q": search_q,
            "add_form": add_form,
        },
    )


@login_required
@role_required("Admin")
def user_edit(request, pk):
    obj = get_object_or_404(TblUser, pk=pk)
    if request.method == "POST":
        form = UserForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'User "{obj.username}" updated successfully.')
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)
    return redirect("user_list")


@login_required
@role_required("Admin")
def user_delete(request, pk):
    obj = get_object_or_404(TblUser, pk=pk)
    if request.method == "POST":
        username = obj.username
        obj.delete()
        messages.success(request, f'User "{username}" deleted successfully.')
    return redirect("user_list")


# ---------------------------------------------------------------------------
# Class Master CRUD (Admin only)
# ---------------------------------------------------------------------------

@login_required
@role_required("Admin")
def class_list(request):
    """List all classes with search & pagination. Also handles Add (POST)."""
    add_form = ClassForm()

    if request.method == "POST" and request.POST.get("action") == "add":
        add_form = ClassForm(request.POST)
        if add_form.is_valid():
            add_form.save()
            messages.success(request, "Class added successfully.")
            return redirect("class_list")
        # Fall through to re-render with errors

    search_q = request.GET.get("q", "").strip()
    qs = TblClass.objects.all()
    if search_q:
        qs = qs.filter(class_name__icontains=search_q)

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/class_master.html", {
        "page_obj": page_obj,
        "search_q": search_q,
        "add_form": add_form,
    })


@login_required
@role_required("Admin")
def class_edit(request, pk):
    """Handle Edit (POST only)."""
    obj = get_object_or_404(TblClass, pk=pk)
    if request.method == "POST":
        form = ClassForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Class "{obj.class_name}" updated successfully.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    return redirect("class_list")


@login_required
@role_required("Admin")
def class_delete(request, pk):
    """Handle Delete (POST only)."""
    obj = get_object_or_404(TblClass, pk=pk)
    if request.method == "POST":
        name = obj.class_name
        obj.delete()
        messages.success(request, f'Class "{name}" deleted successfully.')
    return redirect("class_list")


# ---------------------------------------------------------------------------
# Section Master CRUD (Admin only)
# ---------------------------------------------------------------------------

@login_required
@role_required("Admin")
def section_list(request):
    add_form = SectionForm()

    if request.method == "POST" and request.POST.get("action") == "add":
        add_form = SectionForm(request.POST)
        if add_form.is_valid():
            add_form.save()
            messages.success(request, "Section added successfully.")
            return redirect("section_list")

    search_q = request.GET.get("q", "").strip()
    filter_class = request.GET.get("class_id", "").strip()

    qs = TblSection.objects.select_related("class_field").all()
    if search_q:
        qs = qs.filter(section_name__icontains=search_q)
    if filter_class:
        qs = qs.filter(class_field__class_id=filter_class)

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/section_master.html", {
        "page_obj": page_obj,
        "search_q": search_q,
        "filter_class": filter_class,
        "add_form": add_form,
        "all_classes": TblClass.objects.all(),
    })


@login_required
@role_required("Admin")
def section_edit(request, pk):
    obj = get_object_or_404(TblSection, pk=pk)
    if request.method == "POST":
        form = SectionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Section updated successfully.")
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)
    return redirect("section_list")


@login_required
@role_required("Admin")
def section_delete(request, pk):
    obj = get_object_or_404(TblSection, pk=pk)
    if request.method == "POST":
        name = str(obj)
        obj.delete()
        messages.success(request, f'Section "{name}" deleted successfully.')
    return redirect("section_list")


# ---------------------------------------------------------------------------
# Subject Master CRUD (Admin only)
# ---------------------------------------------------------------------------

@login_required
@role_required("Admin")
def subject_list(request):
    add_form = SubjectForm()

    if request.method == "POST" and request.POST.get("action") == "add":
        add_form = SubjectForm(request.POST)
        if add_form.is_valid():
            add_form.save()
            messages.success(request, "Subject added successfully.")
            return redirect("subject_list")

    search_q = request.GET.get("q", "").strip()
    qs = TblSubject.objects.all()
    if search_q:
        qs = qs.filter(subject_name__icontains=search_q)

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/subject_master.html", {
        "page_obj": page_obj,
        "search_q": search_q,
        "add_form": add_form,
    })


@login_required
@role_required("Admin")
def subject_edit(request, pk):
    obj = get_object_or_404(TblSubject, pk=pk)
    if request.method == "POST":
        form = SubjectForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Subject "{obj.subject_name}" updated successfully.')
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)
    return redirect("subject_list")


@login_required
@role_required("Admin")
def subject_delete(request, pk):
    obj = get_object_or_404(TblSubject, pk=pk)
    if request.method == "POST":
        name = obj.subject_name
        obj.delete()
        messages.success(request, f'Subject "{name}" deleted successfully.')
    return redirect("subject_list")


# ---------------------------------------------------------------------------
# Parent Master CRUD (Admin only)
# ---------------------------------------------------------------------------

@login_required
@role_required("Admin")
def parent_list(request):
    add_form = ParentForm()

    if request.method == "POST" and request.POST.get("action") == "add":
        add_form = ParentForm(request.POST)
        if add_form.is_valid():
            add_form.save()
            messages.success(request, "Parent added successfully.")
            return redirect("parent_list")

    search_q = request.GET.get("q", "").strip()
    qs = TblParent.objects.all()
    if search_q:
        qs = qs.filter(
            models.Q(father_name__icontains=search_q) |
            models.Q(mother_name__icontains=search_q) |
            models.Q(mobile__icontains=search_q) |
            models.Q(email__icontains=search_q)
        )

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/parent_master.html", {
        "page_obj": page_obj,
        "search_q": search_q,
        "add_form": add_form,
    })


@login_required
@role_required("Admin")
def parent_edit(request, pk):
    obj = get_object_or_404(TblParent, pk=pk)
    if request.method == "POST":
        form = ParentForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Parent updated successfully.")
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)
    return redirect("parent_list")


@login_required
@role_required("Admin")
def parent_delete(request, pk):
    obj = get_object_or_404(TblParent, pk=pk)
    if request.method == "POST":
        name = str(obj)
        obj.delete()
        messages.success(request, f"Parent deleted successfully.")
    return redirect("parent_list")


# ---------------------------------------------------------------------------
# Teacher Master CRUD (Admin only)
# ---------------------------------------------------------------------------

@login_required
@role_required("Admin")
def teacher_list(request):
    add_form = TeacherForm()

    if request.method == "POST" and request.POST.get("action") == "add":
        add_form = TeacherForm(request.POST)
        if add_form.is_valid():
            add_form.save()
            messages.success(request, "Teacher added successfully.")
            return redirect("teacher_list")

    search_q = request.GET.get("q", "").strip()
    qs = TblTeacher.objects.all()
    if search_q:
        qs = qs.filter(
            models.Q(name__icontains=search_q) |
            models.Q(mobile__icontains=search_q) |
            models.Q(email__icontains=search_q)
        )

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/teacher_master.html", {
        "page_obj": page_obj,
        "search_q": search_q,
        "add_form": add_form,
    })


@login_required
@role_required("Admin")
def teacher_edit(request, pk):
    obj = get_object_or_404(TblTeacher, pk=pk)
    if request.method == "POST":
        form = TeacherForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Teacher "{obj.name}" updated successfully.')
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)
    return redirect("teacher_list")


@login_required
@role_required("Admin")
def teacher_delete(request, pk):
    obj = get_object_or_404(TblTeacher, pk=pk)
    if request.method == "POST":
        name = obj.name
        obj.delete()
        messages.success(request, f'Teacher "{name}" deleted successfully.')
    return redirect("teacher_list")


# ---------------------------------------------------------------------------
# Student Master CRUD (Admin only for now)
# ---------------------------------------------------------------------------

@login_required
@role_required("Admin")
def student_list(request):
    add_form = StudentForm()

    if request.method == "POST" and request.POST.get("action") == "add":
        add_form = StudentForm(request.POST)
        if add_form.is_valid():
            add_form.save()
            messages.success(request, "Student added successfully.")
            return redirect("student_list")

    search_q = request.GET.get("q", "").strip()
    qs = TblStudent.objects.select_related("class_field", "section_field", "parent_field").all()
    if search_q:
        qs = qs.filter(
            models.Q(first_name__icontains=search_q) |
            models.Q(last_name__icontains=search_q) |
            models.Q(admission_no__icontains=search_q) |
            models.Q(roll_no__icontains=search_q)
        )

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/student_master.html", {
        "page_obj": page_obj,
        "search_q": search_q,
        "add_form": add_form,
        "all_classes": TblClass.objects.all(),
        "all_sections": TblSection.objects.select_related("class_field").all(),
        "all_parents": TblParent.objects.all(),
    })


@login_required
@role_required("Admin")
def student_edit(request, pk):
    obj = get_object_or_404(TblStudent, pk=pk)
    if request.method == "POST":
        form = StudentForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Student "{obj.first_name} {obj.last_name}" updated successfully.')
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)
    return redirect("student_list")


@login_required
@role_required("Admin")
def student_delete(request, pk):
    obj = get_object_or_404(TblStudent, pk=pk)
    if request.method == "POST":
        name = f"{obj.first_name} {obj.last_name}"
        obj.delete()
        messages.success(request, f'Student "{name}" deleted successfully.')
    return redirect("student_list")


# ---------------------------------------------------------------------------
# Teacher Assignment CRUD (Admin only)
# ---------------------------------------------------------------------------

@login_required
@role_required("Admin")
def teacher_assignment_list(request):
    add_form = TeacherAssignmentForm()

    if request.method == "POST" and request.POST.get("action") == "add":
        add_form = TeacherAssignmentForm(request.POST)
        if add_form.is_valid():
            add_form.save()
            messages.success(request, "Assignment added successfully.")
            return redirect("teacher_assignment_list")

    search_q = request.GET.get("q", "").strip()
    qs = TblTeacherAssignment.objects.select_related(
        "teacher_field", "class_field", "section_field", "subject_field"
    ).all()
    if search_q:
        qs = qs.filter(
            models.Q(teacher_field__name__icontains=search_q) |
            models.Q(class_field__class_name__icontains=search_q) |
            models.Q(section_field__section_name__icontains=search_q) |
            models.Q(subject_field__subject_name__icontains=search_q)
        )

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/teacher_assignment_master.html", {
        "page_obj": page_obj,
        "search_q": search_q,
        "add_form": add_form,
        "all_teachers": TblTeacher.objects.all(),
        "all_classes": TblClass.objects.all(),
        "all_sections": TblSection.objects.select_related("class_field").all(),
        "all_subjects": TblSubject.objects.all(),
    })


@login_required
@role_required("Admin")
def teacher_assignment_edit(request, pk):
    obj = get_object_or_404(TblTeacherAssignment, pk=pk)
    if request.method == "POST":
        form = TeacherAssignmentForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Assignment updated successfully.")
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)
    return redirect("teacher_assignment_list")


@login_required
@role_required("Admin")
def teacher_assignment_delete(request, pk):
    obj = get_object_or_404(TblTeacherAssignment, pk=pk)
    if request.method == "POST":
        teacher_name = obj.teacher_field.name
        obj.delete()
        messages.success(request, f'Assignment for "{teacher_name}" deleted successfully.')
    return redirect("teacher_assignment_list")


# ---------------------------------------------------------------------------
# Fee Structure CRUD (Admin only)
# ---------------------------------------------------------------------------

@login_required
@role_required("Admin")
def fee_structure_list(request):
    add_form = FeeStructureForm()

    if request.method == "POST" and request.POST.get("action") == "add":
        add_form = FeeStructureForm(request.POST)
        if add_form.is_valid():
            add_form.save()
            messages.success(request, "Fee structure added successfully.")
            return redirect("fee_structure_list")

    search_q = request.GET.get("q", "").strip()
    qs = TblFeeStructure.objects.select_related("class_field").all()
    if search_q:
        qs = qs.filter(
            models.Q(class_field__class_name__icontains=search_q) |
            models.Q(academic_year__icontains=search_q)
        )

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/fee_structure_master.html", {
        "page_obj": page_obj,
        "search_q": search_q,
        "add_form": add_form,
        "all_classes": TblClass.objects.all(),
    })


@login_required
@role_required("Admin")
def fee_structure_edit(request, pk):
    obj = get_object_or_404(TblFeeStructure, pk=pk)
    if request.method == "POST":
        form = FeeStructureForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Fee structure updated successfully.")
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)
    return redirect("fee_structure_list")


@login_required
@role_required("Admin")
def fee_structure_delete(request, pk):
    obj = get_object_or_404(TblFeeStructure, pk=pk)
    if request.method == "POST":
        label = f"{obj.class_field.class_name} – {obj.academic_year}"
        obj.delete()
        messages.success(request, f'Fee structure "{label}" deleted successfully.')
    return redirect("fee_structure_list")


# ---------------------------------------------------------------------------
# Student Fee CRUD (Admin only)
# ---------------------------------------------------------------------------

_COMMON_FILE_EXTS = ("pdf", "jpg", "jpeg", "png", "gif", "webp", "doc", "docx", "xls", "xlsx", "zip")


def _extract_file_from_ref(transaction_ref):
    """Extract stored filename from transaction_ref that contains a FILE:{name} marker."""
    if not transaction_ref:
        return None
    m = re.search(r"FILE:(\S+)", transaction_ref)
    return m.group(1) if m else None


def _make_fee_ref_filename(student_fee_id, fee_structure_id, original_name):
    """Build: {student_fee_id}_{fee_structure_id}_{YYYYMMDD_HHMMSS}_{safe_name}.{ext}"""
    if "." in original_name:
        base, ext = original_name.rsplit(".", 1)
        ext_suffix = f".{ext.lower()}"
    else:
        base, ext_suffix = original_name, ""
    safe_base = re.sub(r"[^a-zA-Z0-9_-]", "_", base)[:20]
    dt = timezone.now().strftime("%Y%m%d_%H%M%S")
    return f"{student_fee_id}_{fee_structure_id}_{dt}_{safe_base}{ext_suffix}"


@login_required
@role_required("Admin")
def student_fee_list(request):
    add_form = StudentFeeForm()

    if request.method == "POST" and request.POST.get("action") == "add":
        add_form = StudentFeeForm(request.POST, request.FILES)
        if add_form.is_valid():
            student_fee = add_form.save()
            paid_amount = add_form.cleaned_data.get("paid_amount")
            payment_date = add_form.cleaned_data.get("payment_date")
            payment_month = add_form.cleaned_data.get("payment_month")
            payment_method = add_form.cleaned_data.get("payment_method")
            transaction_ref = add_form.cleaned_data.get("transaction_ref")
            payment_reference_file = add_form.cleaned_data.get("payment_reference_file")

            if payment_reference_file:
                filename = _make_fee_ref_filename(
                    student_fee.student_fee_id,
                    student_fee.fee_structure_field.fee_structure_id,
                    payment_reference_file.name,
                )
                ref_path = f"fee_payment_refs/{filename}"
                default_storage.save(ref_path, payment_reference_file)
                file_note = f"FILE:{filename}"
                transaction_ref = (
                    f"{transaction_ref[:28]} | {file_note}" if transaction_ref else file_note
                )[:100]

            if paid_amount and paid_amount > 0:
                # Include payment month in transaction_ref for monthly tracking
                month_note = ""
                if payment_month:
                    month_note = f"Month:{payment_month.strftime('%Y-%m')} | "
                final_ref = f"{month_note}{transaction_ref}" if transaction_ref else month_note
                
                TblFeePayment.objects.create(
                    student_fee_field=student_fee,
                    amount=paid_amount,
                    payment_date=payment_date or timezone.now().date(),
                    payment_method=payment_method or None,
                    transaction_ref=final_ref or None,
                )
            messages.success(request, "Student fee record added successfully.")
            return redirect("student_fee_list")

    search_q = request.GET.get("q", "").strip()
    qs = TblStudentFee.objects.select_related(
        "student_field", "fee_structure_field"
    ).prefetch_related(
        Prefetch(
            "payments",
            queryset=TblFeePayment.objects.order_by("-payment_date", "-payment_id"),
            to_attr="all_payments",
        )
    ).all()
    if search_q:
        qs = qs.filter(
            models.Q(student_field__first_name__icontains=search_q) |
            models.Q(student_field__last_name__icontains=search_q) |
            models.Q(student_field__admission_no__icontains=search_q) |
            models.Q(fee_structure_field__academic_year__icontains=search_q)
        )

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Annotate each fee row with the stored reference file path/name.
    # New files: filename stored in transaction_ref as FILE:{name}. Old files: sf_{id}.* on disk.
    for fee in page_obj.object_list:
        fee.ref_file_path = None
        fee.ref_file_name = None
        last_payment = fee.all_payments[0] if fee.all_payments else None
        filename = _extract_file_from_ref(last_payment.transaction_ref if last_payment else None)
        if filename:
            candidate = f"fee_payment_refs/{filename}"
            if default_storage.exists(candidate):
                fee.ref_file_path = candidate
                fee.ref_file_name = filename
        if not fee.ref_file_path:
            for ext in _COMMON_FILE_EXTS:
                candidate = f"fee_payment_refs/sf_{fee.student_fee_id}.{ext}"
                if default_storage.exists(candidate):
                    fee.ref_file_path = candidate
                    fee.ref_file_name = f"sf_{fee.student_fee_id}.{ext}"
                    break

    return render(request, "accounts/student_fee_master.html", {
        "page_obj": page_obj,
        "search_q": search_q,
        "add_form": add_form,
        "all_students": TblStudent.objects.select_related("class_field", "section_field"),
        "all_fee_structures": TblFeeStructure.objects.select_related("class_field"),
    })


@login_required
@role_required("Admin")
def student_fee_edit(request, pk):
    obj = get_object_or_404(TblStudentFee, pk=pk)
    if request.method == "POST":
        form = StudentFeeForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()

            # Update payment details on the last linked payment record.
            last_payment = obj.payments.order_by("-payment_date", "-payment_id").first()
            if last_payment:
                payment_date = form.cleaned_data.get("payment_date")
                payment_month = form.cleaned_data.get("payment_month")
                payment_method = form.cleaned_data.get("payment_method")
                clean_ref = (form.cleaned_data.get("transaction_ref") or "").strip()
                new_file = form.cleaned_data.get("payment_reference_file")

                if new_file:
                    # Delete old file: check new naming in transaction_ref, then legacy sf_{id}.*
                    old_filename = _extract_file_from_ref(last_payment.transaction_ref)
                    if old_filename:
                        old_path = f"fee_payment_refs/{old_filename}"
                        if default_storage.exists(old_path):
                            default_storage.delete(old_path)
                    else:
                        for ext in _COMMON_FILE_EXTS:
                            old_path = f"fee_payment_refs/sf_{obj.student_fee_id}.{ext}"
                            if default_storage.exists(old_path):
                                default_storage.delete(old_path)
                    filename = _make_fee_ref_filename(
                        obj.student_fee_id,
                        obj.fee_structure_field.fee_structure_id,
                        new_file.name,
                    )
                    ref_path = f"fee_payment_refs/{filename}"
                    default_storage.save(ref_path, new_file)
                    file_note = f"FILE:{filename}"
                    new_transaction_ref = (
                        f"{clean_ref[:28]} | {file_note}" if clean_ref else file_note
                    )[:100]
                else:
                    # Keep existing file reference intact, update only user ref text.
                    old_filename = _extract_file_from_ref(last_payment.transaction_ref)
                    if old_filename:
                        file_note = f"FILE:{old_filename}"
                        new_transaction_ref = (
                            f"{clean_ref[:28]} | {file_note}" if clean_ref else file_note
                        )[:100]
                    else:
                        new_transaction_ref = clean_ref or None

                # Include payment month in transaction_ref for monthly tracking
                month_note = ""
                if payment_month:
                    month_note = f"Month:{payment_month.strftime('%Y-%m')} | "
                final_ref = f"{month_note}{new_transaction_ref}" if new_transaction_ref else month_note

                last_payment.transaction_ref = final_ref or None
                if payment_date:
                    last_payment.payment_date = payment_date
                if payment_method:
                    last_payment.payment_method = payment_method
                last_payment.save()

            messages.success(request, "Student fee record updated successfully.")
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)
    return redirect("student_fee_list")


@login_required
@role_required("Admin")
def student_fee_delete(request, pk):
    obj = get_object_or_404(TblStudentFee, pk=pk)
    if request.method == "POST":
        student_name = f"{obj.student_field.first_name} {obj.student_field.last_name}"
        obj.delete()
        messages.success(request, f'Fee record for "{student_name}" deleted successfully.')
    return redirect("student_fee_list")


# ---------------------------------------------------------------------------
# Fee Payment CRUD (Admin only) - COMMENTED OUT as requested
# ---------------------------------------------------------------------------
"""
@login_required
@role_required("Admin")
def fee_payment_list(request):
    add_form = FeePaymentForm()

    if request.method == "POST" and request.POST.get("action") == "add":
        add_form = FeePaymentForm(request.POST)
        if add_form.is_valid():
            add_form.save()
            messages.success(request, "Fee payment recorded successfully.")
            return redirect("fee_payment_list")

    search_q = request.GET.get("q", "").strip()
    qs = TblFeePayment.objects.select_related("student_fee_field__student_field").all()
    if search_q:
        qs = qs.filter(
            models.Q(student_fee_field__student_field__first_name__icontains=search_q) |
            models.Q(student_fee_field__student_field__last_name__icontains=search_q) |
            models.Q(transaction_ref__icontains=search_q)
        )

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/fee_payment_master.html", {
        "page_obj": page_obj,
        "search_q": search_q,
        "add_form": add_form,
        "all_student_fees": TblStudentFee.objects.select_related("student_field", "fee_structure_field"),
    })


@login_required
@role_required("Admin")
def fee_payment_edit(request, pk):
    obj = get_object_or_404(TblFeePayment, pk=pk)
    if request.method == "POST":
        form = FeePaymentForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Fee payment updated successfully.")
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)
    return redirect("fee_payment_list")


@login_required
@role_required("Admin")
def fee_payment_delete(request, pk):
    obj = get_object_or_404(TblFeePayment, pk=pk)
    if request.method == "POST":
        amount = obj.amount
        obj.delete()
        messages.success(request, f'Payment of ₹{amount} deleted successfully.')
    return redirect("fee_payment_list")
"""

@login_required
@role_required("Admin")
def get_student_pending_amount(request):
    """AJAX endpoint to fetch pending amount for a student given fee structure."""
    from decimal import Decimal
    student_id = request.GET.get("student_id")
    fee_structure_id = request.GET.get("fee_structure_id")

    if not student_id or not fee_structure_id:
        return JsonResponse({"error": "Missing parameters"}, status=400)

    try:
        student = TblStudent.objects.get(pk=student_id)
        fee_structure = TblFeeStructure.objects.get(pk=fee_structure_id)
    except (TblStudent.DoesNotExist, TblFeeStructure.DoesNotExist):
        return JsonResponse({"error": "Invalid student or fee structure"}, status=404)

    existing_records = TblStudentFee.objects.filter(
        student_field=student,
        fee_structure_field=fee_structure,
    )
    existing_paid = existing_records.aggregate(total=Sum("paid_amount"))["total"] or Decimal("0")
    total_fee = fee_structure.total_fee or Decimal("0")
    pending = total_fee - existing_paid
    is_fully_paid = pending <= 0

    return JsonResponse({
        "pending_amount": float(pending),
        "total_fee": float(total_fee),
        "existing_paid": float(existing_paid),
        "is_fully_paid": is_fully_paid,
    })


@login_required
@role_required("Admin")
def get_student_fee_structure(request):
    """AJAX endpoint to fetch fee structure for a student based on their class."""
    student_id = request.GET.get("student_id")
    
    if not student_id:
        return JsonResponse({"error": "Missing student_id"}, status=400)
    
    try:
        student = TblStudent.objects.get(pk=student_id)
    except TblStudent.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)
    
    # Get the latest fee structure for the student's class
    fee_structure = TblFeeStructure.objects.filter(
        class_field=student.class_field
    ).order_by("-academic_year").first()
    
    if not fee_structure:
        return JsonResponse({"error": "No fee structure found for this class"}, status=404)
    
    return JsonResponse({
        "fee_structure_id": fee_structure.fee_structure_id,
        "fee_structure_name": str(fee_structure),
        "total_fee": float(fee_structure.total_fee),
    })
