from typing import Optional, Tuple, TypeAlias

from PIL import Image, ImageDraw, ImageFont

RGBA: TypeAlias = Tuple[int, int, int, int]


class GridArtist:
    def __init__(
            self,
            tile_pixel_width: int,
            tile_pixel_height: int,
            grid_color: RGBA,
            label_color: RGBA,
            font_path: Optional[str] = None,
            font_size: int = 20
            ):
        self.tile_pixel_width = tile_pixel_width
        self.tile_pixel_height = tile_pixel_height
        self.grid_color = grid_color
        self.label_color = label_color
        self.font_path = font_path
        self.font_size = font_size
        self.font = self._load_font()

    def _load_font(self) -> Optional[ImageFont.FreeTypeFont]:
        try:
            if self.font_path:
                font = ImageFont.truetype(self.font_path, self.font_size)
            else:
                try:
                    # Pillow 10+
                    font = ImageFont.load_default(size=self.font_size)
                except AttributeError:  # Старые версии Pillow
                    font = ImageFont.load_default()
        except IOError:
            try:
                font = ImageFont.load_default(size=self.font_size)
            except AttributeError:
                font = ImageFont.load_default()
            except Exception:
                font = None
        return font

    def _draw_lines(self, draw: ImageDraw.ImageDraw, canvas_width: int, canvas_height: int):
        # Рисуем вертикальные линии
        for c in range(canvas_width // self.tile_pixel_width + 1):
            x = c * self.tile_pixel_width
            draw.line([(x, 0), (x, canvas_height)], fill=self.grid_color, width=1)

        # Рисуем горизонтальные линии
        for r in range(canvas_height // self.tile_pixel_height + 1):
            y = r * self.tile_pixel_height
            draw.line([(0, y), (canvas_width, y)], fill=self.grid_color, width=1)

    def _draw_labels(self, draw: ImageDraw.ImageDraw, canvas_width: int, canvas_height: int):
        if not self.font:
            return

        # Метки колонок
        for c in range(canvas_width // self.tile_pixel_width + 1):
            x = c * self.tile_pixel_width
            label_text = str(c)

            # Для более точного позиционирования и избегания выхода за границы
            # можно использовать textbbox (Pillow 9.2.0+)
            if hasattr(draw, "textbbox"):
                bbox = draw.textbbox((x + 2, 2), label_text, font=self.font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                if x + 2 + text_width < canvas_width and 2 + text_height < canvas_height:
                    draw.text((x + 2, 2), label_text, fill=self.label_color, font=self.font)
            else:  # Fallback для старых версий
                draw.text((x + 2, 2), label_text, fill=self.label_color, font=self.font)

        # Метки рядов
        for r in range(canvas_height // self.tile_pixel_height + 1):
            y = r * self.tile_pixel_height
            if r > 0:  # Пропускаем первую строку (0) для меток рядов
                label_text = str(r)

                if hasattr(draw, "textbbox"):
                    bbox = draw.textbbox((2, y + 2), label_text, font=self.font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    if 2 + text_width < canvas_width and y + 2 + text_height < canvas_height:
                        draw.text((2, y + 2), label_text, fill=self.label_color, font=self.font)
                else:
                    draw.text((2, y + 2), label_text, fill=self.label_color, font=self.font)

    def render_on(self, image: Image.Image):
        if self.tile_pixel_width <= 0 or self.tile_pixel_height <= 0:
            return

        draw = ImageDraw.Draw(image)
        self._draw_lines(draw, image.width, image.height)
        if self.font:
            self._draw_labels(draw, image.width, image.height)
        del draw
