"""Reading and writing student profiles.

Two implementations behind one protocol: Firestore for real runs, in-memory for
tests. Nothing above this module knows which it is using, so the whole pipeline
is testable without a network and without a Google Cloud project.

Firestore is the platform's mandated Google Cloud service, and profiles are the
right thing to put in it — they are the only state that is read *and* written
across sessions. Curriculum stays as versioned files; lesson history is
append-only and immutable.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from ..schemas.profile import LanguageLearnerProfile, StudentProfile

STUDENTS = "student_profiles"
LANGUAGE_LEARNERS = "language_learner_profiles"


class ProfileStore(Protocol):
    """Everything the pipeline does to a profile."""

    def get_student(self, student_id: str) -> StudentProfile | None: ...

    def save_student(self, profile: StudentProfile) -> None: ...

    def get_language_learner(
        self, student_id: str, subject: str
    ) -> LanguageLearnerProfile | None: ...

    def save_language_learner(self, profile: LanguageLearnerProfile) -> None: ...


def _stamped(profile):
    """Profiles record when they were last updated, always in UTC."""
    return profile.model_copy(update={"updated_at": datetime.now(timezone.utc)})


class InMemoryProfileStore:
    """A dict-backed store. For tests and offline runs."""

    def __init__(self) -> None:
        self._students: dict[str, StudentProfile] = {}
        self._learners: dict[tuple[str, str], LanguageLearnerProfile] = {}

    def get_student(self, student_id: str) -> StudentProfile | None:
        return self._students.get(student_id)

    def save_student(self, profile: StudentProfile) -> None:
        self._students[profile.student_id] = _stamped(profile)

    def get_language_learner(
        self, student_id: str, subject: str
    ) -> LanguageLearnerProfile | None:
        return self._learners.get((student_id, subject))

    def save_language_learner(self, profile: LanguageLearnerProfile) -> None:
        self._learners[(profile.student_id, profile.subject)] = _stamped(profile)


class FirestoreProfileStore:
    """The real store.

    The client is created lazily so importing this module never needs
    credentials — tests import it freely, and only an actual call touches
    Google Cloud.
    """

    def __init__(self, project: str | None = None, database: str = "(default)") -> None:
        self._project = project
        self._database = database
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from google.cloud import firestore

            self._client = firestore.Client(
                project=self._project, database=self._database
            )
        return self._client

    def get_student(self, student_id: str) -> StudentProfile | None:
        snap = self.client.collection(STUDENTS).document(student_id).get()
        return StudentProfile.model_validate(snap.to_dict()) if snap.exists else None

    def save_student(self, profile: StudentProfile) -> None:
        stamped = _stamped(profile)
        self.client.collection(STUDENTS).document(stamped.student_id).set(
            stamped.model_dump(mode="json")
        )

    def get_language_learner(
        self, student_id: str, subject: str
    ) -> LanguageLearnerProfile | None:
        snap = (
            self.client.collection(LANGUAGE_LEARNERS)
            .document(f"{student_id}__{subject}")
            .get()
        )
        return (
            LanguageLearnerProfile.model_validate(snap.to_dict()) if snap.exists else None
        )

    def save_language_learner(self, profile: LanguageLearnerProfile) -> None:
        stamped = _stamped(profile)
        self.client.collection(LANGUAGE_LEARNERS).document(
            f"{stamped.student_id}__{stamped.subject}"
        ).set(stamped.model_dump(mode="json"))
