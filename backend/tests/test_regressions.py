import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import openai
from fastapi.testclient import TestClient
from pydantic import ValidationError

from main import app
from models.recipe import Recipe, SafetyAnalysis
from services.cleaner import clean_transcript
from services.cooking_assistant import answer_cooking_question
from services.parser_llm import NoRecipeError, RecipeParseError, parse_recipe_with_llm
from services.safety_analyzer import SafetyParseError, analyze_recipe_safety
from utils.youtube import extract_video_id


VIDEO_ID = "dQw4w9WgXcQ"
VIDEO_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"
RECIPE_DATA = {
    "title": "Eggs",
    "estimated_time": "5 minutes",
    "difficulty": "Easy",
    "equipment": ["Pan"],
    "ingredients": [{"name": "Eggs", "quantity": "2"}],
    "steps": [{"step_number": 7, "instruction": "Cook the eggs."}],
}
SAFETY_DATA = {"safety_warnings": [], "first_aid": []}


def mock_completion(content):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


class DataValidationTests(unittest.TestCase):
    def test_video_url_formats_and_invalid_ids(self):
        for url in (
            VIDEO_URL,
            f"https://youtu.be/{VIDEO_ID}?t=1",
            f"https://m.youtube.com/shorts/{VIDEO_ID}",
            f"https://youtube.com/live/{VIDEO_ID}",
        ):
            with self.subTest(url=url):
                self.assertEqual(extract_video_id(url), VIDEO_ID)
        for url in (
            "https://youtube.com/watch?v=bad",
            f"https://notyoutube.com/watch?v={VIDEO_ID}",
            f"https://youtube.com/playlist?v={VIDEO_ID}",
            f"https://youtu.be/{VIDEO_ID}/extra",
        ):
            with self.subTest(url=url):
                self.assertIsNone(extract_video_id(url))

    def test_short_spoken_captions_survive_noise_cleanup(self):
        self.assertEqual(
            clean_transcript(["[Music]", "2 eggs", "[Applause] Add salt", "Bake 20m"]),
            ["2 eggs", "Add salt", "Bake 20m"],
        )

    def test_empty_or_unusable_recipes_are_rejected(self):
        for change in ({"ingredients": []}, {"steps": []}, {"title": "  "}):
            with self.subTest(change=change):
                with self.assertRaises(ValidationError):
                    Recipe.model_validate({**RECIPE_DATA, **change})

    def test_parser_renumbers_steps_and_reports_invalid_output(self):
        with patch("services.parser_llm.get_client") as get_client:
            create = get_client.return_value.chat.completions.create
            create.return_value = mock_completion(json.dumps(RECIPE_DATA))
            recipe = parse_recipe_with_llm(["2 eggs", "Cook the eggs."])
            self.assertEqual(recipe.steps[0].step_number, 1)
            create.return_value = mock_completion(json.dumps({**RECIPE_DATA, "steps": []}))
            with self.assertRaises(RecipeParseError):
                parse_recipe_with_llm(["2 eggs"])
            create.return_value = mock_completion('{"error": "not_a_recipe"}')
            with self.assertRaises(NoRecipeError):
                parse_recipe_with_llm(["A travel vlog with no cooking."])

    def test_invalid_safety_output_is_not_reported_as_no_hazards(self):
        with patch("services.safety_analyzer.get_client") as get_client:
            get_client.return_value.chat.completions.create.return_value = mock_completion("{}")
            with self.assertRaises(SafetyParseError):
                analyze_recipe_safety(Recipe.model_validate(RECIPE_DATA))

    def test_empty_cooking_answer_is_detected(self):
        with patch("services.cooking_assistant.get_client") as get_client:
            get_client.return_value.chat.completions.create.return_value = SimpleNamespace(choices=[])
            self.assertIsNone(answer_cooking_question(RECIPE_DATA, 0, "How long?"))


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_transcript_success_preserves_short_captions(self):
        with (
            patch("main.get_transcript", return_value=["[Music]", "2 eggs", "Cook the eggs."]),
            patch("main.parse_recipe_with_llm", return_value=Recipe.model_validate(RECIPE_DATA)) as parse,
            patch("main.analyze_recipe_safety", return_value=SafetyAnalysis.model_validate(SAFETY_DATA)),
        ):
            response = self.client.get("/transcript/", params={"url": VIDEO_URL})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(parse.call_args.args[0], ["2 eggs", "Cook the eggs."])
        self.assertEqual(response.json()["title"], "Eggs")
        self.assertEqual(response.json()["steps"][0]["instruction"], "Cook the eggs.")

    def test_transcript_rejects_invalid_requests_before_ai(self):
        for params, status in (
            ({"url": "https://youtube.com/watch?v=bad"}, 400),
            ({"url": VIDEO_URL, "mode": "unknown"}, 422),
            ({"url": VIDEO_URL, "mode": "whisper"}, 501),
        ):
            with self.subTest(params=params):
                with patch("main.get_transcript") as get_transcript:
                    response = self.client.get("/transcript/", params=params)
                self.assertEqual(response.status_code, status)
                get_transcript.assert_not_called()

        for captions, status in ((["[Music]"], 422), (["a" * 16_001], 413)):
            with self.subTest(status=status):
                with (
                    patch("main.get_transcript", return_value=captions),
                    patch("main.parse_recipe_with_llm") as parse,
                ):
                    response = self.client.get("/transcript/", params={"url": VIDEO_URL})
                self.assertEqual(response.status_code, status)
                parse.assert_not_called()

    def test_transcript_reports_safety_failure(self):
        with (
            patch("main.get_transcript", return_value=["Cook the eggs."]),
            patch("main.parse_recipe_with_llm", return_value=Recipe.model_validate(RECIPE_DATA)),
            patch("main.analyze_recipe_safety", side_effect=SafetyParseError("bad JSON")),
        ):
            response = self.client.get("/transcript/", params={"url": VIDEO_URL})
        self.assertEqual(response.status_code, 502)
        self.assertIn("safety", response.json()["detail"])

    def test_transcript_reports_non_recipe_captions(self):
        with (
            patch("main.get_transcript", return_value=["A travel vlog with no cooking."]),
            patch("main.parse_recipe_with_llm", side_effect=NoRecipeError("not a recipe")),
            patch("main.analyze_recipe_safety") as safety,
        ):
            response = self.client.get("/transcript/", params={"url": VIDEO_URL})
        self.assertEqual(response.status_code, 422)
        safety.assert_not_called()

    def test_ask_validates_step_and_question(self):
        for change in ({"current_step": -1}, {"current_step": 1}, {"question": "   "}):
            with self.subTest(change=change):
                with patch("main.answer_cooking_question") as answer:
                    response = self.client.post(
                        "/ask/",
                        json={"recipe": RECIPE_DATA, "current_step": 0, "question": "How long?", **change},
                    )
                self.assertEqual(response.status_code, 422)
                answer.assert_not_called()

    def test_ask_returns_answer_and_rejects_empty_ai_reply(self):
        body = {"recipe": RECIPE_DATA, "current_step": 0, "question": "How long?"}
        with patch("main.answer_cooking_question", return_value="  Five minutes.  ") as answer:
            response = self.client.post("/ask/", json=body)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"answer": "Five minutes."})
        self.assertEqual(answer.call_args.kwargs["current_step"], 0)
        with patch("main.answer_cooking_question", return_value=None):
            response = self.client.post("/ask/", json=body)
        self.assertEqual(response.status_code, 502)

    def test_ai_service_failure_is_reported(self):
        body = {"recipe": RECIPE_DATA, "current_step": 0, "question": "How long?"}
        with patch("main.answer_cooking_question", side_effect=openai.OpenAIError("Unavailable")):
            response = self.client.post("/ask/", json=body)
        self.assertEqual(response.status_code, 503)

        with (
            patch("main.get_transcript", return_value=["Cook the eggs."]),
            patch("main.parse_recipe_with_llm", side_effect=openai.OpenAIError("Unavailable")),
        ):
            response = self.client.get("/transcript/", params={"url": VIDEO_URL})
        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
