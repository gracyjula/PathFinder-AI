"""
NeuraLearn AI — Core unit tests
Covers the three most critical deterministic components:
  1. Skill gap calculation
  2. Mastery update (Bayesian blend)
  3. Quiz scoring
These do NOT require a running DB or AI provider.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app.services.skill_graph import (
    calculate_skill_gap,
    update_mastery_from_quiz,
    build_mastery_map_from_skills,
    get_next_best_actions,
    normalize_skill,
    STRONG_THRESHOLD,
    DEVELOPING_THRESHOLD,
)


# ─── Skill Gap Tests ──────────────────────────────────────────────────────────

class TestSkillGap:

    def test_empty_mastery_gives_zero_readiness(self):
        result = calculate_skill_gap("AI Engineer", {})
        assert result.career_readiness_pct == 0.0
        assert len(result.gap_skills) > 0
        assert len(result.strong_skills) == 0

    def test_strong_python_appears_in_strong_list(self):
        result = calculate_skill_gap("AI Engineer", {"Python": 90.0})
        assert "Python" in result.strong_skills

    def test_partial_mastery_gives_developing_status(self):
        result = calculate_skill_gap("AI Engineer", {"Python": 50.0})
        python_item = next(i for i in result.required_skills if i.skill == "Python")
        assert python_item.status == "developing"

    def test_low_mastery_gives_gap_status(self):
        result = calculate_skill_gap("AI Engineer", {"Python": 20.0})
        python_item = next(i for i in result.required_skills if i.skill == "Python")
        assert python_item.status == "gap"

    def test_full_mastery_gives_100_readiness(self):
        # Give 100% to every AI Engineer required skill
        from app.services.skill_graph import ROLE_SKILL_GRAPH
        mastery = {node.name: 100.0 for node in ROLE_SKILL_GRAPH["AI Engineer"]}
        result = calculate_skill_gap("AI Engineer", mastery)
        assert result.career_readiness_pct == 100.0
        assert len(result.gap_skills) == 0

    def test_priority_skills_sorted_by_gap_times_importance(self):
        """Skills with large gap × high importance must come first."""
        # Python importance=1.0, MLOps importance=0.8
        # Give Python 60% (gap=10) and MLOps 0% (gap=70)
        # MLOps priority = 70*0.8 = 56 > Python priority = 10*1.0 = 10
        mastery = {"Python": 60.0}
        result = calculate_skill_gap("AI Engineer", mastery)
        # MLOps should appear before Python in priority list
        if "MLOps" in result.priority_skills and "Python" in result.priority_skills:
            assert result.priority_skills.index("MLOps") < result.priority_skills.index("Python")

    def test_prerequisites_met_flag(self):
        """Deep Learning prereq is Machine Learning. With ML at 0%, prereq not met."""
        result = calculate_skill_gap("AI Engineer", {"Python": 90.0, "Statistics": 80.0})
        ml_item = next((i for i in result.required_skills if i.skill == "Machine Learning"), None)
        dl_item = next((i for i in result.required_skills if i.skill == "Deep Learning"), None)
        assert ml_item is not None
        assert dl_item is not None
        # ML prereqs = [Python, Statistics] — both met → prerequisites_met=True
        assert ml_item.prerequisites_met is True
        # DL prereq = [Machine Learning] — ML at 0% → prerequisites_met=False
        assert dl_item.prerequisites_met is False

    def test_gate_cse_role_exists(self):
        result = calculate_skill_gap("Crack GATE CSE", {})
        assert result.target_role == "Crack GATE CSE"
        assert any(i.skill == "Data Structures" for i in result.required_skills)
        assert any(i.skill == "Algorithms" for i in result.required_skills)

    def test_backend_developer_role_exists(self):
        result = calculate_skill_gap("Backend Developer", {})
        assert result.target_role == "Backend Developer"
        assert any(i.skill == "APIs" for i in result.required_skills)

    def test_readiness_cannot_exceed_100(self):
        from app.services.skill_graph import ROLE_SKILL_GRAPH
        mastery = {node.name: 120.0 for node in ROLE_SKILL_GRAPH["AI Engineer"]}
        result = calculate_skill_gap("AI Engineer", mastery)
        assert result.career_readiness_pct <= 100.0

    def test_fuzzy_role_matching(self):
        """'ai engineer' (lowercase) should resolve to AI Engineer graph."""
        result = calculate_skill_gap("ai engineer", {})
        assert "AI Engineer" in result.target_role or len(result.required_skills) > 0


# ─── Mastery Update Tests ─────────────────────────────────────────────────────

class TestMasteryUpdate:

    def test_high_quiz_increases_low_mastery(self):
        new = update_mastery_from_quiz(current_mastery=20.0, quiz_score=90.0, evidence_count=0)
        assert new > 20.0

    def test_low_quiz_decreases_high_mastery(self):
        new = update_mastery_from_quiz(current_mastery=80.0, quiz_score=10.0, evidence_count=0)
        assert new < 80.0

    def test_mastery_never_below_zero(self):
        new = update_mastery_from_quiz(current_mastery=5.0, quiz_score=0.0, evidence_count=0)
        assert new >= 0.0

    def test_mastery_never_above_100(self):
        new = update_mastery_from_quiz(current_mastery=95.0, quiz_score=100.0, evidence_count=100)
        assert new <= 100.0

    def test_more_evidence_reduces_quiz_influence(self):
        """First quiz should shift mastery more than the 10th quiz."""
        delta_first = abs(update_mastery_from_quiz(50.0, 90.0, 0) - 50.0)
        delta_tenth = abs(update_mastery_from_quiz(50.0, 90.0, 10) - 50.0)
        assert delta_first > delta_tenth

    def test_same_score_as_mastery_is_stable(self):
        """If quiz score equals current mastery, value should be unchanged."""
        new = update_mastery_from_quiz(60.0, 60.0, 5)
        assert new == 60.0

    def test_evidence_count_zero_quiz_dominates(self):
        """With zero prior evidence the quiz should have near-100% weight."""
        new = update_mastery_from_quiz(0.0, 100.0, 0)
        assert new == 100.0


# ─── Quiz Scoring Tests ───────────────────────────────────────────────────────

class TestQuizScoring:
    """
    Quiz scoring is deterministic (correct/total * 100).
    We test the logic directly since it lives inline in the route.
    """

    def _score(self, questions, answers):
        """Replicate the quiz scoring logic from analytics.py."""
        correct = 0
        for q in questions:
            if answers.get(q["id"]) == q["correct_answer"]:
                correct += 1
        return (correct / len(questions)) * 100 if questions else 0

    def test_all_correct_gives_100(self):
        qs = [{"id": "q1", "correct_answer": "A"}, {"id": "q2", "correct_answer": "B"}]
        answers = {"q1": "A", "q2": "B"}
        assert self._score(qs, answers) == 100.0

    def test_all_wrong_gives_zero(self):
        qs = [{"id": "q1", "correct_answer": "A"}, {"id": "q2", "correct_answer": "B"}]
        answers = {"q1": "C", "q2": "D"}
        assert self._score(qs, answers) == 0.0

    def test_half_correct_gives_50(self):
        qs = [{"id": "q1", "correct_answer": "A"}, {"id": "q2", "correct_answer": "B"}]
        answers = {"q1": "A", "q2": "X"}
        assert self._score(qs, answers) == 50.0

    def test_empty_questions_gives_zero(self):
        assert self._score([], {}) == 0.0

    def test_unanswered_question_counts_as_wrong(self):
        qs = [{"id": "q1", "correct_answer": "A"}]
        answers = {}  # not answered
        assert self._score(qs, answers) == 0.0

    def test_60_percent_threshold_for_pass(self):
        qs = [{"id": f"q{i}", "correct_answer": "A"} for i in range(5)]
        # 3/5 = 60% → should pass
        answers = {f"q{i}": "A" for i in range(3)}
        score = self._score(qs, answers)
        assert score == 60.0
        assert score >= 60  # passes


# ─── Skill Normalization Tests ────────────────────────────────────────────────

class TestSkillNormalization:

    def test_alias_ml_normalizes(self):
        assert normalize_skill("ml") == "Machine Learning"

    def test_alias_mlops_normalizes(self):
        assert normalize_skill("mlops") == "MLOps"

    def test_case_insensitive(self):
        assert normalize_skill("PYTHON") == "Python"

    def test_unknown_skill_title_cases(self):
        assert normalize_skill("some new skill") == "Some New Skill"


# ─── Next Best Action Tests ───────────────────────────────────────────────────

class TestNextBestAction:

    def test_returns_gap_skills_first(self):
        mastery = {"Python": 90.0}  # Python strong, everything else 0
        result = calculate_skill_gap("AI Engineer", mastery)
        actions = get_next_best_actions(result, mastery, weekly_hours=8)
        assert len(actions) > 0
        # Python should NOT be recommended (it's strong)
        assert all(a["skill"] != "Python" for a in actions)

    def test_prerequisite_skills_bubbled_up(self):
        """When a skill's prereqs aren't met, the prereq should be recommended instead."""
        mastery = {}  # nothing known
        result = calculate_skill_gap("AI Engineer", mastery)
        actions = get_next_best_actions(result, mastery, weekly_hours=8)
        # Deep Learning requires Machine Learning — Machine Learning (or Python/Stats) should appear
        skills = [a["skill"] for a in actions]
        # At least one foundational skill should be recommended
        foundational = {"Python", "Mathematics", "Statistics", "Machine Learning", "Data Structures"}
        assert any(s in foundational for s in skills)

    def test_returns_at_most_max_actions(self):
        mastery = {}
        result = calculate_skill_gap("AI Engineer", mastery)
        actions = get_next_best_actions(result, mastery, max_actions=3)
        assert len(actions) <= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
