"""
Модуль определяет класс BattleMap для управления сеткой тайлов карты.
"""
from typing import List, Optional
from PIL import Image
from battlemap.sprites.map_tile import MapTileSprite


class BattleMap:
    """
    Управляет 2D сеткой тайлов `MapTileSprite` для игровой карты.
    """

    def __init__(
            self,
            map_width_tiles: int,
            map_height_tiles: int,
            default_tile_image: Optional[Image.Image] = None
            ):
        """
        Инициализирует объект BattleMap.

        Args:
            map_width_tiles (int): Ширина карты в количестве тайлов.
            map_height_tiles (int): Высота карты в количестве тайлов.
            default_tile_image (Optional[Image.Image], optional):
                Изображение для заполнения всех тайлов карты по умолчанию.
                Если None, карта останется пустой (заполнена None).
                По умолчанию None.

        Raises:
            ValueError: Если map_width_tiles или map_height_tiles не являются
                        положительными целыми числами.
        """
        if not (isinstance(map_width_tiles, int) and map_width_tiles > 0 and isinstance(map_height_tiles, int) and map_height_tiles > 0):
            raise ValueError("Размеры карты в тайлах должны быть положительными целыми числами.")

        self.map_width_tiles: int = map_width_tiles
        self.map_height_tiles: int = map_height_tiles
        self.tile_pixel_width: int = MapTileSprite.TILE_WIDTH
        self.tile_pixel_height: int = MapTileSprite.TILE_HEIGHT

        self.tiles: List[List[Optional[MapTileSprite]]] = \
            [[None for _ in range(map_width_tiles)] for _ in range(map_height_tiles)]

        if default_tile_image:
            self.fill_with_default_tiles(default_tile_image)  # Переименовал для ясности

    def fill_with_default_tiles(self, pillow_image: Image.Image):
        """
        Заполняет всю карту тайлами, используя предоставленное изображение.
        Для каждого тайла создается копия изображения.

        Args:
            pillow_image (Image.Image): Изображение для тайлов.

        Raises:
            TypeError: Если pillow_image не является объектом PIL.Image.Image.
        """
        if not isinstance(pillow_image, Image.Image):
            raise TypeError("Изображение для тайла должно быть объектом PIL.Image.Image.")

        for r in range(self.map_height_tiles):
            for c in range(self.map_width_tiles):
                # Копируем изображение, чтобы каждый тайл имел свой независимый экземпляр
                # Это особенно важно, если изображение может быть модифицировано после создания спрайта
                # (хотя MapTileSprite его все равно ресайзит, но это хорошая практика)
                tile_img_copy = pillow_image.copy()
                self.tiles[r][c] = MapTileSprite(
                        pillow_image=tile_img_copy,
                        x=c * self.tile_pixel_width,
                        y=r * self.tile_pixel_height,
                        name=f"map_tile_{r}_{c}"
                        )

    def set_tile(self, row: int, col: int, tile_sprite: MapTileSprite):
        """
        Устанавливает указанный `MapTileSprite` в ячейку карты (row, col).
        Позиция спрайта будет скорректирована, если она не соответствует ячейке.

        Args:
            row (int): Индекс строки.
            col (int): Индекс столбца.
            tile_sprite (MapTileSprite): Спрайт тайла для установки.

        Raises:
            IndexError: Если row или col выходят за пределы карты.
            TypeError: Если tile_sprite не является экземпляром MapTileSprite.
        """
        if not (0 <= row < self.map_height_tiles and 0 <= col < self.map_width_tiles):
            raise IndexError(
                    f"Координаты тайла ({row}, {col}) выходят за пределы карты "
                    f"({self.map_height_tiles}x{self.map_width_tiles})."
                    )
        if not isinstance(tile_sprite, MapTileSprite):
            raise TypeError("Объект должен быть экземпляром MapTileSprite.")

        expected_x = col * self.tile_pixel_width
        expected_y = row * self.tile_pixel_height
        if tile_sprite.x != expected_x or tile_sprite.y != expected_y:
            tile_sprite.set_position(expected_x, expected_y)

        self.tiles[row][col] = tile_sprite

    def get_tile(self, row: int, col: int) -> Optional[MapTileSprite]:
        """
        Возвращает `MapTileSprite` из указанной ячейки (row, col) или None,
        если ячейка пуста или выходит за пределы карты.
        """
        if not (0 <= row < self.map_height_tiles and 0 <= col < self.map_width_tiles):
            return None
        return self.tiles[row][col]

    def get_all_tiles(self) -> List[MapTileSprite]:
        """Возвращает плоский список всех не-None `MapTileSprite` на карте."""
        all_map_tiles: List[MapTileSprite] = []
        for r_idx in range(self.map_height_tiles):
            for c_idx in range(self.map_width_tiles):
                tile = self.tiles[r_idx][c_idx]
                if tile is not None:
                    all_map_tiles.append(tile)
        return all_map_tiles

    @property
    def total_pixel_width(self) -> int:
        """Общая ширина карты в пикселях."""
        return self.map_width_tiles * self.tile_pixel_width

    @property
    def total_pixel_height(self) -> int:
        """Общая высота карты в пикселях."""
        return self.map_height_tiles * self.tile_pixel_height

    def __repr__(self) -> str:
        return (f"<BattleMap(tiles={self.map_width_tiles}x{self.map_height_tiles}, "
                f"tile_size_px={self.tile_pixel_width}x{self.tile_pixel_height})>")