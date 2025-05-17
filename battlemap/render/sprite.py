"""
Модуль предоставляет SpriteRenderer для 2D рендеринга спрайтов со слоями.
"""
import pathlib
from typing import Any, Dict, NewType, Optional, Tuple, TypeAlias  # Добавил типы

from PIL import Image, ImageDraw, ImageFont

from .grid_artist import GridArtist
# Относительные импорты для использования внутри пакета
from ..sprites.base_sprite import BaseSprite
from ..sprites.map_tile import MapTileSprite
from ..sprites.token_tile import TokenTileSprite

RGBA: TypeAlias = Tuple[int, int, int, int]


class SpriteRenderer:
    """
    Рендерер для 2D спрайтов с поддержкой слоев.

    Создает финальное изображение путем последовательного наложения спрайтов
    со слоев в порядке их z-индекса.
    Имеет ограничение на максимальный размер холста.

    Атрибуты класса:
        MAX_TILES_WIDE (int): Максимальная ширина рендера в тайлах.
        MAX_TILES_HIGH (int): Максимальная высота рендера в тайлах.
        DEFAULT_TILE_PIXEL_WIDTH (int): Пиксельная ширина тайла по умолчанию.
        DEFAULT_TILE_PIXEL_HEIGHT (int): Пиксельная высота тайла по умолчанию.
        MAX_RENDER_WIDTH (int): Максимальная ширина холста рендера в пикселях.
        MAX_RENDER_HEIGHT (int): Максимальная высота холста рендера в пикселях.

    Атрибуты экземпляра:
        width (int): Текущая ширина холста рендера.
        height (int): Текущая высота холста рендера.
        background_color (Tuple[int, int, int, int]): Цвет фона RGBA.
        layers (Dict[str, Dict[str, Any]]): Словарь для хранения слоев и их спрайтов.
    """
    MAX_TILES_WIDE: int = 64
    MAX_TILES_HIGH: int = 64

    DEFAULT_TILE_PIXEL_WIDTH: int = MapTileSprite.TILE_WIDTH
    DEFAULT_TILE_PIXEL_HEIGHT: int = MapTileSprite.TILE_HEIGHT

    MAX_RENDER_WIDTH: int = MAX_TILES_WIDE * DEFAULT_TILE_PIXEL_WIDTH
    MAX_RENDER_HEIGHT: int = MAX_TILES_HIGH * DEFAULT_TILE_PIXEL_HEIGHT

    def __init__(
            self, width: int, height: int,
            background_color: RGBA = (0, 0, 0, 0),
            grid_color: RGBA = (128, 128, 128, 150),
            label_color: RGBA = (255, 255, 255, 200),
            label_font_path: Optional[str] = None,
            label_font_size: int = 20
            ):
        """
        Инициализирует SpriteRenderer.

        Args:
            width (int): Желаемая ширина холста. Будет ограничена MAX_RENDER_WIDTH.
            height (int): Желаемая высота холста. Будет ограничена MAX_RENDER_HEIGHT.
            background_color (Tuple[int, int, int, int], optional):
                Цвет фона в формате RGBA. По умолчанию прозрачный (0,0,0,0).

        Raises:
            ValueError: Если начальные width или height (до ограничения)
                        не являются положительными целыми числами.
        """
        if not (isinstance(width, int) and width > 0 and
                isinstance(height, int) and height > 0):
            raise ValueError("Начальные ширина и высота должны быть положительными целыми числами.")

        processed_width = min(width, self.MAX_RENDER_WIDTH)
        processed_height = min(height, self.MAX_RENDER_HEIGHT)

        # Эта проверка уже не так критична, так как выше есть проверка на >0
        # if not (processed_width > 0 and processed_height > 0):
        #     processed_width = max(1, processed_width)
        #     processed_height = max(1, processed_height)

        if width > self.MAX_RENDER_WIDTH or height > self.MAX_RENDER_HEIGHT:
            # Логирование вместо print для библиотеки
            # import logging
            # logging.info(f"SpriteRenderer: Requested size ({width}x{height}) exceeds max "
            #              f"({self.MAX_RENDER_WIDTH}x{self.MAX_RENDER_HEIGHT}). "
            #              f"Set to {processed_width}x{processed_height}.")
            pass  # В библиотеке лучше не печатать в stdout

        self.width: int = processed_width
        self.height: int = processed_height
        self.background_color: RGBA = background_color
        self.layers: Dict[str, Dict[str, Any]] = {}
        self.grid_color: RGBA = grid_color
        self.label_color: RGBA = label_color
        self.label_font_path: Optional[str] = label_font_path
        self.label_font_size: int = label_font_size

        self.grid_artist = GridArtist(
                tile_pixel_width=self.DEFAULT_TILE_PIXEL_WIDTH,
                tile_pixel_height=self.DEFAULT_TILE_PIXEL_HEIGHT,
                grid_color=grid_color,
                label_color=label_color,
                font_path=label_font_path,
                font_size=label_font_size
                )

    def add_layer(self, layer_name: str, z_index: int = 0, visible: bool = True):
        """
        Добавляет новый слой или обновляет существующий.

        Args:
            layer_name (str): Уникальное имя слоя.
            z_index (int, optional): Порядок отрисовки (меньшие значения рисуются раньше).
                                     По умолчанию 0.
            visible (bool, optional): Видимость слоя. По умолчанию True.

        Raises:
            ValueError: Если имя слоя некорректно или z_index не целое число.
        """
        if not isinstance(layer_name, str) or not layer_name:
            raise ValueError("Имя слоя должно быть непустой строкой.")
        if not isinstance(z_index, int):
            raise ValueError("Z-index должен быть целым числом.")

        if layer_name in self.layers:
            self.layers[layer_name]['z_index'] = z_index
            self.layers[layer_name]['visible'] = visible
        else:
            self.layers[layer_name] = {'sprites': [], 'z_index': z_index, 'visible': visible}

    def add_sprite(
            self, layer_name: str, sprite: BaseSprite | Image.Image,
            x: Optional[int] = None, y: Optional[int] = None
            ):
        """
        Добавляет спрайт на указанный слой.

        Если `sprite` является экземпляром `BaseSprite` (или его наследником),
        его собственные координаты x, y будут использованы, если `x` и `y`
        аргументы метода не переданы. Если `x` и/или `y` переданы, они
        перезапишут позицию объекта `sprite`.

        Если `sprite` является `PIL.Image.Image`, аргументы `x` и `y` обязательны.
        Для такого изображения будет создан временный `BaseSprite`.

        Args:
            layer_name (str): Имя слоя, на который добавляется спрайт.
            sprite (BaseSprite | Image.Image): Объект спрайта или PIL Image.
            x (Optional[int], optional): X-координата для спрайта.
                                         Используется для PIL Image или для
                                         переопределения позиции BaseSprite.
            y (Optional[int], optional): Y-координата для спрайта.

        Raises:
            ValueError: Если слой не существует, или если для PIL.Image не переданы x, y.
            TypeError: Если `sprite` не является `BaseSprite` или `PIL.Image.Image`.
        """
        if layer_name not in self.layers:
            raise ValueError(f"Слой '{layer_name}' не существует.")

        if isinstance(sprite, BaseSprite):
            if x is not None:
                sprite.x = x
            if y is not None:
                sprite.y = y
            self.layers[layer_name]['sprites'].append(sprite)
        elif isinstance(sprite, Image.Image):
            if x is None or y is None:
                raise ValueError("Координаты x и y обязательны при добавлении PIL.Image напрямую.")
            temp_sprite = BaseSprite(sprite, x, y, name=f"pil_img_on_{layer_name}")
            self.layers[layer_name]['sprites'].append(temp_sprite)
        else:
            raise TypeError("Добавляемый объект должен быть экземпляром BaseSprite или PIL.Image.Image.")

    def render(
            self,
            draw_grid: bool = False,
            ) -> Image.Image:
        """
        Отрисовывает все видимые слои и спрайты в единое изображение.

        Спрайты типа `TokenTileSprite` (и его наследники) будут отмасштабированы
        до их `logical_pixel_width` и `logical_pixel_height`.
        Спрайты на слое с именем "background", не являющиеся `MapTileSprite` или
        `TokenTileSprite`, будут приведены к размеру 64x64 (если правило не изменено).

        Args:
            draw_grid (bool, optional): Если True, нарисовать сетку. По умолчанию False.
            grid_color (Tuple[int,int,int,int], optional): Цвет линий сетки RGBA.
                                                           По умолчанию полупрозрачный серый.
            label_color (Tuple[int,int,int,int], optional): Цвет меток координат RGBA.
                                                            По умолчанию полупрозрачный белый.
            label_font_path (Optional[str], optional): Путь к файлу шрифта (.ttf, .otf)
                                                       для меток. Если None, используется
                                                       шрифт Pillow по умолчанию.
            label_font_size (int, optional): Размер шрифта для меток, если используется
                                             файл шрифта. По умолчанию 10.

        Returns:
            Image.Image: Финальное отрендеренное изображение в формате RGBA.
        """

        # TODO: Нужна проверка прозрачности на слоях, видно ли определённый слой за другими, видно ли определённый
        #  токен, под слоями
        # self.width и self.height уже ограничены
        final_image = Image.new("RGBA", (self.width, self.height), self.background_color)

        sorted_layer_names = sorted(
                (name for name, data in self.layers.items() if data.get('visible', True)),
                key=lambda name: self.layers[name]['z_index']
                )

        for layer_name in sorted_layer_names:
            layer_data = self.layers[layer_name]
            for sprite_obj in layer_data['sprites']:
                if not sprite_obj.visible:
                    continue

                current_sprite_texture = sprite_obj.image
                image_to_paste = current_sprite_texture

                if isinstance(sprite_obj, TokenTileSprite):
                    logical_w = sprite_obj.logical_pixel_width
                    logical_h = sprite_obj.logical_pixel_height
                    if current_sprite_texture.size != (logical_w, logical_h):
                        try:
                            image_to_paste = current_sprite_texture.resize(
                                    (logical_w, logical_h), Image.Resampling.LANCZOS
                                    )
                        except Exception as e:
                            raise ValueError(f"SpriteRenderer: Error resizing token '{sprite_obj.name}': {e}")

                elif layer_name == "background" and \
                        not isinstance(sprite_obj, MapTileSprite) and \
                        not isinstance(sprite_obj, TokenTileSprite):
                    # Это специальное правило для нетипизированных спрайтов на фоне
                    # Возможно, его стоит сделать настраиваемым или убрать из ядра рендерера
                    target_bg_size = (64, 64)
                    if image_to_paste.size != target_bg_size:
                        try:
                            image_to_paste = image_to_paste.resize(target_bg_size, Image.Resampling.LANCZOS)
                        except Exception as e:
                            # logging.warning(f"SpriteRenderer: Error resizing background sprite '{sprite_obj.name}': {e}")
                            pass

                # Координаты спрайта относительно холста рендерера
                # Спрайты могут быть частично или полностью за пределами холста,
                # Pillow обработает это корректно при paste.
                x_pos, y_pos = sprite_obj.x, sprite_obj.y
                final_image.paste(
                        image_to_paste,
                        (x_pos, y_pos),
                        image_to_paste
                        )  # Используем альфа-канал спрайта как маску
        if draw_grid and self.grid_artist:
            self.grid_artist.render_on(final_image)


        return final_image


    def clear_layer(self, layer_name: str, remove_layer_definition: bool = False):
        """
        Очищает все спрайты с указанного слоя.

        Args:
            layer_name (str): Имя слоя для очистки.
            remove_layer_definition (bool, optional): Если True, слой будет полностью
                                                      удален. Иначе только его спрайты.
                                                      По умолчанию False.
        """
        if layer_name in self.layers:
            self.layers[layer_name]['sprites'] = []
            if remove_layer_definition:
                del self.layers[layer_name]
        # else: # Слой не найден, можно залогировать или проигнорировать
        # logging.info(f"SpriteRenderer: Layer '{layer_name}' not found for clearing.")

    def clear_all_layers_sprites(self):
        """Очищает спрайты со всех слоев, но оставляет сами слои."""
        for layer_name in self.layers:
            self.layers[layer_name]['sprites'] = []

    def reset(
            self, width: Optional[int] = None, height: Optional[int] = None,
            background_color: Optional[Tuple[int, int, int, int]] = None
            ):
        """
        Сбрасывает рендерер: удаляет все слои и спрайты, может изменить
        размер холста (с учетом ограничений) и цвет фона.

        Args:
            width (Optional[int], optional): Новая желаемая ширина холста.
            height (Optional[int], optional): Новая желаемая высота холста.
            background_color (Optional[Tuple[int,int,int,int]], optional): Новый цвет фона.
        """
        new_width = width if width is not None else self.width
        new_height = height if height is not None else self.height

        # Проверка на положительность перед ограничением (если переданы новые)
        if width is not None and width <= 0:
            new_width = self.width  # revert
        if height is not None and height <= 0:
            new_height = self.height  # revert

        processed_width = min(new_width, self.MAX_RENDER_WIDTH)
        processed_height = min(new_height, self.MAX_RENDER_HEIGHT)

        # Гарантируем, что размеры остаются положительными даже после min()
        # (на случай если self.MAX_RENDER_WIDTH/HEIGHT некорректны, хотя не должны)
        self.width = max(1, processed_width)
        self.height = max(1, processed_height)

        if (width is not None and width > self.MAX_RENDER_WIDTH) or \
                (height is not None and height > self.MAX_RENDER_HEIGHT):
            # logging.info(f"SpriteRenderer (reset): Requested size ({width}x{height}) exceeds max. "
            #              f"Set to {self.width}x{self.height}.")
            pass

        if background_color is not None:
            self.background_color = background_color

        self.layers = {}

    def set_layer_visibility(self, layer_name: str, visible: bool):
        """
        Устанавливает видимость для указанного слоя.

        Args:
            layer_name (str): Имя слоя.
            visible (bool): True, чтобы сделать слой видимым, False - невидимым.

        Raises:
            KeyError: Если слой с таким именем не существует.
        """
        if layer_name not in self.layers:
            raise KeyError(f"Слой '{layer_name}' не найден.")
        self.layers[layer_name]['visible'] = visible
