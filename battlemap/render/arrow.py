import math
from typing import Optional, Tuple

from PIL import Image, ImageDraw


def create_arrow_image(
        start_xy: Tuple[int, int],
        end_xy: Tuple[int, int],
        color: Tuple[int, int, int, int] = (255, 255, 0, 200),  # Полупрозрачный желтый
        thickness: int = 3,
        arrowhead_length: int = 15,
        arrowhead_angle: float = 30.0
        ) -> Tuple[Optional[Image.Image], Tuple[int, int]]:
    """
    Создает изображение PIL.Image с нарисованной стрелкой.

    Args:
        start_xy (Tuple[int, int]): Координаты начала стрелки (x, y).
        end_xy (Tuple[int, int]): Координаты конца стрелки (наконечника) (x, y).
        color (Tuple[int, int, int, int]): Цвет стрелки RGBA.
        thickness (int): Толщина линии стрелки.
        arrowhead_length (int): Длина "усиков" наконечника стрелки.
        arrowhead_angle (float): Угол (в градусах) между линией стрелки и "усиком" наконечника.

    Returns:
        Tuple[Optional[Image.Image], Tuple[int, int]]:
            Кортеж: (Изображение стрелки или None, если start и end совпадают;
                     Координаты левого верхнего угла этого изображения (x, y))
    """
    x1, y1 = start_xy
    x2, y2 = end_xy

    # Если точки совпадают, не рисуем стрелку
    if x1 == x2 and y1 == y2:
        return None, (x1, y1)

    # Определяем границы изображения, чтобы вместить стрелку
    min_x = min(x1, x2)
    max_x = max(x1, x2)
    min_y = min(y1, y2)
    max_y = max(y1, y2)

    # Добавляем поля для толщины линии и наконечника
    padding = max(thickness, arrowhead_length) + 5
    img_left = min_x - padding
    img_top = min_y - padding
    img_right = max_x + padding
    img_bottom = max_y + padding

    img_width = img_right - img_left
    img_height = img_bottom - img_top

    # Координаты точек внутри нового изображения
    draw_x1 = x1 - img_left
    draw_y1 = y1 - img_top
    draw_x2 = x2 - img_left
    draw_y2 = y2 - img_top

    # Создаем прозрачное изображение нужного размера
    try:
        arrow_img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(arrow_img)
    except ValueError:  # Слишком большой размер изображения
        print(f"Warning: Cannot create arrow image, calculated size ({img_width}x{img_height}) too large.")
        return None, start_xy

    # Рисуем основную линию
    draw.line([(draw_x1, draw_y1), (draw_x2, draw_y2)], fill=color, width=thickness)

    # Рисуем наконечник
    angle_rad = math.radians(arrowhead_angle)
    line_angle = math.atan2(draw_y1 - draw_y2, draw_x1 - draw_x2)  # Угол линии от конца к началу

    # Координаты концов "усиков" наконечника
    angle1 = line_angle + angle_rad
    arrow_x1 = draw_x2 + arrowhead_length * math.cos(angle1)
    arrow_y1 = draw_y2 + arrowhead_length * math.sin(angle1)

    angle2 = line_angle - angle_rad
    arrow_x2 = draw_x2 + arrowhead_length * math.cos(angle2)
    arrow_y2 = draw_y2 + arrowhead_length * math.sin(angle2)

    draw.line([(arrow_x1, arrow_y1), (draw_x2, draw_y2)], fill=color, width=thickness)
    draw.line([(arrow_x2, arrow_y2), (draw_x2, draw_y2)], fill=color, width=thickness)

    del draw
    return arrow_img, (img_left, img_top)
