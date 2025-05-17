"""
Модуль определяет типы размеров токенов и базовый класс для спрайтов токенов.
"""
from enum import Enum
from typing import Tuple
from PIL import Image
from battlemap.sprites.base_sprite import BaseSprite
from battlemap.sprites.map_tile import MapTileSprite  # Для констант размера тайла


class TokenSize(Enum):
    """
    Перечисление для определения логического размера токена на карте в тайлах.
    """
    SIZE_1x1 = (1, 1)
    SIZE_2x2 = (2, 2)
    SIZE_3x3 = (3, 3)

    def __init__(self, width_tiles: int, height_tiles: int):
        """Не используется напрямую, Enum обрабатывает это."""
        self._width_tiles_val = width_tiles
        self._height_tiles_val = height_tiles

    @property
    def tiles_width(self) -> int:
        """Ширина токена в единицах тайлов."""
        return self.value[0]  # Enum.value хранит кортеж

    @property
    def tiles_height(self) -> int:
        """Высота токена в единицах тайлов."""
        return self.value[1]  # Enum.value хранит кортеж

    def get_logical_pixel_dimensions(self) -> Tuple[int, int]:
        """
        Возвращает логический размер токена в пикселях, который он должен
        занимать на карте при рендеринге. Рассчитывается на основе
        размера одного тайла из `MapTileSprite`.
        """
        return (self.tiles_width * MapTileSprite.TILE_WIDTH,
                self.tiles_height * MapTileSprite.TILE_HEIGHT)

    def __str__(self) -> str:
        return f"{self.tiles_width}x{self.tiles_height} tiles"


class TokenTileSprite(BaseSprite):
    """
    Базовый класс для спрайтов, представляющих игровые токены.

    Текстура (изображение) такого спрайта всегда приводится к фиксированному
    размеру `FIXED_TEXTURE_SIZE` (например, 70x70 пикселей).
    Логический размер токена на карте определяется атрибутом `token_size_enum`
    и используется рендерером для масштабирования текстуры при отрисовке.

    Атрибуты класса:
        TEXTURE_WIDTH (int): Ширина текстуры токена по умолчанию.
        TEXTURE_HEIGHT (int): Высота текстуры токена по умолчанию.
        FIXED_TEXTURE_SIZE (Tuple[int, int]): Кортеж (TEXTURE_WIDTH, TEXTURE_HEIGHT).
    """
    TEXTURE_WIDTH: int = MapTileSprite.TILE_WIDTH
    TEXTURE_HEIGHT: int = MapTileSprite.TILE_HEIGHT
    FIXED_TEXTURE_SIZE: tuple[int, int] = (TEXTURE_WIDTH, TEXTURE_HEIGHT)

    def __init__(
            self,
            pillow_image: Image.Image,
            token_size: TokenSize,
            initially_visible: bool = True,
            x: int = 0,
            y: int = 0,
            name: str = "token_sprite",
            ):
        """
        Инициализирует TokenTileSprite.

        Args:
            pillow_image (Image.Image): Исходное изображение для текстуры токена.
                                       Будет изменено до FIXED_TEXTURE_SIZE.
            token_size (TokenSize): Логический размер токена на карте.
            initially_visible (bool, optional): Начальная видимость спрайта.
                                                По умолчанию True.
            x (int, optional): Начальная X-координата. По умолчанию 0.
            y (int, optional): Начальная Y-координата. По умолчанию 0.
            name (str, optional): Имя спрайта. По умолчанию "token_sprite".
        """
        self.token_size_enum: TokenSize = token_size

        processed_image: Image.Image
        if pillow_image.size != self.FIXED_TEXTURE_SIZE:
            try:
                processed_image = pillow_image.resize(
                        self.FIXED_TEXTURE_SIZE,
                        Image.Resampling.LANCZOS
                        )
            except Exception as e:
                # Логирование или предупреждение
                print(
                    f"Warning: TokenTileSprite '{name}': Error resizing image to {self.FIXED_TEXTURE_SIZE}: {e}. "
                    f"Using original size {pillow_image.size}."
                    )
                processed_image = pillow_image
        else:
            processed_image = pillow_image

        super().__init__(processed_image, x, y, name)
        self.visible = initially_visible

    @property
    def logical_pixel_width(self) -> int:
        """
        Логическая ширина в пикселях, которую токен должен занимать на карте.
        Используется рендерером для масштабирования текстуры.
        """
        return self.token_size_enum.get_logical_pixel_dimensions()[0]

    @property
    def logical_pixel_height(self) -> int:
        """
        Логическая высота в пикселях, которую токен должен занимать на карте.
        Используется рендерером для масштабирования текстуры.
        """
        return self.token_size_enum.get_logical_pixel_dimensions()[1]

    def hide(self):
        """Устанавливает спрайт как невидимый."""
        self.visible = False

    def show(self):
        """Устанавливает спрайт как видимый."""
        self.visible = True

    def toggle_visibility(self):
        """Переключает состояние видимости спрайта."""
        self.visible = not self.visible

    @BaseSprite.image.setter
    def image(self, new_pillow_image: Image.Image):
        """
        Устанавливает новое изображение для текстуры токена.
        Новое изображение будет конвертировано в RGBA и изменено до FIXED_TEXTURE_SIZE.
        """
        if not isinstance(new_pillow_image, Image.Image):
            raise TypeError("Новое изображение должно быть объектом PIL.Image.Image.")

        resized_image: Image.Image
        if new_pillow_image.size != self.FIXED_TEXTURE_SIZE:
            try:
                resized_image = new_pillow_image.resize(
                        self.FIXED_TEXTURE_SIZE,
                        Image.Resampling.LANCZOS
                        )
            except Exception as e:
                print(
                    f"Warning: TokenTileSprite '{self.name}': Error resizing new image: {e}. "
                    f"Using original size {new_pillow_image.size}."
                    )
                resized_image = new_pillow_image
        else:
            resized_image = new_pillow_image

        # Используем BaseSprite.image.fset для вызова сеттера родительского класса
        # Это важно, если в BaseSprite.image.setter есть своя логика (например, конвертация в RGBA)
        BaseSprite.image.fset(self, resized_image)

    def set_grid_position(
            self, grid_col: int, grid_row: int,
            tile_width: int = MapTileSprite.TILE_WIDTH,
            tile_height: int = MapTileSprite.TILE_HEIGHT
            ):
        """
        Устанавливает позицию спрайта на основе координат сетки (тайлов).
        Левый верхний угол спрайта будет совмещен с левым верхним углом ячейки сетки.

        Args:
            grid_col (int): Индекс столбца в сетке (начиная с 0).
            grid_row (int): Индекс строки в сетке (начиная с 0).
            tile_width (int, optional): Ширина одного тайла сетки в пикселях.
                                        По умолчанию используется MapTileSprite.TILE_WIDTH.
            tile_height (int, optional): Высота одного тайла сетки в пикселях.
                                         По умолчанию используется MapTileSprite.TILE_HEIGHT.
        """
        if not (isinstance(grid_col, int) and isinstance(grid_row, int)):
            raise ValueError("Координаты сетки (grid_col, grid_row) должны быть целыми числами.")

        self.x = grid_col * tile_width
        self.y = grid_row * tile_height

    def get_grid_position(
            self,
            tile_width: int = MapTileSprite.TILE_WIDTH,
            tile_height: int = MapTileSprite.TILE_HEIGHT
            ) -> Tuple[int, int]:
        """
        Возвращает текущую позицию спрайта в координатах сетки (столбец, строка).
        Рассчитывается на основе текущих пиксельных координат x, y и размеров тайла.
        Округление до ближайшего целого тайла для левого верхнего угла.

        Args:
            tile_width (int, optional): Ширина одного тайла сетки в пикселях.
            tile_height (int, optional): Высота одного тайла сетки в пикселях.

        Returns:
            Tuple[int, int]: Кортеж (grid_col, grid_row).

        Raises:
            ValueError: Если tile_width или tile_height не положительные.
        """
        if tile_width <= 0 or tile_height <= 0:
            raise ValueError("Размеры тайла для расчета сеточной позиции должны быть положительными.")

        # Округление к ближайшему тайлу для левого верхнего угла
        # Например, если тайл 70, x=30 -> col=0; x=36 -> col=1 (если округлять стандартно)
        # или x=75 -> col=1.
        # Для привязки левого верхнего угла к сетке, лучше использовать floor или round,
        # в зависимости от желаемого поведения при перетаскивании.
        # round() - к ближайшему.
        grid_col = round(self.x / tile_width)
        grid_row = round(self.y / tile_height)
        return grid_col, grid_row

    # --- КОНЕЦ ДОБАВЛЕННЫХ МЕТОДОВ ---

    def __repr__(self) -> str:
        return (f"<{self.__class__.__name__}(name='{self.name}', "
                f"texture_size={self.size}, "
                f"logical_tiles={self.token_size_enum}, "
                f"logical_px={self.logical_pixel_width}x{self.logical_pixel_height}, "
                f"pos=({self.x},{self.y}), visible={self.visible})>")
