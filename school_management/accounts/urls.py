from django.urls import path

from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("teacher/dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
    path("teacher/assignments/", views.teacher_my_assignments, name="teacher_my_assignments"),
    path("teacher/students/", views.teacher_my_students, name="teacher_my_students"),
    path("teacher/attendance/", views.teacher_attendance_manage, name="teacher_attendance_manage"),
    path("teacher/attendance/history/", views.teacher_attendance_history, name="teacher_attendance_history"),
    path("teacher/profile/", views.teacher_profile, name="teacher_profile"),
    path("parent/dashboard/", views.parent_dashboard, name="parent_dashboard"),
    path("parent/my-child/", views.parent_my_child, name="parent_my_child"),
    path("parent/attendance/", views.parent_attendance, name="parent_attendance"),
    path("parent/fee-status/", views.parent_fee_status, name="parent_fee_status"),
    path("parent/payment-history/", views.parent_payment_history, name="parent_payment_history"),
    path("parent/profile/", views.parent_profile, name="parent_profile"),
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("student/profile/", views.student_profile, name="student_profile"),
    path("student/attendance/", views.student_attendance, name="student_attendance"),
    path("student/fee-status/", views.student_fee_status, name="student_fee_status"),
    path("student/receipts/", views.student_receipts, name="student_receipts"),
    path("teacher/homework/", views.teacher_homework_dashboard, name="teacher_homework_dashboard"),
    path("teacher/homework/list/", views.teacher_homework_list, name="teacher_homework_list"),
    path("teacher/homework/create/", views.teacher_homework_create, name="teacher_homework_create"),
    path("homework/create/", views.teacher_homework_create),
    path("teacher/homework/<int:pk>/edit/", views.teacher_homework_edit, name="teacher_homework_edit"),
    path("teacher/homework/<int:pk>/delete/", views.teacher_homework_delete, name="teacher_homework_delete"),
    path("teacher/homework/<int:pk>/report/", views.teacher_homework_report, name="teacher_homework_report"),
    path("student/homework/", views.student_homework_list, name="student_homework_list"),
    path("student/homework/<int:pk>/", views.student_homework_detail, name="student_homework_detail"),
    path("student/homework/<int:pk>/complete/", views.student_homework_complete, name="student_homework_complete"),
    path("parent/homework/", views.parent_homework_list, name="parent_homework_list"),
    path("parent/homework/<int:pk>/", views.parent_homework_detail, name="parent_homework_detail"),
    path("parent/homework/<int:pk>/complete/", views.parent_homework_complete, name="parent_homework_complete"),
    # User Management
    path("admin/users/", views.user_list, name="user_list"),
    path("admin/users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("admin/users/<int:pk>/delete/", views.user_delete, name="user_delete"),
    # Class Master
    path("admin/classes/", views.class_list, name="class_list"),
    path("admin/classes/<int:pk>/edit/", views.class_edit, name="class_edit"),
    path("admin/classes/<int:pk>/delete/", views.class_delete, name="class_delete"),
    # Section Master
    path("admin/sections/", views.section_list, name="section_list"),
    path("admin/sections/<int:pk>/edit/", views.section_edit, name="section_edit"),
    path("admin/sections/<int:pk>/delete/", views.section_delete, name="section_delete"),
    # Subject Master
    path("admin/subjects/", views.subject_list, name="subject_list"),
    path("admin/subjects/<int:pk>/edit/", views.subject_edit, name="subject_edit"),
    path("admin/subjects/<int:pk>/delete/", views.subject_delete, name="subject_delete"),
    # Parent Master
    path("admin/parents/", views.parent_list, name="parent_list"),
    path("admin/parents/<int:pk>/edit/", views.parent_edit, name="parent_edit"),
    path("admin/parents/<int:pk>/delete/", views.parent_delete, name="parent_delete"),
    # Teacher Master
    path("admin/teachers/", views.teacher_list, name="teacher_list"),
    path("admin/teachers/<int:pk>/edit/", views.teacher_edit, name="teacher_edit"),
    path("admin/teachers/<int:pk>/delete/", views.teacher_delete, name="teacher_delete"),
    # Student Master
    path("admin/students/", views.student_list, name="student_list"),
    path("admin/students/<int:pk>/edit/", views.student_edit, name="student_edit"),
    path("admin/students/<int:pk>/delete/", views.student_delete, name="student_delete"),
    # Teacher Assignment
    path("admin/assignments/", views.teacher_assignment_list, name="teacher_assignment_list"),
    path("admin/assignments/<int:pk>/edit/", views.teacher_assignment_edit, name="teacher_assignment_edit"),
    path("admin/assignments/<int:pk>/delete/", views.teacher_assignment_delete, name="teacher_assignment_delete"),
    # Fee Structure
    path("admin/fee-structures/", views.fee_structure_list, name="fee_structure_list"),
    path("admin/fee-structures/<int:pk>/edit/", views.fee_structure_edit, name="fee_structure_edit"),
    path("admin/fee-structures/<int:pk>/delete/", views.fee_structure_delete, name="fee_structure_delete"),
    # Student Fee
    path("admin/student-fees/", views.student_fee_list, name="student_fee_list"),
    path("admin/student-fees/<int:pk>/edit/", views.student_fee_edit, name="student_fee_edit"),
    path("admin/student-fees/<int:pk>/delete/", views.student_fee_delete, name="student_fee_delete"),
    # Fee Payment (Commented out as payments are managed via StudentFeeForm)
    # path("admin/fee-payments/", views.fee_payment_list, name="fee_payment_list"),
    # path("admin/fee-payments/<int:pk>/edit/", views.fee_payment_edit, name="fee_payment_edit"),
    # path("admin/fee-payments/<int:pk>/delete/", views.fee_payment_delete, name="fee_payment_delete"),

    # API Endpoints
    path("api/student-pending-amount/", views.get_student_pending_amount, name="get_student_pending_amount"),
    path("api/student-fee-structure/", views.get_student_fee_structure, name="get_student_fee_structure"),
]
