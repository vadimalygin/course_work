import re
from decimal import Decimal, InvalidOperation

from .course_data import CourseDataError


def _required_list(value, field, step):
    if not isinstance(value, list):
        raise CourseDataError(f"Step {step['id']} is missing its {field} list.")
    return value


def _normalize_answer(value):
    return re.sub(r"\s+", "", value).replace(",", ".").casefold()


def _decimal(value):
    try:
        return Decimal(value.strip().replace(",", "."))
    except (AttributeError, InvalidOperation):
        return None


def _grade_choice(step, form_data):
    options = _required_list(step["source"].get("options"), "options", step)
    if step["source"].get("is_always_correct"):
        return True

    if step["source"].get("is_multiple_choice"):
        correct_options = set()
        for index, option in enumerate(options):
            if not isinstance(option, dict) or not isinstance(option.get("is_correct"), bool):
                raise CourseDataError(f"Step {step['id']} has an invalid choice answer key.")
            if option["is_correct"]:
                correct_options.add(str(index))
        if not correct_options:
            return None

        selected_options = form_data.getlist("answers")
        if any(not value.isdigit() or int(value) >= len(options) for value in selected_options):
            return False
        return set(selected_options) == correct_options

    try:
        selected = int(form_data.get("answer", ""))
    except (TypeError, ValueError):
        return False
    if selected < 0 or selected >= len(options):
        return False
    if not isinstance(options[selected], dict) or not isinstance(options[selected].get("is_correct"), bool):
        raise CourseDataError(f"Step {step['id']} has an invalid choice answer key.")
    return options[selected]["is_correct"]


def _grade_fill_blanks(step, form_data):
    components = _required_list(step["source"].get("components"), "components", step)
    fields = [component for component in components if isinstance(component, dict) and component.get("type") == "input"]
    if not fields:
        raise CourseDataError(f"Step {step['id']} has no fill-in answer fields.")
    answers = form_data.getlist("answers")
    if len(answers) != len(fields):
        return False

    case_sensitive = bool(step["source"].get("is_case_sensitive", False))
    for answer, field in zip(answers, fields):
        options = _required_list(field.get("options"), "fill-in options", step)
        accepted = [
            option.get("text")
            for option in options
            if isinstance(option, dict) and option.get("is_correct") is True
        ]
        if not accepted:
            raise CourseDataError(f"Step {step['id']} has a fill-in field without correct answers.")
        if case_sensitive:
            if answer not in accepted:
                return False
        elif answer.strip().casefold() not in {value.strip().casefold() for value in accepted if isinstance(value, str)}:
            return False
    return True


def _grade_matching(step, form_data):
    pairs = _required_list(step["source"].get("pairs"), "pairs", step)
    answers = form_data.getlist("answers")
    if len(answers) != len(pairs):
        return False
    for pair, answer in zip(pairs, answers):
        if not isinstance(pair, dict) or not isinstance(pair.get("second"), str):
            raise CourseDataError(f"Step {step['id']} has an invalid matching answer key.")
        if answer != pair["second"]:
            return False
    return True


def sorting_expected_indexes(step):
    options = _required_list(step["source"].get("options"), "options", step)
    text = step["content"].casefold()
    if "убыва" in text or "descending" in text:
        reverse = True
    elif "возраста" in text or "ascending" in text:
        reverse = False
    else:
        return None

    values = [option.get("text") if isinstance(option, dict) else None for option in options]
    numbers = [_decimal(value) for value in values]
    if any(not isinstance(value, str) for value in values) or any(number is None for number in numbers):
        return None
    return sorted(range(len(values)), key=numbers.__getitem__, reverse=reverse)


def _grade_sorting(step, form_data):
    options = _required_list(step["source"].get("options"), "options", step)
    expected_indexes = sorting_expected_indexes(step)
    if expected_indexes is None:
        return None

    values = [option["text"] for option in options]
    answers = form_data.getlist("answers")
    if len(answers) != len(values):
        return False
    expected_order = [values[index] for index in expected_indexes]
    return answers == expected_order


def _grade_math(step, form_data):
    expected = step["source"].get("answer")
    if not isinstance(expected, str):
        raise CourseDataError(f"Step {step['id']} has no valid math answer.")
    return _normalize_answer(form_data.get("answer", "")) == _normalize_answer(expected)


def _grade_number(step, form_data):
    options = _required_list(step["source"].get("options"), "options", step)
    answer = _decimal(form_data.get("answer", ""))
    if answer is None:
        return False
    for option in options:
        if not isinstance(option, dict) or not isinstance(option.get("answer"), str):
            raise CourseDataError(f"Step {step['id']} has an invalid number answer key.")
        expected = _decimal(option["answer"])
        tolerance = _decimal(option.get("max_error", "0"))
        if expected is None or tolerance is None or tolerance < 0:
            raise CourseDataError(f"Step {step['id']} has invalid number grading data.")
        if abs(answer - expected) <= tolerance:
            return True
    return False


def check_answer(step, form_data):
    graders = {
        "choice": _grade_choice,
        "fill-blanks": _grade_fill_blanks,
        "matching": _grade_matching,
        "sorting": _grade_sorting,
        "math": _grade_math,
        "number": _grade_number,
    }
    grader = graders.get(step["type"])
    return grader(step, form_data) if grader else None
