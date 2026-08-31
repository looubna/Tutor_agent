"""Create one realistic student profile and round-trip it through Firestore.

The student mirrors the Curriculum agent's live run: they have finished the
A1.1 opener plus the first two classroom lessons, so they have evidence for
vocabulary and communication and none at all for grammar. Nothing here is
invented — every mastery entry names the lesson it came from.
"""
from datetime import datetime, timezone

from zanoba_agent.schemas.profile import (
    Demographics, LanguageGoals, LanguageKnowledge, LanguageLearnerProfile,
    LearningPreferences, MasteryEntry, Misconception, RecurringError,
    SkillLevel, StudentProfile, SubjectLearning,
)
from zanoba_agent.store.profiles import FirestoreProfileStore

SID = "stu-demo-1"
D = lambda d: datetime(2026, 8, d, tzinfo=timezone.utc)

student = StudentProfile(
    student_id=SID,
    demographics=Demographics(age=27, grade="adult"),
    school_system="DE",
    learning=[
        SubjectLearning(
            subject="german",
            overall_level="a1-1",
            mastery=[
                MasteryEntry(item_id="a1-1.classroom.l1", score=0.82, attempts=9, correct=7,
                             last_seen_at=D(3), evidence_lesson_ids=["a1-1.classroom.l1"]),
                MasteryEntry(item_id="a1-1.classroom.l2", score=0.55, attempts=6, correct=3,
                             last_seen_at=D(5), evidence_lesson_ids=["a1-1.classroom.l2"]),
            ],
            misconceptions=[
                Misconception(concept="du-vs-sie",
                              description="Uses du with strangers, treating Sie as merely formal rather than required.",
                              severity="medium", first_seen_at=D(3),
                              evidence_lesson_ids=["a1-1.classroom.l1"]),
            ],
            recurring_errors=[
                RecurringError(tag="umlaut-dropped", description="Writes 'schon' for 'schön'.",
                               count=3, examples=["schon", "horen", "Madchen"]),
            ],
            strengths=["Recalls greetings quickly and uses them unprompted."],
            weaknesses=["Spelling aloud slows down after the first few letters."],
        )
    ],
    learning_preferences=LearningPreferences(
        preferred_explanation="Short examples before any rule.",
        correction_style="delayed", likes_conversation=True,
        likes_visual_material=True, preferred_topics=["travel", "food"],
    ),
)

learner = LanguageLearnerProfile(
    student_id=SID, subject="german",
    native_language="fr", target_language="de",
    overall_band="A1", current_level_id="a1-1",
    skills=[
        SkillLevel(skill="reading", band="A1", evidence_lesson_ids=["a1-1.classroom.l1"]),
        SkillLevel(skill="speaking", band="A1", evidence_lesson_ids=["a1-1.classroom.l2"]),
    ],
    knowledge=[
        LanguageKnowledge(area="vocabulary", overall_mastery=0.68, topics=[
            MasteryEntry(item_id="greetings", score=0.82, attempts=9, correct=7,
                         last_seen_at=D(3), evidence_lesson_ids=["a1-1.classroom.l1"]),
        ]),
        # No grammar lesson has happened yet, so grammar holds a zero with no
        # evidence — which the schema allows only because the score is zero.
        LanguageKnowledge(area="grammar", overall_mastery=0.0, topics=[]),
    ],
    misconceptions=student.learning[0].misconceptions,
    recurring_errors=student.learning[0].recurring_errors,
    strengths=student.learning[0].strengths,
    weaknesses=student.learning[0].weaknesses,
    learning_preferences=student.learning_preferences,
    goals=LanguageGoals(short_term=["Introduce myself without notes."],
                        long_term=["Hold a 10-minute conversation at A2."]),
)

store = FirestoreProfileStore(project="ai-tutor-zanoba")
store.save_student(student)
store.save_language_learner(learner)
print("written to Firestore")

back_s = store.get_student(SID)
back_l = store.get_language_learner(SID, "german")
assert back_s and back_l, "round-trip failed"
g = back_s.for_subject("german")
print(f"  student_profile        {back_s.student_id} | {back_s.school_system} | updated {back_s.updated_at:%H:%M:%S}")
print(f"    german mastery       {[(m.item_id.split('.')[-1], m.score) for m in g.mastery]}")
print(f"    misconception        {g.misconceptions[0].concept} ({g.misconceptions[0].severity})")
print(f"    recurring error      {g.recurring_errors[0].tag} x{g.recurring_errors[0].count}")
print(f"  language_learner       band {back_l.overall_band} | level {back_l.current_level_id} | native {back_l.native_language}")
print(f"    knowledge            {[(k.area, k.overall_mastery) for k in back_l.knowledge]}")
print(f"    goals(short)         {back_l.goals.short_term}")
