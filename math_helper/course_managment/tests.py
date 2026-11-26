import re
import tempfile
from pathlib import Path

from django.http import QueryDict
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .course_data import CourseDataError, _sanitize_html, load_lessons
from .grading import check_answer


class CourseDataTests(SimpleTestCase):
    def test_loads_all_lessons_and_steps_in_numeric_order(self):
        root = Path(__file__).resolve().parents[2] / "algebra_course"
        lessons = load_lessons(root)

        self.assertEqual([lesson["number"] for lesson in lessons], list(range(1, 14)))
        self.assertEqual(sum(len(lesson["steps"]) for lesson in lessons), 81)
        self.assertEqual(
            [step["position"] for step in lessons[1]["steps"]],
            list(range(1, len(lessons[1]["steps"]) + 1)),
        )

    def test_rejects_malformed_step_json(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            lesson_directory = Path(temporary_directory) / "lesson_1"
            lesson_directory.mkdir()
            (lesson_directory / "123_1_text.step").write_text("{", encoding="utf-8")

            with self.assertRaises(CourseDataError):
                load_lessons(temporary_directory)

    def test_sanitizes_course_html(self):
        sanitized = _sanitize_html(
            '<p class="ignored">Safe <strong>content</strong></p>'
            '<script>alert(1)</script><img src="javascript:alert(1)" alt="example">'
        )

        self.assertIn("<p>Safe <strong>content</strong></p>", sanitized)
        self.assertNotIn("alert", sanitized)
        self.assertNotIn("javascript:", sanitized)
        self.assertIn('<img alt="example">', sanitized)
        self.assertIn('name="example.png"', _sanitize_html(
            '<img src="https://example.com/image.png" alt="example" name="example.png">'
        ))

    def test_normalizes_multiline_display_math(self):
        sanitized = _sanitize_html(
            r'<p><span class="math-tex">\[5 + 3 = 5 \\ = 6 \\ = 8\]</span></p>'
        )

        self.assertIn(r"\begin{gathered}", sanitized)
        self.assertIn(r"\end{gathered}", sanitized)
        self.assertNotIn(r"\begin{aligned}", sanitized)

    def test_does_not_wrap_inline_or_single_line_display_math(self):
        sanitized = _sanitize_html(
            r'<p>\(m + n = s\) and \[5 + 3 = 8\]</p>'
        )

        self.assertIn(r"\(m + n = s\)", sanitized)
        self.assertIn(r"\[5 + 3 = 8\]", sanitized)
        self.assertNotIn(r"\begin{gathered}", sanitized)

    def test_lesson_four_multiline_expression_is_normalized(self):
        lessons = load_lessons()
        step = lessons[3]["steps"][1]

        self.assertIn(r"\begin{gathered}", step["content"])
        self.assertIn(r"\end{gathered}", step["content"])

    def test_rewrites_stepik_step_links_to_local_routes(self):
        sanitized = _sanitize_html(
            '<a href="https://stepik.org/lesson/1733920/step/12">шаг 12</a>'
            '<a href="https://example.com/help">справка</a>',
            {("1733920", 12): "/learn/lesson/9/step/12/"},
        )

        self.assertIn('href="/learn/lesson/9/step/12/"', sanitized)
        self.assertIn('href="https://example.com/help"', sanitized)
        self.assertNotIn("stepik.org", sanitized)

    def test_all_course_stepik_step_links_resolve_locally(self):
        root = Path(__file__).resolve().parents[2] / "algebra_course"
        lessons = load_lessons(root)
        course_content = "\n".join(
            step["content"]
            for lesson in lessons
            for step in lesson["steps"]
        )

        self.assertNotIn("stepik.org/lesson/", course_content)
        final_lesson_step = lessons[8]["steps"][13]["content"]
        self.assertIn('href="/learn/lesson/9/step/12/"', final_lesson_step)

    def test_course_images_use_existing_local_static_assets(self):
        lessons = load_lessons()
        course_content = "\n".join(
            step["content"]
            for lesson in lessons
            for step in lesson["steps"]
        )
        image_sources = re.findall(
            r'<img\b[^>]*\bsrc=["\']([^"\']+)["\']',
            course_content,
            re.IGNORECASE,
        )
        static_root = Path(__file__).resolve().parents[1] / "static"

        self.assertTrue(image_sources)
        for source in image_sources:
            with self.subTest(source=source):
                self.assertTrue(
                    source.startswith("/static/course_management/images/")
                )
                asset_path = static_root / source.removeprefix("/static/")
                self.assertTrue(asset_path.is_file())


class GradingTests(SimpleTestCase):
    def test_checks_choice_fill_blanks_matching_and_sorting_answers(self):
        choice = {
            "id": "choice",
            "type": "choice",
            "source": {"options": [{"is_correct": False}, {"is_correct": True}]},
        }
        fill_blanks = {
            "id": "fill",
            "type": "fill-blanks",
            "source": {
                "components": [{
                    "type": "input",
                    "options": [{"text": "1", "is_correct": True}],
                }],
            },
        }
        matching = {
            "id": "matching",
            "type": "matching",
            "source": {"pairs": [{"first": "1", "second": "2"}]},
        }
        sorting = {
            "id": "sorting",
            "type": "sorting",
            "content": "Расставьте числа в порядке убывания",
            "source": {"options": [{"text": "63"}, {"text": "12"}, {"text": "2"}]},
        }

        self.assertTrue(check_answer(choice, QueryDict("answer=1")))
        self.assertFalse(check_answer(choice, QueryDict("answer=0")))
        self.assertTrue(check_answer(fill_blanks, QueryDict("answers=1")))
        self.assertTrue(check_answer(matching, QueryDict("answers=2")))
        self.assertTrue(check_answer(sorting, QueryDict("answers=63&answers=12&answers=2")))
        self.assertFalse(check_answer(sorting, QueryDict("answers=2&answers=12&answers=63")))

    def test_multiple_choice_requires_an_explicit_answer_key(self):
        keyed_step = {
            "id": "multi-choice",
            "type": "choice",
            "source": {
                "is_multiple_choice": True,
                "options": [
                    {"is_correct": True},
                    {"is_correct": False},
                    {"is_correct": True},
                ],
            },
        }
        no_key_step = {
            "id": "unscored-multi-choice",
            "type": "choice",
            "source": {
                "is_multiple_choice": True,
                "options": [{"is_correct": False}, {"is_correct": False}],
            },
        }

        self.assertTrue(check_answer(keyed_step, QueryDict("answers=0&answers=2")))
        self.assertFalse(check_answer(keyed_step, QueryDict("answers=0")))
        self.assertIsNone(check_answer(no_key_step, QueryDict("answers=0")))

    def test_checks_math_and_number_answers_without_evaluating_code(self):
        math_step = {"id": "math", "type": "math", "source": {"answer": "12/28"}}
        number_step = {
            "id": "number",
            "type": "number",
            "source": {"options": [{"answer": "15,625", "max_error": "0"}]},
        }

        self.assertTrue(check_answer(math_step, QueryDict("answer=12+%2F+28")))
        self.assertTrue(check_answer(number_step, QueryDict("answer=15%2C625")))
        self.assertFalse(check_answer(number_step, QueryDict("answer=__import__")))

    def test_leaves_manual_and_generated_answer_types_ungraded(self):
        for step_type in ("text", "free-answer", "string", "random-tasks"):
            with self.subTest(step_type=step_type):
                self.assertIsNone(check_answer({"id": step_type, "type": step_type, "source": {}}, QueryDict("answer=test")))


class CourseViewerPageTests(TestCase):
    def test_existing_courses_page_links_to_the_viewer(self):
        response = self.client.get(reverse("homepage:courses"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/static/css/bootstrap.min.css"')
        self.assertNotContains(response, "site.css")
        self.assertNotContains(response, "bootstrap-theme.css")
        self.assertContains(
            response,
            reverse("course_management:course_index"),
        )

    def test_course_and_lesson_pages_render(self):
        course_response = self.client.get(reverse("course_management:course_index"))
        lesson_response = self.client.get(
            reverse("course_management:lesson_detail", args=[1])
        )

        self.assertEqual(course_response.status_code, 200)
        self.assertContains(course_response, "Предисловие")
        self.assertEqual(lesson_response.status_code, 200)
        self.assertContains(lesson_response, "Шаг 1")

    def test_step_page_renders_content_and_navigation(self):
        response = self.client.get(
            reverse("course_management:step_detail", args=[1, 1])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Здраствуй дорогой читатель")
        self.assertContains(response, "Следующий шаг")

    def test_mathjax_is_loaded_for_course_steps(self):
        response = self.client.get(
            reverse("course_management:step_detail", args=[4, 3])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MathJax")
        self.assertContains(response, "mathjax_process")
        self.assertContains(response, r"\begin{gathered}n \text{ раз}")
        self.assertContains(response, r"\mathbb{N}")
        self.assertContains(
            response,
            "/static/course_management/mathjax/tex-chtml.js",
        )
        self.assertNotContains(
            response,
            "cdn.jsdelivr.net",
        )

    def test_interactive_number_lines_are_loaded_for_illustrated_steps(self):
        response = self.client.get(
            reverse("course_management:step_detail", args=[4, 6])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'src="/static/course_management/number_line.js?v=5"',
        )
        self.assertEqual(
            response.content.decode().count('name="natural number line'),
            5,
        )

    def test_fill_blank_steps_render_the_text_components_between_inputs(self):
        answer_url = reverse("course_management:step_detail", args=[10, 3])
        response = self.client.get(answer_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "a = 5, n = 3; r =")
        self.assertContains(response, "a = 2, n = 3; r =")
        self.assertContains(response, "a = 3, n = 2; r =")
        self.assertEqual(response.content.decode().count('name="answers"'), 4)

        inverse_step = self.client.get(
            reverse("course_management:step_detail", args=[10, 7])
        )
        self.assertContains(inverse_step, "Если через 5 поколений мы планируем иметь 243 овцы")
        self.assertContains(inverse_step, "овцы (овец).")
        self.assertEqual(inverse_step.content.decode().count('name="answers"'), 4)

        submission = self.client.post(
            answer_url,
            {"answers": ["125", "8", "9", "243"]},
        )
        self.assertIs(submission.context["submission_correct"], True)

    def test_multiplication_diagrams_are_available_to_the_interactive_number_line(self):
        response = self.client.get(
            reverse("course_management:step_detail", args=[7, 9])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="whole number line 3х2.png"')
        self.assertContains(response, 'name="whole number line 3х.png"')
        self.assertContains(response, 'name="whole number line 3 = 1.png"')
        self.assertContains(
            response,
            'src="/static/course_management/number_line.js?v=5"',
        )

    def test_fraction_pie_diagrams_are_available_to_the_interactive_pie(self):
        response = self.client.get(
            reverse("course_management:step_detail", args=[9, 5])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'src="/static/course_management/fraction_pie.js?v=2"',
        )
        self.assertContains(response, 'name="ratio 3+2 8.png"')
        self.assertContains(response, 'name="ratio 3х2 8.png"')
        self.assertContains(response, 'data-course-lesson="9"')

    def test_correct_choice_submission_returns_feedback(self):
        lessons = load_lessons()
        lesson = next(
            item
            for item in lessons
            if any(
                step["type"] == "choice"
                and not step["source"].get("is_multiple_choice")
                and any(option.get("is_correct") for option in step["source"]["options"])
                for step in item["steps"]
            )
        )
        step = next(
            item
            for item in lesson["steps"]
            if item["type"] == "choice"
            and not item["source"].get("is_multiple_choice")
            and any(option.get("is_correct") for option in item["source"]["options"])
        )
        correct_answer = next(
            index
            for index, option in enumerate(step["source"]["options"])
            if option["is_correct"]
        )
        response = self.client.post(
            reverse(
                "course_management:step_detail",
                args=[lesson["number"], step["position"]],
            ),
            {"answer": str(correct_answer)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIs(response.context["submission_correct"], True)

    def test_matching_exercise_accepts_drag_order_and_renders_controls(self):
        lesson = load_lessons()[2]
        step = lesson["steps"][2]
        url = reverse(
            "course_management:step_detail",
            args=[lesson["number"], step["position"]],
        )

        page = self.client.get(url)
        correct_answers = [pair["second"] for pair in step["source"]["pairs"]]
        response = self.client.post(url, {"answers": correct_answers})

        self.assertEqual(page.status_code, 200)
        self.assertEqual(len(page.context["matching_options"]), len(correct_answers))
        self.assertContains(page, "data-sortable-list")
        self.assertContains(page, "data-sortable-handle")
        self.assertContains(page, "Переместить вверх")
        self.assertContains(page, 'src="/static/course_management/drag_order.js?v=2"')
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.context["submission_correct"], True)

    def test_sorting_exercise_renders_left_aligned_drag_handles(self):
        response = self.client.get(
            reverse("course_management:step_detail", args=[6, 3])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-sortable-list")
        self.assertContains(response, "data-sortable-handle")
        self.assertContains(response, "text-start")

    def test_random_task_values_are_stable_for_the_session(self):
        lessons = load_lessons()
        lesson = next(item for item in lessons if any(step["type"] == "random-tasks" for step in item["steps"]))
        step = next(item for item in lesson["steps"] if item["type"] == "random-tasks")
        url = reverse(
            "course_management:step_detail",
            args=[lesson["number"], step["position"]],
        )

        first_response = self.client.get(url)
        second_response = self.client.get(url)

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(
            first_response.context["random_task_prompt"],
            second_response.context["random_task_prompt"],
        )
        self.assertNotContains(first_response, r"\x")

    def test_missing_lesson_returns_404(self):
        response = self.client.get(
            reverse("course_management:lesson_detail", args=[999])
        )

        self.assertEqual(response.status_code, 404)
