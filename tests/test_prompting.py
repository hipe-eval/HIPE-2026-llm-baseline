from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hipe2026_mistral_baseline.io_hipe import load_jsonl
from hipe2026_mistral_baseline.pair_generation import build_pair_tasks
from hipe2026_mistral_baseline.prompting import build_prompt


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_input.jsonl"


class TestPrompting(unittest.TestCase):
    def test_prompt_places_pair_context_after_article_text(self) -> None:
        document = load_jsonl(FIXTURE_PATH)[0]
        task = build_pair_tasks(document)[0]
        template = (
            "Document language: {language}\n"
            "Publication date: {publication_date}\n"
            "Article text:\n{article_text}\n\n"
            "{pair_context}"
        )

        prompt = build_prompt(task, template)

        article_text_index = prompt.index("Article text:")
        pair_context_index = prompt.index("Pair to classify:")

        self.assertLess(article_text_index, pair_context_index)
        self.assertIn(task.text, prompt)
        self.assertIn(task.pair.person_value, prompt)
        self.assertIn(task.pair.place_value, prompt)


if __name__ == "__main__":
    unittest.main()
