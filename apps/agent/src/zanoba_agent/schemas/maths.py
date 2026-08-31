"""The shape of a French maths lesson, as maths-et-tiques writes one.

A language lesson is photographs and speech bubbles. A maths lesson is none of
those — it is a numbered argument, and the French *cours* has a form that every
student in the system recognises. Taken from Yvan Monka's own documents
(maths-et-tiques.fr, Académie de Strasbourg), the skeleton is:

    LES FRACTIONS (Partie 1)
        note historique — where the idea comes from
        I. Écriture fractionnaire
           1) Géométriquement          + Vidéo https://youtu.be/...
           2) Dans la vie
           3) Vocabulaire
        Remarque :
        II. Fraction et quotient
           3) Définition
        Méthode : Placer une fraction sur une demi-droite graduée
           Vidéo https://youtu.be/...
        Exercices conseillés | En devoir

Three things about it are worth copying rather than inventing around.

The labelled blocks are a fixed vocabulary — Définition, Propriété, Théorème,
Méthode, Exemple, Remarque — and a French student reads them as signposts. A
*Méthode* is not an *Exemple*: the first is a procedure to follow, the second is
an instance of it, and running them together loses the distinction the notation
exists to carry.

Sections are numbered in roman, subsections in arabic. That is how the class
refers to them out loud, so the numbering is content, not decoration.

And a chapter is split into *Parties* when it is too long for one sitting, which
is exactly the lesson boundary this pipeline needs.
"""

from __future__ import annotations

import re
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, model_validator

# The labelled blocks, with the exact French wording the documents use. The
# label is the interface: a student who sees "Propriété" knows it is something
# to be used and not proved, and one who sees "Méthode" knows to follow it.
BLOCK_LABELS: dict[str, str] = {
    "definition": "Définition",
    "propriete": "Propriété",
    "theoreme": "Théorème",
    "methode": "Méthode",
    "exemple": "Exemple",
    "remarque": "Remarque",
    "regle": "Règle",
    "consequence": "Conséquence",
    "demonstration": "Démonstration",
}

BlockKind = Literal[
    "definition", "propriete", "theoreme", "methode", "exemple",
    "remarque", "regle", "consequence", "demonstration",
]

_YOUTUBE = re.compile(r"^https?://(youtu\.be/|(www\.)?youtube\.com/)", re.I)


class Video(BaseModel):
    """A "Vidéo https://youtu.be/…" line.

    Kept as its own field rather than as prose because on the site it is a
    consistent affordance — every section that has one puts it in the same
    place, and a student learns to look there.
    """

    url: str
    label: str = "Vidéo"

    @model_validator(mode="after")
    def _is_a_video_link(self) -> Video:
        if self.url and not _YOUTUBE.match(self.url):
            raise ValueError(f"{self.url!r} is not a video link")
        return self


class Block(BaseModel):
    """One labelled block: a Définition, a Propriété, a Méthode."""

    kind: BlockKind
    title: str = Field(
        default="",
        description="What follows the label, e.g. Méthode : Placer une fraction "
        "sur une demi-droite graduée.",
    )
    body: str = Field(
        description="The content. Maths in LaTeX between $…$, which the Beamer "
        "renderer passes through untouched."
    )
    video: Video | None = None
    steps: list[str] = Field(
        default_factory=list,
        description="For a Méthode: the numbered steps of the procedure. A "
        "method with no steps is an example wearing the wrong label.",
    )

    @property
    def label(self) -> str:
        return BLOCK_LABELS[self.kind]

    @model_validator(mode="after")
    def _a_method_is_a_procedure(self) -> Block:
        if self.kind == "methode" and not self.steps and not self.body.strip():
            raise ValueError(
                "a Méthode with neither steps nor body is a heading. A method is "
                "a procedure the student can follow."
            )
        return self


class SubSection(BaseModel):
    """A numbered subsection: "1) Géométriquement"."""

    number: int = Field(ge=1, le=9)
    title: str
    body: str = ""
    video: Video | None = None
    blocks: list[Block] = Field(default_factory=list)


class Section(BaseModel):
    """A roman-numbered section: "I. Écriture fractionnaire".

    The numbering is how the class refers to it out loud, so it is carried
    explicitly rather than left to a list renderer to invent.
    """

    numeral: str = Field(
        description='Roman numeral: "I", "II", "III".',
        pattern=r"^(I{1,3}|IV|V|VI{1,3}|IX|X)$",
    )
    title: str
    intro: str = ""
    video: Video | None = None
    subsections: list[SubSection] = Field(default_factory=list)
    blocks: list[Block] = Field(default_factory=list)

    @model_validator(mode="after")
    def _a_section_has_something_in_it(self) -> Section:
        if not (self.subsections or self.blocks or self.intro.strip()):
            raise ValueError(
                f"section {self.numeral}. {self.title!r} is empty"
            )
        return self


class ExerciseRefs(BaseModel):
    """The "Exercices conseillés | En devoir" table that closes each part."""

    conseilles: list[str] = Field(
        default_factory=list, description='e.g. ["p74 n°1, 2, 3", "p75 n°5, 6, 7"]'
    )
    en_devoir: list[str] = Field(default_factory=list)
    manuel: str = Field(
        default="", description='The textbook, e.g. "Myriade 6e - Bordas Éd.2016".'
    )


class MathsCours(BaseModel):
    """One *cours* — one Partie of one chapter, which is one lesson.

    This is the STEM counterpart of a language lesson's slide components: it says
    what the document IS rather than carrying a wall of prose the renderer has
    to guess at.
    """

    kind: Literal["maths_cours"] = "maths_cours"
    chapter: str = Field(description='The chapter, e.g. "LES FRACTIONS".')
    partie: int = Field(
        default=1, ge=1, le=4,
        description="Which part of the chapter. A chapter is split when it is "
        "too long for one sitting, and that split is the lesson boundary.",
    )
    level: str = Field(description='The class, e.g. "6e".')
    note_historique: str = Field(
        default="",
        description="Where the idea comes from. Every cours on the site opens "
        "with one, and it is the only part a student reads for pleasure.",
    )
    activite: str = Field(
        default="", description='An opening group activity, e.g. "Partages".'
    )
    sections: list[Section] = Field(min_length=1, max_length=6)
    exercices: ExerciseRefs | None = None
    auteur: str = Field(
        default="",
        description="Attribution line, where the material follows a published "
        "course. Left empty for material this pipeline wrote itself.",
    )

    @property
    def title(self) -> str:
        return (f"{self.chapter} (Partie {self.partie})" if self.partie > 1
                or self.chapter.endswith(")") else self.chapter)

    @model_validator(mode="after")
    def _sections_are_numbered_in_order(self) -> MathsCours:
        order = ["I", "II", "III", "IV", "V", "VI"]
        want = order[:len(self.sections)]
        got = [s.numeral for s in self.sections]
        if got != want:
            raise ValueError(
                f"sections are numbered {got}; they should run {want}. The "
                "numbering is how the class refers to them out loud."
            )
        return self


MathsComponent = Annotated[Union[MathsCours], Field(discriminator="kind")]
