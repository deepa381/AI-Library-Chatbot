"""
enrichment.py
=============
STEP 6 of the pipeline: generates every AI-specific field the spec asks for
(mood, writing style, difficulty, reading level, target audience, learning
outcomes, skills covered, recommendation keywords, fantasy/sci-fi elements,
search_text, short/long AI summaries, recommendation_reason).

Two tiers, matching how you'd actually run this in production:

  1. `rule_based_enrich()` (used here) — deterministic, explainable, free,
     driven by GENRE_PROFILE + the book's own subjects/description. Good
     enough for a first pass / demo, and a safe fallback when an LLM call
     fails or is rate-limited.

  2. `llm_enrich()` (stub) — for production quality, replace/augment this
     with a real LLM call (e.g. the Claude API) per book, using a prompt
     like:
        "Given this book's title, authors, description, and subjects,
         return JSON with: mood[], writing_style[], difficulty_level,
         reading_level, target_audience[], learning_outcomes[],
         skills_covered[], recommendation_keywords[10-30],
         short_ai_summary (1 sentence), long_ai_summary (150-250 words),
         recommendation_reason (1-2 sentences)."
     Batch these calls (e.g. 20-50 books per LLM call) to control cost at
     3,000-5,000-book scale, and cache results in data/processed/.
"""
import math
import re

from pipeline.config import GENRE_PROFILE, GENRE_LEARNING_OUTCOMES, WORDS_PER_MINUTE

FANTASY_TERMS = {"magic", "dragons", "kingdoms", "mythology", "witchcraft", "gods", "quest", "wizard"}
SCIFI_TERMS = {"space", "ai", "artificial intelligence", "robots", "cyberpunk", "time travel",
               "space travel", "first contact", "virtual reality"}

DEFAULT_PROFILE = dict(mood=["Educational"], style=["Narrative"], difficulty="Intermediate",
                        reading_level="Adult", audience=["General Readers"])


def _skills_from_subjects(subjects):
    subject_skill_map = {
        "personal finance": "Finance", "investing": "Finance", "leadership": "Management",
        "entrepreneurship": "Entrepreneurship", "productivity": "Productivity",
        "psychology": "Psychology", "history": "History", "technology": "Technology",
        "communication": "Communication", "cosmology": "Physics", "physics": "Physics",
    }
    skills = set()
    for s in subjects:
        skills.add(subject_skill_map.get(s.lower(), None))
    return sorted(s for s in skills if s)


def _recommendation_keywords(rec):
    pool = set()
    pool.update(w.lower() for w in (rec.get("subjects") or []))
    pool.update((rec.get("genre") or "").lower().split())
    pool.update((rec.get("subgenre") or "").lower().replace("/", " ").split())
    title_words = re.findall(r"[a-zA-Z]{4,}", (rec.get("title") or "").lower())
    pool.update(title_words[:5])
    pool.discard("")
    kws = sorted(pool)
    # pad/trim to the 10-30 range the spec asks for
    return kws[:30] if len(kws) >= 10 else kws


def _elements(subjects, term_set):
    subj_lower = {s.lower() for s in subjects}
    return sorted(term_set & subj_lower) or None


def _reading_time_minutes(pages):
    if not pages:
        return None
    words = pages * 275  # ~275 words/page average for trade fiction
    return round(words / WORDS_PER_MINUTE)


def _short_summary(rec):
    return f"{rec['title']} by {', '.join(rec['authors'])} — {rec.get('subgenre') or rec.get('genre')} exploring {', '.join((rec.get('subjects') or ['its themes'])[:2])}."


def _long_summary(rec):
    subj = ", ".join((rec.get("subjects") or [])[:5]) or "its central themes"
    return (
        f"{rec['title']}, written by {', '.join(rec['authors'])} and first published in "
        f"{rec.get('pub_year') or 'an unknown year'}, is a {rec.get('genre', 'book').lower()} work "
        f"({rec.get('subgenre') or 'general'}) set against a backdrop of {rec.get('country_setting') or 'its story world'} "
        f"during {rec.get('time_setting') or 'its narrative period'}. {rec.get('description', '')} "
        f"Readers drawn to {subj} will find this book especially rewarding, and it is commonly recommended "
        f"for {', '.join(GENRE_PROFILE.get(rec.get('genre'), DEFAULT_PROFILE)['audience'])} looking for a "
        f"{'/'.join(GENRE_PROFILE.get(rec.get('genre'), DEFAULT_PROFILE)['mood']).lower()} reading experience "
        f"at a {GENRE_PROFILE.get(rec.get('genre'), DEFAULT_PROFILE)['difficulty'].lower()} difficulty level."
    ).strip()


def _recommendation_reason(rec):
    profile = GENRE_PROFILE.get(rec.get("genre"), DEFAULT_PROFILE)
    return (f"Recommended for readers who enjoy {profile['mood'][0].lower()} "
            f"{rec.get('genre', 'stories').lower()} with a {profile['style'][0].lower()} style, "
            f"especially fans of themes like {', '.join((rec.get('subjects') or [])[:2]) or rec.get('genre')}.")


def rule_based_enrich(rec):
    profile = GENRE_PROFILE.get(rec.get("genre"), DEFAULT_PROFILE)
    subjects = rec.get("subjects") or []

    rec["mood"] = profile["mood"]
    rec["writing_style"] = profile["style"]
    rec["difficulty_level"] = profile["difficulty"]
    rec["reading_level"] = profile["reading_level"]
    rec["target_audience"] = profile["audience"]
    rec["learning_outcomes"] = GENRE_LEARNING_OUTCOMES.get(rec.get("genre"), [])
    rec["skills_covered"] = _skills_from_subjects(subjects)
    rec["recommendation_keywords"] = _recommendation_keywords(rec)
    rec["fantasy_elements"] = _elements(subjects, FANTASY_TERMS) if rec.get("genre") == "Fantasy" else None
    rec["scifi_elements"] = _elements(subjects, SCIFI_TERMS) if rec.get("genre") == "Science Fiction" else None
    rec["reading_time_minutes"] = _reading_time_minutes(rec.get("pages"))
    rec["themes"] = subjects[:6]
    rec["keywords"] = rec["recommendation_keywords"][:15]
    rec["tags"] = sorted(set(subjects) | set(profile["mood"]))

    rec["search_text"] = " | ".join(filter(None, [
        rec.get("title"), ", ".join(rec.get("authors") or []),
        rec.get("genre"), rec.get("subgenre"), rec.get("description"),
        ", ".join(rec.get("keywords") or []), ", ".join(rec.get("tags") or []),
        ", ".join(subjects),
    ]))

    rec["short_ai_summary"] = _short_summary(rec)
    rec["long_ai_summary"] = _long_summary(rec)
    rec["recommendation_reason"] = _recommendation_reason(rec)
    return rec


def llm_enrich(rec, client=None):
    """
    STUB for production use. Wire this up to the Anthropic API to replace/
    refine the rule-based fields above with model-generated judgments,
    e.g.:

        prompt = f'''Given this book, return ONLY JSON with keys mood,
        writing_style, difficulty_level, reading_level, target_audience,
        learning_outcomes, skills_covered, recommendation_keywords (10-30),
        short_ai_summary, long_ai_summary (150-250 words), recommendation_reason.
        Title: {rec["title"]}
        Authors: {rec["authors"]}
        Description: {rec["description"]}
        Subjects: {rec["subjects"]}'''

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        # parse response, json.loads, merge into rec

    Left unimplemented here so the pipeline runs with zero external
    dependencies/keys out of the box; call this instead of
    rule_based_enrich() once you have API access wired in.
    """
    raise NotImplementedError("Wire this to your LLM provider for production-grade enrichment.")


def enrich_all(records):
    return [rule_based_enrich(r) for r in records]
