"""
Модуль определяет спрайт для одного тайла карты.
"""
from PIL import Image
from battlemap.sprites.base_sprite import BaseSprite

class MapTileSprite(BaseSprite):
    """
    Спрайт для одного тайла карты.
    Гарантирует, что его изображение всегда имеет фиксированный размер,
    определяемый константами TILE_WIDTH и TILE_HEIGHT.

    Атрибуты класса:
        TILE_WIDTH (int): Стандартная ширина тайла в пикселях.
        TILE_HEIGHT (int): Стандартная высота тайла в пикселях.
        TARGET_SIZE (Tuple[int, int]): Кортеж (TILE_WIDTH, TILE_HEIGHT).
    """
    TILE_WIDTH: int = 70
    TILE_HEIGHT: int = 70
    TARGET_SIZE: tuple[int, int] = (TILE_WIDTH, TILE_HEIGHT)

    def __init__(self, pillow_image: Image.Image, x: int = 0, y: int = 0, name: str = "map_tile"):
        """
        Инициализирует MapTileSprite.

        Args:
            pillow_image (Image.Image): Исходное изображение для тайла.
                                       Оно будет изменено до TARGET_SIZE.
            x (int, optional): Начальная X-координата. По умолчанию 0.
            y (int, optional): Начальная Y-координата. По умолчанию 0.
            name (str, optional): Имя спрайта. По умолчанию "map_tile".
        """
        super().__init__(pillow_image, x, y, name)
        self._force_target_size()

    def _force_target_size(self):
        """
        Принудительно изменяет размер внутреннего изображения `_raw_image`
        до `TARGET_SIZE`. Использует `Image.Resampling.LANCZOS` для качественного ресайза.
        """
        if self._raw_image.size != self.TARGET_SIZE:
            try:
                self._raw_image = self._raw_image.resize(self.TARGET_SIZE, Image.Resampling.LANCZOS)
            except Exception as e:
                # В библиотеке лучше не выводить print, а логировать или дать возможность обработать
                # Для простоты оставим print, но это место для улучшения (например, logging)
                print(f"Warning: MapTileSprite '{self.name}': Error resizing image to {self.TARGET_SIZE}: {e}. "
                      f"Original size {self._raw_image.size} kept.")


    @BaseSprite.image.setter
    def image(self, new_pillow_image: Image.Image):
        """
        Устанавливает новое изображение для тайла.
        Новое изображение будет конвертировано в RGBA и изменено до TARGET_SIZE.

        Args:
            new_pillow_image (Image.Image): Новый объект PIL.Image.Image.
        """
        # Вызов сеттера родительского класса через BaseSprite.image.fset(self, new_pillow_image)
        # или напрямую, как здесь, если уверены в последствиях.
        # Это установит self._raw_image и конвертирует в RGBA.
        if not isinstance(new_pillow_image, Image.Image):
            raise TypeError("Новое изображение должно быть объектом PIL.Image.Image.")
        self._raw_image = new_pillow_image.convert("RGBA")
        self._force_target_size() # Затем применяем наше правило размера