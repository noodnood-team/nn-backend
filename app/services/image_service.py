from app.core.errors import ImageValidationError

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ImageService:
    def __init__(self, max_image_size_bytes: int) -> None:
        self._max_image_size_bytes = max_image_size_bytes

    def validate(self, image_bytes: bytes, content_type: str | None) -> None:
        if not content_type or content_type.lower() not in ALLOWED_IMAGE_TYPES:
            raise ImageValidationError("Unsupported image type")
        if len(image_bytes) == 0:
            raise ImageValidationError("Uploaded image is empty")
        if len(image_bytes) > self._max_image_size_bytes:
            raise ImageValidationError("Image exceeds maximum size")

    def preprocess(self, image_bytes: bytes) -> bytes:
        return image_bytes
