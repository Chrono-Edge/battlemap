import os
from typing import Set, Tuple, Optional
from PIL import Image
import time


# --- Импорты из вашей библиотеки ---
# Убедитесь, что пакет 'battlemap' доступен (например, через PYTHONPATH
# или установку пакета, или запуская скрипт из папки 'project')
from battlemap.render.sprite import SpriteRenderer
from battlemap.render.arrow import create_arrow_image
from battlemap.sprites.base_sprite import BaseSprite
from battlemap.sprites.map_tile import MapTileSprite  # Для размеров тайла
from battlemap.sprites.token_tile import TokenSize
from battlemap.types.token import Token, TokenId

# --- Параметры ---
BG_IMAGE_PATH = "C:\\Users\\Pugemon\\Downloads\\Telegram Desktop\\Road Chase Scene - Spring - Day.webp"  # <--- ЗАМЕНИТЕ на путь к вашему фону
TOKEN_IMAGE_PATH = "C:\\Users\\Pugemon\\Downloads\\Telegram Desktop\\Human_Commoner_11.png"  # <--- ЗАМЕНИТЕ на путь к
# вашему токену

OUTPUT_DIR = "render_output"  # Папка для сохранения результатов
ARROW_OUTPUT_FILE = "render_with_arrow.png"
MOVED_OUTPUT_FILE = "render_after_move.png"

# Параметры токена и движения
TOKEN_LOGICAL_SIZE = TokenSize.SIZE_3x3  # Логический размер токена
TOKEN_START_GRID_POS: Tuple[int, int] = (0, 0)  # Начальная ячейка (Колонка, Ряд)
TOKEN_END_GRID_POS: Tuple[int, int] = (1, 3)  # Конечная ячейка (Колонка, Ряд)

# Параметры для стрелки и тега
ARROW_TAG = "_move_preview_arrow"
ARROW_LAYER = "effects_layer"  # Слой для стрелки


# --- Вспомогательная функция для создания плейсхолдеров ---
def create_placeholder_image(
        width: int,
        height: int,
        color: Tuple[int, int, int, int],
        text: Optional[str] = None
        ) -> Image.Image:
    """Создает простое изображение-плейсхолдер."""
    img = Image.new("RGBA", (width, height), color)
    if text:
        from PIL import ImageDraw  # Локальный импорт
        draw = ImageDraw.Draw(img)
        try:
            # Пытаемся использовать шрифт по умолчанию большего размера
            from PIL import ImageFont
            try:
                font = ImageFont.load_default(size=max(15, min(width, height) // 5))
            except AttributeError:
                font = ImageFont.load_default()  # Старая версия Pillow?
            except OSError:
                font = None  # Шрифта нет
        except ImportError:
            font = None  # Pillow старый

        if font:
            # Рисуем текст по центру
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = (width - text_width) // 2
            text_y = (height - text_height) // 2
            draw.text((text_x, text_y), text, fill=(255, 255, 255, 200), font=font)
        del draw
    return img


# --- Основная логика ---
def main():
    # 1. Загрузка или создание изображений
    try:
        background_img = Image.open(BG_IMAGE_PATH).convert("RGBA")
        print(f"Фон загружен: {BG_IMAGE_PATH}")
    except FileNotFoundError:
        print(f"Предупреждение: Файл фона не найден '{BG_IMAGE_PATH}'. Создаем плейсхолдер 8x6 тайлов.")
        # Создаем фон размером, например, 8x6 тайлов
        bg_width = 8 * MapTileSprite.TILE_WIDTH
        bg_height = 6 * MapTileSprite.TILE_HEIGHT
        background_img = create_placeholder_image(bg_width, bg_height, (40, 60, 40, 255), "Background")

    try:
        token_texture_img = Image.open(TOKEN_IMAGE_PATH)  # Token класс сам конвертирует и ресайзит
        print(f"Текстура токена загружена: {TOKEN_IMAGE_PATH}")
    except FileNotFoundError:
        print(f"Предупреждение: Файл токена не найден '{TOKEN_IMAGE_PATH}'. Создаем плейсхолдер 70x70.")
        token_texture_img = create_placeholder_image(
            MapTileSprite.TILE_WIDTH,
            MapTileSprite.TILE_HEIGHT,
            (200, 50, 50, 255),
            "Token"
            )

    # 2. Создание и настройка рендерера
    # Размер рендерера берем из фона (он будет ограничен внутри рендерера, если > максимума)
    map_width_px = background_img.width
    map_height_px = background_img.height

    renderer = SpriteRenderer(width=map_width_px, height=map_height_px, background_color=(0, 0, 0, 0))

    # Добавляем слои
    renderer.add_layer("map_background_layer", z_index=0)
    renderer.add_layer("tokens_layer", z_index=10)
    renderer.add_layer(ARROW_LAYER, z_index=15)  # Слой для стрелки поверх токенов

    start_time = time.time()
    # 3. Создание спрайтов
    background_sprite = BaseSprite(background_img, x=0, y=0, name="background")

    # Создаем токен
    token_id_counter = 1  # Простой счетчик ID
    token = Token(
            pillow_image=token_texture_img,
            token_size=TOKEN_LOGICAL_SIZE,
            token_id=TokenId(token_id_counter),
            name="MyToken"
            )

    # --- Рендер 1: С токеном в начальной позиции и стрелкой ---
    print(f"Подготовка рендера 1: Токен в {TOKEN_START_GRID_POS}, стрелка к {TOKEN_END_GRID_POS}...")

    # Устанавливаем начальную позицию токена
    token.set_grid_position(TOKEN_START_GRID_POS[0], TOKEN_START_GRID_POS[1])

    # Вычисляем пиксельные координаты для стрелки (центры ячеек)
    tile_w = MapTileSprite.TILE_WIDTH
    tile_h = MapTileSprite.TILE_HEIGHT
    start_center_x = (TOKEN_START_GRID_POS[0] + 0.5) * tile_w
    start_center_y = (TOKEN_START_GRID_POS[1] + 0.5) * tile_h
    end_center_x = (TOKEN_END_GRID_POS[0] + 0.5) * tile_w
    end_center_y = (TOKEN_END_GRID_POS[1] + 0.5) * tile_h

    # Создаем стрелку
    arrow_img, arrow_pos = create_arrow_image(
            (int(start_center_x), int(start_center_y)),
            (int(end_center_x), int(end_center_y))
            # Можно передать другие параметры цвета, толщины и т.д.
            )

    # Добавляем спрайты в рендерер для первого кадра
    renderer.add_sprite("map_background_layer", background_sprite)
    renderer.add_sprite("tokens_layer", token)  # Токен в начальной позиции
    if arrow_img:
        arrow_sprite = BaseSprite(arrow_img, arrow_pos[0], arrow_pos[1], name=ARROW_TAG)
        renderer.add_sprite(ARROW_LAYER, arrow_sprite)
    else:
        print("Предупреждение: Не удалось создать стрелку (возможно, точки совпадают).")

    # Рендерим и сохраняем первый кадр
    output_image_arrow = renderer.render(True)

    # Создаем папку вывода, если ее нет
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    save_path_arrow = os.path.join(OUTPUT_DIR, ARROW_OUTPUT_FILE)
    try:
        output_image_arrow.save(save_path_arrow)
        print(f"Изображение со стрелкой сохранено в: {save_path_arrow}")
    except Exception as e:
        print(f"Ошибка сохранения изображения со стрелкой: {e}")

    # --- Рендер 2: С токеном в конечной позиции ---
    print(f"Подготовка рендера 2: Токен перемещен в {TOKEN_END_GRID_POS}...")

    # Перемещаем токен в конечную позицию
    # Объект token уже находится в списке спрайтов рендерера,
    # нам нужно только изменить его состояние (координаты x, y).
    token.set_grid_position(TOKEN_END_GRID_POS[0], TOKEN_END_GRID_POS[1])

    # Рендерим и сохраняем второй кадр
    # Рендерер использует актуальное состояние объектов в слоях
    output_image_moved = renderer.render()
    print(f"Время на обработку: {time.time() - start_time}")
    save_path_moved = os.path.join(OUTPUT_DIR, MOVED_OUTPUT_FILE)
    try:
        output_image_moved.save(save_path_moved)
        print(f"Изображение с перемещенным токеном сохранено в: {save_path_moved}")
    except Exception as e:
        print(f"Ошибка сохранения изображения с перемещенным токеном: {e}")


    print("Готово.")


if __name__ == "__main__":
    main()