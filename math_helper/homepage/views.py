from django.shortcuts import render

from course_management.course_data import load_lessons


def homepage(request):
    lessons = load_lessons()
    context = {
        "lesson_count": len(lessons),
        "step_count": sum(len(lesson["steps"]) for lesson in lessons),
        'features': [],
    }
    return render(request, 'homepage/homepage.html', context)


def about(request):
    lessons = load_lessons()
    return render(request, 'homepage/about.html', {
        "lesson_count": len(lessons),
        "step_count": sum(len(lesson["steps"]) for lesson in lessons),
    })


def courses(request):
    lessons = load_lessons()
    courses = [
        {
            "id": 1,
            "title": "Пособие по алгебре",
            "description": (
                "Последовательно разберите числовые множества, арифметические операции "
                "и другие основные темы школьной алгебры."
            ),
            "lesson_count": len(lessons),
            "step_count": sum(len(lesson["steps"]) for lesson in lessons),
            "level": "Средний уровень",
        },
    ]
    return render(request, 'homepage/courses.html', {'courses': courses})

