import json
import re
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from django.conf import settings
from django.urls import reverse


class CourseDataError(ValueError):
    pass


_LESSON_DIRECTORY = re.compile(r"lesson_(\d+)$")
_STEP_FILE = re.compile(r"(?P<lesson_id>\d+)_(?P<step_number>\d+)_[^/]+\.step$")
_STEPIK_STEP_URL = re.compile(r"/lesson/(?P<lesson_id>\d+)/step/(?P<step_number>\d+)/?$")
_LESSON_TITLES = {
    1: "Предисловие",
    2: "Введение. Общее определение математики",
    3: "Счёт и натуральные числа",
    4: "Сумма и разность",
    5: "Первый конец математики",
    6: "Новое начало. Целые числа",
    7: "Умножение и деление",
    8: "Второй конец математики",
    9: "Новое начало. Рациональные числа",
    10: "Степень и корень",
    11: "Логарифм. Число Эйлера",
    12: "Третий конец математики",
    13: "Послесловие",
}
_ALLOWED_TAGS = {
    "a", "br", "div", "em", "h2", "h3", "h4", "hr", "img", "li", "ol",
    "p", "span", "strong", "sub", "sup", "table", "tbody", "td", "th",
    "tr", "u", "ul",
}
_VOID_TAGS = {"br", "hr", "img"}
_DISCARDED_TAGS = {"iframe", "object", "script", "style", "svg"}


def _safe_url(value, *, image=False, local_step_links=None):
    if not image and local_step_links is not None:
        parsed = urlsplit(value.strip())
        if parsed.hostname and parsed.hostname.lower() in {"stepik.org", "www.stepik.org"}:
            match = _STEPIK_STEP_URL.fullmatch(parsed.path)
            if match:
                target = local_step_links.get(
                    (match.group("lesson_id"), int(match.group("step_number")))
                )
                if target:
                    return target

    parsed = urlsplit(value.strip())
    allowed_schemes = {"http", "https"} if image else {"http", "https", "mailto"}
    if parsed.scheme and parsed.scheme.lower() not in allowed_schemes:
        return None
    if parsed.netloc and parsed.scheme.lower() not in {"http", "https"}:
        return None
    if value.strip().startswith("//"):
        return None
    return value.strip()


class _CourseHTMLSanitizer(HTMLParser):
    def __init__(self, local_step_links=None):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.discard_depth = 0
        self.local_step_links = local_step_links

    def handle_starttag(self, tag, attrs):
        if self.discard_depth:
            if tag in _DISCARDED_TAGS:
                self.discard_depth += 1
            return
        if tag in _DISCARDED_TAGS:
            self.discard_depth = 1
            return
        if tag not in _ALLOWED_TAGS:
            return

        safe_attrs = []
        for name, value in attrs:
            if value is None:
                continue
            if tag == "a" and name == "href":
                value = _safe_url(value, local_step_links=self.local_step_links)
            elif tag == "img" and name == "src":
                value = _safe_url(value, image=True)
            elif tag == "img" and name in {"alt", "height", "name", "width"}:
                if name in {"height", "width"} and not value.isdigit():
                    continue
                if name == "name" and not re.fullmatch(r"[\w .+=-]+", value):
                    continue
            elif tag == "span" and name == "class":
                pass
            else:
                continue
            if value is not None:
                safe_attrs.append(f' {name}="{escape(value, quote=True)}"')

        if tag == "a":
            safe_attrs.append(' rel="noopener noreferrer"')
        self.parts.append(f"<{tag}{''.join(safe_attrs)}>")

    def handle_endtag(self, tag):
        if self.discard_depth:
            if tag in _DISCARDED_TAGS:
                self.discard_depth -= 1
            return
        if tag in _ALLOWED_TAGS and tag not in _VOID_TAGS:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.discard_depth:
            self.parts.append(escape(data))


def _sanitize_html(value, local_step_links=None):
    parser = _CourseHTMLSanitizer(local_step_links)
    parser.feed(value)
    parser.close()
    sanitized = "".join(parser.parts)
    return _normalize_multiline_display_math(sanitized)


_DISPLAY_MATH_RE = re.compile(r"\\\[([\s\S]*?)\\\]")
_ALIGNED_ENVIRONMENT_RE = re.compile(
    r"\\begin\{(?:aligned|align|gathered|gather|array|split)\}"
)


def _normalize_multiline_display_math(value):
    def normalize_match(match):
        body = match.group(1)
        if (
            "\\\\" not in body
            or _ALIGNED_ENVIRONMENT_RE.search(body)
        ):
            return match.group(0)
        return rf"\[\begin{{gathered}}{body}\end{{gathered}}\]"

    return _DISPLAY_MATH_RE.sub(normalize_match, value)


def course_root():
    configured_root = getattr(settings, "ALGEBRA_COURSE_ROOT", None)
    if configured_root is not None:
        return Path(configured_root)
    return Path(settings.BASE_DIR).parent / "algebra_course"


def _read_step(filepath, local_step_links):
    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CourseDataError(f"Unable to read course step {filepath}: {exc}") from exc

    if not isinstance(data, dict) or not isinstance(data.get("block"), dict):
        raise CourseDataError(f"Course step {filepath} must contain a block object.")

    block = data["block"]
    step_type = block.get("name")
    text = block.get("text", "")
    source = block.get("source", {})
    if not isinstance(step_type, str) or not step_type:
        raise CourseDataError(f"Course step {filepath} has no valid block name.")
    if not isinstance(text, str) or not isinstance(source, dict):
        raise CourseDataError(f"Course step {filepath} has invalid block content.")

    if step_type == "fill-blanks":
        components = source.get("components", [])
        if isinstance(components, list):
            for component in components:
                if (
                    isinstance(component, dict)
                    and component.get("type") == "text"
                    and isinstance(component.get("text"), str)
                ):
                    component["text"] = _sanitize_html(component["text"], local_step_links)

    return {
        "id": str(data.get("id", filepath.stem)),
        "type": step_type,
        "content": _sanitize_html(text, local_step_links),
        "source": source,
        "feedback_correct": data.get("feedback_correct") or "",
        "feedback_wrong": data.get("feedback_wrong") or "",
        "has_review": bool(data.get("has_review", False)),
        "is_deprecated": bool(block.get("is_deprecated", False)),
        "filename": filepath.name,
    }


def load_lessons(root=None):
    root = Path(root) if root is not None else course_root()
    if not root.is_dir():
        raise CourseDataError(f"Course directory does not exist: {root}")

    lesson_directories = []
    for path in root.iterdir():
        match = _LESSON_DIRECTORY.fullmatch(path.name)
        if path.is_dir() and match:
            lesson_directories.append((int(match.group(1)), path))
    lesson_directories.sort(key=lambda item: item[0])

    if not lesson_directories:
        raise CourseDataError(f"No lesson directories found in {root}")

    local_step_links = {}
    lesson_files = []
    for lesson_number, directory in lesson_directories:
        step_files = []
        for filepath in directory.glob("*.step"):
            match = _STEP_FILE.fullmatch(filepath.name)
            if not match:
                raise CourseDataError(f"Unexpected step filename: {filepath}")
            step_files.append((int(match.group("step_number")), filepath, match.group("lesson_id")))
        step_files.sort(key=lambda item: (item[0], item[1].name))

        source_lesson_ids = {source_lesson_id for _, _, source_lesson_id in step_files}
        if len(source_lesson_ids) > 1:
            raise CourseDataError(f"Lesson directory {directory} contains multiple source lesson IDs.")
        if source_lesson_ids:
            source_lesson_id = source_lesson_ids.pop()
            for position, (source_step_number, _, _) in enumerate(step_files, start=1):
                local_step_links[(source_lesson_id, source_step_number)] = reverse(
                    "course_management:step_detail",
                    args=(lesson_number, position),
                )

        lesson_files.append((lesson_number, step_files))

    lessons = []
    for lesson_number, step_files in lesson_files:
        steps = []
        for position, (order, filepath, _) in enumerate(step_files, start=1):
            step = _read_step(filepath, local_step_links)
            step.update({"order": order, "position": position})
            steps.append(step)

        lessons.append({
            "number": lesson_number,
            "title": _LESSON_TITLES.get(lesson_number, f"Урок {lesson_number}"),
            "steps": steps,
        })

    return lessons
