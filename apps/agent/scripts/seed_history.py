"""Append the demo student's completed lessons to Firestore.

Matches the profile seeded by seed_profile.py: the A1.1 opener, then the
vocabulary and communication lessons of the classroom chapter. The grammar
lesson is deliberately absent — that is the one being planned.
"""
from datetime import datetime, timezone
from zanoba_agent.store.history import (
    CompletedLesson, FirestoreLessonHistory, LessonAssessment)

D = lambda d: datetime(2026, 8, d, tzinfo=timezone.utc)
SID = "stu-demo-1"
store = FirestoreLessonHistory(project="ai-tutor-zanoba")

lessons = [
    CompletedLesson(
        lesson_id="a1-1.get-started.l1", subject="german", level_id="a1-1",
        completed_at=D(1),
        objectives_completed=["I know what the twelve chapters of A1.1 cover."]),
    CompletedLesson(
        lesson_id="a1-1.classroom.l1", subject="german", level_id="a1-1",
        completed_at=D(3),
        objectives_completed=["I can greet someone in German at any time of day.",
                              "I can say goodbye at the end of a class."],
        objectives_unfinished=["I can tell when to use du and when to use Sie."],
        assessment=LessonAssessment(score=0.78, items_correct=7, items_total=9,
                                    error_tags=["umlaut-dropped", "du-vs-sie"]),
        observations=["Confident with greetings; used them unprompted."]),
    CompletedLesson(
        lesson_id="a1-1.classroom.l2", subject="german", level_id="a1-1",
        completed_at=D(5),
        objectives_completed=["I can ask someone to repeat something."],
        objectives_unfinished=["I can spell my name letter by letter."],
        assessment=LessonAssessment(score=0.50, items_correct=3, items_total=6,
                                    error_tags=["umlaut-dropped"]),
        observations=["Slowed down markedly after the first few letters."]),
]
for x in lessons:
    store.record(SID, x)
print(f"recorded {len(lessons)} lessons")
back = store.completed_lessons(SID, "german")
print("read back:", [(x.lesson_id.split('.')[-2:], x.assessment.score if x.assessment else None) for x in back])
