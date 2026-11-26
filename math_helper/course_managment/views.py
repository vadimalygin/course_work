import random
import re
from decimal import Decimal, InvalidOperation

from django.http import Http404
from django.shortcuts import render

from .course_data import CourseDataError, load_lessons
from .grading import check_answer, sorting_expected_indexes


def _ordered_options(request, session_key, values, correct_order=None):
    order = request.session.get(session_key)
    if not isinstance(order, list) or sorted(order) != list(range(len(values))):
        order = list(range(len(values)))
        random.shuffle(order)
        if len(order) > 1 and order == correct_order:
            order = order[1:] + order[:1]
        request.session[session_key] = order
    return [{"value": values[index]} for index in order]


def _apply_submitted_order(options, submitted_values):
    remaining = list(options)
    ordered = []
    for value in submitted_values:
        for index, option in enumerate(remaining):
            if option["value"] == value:
                ordered.append(remaining.pop(index))
                break
    return ordered + remaining


def course_index(request):
    lessons = load_lessons()
    return render(request, "course_management/course_index.html", {
        "course_title": "Пособие по алгебре",
        "lessons": lessons,
        "step_count": sum(len(lesson["steps"]) for lesson in lessons),
    })


def lesson_detail_view(request, lesson_number):
    lessons = load_lessons()
    lesson = next((item for item in lessons if item["number"] == lesson_number), None)
    if lesson is None:
        raise Http404("Урок не найден")
    return render(request, "course_management/lesson_detail.html", {
        "course_title": "Пособие по алгебре",
        "lessons": lessons,
        "lesson": lesson,
    })


def _random_task_prompt(step, request, lesson_number, step_number):
    template = step["source"].get("task")
    if not isinstance(template, str):
        return None

    ranges = step["source"].get("ranges")
    if not isinstance(ranges, list) or not ranges:
        raise CourseDataError(f"Random task {step['id']} has no valid ranges.")

    session_key = f"algebra_random_task_{lesson_number}_{step_number}"
    values = request.session.get(session_key)
    if not isinstance(values, dict):
        values = {}
        for item in ranges:
            if not isinstance(item, dict):
                raise CourseDataError(f"Random task {step['id']} has an invalid range.")
            variable = item.get("variable")
            if not isinstance(variable, str) or not re.fullmatch(r"[A-Za-z]\w*", variable):
                raise CourseDataError(f"Random task {step['id']} has an invalid variable.")
            try:
                start = Decimal(item["num_from"])
                end = Decimal(item["num_to"])
                increment = Decimal(item["num_step"])
            except (KeyError, InvalidOperation) as exc:
                raise CourseDataError(f"Random task {step['id']} has invalid numeric ranges.") from exc
            if increment <= 0 or end < start:
                raise CourseDataError(f"Random task {step['id']} has an invalid range.")

            count = int((end - start) // increment) + 1
            value = start + increment * random.randrange(count)
            values[variable] = format(value.normalize(), "f")
        request.session[session_key] = values

    prompt = template
    for item in ranges:
        variable = item["variable"]
        value = values.get(variable)
        if not isinstance(value, str):
            raise CourseDataError(f"Random task {step['id']} is missing a generated value.")
        prompt = prompt.replace("\\" + variable, value)
    return prompt


def step_detail_view(request, lesson_number, step_number):
    lessons = load_lessons()
    lesson = next((item for item in lessons if item["number"] == lesson_number), None)
    if lesson is None:
        raise Http404("Урок не найден")
    if step_number < 1 or step_number > len(lesson["steps"]):
        raise Http404("Шаг не найден")

    step = lesson["steps"][step_number - 1]
    all_steps = [
        (item["number"], current_step["position"])
        for item in lessons
        for current_step in item["steps"]
    ]
    current_index = all_steps.index((lesson_number, step_number))
    previous_step = all_steps[current_index - 1] if current_index > 0 else None
    next_step = all_steps[current_index + 1] if current_index + 1 < len(all_steps) else None

    submission_message = None
    submission_correct = None
    if request.method == "POST":
        submission_correct = check_answer(step, request.POST)
        if submission_correct is None:
            submission_message = "Ответ отправлен. Автоматическая проверка для этого шага недоступна."
        elif submission_correct:
            submission_message = step["feedback_correct"] or "Верно!"
        else:
            submission_message = step["feedback_wrong"] or "Попробуйте ещё раз."

    matching_options = []
    sorting_options = []
    if step["type"] == "matching":
        pairs = step["source"].get("pairs")
        if not isinstance(pairs, list):
            raise CourseDataError(f"Matching step {step['id']} has no valid pairs.")
        values = [pair.get("second") for pair in pairs if isinstance(pair, dict)]
        if len(values) != len(pairs) or any(not isinstance(value, str) for value in values):
            raise CourseDataError(f"Matching step {step['id']} has invalid pairs.")
        matching_options = _ordered_options(
            request,
            f"algebra_matching_order_{lesson_number}_{step_number}",
            values,
            list(range(len(values))),
        )
        if request.method == "POST":
            matching_options = _apply_submitted_order(
                matching_options,
                request.POST.getlist("answers"),
            )
    elif step["type"] == "sorting":
        source_options = step["source"].get("options")
        if not isinstance(source_options, list):
            raise CourseDataError(f"Sorting step {step['id']} has no valid options.")
        values = [
            option.get("text") if isinstance(option, dict) else None
            for option in source_options
        ]
        if any(not isinstance(value, str) for value in values):
            raise CourseDataError(f"Sorting step {step['id']} has invalid options.")
        sorting_options = _ordered_options(
            request,
            f"algebra_sorting_order_{lesson_number}_{step_number}",
            values,
            sorting_expected_indexes(step),
        )
        if request.method == "POST":
            sorting_options = _apply_submitted_order(
                sorting_options,
                request.POST.getlist("answers"),
            )

    return render(request, "course_management/step_detail.html", {
        "course_title": "Пособие по алгебре",
        "lessons": lessons,
        "lesson": lesson,
        "step": step,
        "progress_percent": round(step_number / len(lesson["steps"]) * 100),
        "previous_step": previous_step,
        "next_step": next_step,
        "submission_message": submission_message,
        "submission_correct": submission_correct,
        "submitted_answer": request.POST.get("answer", ""),
        "submitted_answers": request.POST.getlist("answers"),
        "matching_options": matching_options,
        "sorting_options": sorting_options,
        "random_task_prompt": (
            _random_task_prompt(step, request, lesson_number, step_number)
            if step["type"] == "random-tasks"
            else None
        ),
    })
