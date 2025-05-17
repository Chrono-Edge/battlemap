"""
Модуль определяет базовый класс для всех спрайтов в системе рендеринга.
"""
from typing import Tuple
from PIL import Image


class BaseSprite:
    """
    Базовый класс для 2D спрайтов.

    Атрибуты:
        x (int): Координата X левого верхнего угла спрайта на холсте.
        y (int): Координата Y левого верхнего угла спрайта на холсте.
        name (str): Имя спрайта, полезно для отладки.
        visible (bool): Определяет, будет ли спрайт отрисован.
        _raw_image (Image.Image): Приватный атрибут, хранящий PIL Image объект (в RGBA).
    """

    def __init__(self, pillow_image: Image.Image, x: int = 0, y: int = 0, name: str = ""):
        """
        Инициализирует объект BaseSprite.

        Args:
            pillow_image (Image.Image): Исходное изображение Pillow для спрайта.
            x (int, optional): Начальная X-координата. По умолчанию 0.
            y (int, optional): Начальная Y-координата. По умолчанию 0.
            name (str, optional): Имя спрайта. Если не указано, генерируется.
                                По умолчанию "".

        Raises:
            TypeError: Если pillow_image не является объектом PIL.Image.Image.
            ValueError: Если x или y не являются целыми числами.
        """
        if not isinstance(pillow_image, Image.Image):
            raise TypeError("pillow_image должен быть объектом PIL.Image.Image.")
        if not (isinstance(x, int) and isinstance(y, int)):
            raise ValueError("Координаты спрайта (x, y) должны быть целыми числами.")

        self._raw_image: Image.Image = pillow_image.convert("RGBA")
        self.x: int = x
        self.y: int = y
        self.name: str = name if name else f"{self.__class__.__name__}_{id(self)}"
        self.visible: bool = True

    @property
    def image(self) -> Image.Image:
        """
        Возвращает объект PIL.Image.Image для этого спрайта.
        Изображение всегда в формате RGBA.
        """
        return self._raw_image

    @image.setter
    def image(self, new_pillow_image: Image.Image):
        """
        Устанавливает новое изображение для спрайта.
        Новое изображение будет конвертировано в RGBA.

        Args:
            new_pillow_image (Image.Image): Новый объект PIL.Image.Image.

        Raises:
            TypeError: Если new_pillow_image не является объектом PIL.Image.Image.
        """
        if not isinstance(new_pillow_image, Image.Image):
            raise TypeError("Новое изображение должно быть объектом PIL.Image.Image.")
        self._raw_image = new_pillow_image.convert("RGBA")

    @property
    def width(self) -> int:
        """Ширина текущего изображения спрайта в пикселях."""
        return self._raw_image.width

    @property
    def height(self) -> int:
        """Высота текущего изображения спрайта в пикселях."""
        return self._raw_image.height

    @property
    def size(self) -> Tuple[int, int]:
        """Размер текущего изображения спрайта (ширина, высота) в пикселях."""
        return self._raw_image.size

    def set_position(self, x: int, y: int):
        """
        Устанавливает новую позицию (x, y) для спрайта.

        Args:
            x (int): Новая X-координата.
            y (int): Новая Y-координата.

        Raises:
            ValueError: Если x или y не являются целыми числами.
        """
        if not (isinstance(x, int) and isinstance(y, int)):
            raise ValueError("Координаты (x, y) должны быть целыми числами.")
        self.x = x
        self.y = y

    def move(self, dx: int, dy: int):
        """
        Сдвигает спрайт на указанные смещения dx и dy.

        Args:
            dx (int): Смещение по оси X.
            dy (int): Смещение по оси Y.

        Raises:
            ValueError: Если dx или dy не являются целыми числами.
        """
        if not (isinstance(dx, int) and isinstance(dy, int)):
            raise ValueError("Смещения (dx, dy) должны быть целыми числами.")
        self.x += dx
        self.y += dy

    def __repr__(self) -> str:
        """Возвращает строковое представление объекта для отладки."""
        return (f"<{self.__class__.__name__}(name='{self.name}', size={self.size}, "
                f"pos=({self.x},{self.y}), visible={self.visible})>")