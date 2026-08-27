"""
NeuraLearn AI — Role Skill Graph & Mastery Engine
==================================================

Deterministic layer that defines:
  - Required skills per target role with importance weights
  - Prerequisite relationships between skills
  - Mastery thresholds (strong / developing / gap)
  - Skill-gap calculation grounded in learner mastery data

The LLM is NOT used for any computation in this module.
The LLM is used only for generating human-readable explanations
*after* the numbers are calculated here.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ─── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class SkillNode:
    name: str
    importance: float          # 0–1, weight in gap calculation
    prerequisites: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class SkillGapItem:
    skill: str
    required_importance: float
    current_mastery: float     # 0–100
    gap_score: float           # 0–100 (higher = bigger gap)
    status: str                # "strong" | "developing" | "gap"
    prerequisites: list[str] = field(default_factory=list)
    prerequisites_met: bool = True


@dataclass
class SkillGapResult:
    target_role: str
    required_skills: list[SkillGapItem]
    overall_gap_pct: float
    career_readiness_pct: float
    priority_skills: list[str]           # ordered: biggest gap × highest importance first
    strong_skills: list[str]
    developing_skills: list[str]
    gap_skills: list[str]


# ─── Role → Required Skills Graph ─────────────────────────────────────────────
# importance: 1.0 = essential, 0.5 = important, 0.3 = nice-to-have

ROLE_SKILL_GRAPH: dict[str, list[SkillNode]] = {

    "AI Engineer": [
        SkillNode("Python",            1.0, [],                              "Core programming language for AI/ML"),
        SkillNode("Mathematics",       0.7, [],                              "Linear algebra, calculus, probability"),
        SkillNode("Statistics",        0.7, ["Mathematics"],                 "Statistical inference and analysis"),
        SkillNode("Machine Learning",  1.0, ["Python", "Statistics"],        "Supervised and unsupervised learning"),
        SkillNode("Deep Learning",     0.9, ["Machine Learning"],            "Neural networks, CNNs, RNNs"),
        SkillNode("NLP",               0.8, ["Deep Learning"],               "Text processing and language models"),
        SkillNode("Transformers",      0.8, ["NLP", "Deep Learning"],        "Attention mechanisms, BERT, GPT"),
        SkillNode("LangChain",         0.7, ["Transformers", "Python"],      "LLM application framework"),
        SkillNode("Generative AI",     0.8, ["Transformers"],                "LLMs, diffusion models, prompting"),
        SkillNode("Git",               0.6, [],                              "Version control"),
        SkillNode("Linux",             0.5, [],                              "Command-line proficiency"),
        SkillNode("Docker",            0.7, ["Linux", "Python"],             "Containerization"),
        SkillNode("APIs",              0.6, ["Python"],                      "REST API design and consumption"),
        SkillNode("MLOps",             0.8, ["Docker", "Machine Learning"],  "Model deployment and monitoring"),
        SkillNode("Cloud",             0.6, ["Docker"],                      "AWS/GCP/Azure for ML workloads"),
    ],

    "ML Engineer": [
        SkillNode("Python",            1.0, [],                              "Core language"),
        SkillNode("Mathematics",       0.8, [],                              "Linear algebra, calculus"),
        SkillNode("Statistics",        0.8, ["Mathematics"],                 "Probability and inference"),
        SkillNode("Machine Learning",  1.0, ["Python", "Statistics"],        "Core ML algorithms"),
        SkillNode("Deep Learning",     0.9, ["Machine Learning"],            "Neural network architectures"),
        SkillNode("TensorFlow",        0.7, ["Deep Learning"],               "ML framework"),
        SkillNode("PyTorch",           0.8, ["Deep Learning"],               "ML research framework"),
        SkillNode("Git",               0.6, [],                              "Version control"),
        SkillNode("Linux",             0.6, [],                              "System proficiency"),
        SkillNode("Docker",            0.8, ["Linux"],                       "Containerization"),
        SkillNode("MLOps",             0.9, ["Docker", "Machine Learning"],  "Production ML systems"),
        SkillNode("Cloud",             0.7, ["Docker"],                      "Cloud ML services"),
        SkillNode("SQL",               0.5, [],                              "Data querying"),
    ],

    "Data Scientist": [
        SkillNode("Python",            1.0, [],                              "Core language"),
        SkillNode("Statistics",        1.0, [],                              "Hypothesis testing, distributions"),
        SkillNode("Mathematics",       0.7, [],                              "Linear algebra, calculus"),
        SkillNode("SQL",               0.9, [],                              "Data extraction and manipulation"),
        SkillNode("Machine Learning",  0.9, ["Python", "Statistics"],        "Predictive modelling"),
        SkillNode("Data Analysis",     1.0, ["Python", "SQL"],               "EDA, pandas, numpy"),
        SkillNode("Data Visualization",0.8, ["Data Analysis"],               "Matplotlib, Seaborn, Tableau"),
        SkillNode("Deep Learning",     0.6, ["Machine Learning"],            "Neural networks"),
        SkillNode("NLP",               0.5, ["Deep Learning"],               "Text data analysis"),
        SkillNode("Git",               0.6, [],                              "Version control"),
        SkillNode("Cloud",             0.5, [],                              "Cloud data platforms"),
    ],

    "Full Stack Developer": [
        SkillNode("HTML/CSS",          1.0, [],                              "Web fundamentals"),
        SkillNode("JavaScript",        1.0, ["HTML/CSS"],                    "Client-side scripting"),
        SkillNode("React",             0.9, ["JavaScript"],                  "Frontend framework"),
        SkillNode("TypeScript",        0.7, ["JavaScript"],                  "Typed JavaScript"),
        SkillNode("Node.js",           0.9, ["JavaScript"],                  "Backend JavaScript runtime"),
        SkillNode("SQL",               0.8, [],                              "Relational databases"),
        SkillNode("APIs",              0.9, ["Node.js"],                     "REST/GraphQL API design"),
        SkillNode("Git",               0.8, [],                              "Version control"),
        SkillNode("Docker",            0.6, [],                              "Containerization"),
        SkillNode("Cloud",             0.6, ["Docker"],                      "Deployment platforms"),
        SkillNode("System Design",     0.7, ["APIs", "SQL"],                 "Architecture patterns"),
    ],

    "Cloud Engineer": [
        SkillNode("Linux",             1.0, [],                              "Linux administration"),
        SkillNode("Networking",        0.8, [],                              "TCP/IP, DNS, routing"),
        SkillNode("Git",               0.7, [],                              "Version control"),
        SkillNode("Python",            0.7, [],                              "Scripting and automation"),
        SkillNode("Docker",            0.9, ["Linux"],                       "Containerization"),
        SkillNode("Kubernetes",        0.9, ["Docker"],                      "Container orchestration"),
        SkillNode("Cloud",             1.0, ["Linux", "Networking"],         "AWS/GCP/Azure services"),
        SkillNode("Terraform",         0.8, ["Cloud"],                       "Infrastructure as code"),
        SkillNode("CI/CD",             0.8, ["Git", "Docker"],               "DevOps pipelines"),
        SkillNode("Security",          0.7, ["Networking"],                  "Cloud security and IAM"),
    ],

    "Software Engineer": [
        SkillNode("Python",            0.7, [],                              "General purpose language"),
        SkillNode("Java",              0.7, [],                              "Enterprise language"),
        SkillNode("JavaScript",        0.7, [],                              "Web language"),
        SkillNode("Data Structures",   1.0, [],                              "Arrays, trees, graphs, heaps"),
        SkillNode("Algorithms",        1.0, ["Data Structures"],             "Sorting, searching, DP"),
        SkillNode("System Design",     0.9, ["Algorithms"],                  "Architecture and design patterns"),
        SkillNode("SQL",               0.7, [],                              "Database fundamentals"),
        SkillNode("Git",               0.8, [],                              "Version control"),
        SkillNode("APIs",              0.7, [],                              "REST API design"),
        SkillNode("Operating Systems", 0.6, [],                              "OS concepts"),
        SkillNode("Networking",        0.5, [],                              "HTTP, TCP, DNS basics"),
    ],

    "Generative AI Engineer": [
        SkillNode("Python",            1.0, [],                              "Core language"),
        SkillNode("Machine Learning",  0.8, ["Python"],                      "ML fundamentals"),
        SkillNode("Deep Learning",     0.9, ["Machine Learning"],            "Neural network architectures"),
        SkillNode("Transformers",      1.0, ["Deep Learning"],               "Attention and transformer models"),
        SkillNode("Generative AI",     1.0, ["Transformers"],                "LLMs, diffusion, prompting"),
        SkillNode("LangChain",         0.9, ["Generative AI", "Python"],     "LLM application framework"),
        SkillNode("APIs",              0.8, ["Python"],                      "LLM API integration"),
        SkillNode("Vector Databases",  0.7, ["Python"],                      "Embeddings and semantic search"),
        SkillNode("RAG",               0.8, ["Vector Databases", "LangChain"], "Retrieval-Augmented Generation"),
        SkillNode("Prompt Engineering",0.9, ["Generative AI"],               "Effective LLM prompting"),
        SkillNode("Git",               0.6, [],                              "Version control"),
        SkillNode("Docker",            0.6, ["Python"],                      "Deployment"),
        SkillNode("MLOps",             0.6, ["Docker"],                      "LLM ops and monitoring"),
    ],

    "Data Analyst": [
        SkillNode("SQL",               1.0, [],                              "Data querying"),
        SkillNode("Excel",             0.8, [],                              "Spreadsheet analysis"),
        SkillNode("Python",            0.8, [],                              "Analysis scripting"),
        SkillNode("Statistics",        0.9, [],                              "Statistical analysis"),
        SkillNode("Data Analysis",     1.0, ["SQL", "Python"],               "EDA and insights"),
        SkillNode("Data Visualization",0.9, ["Data Analysis"],               "Charts, dashboards, BI tools"),
        SkillNode("Machine Learning",  0.5, ["Python", "Statistics"],        "Predictive analysis"),
        SkillNode("Git",               0.4, [],                              "Version control"),
    ],
}

# Alias normalization — maps common user input to canonical skill names
SKILL_ALIASES: dict[str, str] = {
    "ml": "Machine Learning",
    "basic ml": "Machine Learning",
    "dl": "Deep Learning",
    "nlp": "NLP",
    "ds": "Data Structures",
    "dsa": "Data Structures",
    "js": "JavaScript",
    "ts": "TypeScript",
    "aws": "Cloud",
    "gcp": "Cloud",
    "azure": "Cloud",
    "k8s": "Kubernetes",
    "tf": "TensorFlow",
    "pytorch": "PyTorch",
    "langchain": "LangChain",
    "genai": "Generative AI",
    "generative ai": "Generative AI",
    "llm": "Generative AI",
    "llms": "Generative AI",
    "transformers": "Transformers",
    "bert": "Transformers",
    "gpt": "Transformers",
    "mlops": "MLOps",
    "devops": "CI/CD",
    "cicd": "CI/CD",
    "ci/cd": "CI/CD",
    "system design": "System Design",
    "data structures": "Data Structures",
    "algorithms": "Algorithms",
    "data visualization": "Data Visualization",
    "pandas": "Data Analysis",
    "numpy": "Data Analysis",
    "data analysis": "Data Analysis",
    "rag": "RAG",
    "vector db": "Vector Databases",
    "vector databases": "Vector Databases",
    "prompt engineering": "Prompt Engineering",
}

# Mastery thresholds
STRONG_THRESHOLD = 70.0      # >= 70 → strong
DEVELOPING_THRESHOLD = 35.0  # 35–69 → developing
# < 35 → gap


# ─── Mastery Helpers ──────────────────────────────────────────────────────────

def normalize_skill(skill: str) -> str:
    """Normalize a skill name to its canonical form."""
    s = skill.strip().lower()
    return SKILL_ALIASES.get(s, skill.strip().title())


def initial_mastery_from_label(skill_label: str) -> float:
    """
    Convert a self-reported skill label to an initial mastery score.
    Used during onboarding when no quiz data exists yet.
    "strong" → 75, "intermediate" → 50, "basic" → 30, just "known" → 40
    """
    label = skill_label.lower()
    if "strong" in label or "expert" in label or "advanced" in label:
        return 75.0
    if "intermediate" in label or "good" in label:
        return 55.0
    if "basic" in label or "beginner" in label or "familiar" in label:
        return 30.0
    # Default for skills listed without a qualifier → they said they have it
    return 40.0


def mastery_from_experience_level(experience_level: str) -> float:
    """Base mastery to apply to known skills based on overall experience level."""
    lvl = (experience_level or "beginner").lower()
    if lvl == "advanced":
        return 70.0
    if lvl == "intermediate":
        return 55.0
    return 35.0


# ─── Skill Gap Engine ─────────────────────────────────────────────────────────

def get_role_skills(target_role: str) -> list[SkillNode]:
    """Return the skill nodes for a role, with fuzzy matching."""
    # Exact match
    if target_role in ROLE_SKILL_GRAPH:
        return ROLE_SKILL_GRAPH[target_role]
    # Case-insensitive match
    for role, nodes in ROLE_SKILL_GRAPH.items():
        if role.lower() == target_role.lower():
            return nodes
    # Partial match
    for role, nodes in ROLE_SKILL_GRAPH.items():
        if target_role.lower() in role.lower() or role.lower() in target_role.lower():
            return nodes
    # Fallback — return AI Engineer as a reasonable default
    return ROLE_SKILL_GRAPH["AI Engineer"]


def calculate_skill_gap(
    target_role: str,
    mastery_map: dict[str, float],          # skill → 0–100 mastery score
    experience_level: str = "beginner",
) -> SkillGapResult:
    """
    Pure deterministic skill-gap calculation.
    mastery_map: keys are canonical skill names, values are 0–100.
    """
    nodes = get_role_skills(target_role)

    items: list[SkillGapItem] = []
    weighted_gap_sum = 0.0
    weighted_readiness_sum = 0.0
    total_weight = 0.0

    for node in nodes:
        mastery = mastery_map.get(node.name, 0.0)

        # Gap score: how far below "strong" threshold
        gap_score = max(0.0, STRONG_THRESHOLD - mastery)

        # Status classification
        if mastery >= STRONG_THRESHOLD:
            status = "strong"
        elif mastery >= DEVELOPING_THRESHOLD:
            status = "developing"
        else:
            status = "gap"

        # Check prerequisites
        prereqs_met = all(
            mastery_map.get(p, 0.0) >= DEVELOPING_THRESHOLD
            for p in node.prerequisites
        )

        items.append(SkillGapItem(
            skill=node.name,
            required_importance=node.importance,
            current_mastery=round(mastery, 1),
            gap_score=round(gap_score, 1),
            status=status,
            prerequisites=node.prerequisites,
            prerequisites_met=prereqs_met,
        ))

        weighted_gap_sum += gap_score * node.importance
        weighted_readiness_sum += mastery * node.importance
        total_weight += node.importance * 100.0   # max possible contribution

    overall_gap_pct = round((weighted_gap_sum / (total_weight or 1)) * 100, 1)
    career_readiness_pct = round(weighted_readiness_sum / (sum(n.importance for n in nodes) or 1), 1)

    # Priority = gap × importance, descending
    gap_items_sorted = sorted(
        [i for i in items if i.status != "strong"],
        key=lambda x: x.gap_score * x.required_importance,
        reverse=True,
    )
    priority_skills = [i.skill for i in gap_items_sorted]

    strong = [i.skill for i in items if i.status == "strong"]
    developing = [i.skill for i in items if i.status == "developing"]
    gap = [i.skill for i in items if i.status == "gap"]

    return SkillGapResult(
        target_role=target_role,
        required_skills=items,
        overall_gap_pct=overall_gap_pct,
        career_readiness_pct=min(100.0, round(career_readiness_pct, 1)),
        priority_skills=priority_skills,
        strong_skills=strong,
        developing_skills=developing,
        gap_skills=gap,
    )


def build_mastery_map_from_skills(
    known_skills: list[str],
    experience_level: str = "beginner",
) -> dict[str, float]:
    """
    Build an initial mastery map from a flat list of known skills.
    Used during onboarding before any quiz evidence exists.
    """
    base = mastery_from_experience_level(experience_level)
    result: dict[str, float] = {}
    for skill in known_skills:
        canonical = normalize_skill(skill)
        result[canonical] = base
    return result


def update_mastery_from_quiz(
    current_mastery: float,
    quiz_score: float,
    evidence_count: int,
) -> float:
    """
    Bayesian-style update: blend existing mastery with new quiz evidence.
    More evidence → quiz score has less relative influence (credibility weighting).
    Formula: new = (old * weight_old + quiz * weight_new) / (weight_old + weight_new)
    weight_new = 1 / (1 + evidence_count * 0.2)  — decreases as more data accumulates
    """
    weight_new = 1.0 / (1.0 + evidence_count * 0.2)
    weight_old = 1.0 - weight_new
    new_mastery = (current_mastery * weight_old) + (quiz_score * weight_new)
    return round(min(100.0, max(0.0, new_mastery)), 1)


def get_next_best_actions(
    gap_result: SkillGapResult,
    mastery_map: dict[str, float],
    weekly_hours: int = 10,
    max_actions: int = 3,
) -> list[dict]:
    """
    Determine the top N learning actions based on:
    1. Skill is a gap (not strong)
    2. Prerequisites are met
    3. Priority (gap × importance)

    Returns a list of action dicts with skill, reason, and estimated hours.
    """
    actions = []

    for item in gap_result.required_skills:
        if item.status == "strong":
            continue
        if not item.prerequisites_met:
            # Recommend prerequisites first
            for prereq in item.prerequisites:
                prereq_mastery = mastery_map.get(prereq, 0.0)
                if prereq_mastery < DEVELOPING_THRESHOLD:
                    actions.append({
                        "skill": prereq,
                        "reason": f"Prerequisite for {item.skill} — currently at {prereq_mastery:.0f}% mastery",
                        "priority": item.required_importance * 1.2,  # bump prereqs higher
                        "estimated_hours": max(5, int(weekly_hours * 0.4)),
                        "type": "prerequisite",
                    })
            continue

        actions.append({
            "skill": item.skill,
            "reason": f"Current mastery {item.current_mastery:.0f}% — gap of {item.gap_score:.0f} points toward the {gap_result.target_role} target",
            "priority": item.gap_score * item.required_importance,
            "estimated_hours": max(3, int(weekly_hours * 0.5)),
            "type": "skill_gap",
        })

    # Deduplicate and sort by priority
    seen = set()
    unique_actions = []
    for a in sorted(actions, key=lambda x: x["priority"], reverse=True):
        if a["skill"] not in seen:
            seen.add(a["skill"])
            unique_actions.append(a)

    return unique_actions[:max_actions]


def list_known_roles() -> list[str]:
    return list(ROLE_SKILL_GRAPH.keys())
