from .views import get_user_role

MENU_BY_ROLE = {
    "Admin": [
        {"label": "Dashboard", "url_name": "admin_dashboard", "icon": "bi-speedometer2"},
        {"label": "Students", "url_name": "student_list", "icon": "bi-people-fill"},
        {"label": "Teachers", "url_name": "teacher_list", "icon": "bi-person-badge-fill"},
        {"label": "Parents", "url_name": "parent_list", "icon": "bi-person-heart"},
        {"label": "Classes", "url_name": "class_list", "icon": "bi-building-fill"},
        {"label": "Sections", "url_name": "section_list", "icon": "bi-diagram-3-fill"},
        {"label": "Subjects", "url_name": "subject_list", "icon": "bi-journal-bookmark-fill"},
        {"label": "Assignments", "url_name": "teacher_assignment_list", "icon": "bi-diagram-2-fill"},
        {"label": "Attendance", "url_name": "admin_dashboard", "icon": "bi-calendar-check-fill"},
        {
            "label": "Fees",
            "icon": "bi-cash-coin",
            "children": [
                {"label": "Structure", "url_name": "fee_structure_list"},
                {"label": "Student Fees", "url_name": "student_fee_list"},
                # {"label": "Payments", "url_name": "fee_payment_list"},
            ],
        },
        {"label": "Reports", "url_name": "admin_dashboard", "icon": "bi-bar-chart-fill"},
        {"label": "Users", "url_name": "user_list", "icon": "bi-gear-fill"},
    ],
    "Teacher": [
        {"label": "Dashboard", "url_name": "teacher_dashboard", "icon": "bi-speedometer2"},
        {"label": "Homework", "url_name": "teacher_homework_dashboard", "icon": "bi-journal-text"},
        {"label": "My Class", "url_name": "teacher_my_assignments", "icon": "bi-journal-check"},
        {"label": "My Students", "url_name": "teacher_my_students", "icon": "bi-people"},
        {
            "label": "Attendance",
            "icon": "bi-check2-square",
            "children": [
                {"label": "Mark Attendance", "url_name": "teacher_attendance_manage"},
                {"label": "History", "url_name": "teacher_attendance_history"},
            ],
        },
        {"label": "Profile", "url_name": "teacher_profile", "icon": "bi-person-circle"},
    ],
    "Parent": [
        {"label": "Dashboard", "url_name": "parent_dashboard", "icon": "bi-speedometer2"},
        {"label": "Homework", "url_name": "parent_homework_list", "icon": "bi-journal-text"},
        {"label": "My Child", "url_name": "parent_my_child", "icon": "bi-person-heart"},
        {"label": "Attendance", "url_name": "parent_attendance", "icon": "bi-calendar-check"},
        {"label": "Fee Status", "url_name": "parent_fee_status", "icon": "bi-cash-coin"},
        {"label": "Payment History", "url_name": "parent_payment_history", "icon": "bi-receipt"},
        {"label": "Profile", "url_name": "parent_profile", "icon": "bi-person-circle"},
    ],
    "Student": [
        {"label": "Dashboard", "url_name": "student_dashboard", "icon": "bi-speedometer2"},
        {"label": "Homework", "url_name": "student_homework_list", "icon": "bi-journal-text"},
        {"label": "My Profile", "url_name": "student_profile", "icon": "bi-person-vcard"},
        {"label": "Attendance", "url_name": "student_attendance", "icon": "bi-calendar-check"},
    ],
}


def role_menu(request):
    if not request.user.is_authenticated:
        return {
            "current_role": None,
            "sidebar_menu": [],
        }

    role = get_user_role(request.user)
    return {
        "current_role": role,
        "sidebar_menu": MENU_BY_ROLE.get(role, []),
    }
