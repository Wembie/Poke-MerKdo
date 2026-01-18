"""Image caching system"""

from io import BytesIO
from pathlib import Path

from diskcache import Cache
from PIL.Image import Image as PILImage
from PIL.Image import open as pil_open
from requests import get as requests_get

from poke_merkdo.config import CACHE_DIR, CACHE_EXPIRY_DAYS


class ImageCache:
    """Disk-based cache for card images"""

    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache = Cache(str(cache_dir))
        self.expiry_seconds = CACHE_EXPIRY_DAYS * 24 * 60 * 60

    def get_image(self, url: str, card_id: str) -> Path | None:
        """
        Get image from cache or download it.
        Returns path to cached image file.
        """
        if not url:
            return None

        cache_key = f"img_{card_id}"

        cached_path = self.cache.get(cache_key)
        if cached_path and Path(cached_path).exists():
            return Path(cached_path)

        try:
            image_path = self._download_image(url, card_id)
            if image_path:
                self.cache.set(cache_key, str(image_path), expire=self.expiry_seconds)
                return image_path
        except Exception as e:
            print(f"Error downloading image for {card_id}: {e}")
            return None

        return None

    def _download_image(self, url: str, card_id: str) -> Path | None:
        """Download image from URL and save to cache"""
        try:
            response = requests_get(url, timeout=30)
            response.raise_for_status()

            image_path = self.cache_dir / f"{card_id}.jpg"

            img: PILImage = pil_open(BytesIO(response.content))
            img = img.convert("RGB")
            img.save(image_path, "JPEG", quality=95)

            return image_path

        except Exception as e:
            print(f"Failed to download image: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear all cached images"""
        self.cache.clear()

    def get_cache_size(self) -> int:
        """Get cache size in bytes"""
        total_size = 0
        for item in self.cache_dir.iterdir():
            if item.is_file():
                total_size += item.stat().st_size
        return total_size
