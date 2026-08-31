"""Curriculum state — what the syllabus contains, for every subject we teach.

The diagram draws two curriculum stores, not one: `Languages Curriculum_state`
is organised by CEFR level and skill focus, `STEM Curriculum_state` by grade,
subject and unit. They are different shapes because the domains are, and
flattening them into one model would mean a pile of fields that are null half
the time.

Both are read-only reference data, authored as JSON and versioned in the repo.
Nothing here records what a student knows — that is the student profile's job,
and keeping the two apart is the point of the split. A curriculum says "this is
what exists"; a profile says "this is where one learner stands in it".
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# The focuses a booked language lesson can have. Exactly one is primary, and the
# planner must keep it dominant — a communication lesson that drifts into
# grammar because errors appeared is the failure this constrains.
#
# "speaking" is the chapter's closing hour, where the learner talks about the
# whole chapter rather than about one new function. It plans as a communication
# lesson — same stages, same task-first shape — and is named separately because
# the syllabus distinguishes them and the tutor should know which it is running.
LanguageFocus = Literal[
    "reading", "vocabulary", "grammar", "communication", "speaking",
]

# The CEFR band. This is the framework's own scale, and it is what a CEFR
# appropriateness check reasons about — "is this text A1?" is a question about
# the band, never about the sub-level.
CEFRBand = Literal["A1", "A2", "B1", "B2", "C1", "C2"]

# Not every lesson teaches a skill. A course opener and an end-of-chapter
# review are real bookable hours, but they have no dominant focus.
LessonKind = Literal["lesson", "orientation", "review"]


class LanguageLesson(BaseModel):
    """One bookable lesson. A booking points here, not at the chapter.

    `focus` is the lesson's own property, not the chapter's — a single chapter
    runs vocabulary, then communication, then grammar over its lessons, and the
    planner needs to know which one it is being asked to teach. It is the
    dominant focus for the whole hour; grammar errors surfacing inside a
    communication lesson do not turn it into a grammar lesson.

    Orientation and review lessons carry no focus, because they teach no single
    skill. `kind` keeps them out of the planner's focus logic instead of
    forcing a wrong value into `focus`.
    """

    id: str
    title: str
    order: int
    focus: LanguageFocus | None = Field(
        default=None,
        description="The dominant skill. None for orientation and review lessons.",
    )
    kind: LessonKind = "lesson"
    summary: str = ""
    objectives: list[str] = Field(
        default_factory=list,
        description='Can-do statements, e.g. "I can greet someone in German".',
    )
    prerequisites: list[str] = Field(
        default_factory=list,
        description="Lesson ids that should come first. Ids, never prose.",
    )


class LanguageChapter(BaseModel):
    """A CEFR can-do statement, and the lessons that build up to it.

    The title is the descriptor itself — "I can order in a caf\u00e9 and read a
    menu" — so the chapter states what the student will be able to do, not what
    topic gets covered.
    """

    id: str
    title: str
    order: int
    emoji: str = ""
    theme: str = Field(default="", description="Source theme, e.g. a Goethe Themenbereich.")
    lessons: list[LanguageLesson] = Field(default_factory=list)


class LanguageLevel(BaseModel):
    """One teachable level, and the chapters that run through it.

    A CEFR band is a year of study, far too big to book a lesson against, so
    the school splits each band in two: A1.1 then A1.2. That split is what a
    student is enrolled in and what a booking carries, so it is the identity
    here — `id` is `a1-1`, and `band` is the `A1` it belongs to.

    Both are kept because they answer different questions. Ordering, booking
    and "what comes next" run off `id`; anything asking whether material suits
    the learner's CEFR level runs off `band`.
    """

    id: str = Field(description='Teachable sub-level id, e.g. "a1-1".')
    band: CEFRBand = Field(description='The CEFR band it sits in, e.g. "A1".')
    label: str = Field(default="", description='Display label, e.g. "A1.1 — Beginner".')
    order: int = Field(default=0, description="Position in the ladder, a1-1 first.")
    description: str = ""
    chapters: list[LanguageChapter] = Field(default_factory=list)


class LanguageCurriculum(BaseModel):
    """`Languages Curriculum_state` from the diagram. One file per subject."""

    curriculum_id: str
    subject: str = Field(description='Subject id, e.g. "german".')
    target_language: str = Field(description='What is being learnt, e.g. "de".')
    framework: str = Field(default="CEFR", description="The level framework in use.")
    levels: list[LanguageLevel] = Field(default_factory=list)


class StemConcept(BaseModel):
    """One idea a lesson teaches. Mastery is tracked per concept, not per lesson,
    because a student can pass a lesson and still miss one idea inside it."""

    id: str
    title: str


class StemLesson(BaseModel):
    """One teachable lesson inside a unit."""

    id: str
    title: str
    order: int
    prerequisites: list[str] = Field(default_factory=list)
    concepts: list[StemConcept] = Field(default_factory=list)
    learning_outcomes: list[str] = Field(default_factory=list)


class StemUnit(BaseModel):
    """A chapter of a subject at one grade."""

    id: str
    title: str
    order: int
    lessons: list[StemLesson] = Field(default_factory=list)


ProgramKind = Literal["grade", "course"]


class StemProgram(BaseModel):
    """One enrollable block of study: a school grade, or a named course.

    The diagram nests units under `grades`, which holds for Pre-K–8 where a
    year of school is the unit of enrollment. It breaks above that: Algebra 1,
    Linear algebra and Multivariable calculus are courses a student takes, not
    years they are in, and there is no grade to file them under.

    So a program is either kind. `age_range` is meaningful for a grade and
    empty for a course; `order` places both on one ladder so "what comes next"
    stays answerable across the boundary.
    """

    id: str
    label: str
    kind: ProgramKind
    order: int = 0
    age_range: str = Field(default="", description="Grades only; empty for courses.")
    programme: str = Field(
        default="",
        description=(
            "The syllabus this belongs to. Maths runs two — the French "
            "programme and the US Pre-K-8 / High-school ladder — and a lesson "
            "is only comparable to others inside the same one."
        ),
    )
    group: str = Field(default="", description='Heading inside a programme, e.g. "Collège".')
    units: list[StemUnit] = Field(default_factory=list)


class StemCurriculum(BaseModel):
    """`STEM Curriculum_state` from the diagram.

    One file per subject, matching how the language curricula are stored, so
    adding physics is a new file rather than a schema change.
    """

    curriculum_id: str
    subject: str = Field(description='Subject id, e.g. "mathematics".')
    education_system: str = Field(description='e.g. "US" or "FR".')
    language: str = Field(description="The language of instruction.")
    academic_year: str = ""
    programs: list[StemProgram] = Field(default_factory=list)
