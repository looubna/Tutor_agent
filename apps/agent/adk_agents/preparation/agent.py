"""Exposes the preparation pipeline to the `adk` CLI.

`adk run adk_agents/preparation` and `adk web` both look for `root_agent` in a
directory like this one. Keeping it as a thin re-export means the CLI and the
Cloud Run service drive exactly the same graph.
"""
from zanoba_agent.agents import curriculum_agent as _ca, diagnostic_agent as _da
from zanoba_agent.agents import planner_tools as _pt
from zanoba_agent.store.history import FirestoreLessonHistory
from zanoba_agent.store.profiles import FirestoreProfileStore
from zanoba_agent.workflows.preparation import preparation_workflow
import os

_project = os.environ.get("GOOGLE_CLOUD_PROJECT", "ai-tutor-zanoba")
_history = FirestoreLessonHistory(project=_project)
_profiles = FirestoreProfileStore(project=_project)
_ca.set_history_store(_history)
_da.set_stores(_profiles, _history)
_pt.set_stores(_profiles, _history)

root_agent = preparation_workflow
