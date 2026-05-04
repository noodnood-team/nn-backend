from openai import AsyncOpenAI
from app.core.logging import get_logger
from app.schemas.predict import NutritionPrediction

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "You are a friendly nutrition assistant. Given estimated macros for a meal, "
    "write one short answer that briefly summarizes the numbers "
    "and offers one practical, non-alarmist tip. Do not claim medical certainty; "
    "these are estimates from an image."
)

class OpenAIService:
    def __init__(self, api_key: str, model: str, timeout: float) -> None:
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout) if api_key else None
        self._model = model

    async def generate_message(self, nutrition: NutritionPrediction) -> str | None:
        if self._client is None:
            return None
        user_content = (
            f"Estimated nutrition for this meal: "
            f"calories={nutrition.calories}, protein_g={nutrition.protein}, "
            f"carbs_g={nutrition.carbs}, fat_g={nutrition.fat}. "
            "Respond with the short answer only."
        )
        try:
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
            )
            choice = resp.choices[0].message.content if resp.choices else None
            text = (choice or "").strip()
            return text or None
        except Exception as exc:
            logger.warning("Openai message generation failed: %s", exc)
            return None
