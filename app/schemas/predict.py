from pydantic import BaseModel, model_validator


class NutritionPrediction(BaseModel):
    calories: float
    protein: float
    carbs: float
    fat: float


class PredictResponse(BaseModel):
    ok: bool = True
    prediction: NutritionPrediction | None = None
    message: str | None = None
    

class FoodValidation(BaseModel):
    valid: bool
    reason: str | None = None
