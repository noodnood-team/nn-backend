from pydantic import BaseModel


class NutritionPrediction(BaseModel):
    calories: float
    protein: float
    carbs: float
    fat: float


class PredictResponse(BaseModel):
    ok: bool = True
    prediction: NutritionPrediction
