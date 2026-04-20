"""Food vs non-food gate using CLIP zero-shot classification."""

from __future__ import annotations

import asyncio
import io
import threading

from PIL import Image, UnidentifiedImageError

from app.schemas.predict import FoodValidation

NON_FOOD_IMAGE_MESSAGES = (
    "This doesn't look like a food image. Please upload a photo of a meal.",
    "This image does not appear to be a food photo. Please upload a clear image of your meal.",
    "I could not detect food in this image. Please try again with a clearer meal photo.",
)

# Contrastive prompts: softmax index 0 = food-like.
_CLIP_TEXTS = (
    "a photo of food, a meal, or ingredients",
    "a photo with no food, such as scenery, people, text, or random objects",
)

_load_lock = threading.Lock()
_infer_lock = threading.Lock()
_clip_state: dict[str, object | None] = {
    "model_id": None,
    "model": None,
    "processor": None,
}


def _ensure_clip(model_id: str) -> tuple[object, object]:
    with _load_lock:
        if _clip_state["model"] is None or _clip_state["model_id"] != model_id:
            import torch
            from transformers import CLIPModel, CLIPProcessor

            processor = CLIPProcessor.from_pretrained(model_id)
            model = CLIPModel.from_pretrained(model_id)
            model.eval()
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model.to(device)
            _clip_state["processor"] = processor
            _clip_state["model"] = model
            _clip_state["model_id"] = model_id
        return _clip_state["model"], _clip_state["processor"]


def _compute_food_probability(image_bytes: bytes, model_id: str) -> float:
    """Return softmax probability for the food-aligned label (index 0)."""
    import torch

    model, processor = _ensure_clip(model_id)
    device = next(model.parameters()).device

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except (OSError, UnidentifiedImageError, ValueError):
        return 0.0

    inputs = processor(text=list(_CLIP_TEXTS), images=image, return_tensors="pt", padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with _infer_lock:
        with torch.no_grad():
            outputs = model(**inputs)

    logits = outputs.logits_per_image
    probs = logits.softmax(dim=1)[0]
    return float(probs[0].item())


class FoodValidationService:
    def __init__(self, model_id: str, food_probability_threshold: float) -> None:
        self._model_id = model_id
        self._threshold = food_probability_threshold

    async def validate(self, image_bytes: bytes, content_type: str | None) -> FoodValidation:
        _ = content_type
        prob = await asyncio.to_thread(_compute_food_probability, image_bytes, self._model_id)
        
        print("--------------------------------")
        print(f"Food probability: {prob}")
        print("--------------------------------")
        
        if prob >= self._threshold:
            return FoodValidation(valid=True)
        return FoodValidation(valid=False, reason="clip_low_food_probability")
