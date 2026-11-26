# Algebra Course Viewer

The viewer reads lesson and step JSON directly from the sibling `algebra_course/`
directory. It does not import the course into the database.

- Open `/learn/` to browse the course.
- Open `/learn/lesson/<lesson-number>/` to browse a lesson's steps.
- Open `/learn/lesson/<lesson-number>/step/<step-number>/` to view and answer a step.

Choice, fill-in-the-blank, matching, sorting, math, and number steps are checked
when their answer data is available. Free-answer, string, and random-task steps
are shown without automatic scoring. Code stored in step data is never executed.
Matching and sorting options can be reordered by dragging or with the accessible
up/down controls.
Natural- and whole-number-line illustrations have an interactive line beneath
them where learners can select a point and visualize addition or subtraction
jumps, including signed steps. Multiplication diagrams in the multiplication
lesson show products as repeated addition.
Fraction diagrams in lesson 9 have interactive pie models for partitioning,
equivalent fractions, addition, multiplication, and division.
LaTeX in course content is rendered by MathJax 3, loaded from jsDelivr.

Run the app's tests with `python manage.py test course_management` from the
`math_helper/` project directory.
