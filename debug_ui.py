# /project/debug_ui.py
import math
import tkinter as tk
from tkinter import filedialog, ttk

from PIL import Image, ImageTk

from battlemap.render.arrow import create_arrow_image
# Импорты из библиотеки
from battlemap.render.sprite import SpriteRenderer
from battlemap.sprites.base_sprite import BaseSprite  # Для фона карты
from battlemap.sprites.map_tile import MapTileSprite  # Для TILE_WIDTH/HEIGHT
from battlemap.sprites.token_tile import TokenSize
from battlemap.types.battle_map import BattleMap  # Импортируем BattleMap
from battlemap.types.token import Token, TokenId


class DebugUI:
    # Константы рендерера для ограничения размера карты
    MAX_RENDER_WIDTH = SpriteRenderer.MAX_RENDER_WIDTH
    MAX_RENDER_HEIGHT = SpriteRenderer.MAX_RENDER_HEIGHT

    def __init__(self, renderer: SpriteRenderer):
        self.renderer = renderer
        self.tk_root = tk.Tk()
        self.tk_root.title("Отладочный интерфейс BattleMap Renderer")

        # --- Состояние ---
        # Теперь BattleMap существует параллельно с фоновым спрайтом
        self.map_background_sprite: BaseSprite | None = None
        self.battle_map_instance: BattleMap | None = None  # Логическая сетка карты
        self.loaded_tokens: list[Token] = []

        # --- Состояние вида и интеракций (без изменений) ---
        self.display_scale = 1.0
        self.canvas_view_x = 0.0
        self.canvas_view_y = 0.0
        self.selected_token: Token | None = None
        self.dragging_token = False
        self.panning_canvas = False
        self.last_mouse_x_canvas = 0
        self.last_mouse_y_canvas = 0

        # --- Tkinter Vars ---
        self.token_size_var = tk.StringVar(value=TokenSize.SIZE_1x1.name)
        self.token_x_var = tk.StringVar()
        self.token_y_var = tk.StringVar()
        self.token_grid_col_var = tk.StringVar()
        self.token_grid_row_var = tk.StringVar()
        self.snap_to_grid_var = tk.BooleanVar(value=True)
        self.draw_grid_var = tk.BooleanVar(value=True)

        # --- GUI Layout ---
        main_frame = ttk.Frame(self.tk_root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        left_panel = ttk.Frame(main_frame, padding="5", relief=tk.SUNKEN, borderwidth=1)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        right_panel = ttk.Frame(main_frame, padding="5")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tk_canvas = tk.Canvas(right_panel, width=renderer.width, height=renderer.height, bg="darkgrey")
        self.tk_canvas.pack(fill=tk.BOTH, expand=True)
        self.tk_image_ref = None

        # --- Привязка событий (без изменений) ---
        self.tk_canvas.bind("<Configure>", self.on_canvas_resize_or_configure)
        self.tk_canvas.bind("<ButtonPress-1>", self.on_mouse_left_press)
        self.tk_canvas.bind("<B1-Motion>", self.on_mouse_left_motion)
        self.tk_canvas.bind("<ButtonRelease-1>", self.on_mouse_left_release)
        self.tk_canvas.bind("<ButtonPress-2>", self.on_mouse_middle_press)
        self.tk_canvas.bind("<ButtonPress-3>", self.on_mouse_middle_press)
        self.tk_canvas.bind("<B2-Motion>", self.on_mouse_middle_motion)
        self.tk_canvas.bind("<B3-Motion>", self.on_mouse_middle_motion)
        self.tk_canvas.bind("<ButtonRelease-2>", self.on_mouse_middle_release)
        self.tk_canvas.bind("<ButtonRelease-3>", self.on_mouse_middle_release)
        self.tk_canvas.bind("<MouseWheel>", self.on_mouse_wheel_windows_linux)
        self.tk_canvas.bind("<Button-4>", self.on_mouse_wheel_macos_up)
        self.tk_canvas.bind("<Button-5>", self.on_mouse_wheel_macos_down)

        # --- Элементы управления ---
        # Карта (теперь только фоновое изображение)
        map_frame = ttk.LabelFrame(left_panel, text="Карта (Фон)")
        map_frame.pack(fill=tk.X, pady=5)
        map_load_button = ttk.Button(map_frame, text="Загрузить фон карты", command=self.load_map_image_action)
        map_load_button.pack(fill=tk.X, pady=5)
        self.map_label = ttk.Label(map_frame, text="Фон не загружен", wraplength=180)
        self.map_label.pack(pady=2, anchor=tk.W)
        self.map_info_label = ttk.Label(map_frame, text="Размер сетки: -", wraplength=180)  # Метка для размера сетки
        self.map_info_label.pack(pady=2, anchor=tk.W)

        # Чекбокс сетки
        self.grid_check = ttk.Checkbutton(
                map_frame,
                text="Показывать сетку",
                variable=self.draw_grid_var,
                command=self.display_rendered_image
                )
        self.grid_check.pack(anchor=tk.W, pady=(5, 0))

        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Токены (без изменений в UI, но логика будет использовать BattleMap)
        token_frame = ttk.LabelFrame(left_panel, text="Токены")
        token_frame.pack(fill=tk.X, pady=5)
        token_load_button = ttk.Button(token_frame, text="Добавить токен", command=self.load_token_image_action)
        token_load_button.pack(pady=5, fill=tk.X)
        ttk.Label(token_frame, text="Размер нов. токена:").pack(pady=2, anchor=tk.W)
        token_sizes = [size.name for size in TokenSize]
        token_size_menu = ttk.OptionMenu(token_frame, self.token_size_var, TokenSize.SIZE_1x1.name, *token_sizes)
        token_size_menu.pack(pady=2, fill=tk.X)
        ttk.Label(token_frame, text="Список токенов:").pack(pady=(10, 0), anchor=tk.W)
        self.tokens_listbox = tk.Listbox(token_frame, height=6, exportselection=False)
        self.tokens_listbox.pack(pady=5, fill=tk.X, expand=True)
        self.tokens_listbox.bind("<<ListboxSelect>>", self.on_token_listbox_select)
        remove_token_button = ttk.Button(
                token_frame,
                text="Удалить выбранный токен",
                command=self.remove_selected_token_action
                )
        remove_token_button.pack(pady=2, fill=tk.X)

        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Выбранный токен (без изменений в UI)
        selected_token_frame = ttk.LabelFrame(left_panel, text="Выбранный токен")
        selected_token_frame.pack(fill=tk.X, pady=5)
        self.selected_token_label = ttk.Label(selected_token_frame, text="Нет", wraplength=180)
        self.selected_token_label.pack(pady=2, anchor=tk.W)
        grid_pos_frame = ttk.Frame(selected_token_frame)
        grid_pos_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(grid_pos_frame, text="Кол:").pack(side=tk.LEFT, padx=(0, 2))
        self.token_grid_col_entry = ttk.Entry(grid_pos_frame, textvariable=self.token_grid_col_var, width=4)
        self.token_grid_col_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(grid_pos_frame, text="Ряд:").pack(side=tk.LEFT, padx=(0, 2))
        self.token_grid_row_entry = ttk.Entry(grid_pos_frame, textvariable=self.token_grid_row_var, width=4)
        self.token_grid_row_entry.pack(side=tk.LEFT)
        apply_grid_pos_button = ttk.Button(
                grid_pos_frame,
                text="Задать поз.",
                command=self.apply_token_grid_position_from_entry,
                width=8
                )
        apply_grid_pos_button.pack(side=tk.LEFT, padx=5)
        pixel_pos_frame = ttk.Frame(selected_token_frame)
        pixel_pos_frame.pack(fill=tk.X, pady=(2, 0))
        ttk.Label(pixel_pos_frame, text="Пикс. X:").pack(side=tk.LEFT, padx=(0, 2))
        self.token_x_entry = ttk.Entry(pixel_pos_frame, textvariable=self.token_x_var, width=5)
        self.token_x_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(pixel_pos_frame, text="Пикс. Y:").pack(side=tk.LEFT, padx=(0, 2))
        self.token_y_entry = ttk.Entry(pixel_pos_frame, textvariable=self.token_y_var, width=5)
        self.token_y_entry.pack(side=tk.LEFT)
        apply_pixel_pos_button = ttk.Button(
                pixel_pos_frame,
                text="Задать поз.",
                command=self.apply_token_pixel_position_from_entry,
                width=8
                )
        apply_pixel_pos_button.pack(side=tk.LEFT, padx=5)
        snap_to_grid_check = ttk.Checkbutton(
                selected_token_frame,
                text="Привязывать к сетке",
                variable=self.snap_to_grid_var
                )
        snap_to_grid_check.pack(pady=5, anchor=tk.W)

        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        clear_all_button = ttk.Button(left_panel, text="Очистить всё (сброс)", command=self.clear_all_action)
        clear_all_button.pack(pady=5, fill=tk.X)

        self.preview_arrow_sprite: BaseSprite | None = None  # Спрайт для стрелки предпросмотра
        self.temp_arrow_layer = "_preview_arrow_layer"  # Имя временного слоя

        self._ensure_temp_arrow_layer()

        self.reset_and_setup()  # Вызываем обновленный сброс
        self.display_rendered_image()

    def _ensure_temp_arrow_layer(self):
        """Гарантирует наличие временного слоя для стрелки."""
        if self.temp_arrow_layer not in self.renderer.layers:
            # Добавляем с высоким z_index, чтобы быть поверх токенов, но под UI (если будет)
            self.renderer.add_layer(self.temp_arrow_layer, z_index=15, visible=True)

    def reset_and_setup(self):
        """Полный сброс UI, рендерера и состояния карты/токенов."""
        self.map_background_sprite = None
        self.battle_map_instance = None  # Сбрасываем и логическую карту
        self.loaded_tokens = []

        self.map_label.config(text="Фон не загружен")
        self.map_info_label.config(text="Размер сетки: -")  # Сбрасываем инфо о сетке
        self.tokens_listbox.delete(0, tk.END)
        self.selected_token = None
        self.update_selected_token_display(None)

        self.display_scale = 1.0
        self.canvas_view_x = 0.0
        self.canvas_view_y = 0.0

        # Сброс рендерера к дефолтным размерам и слоям
        self.renderer.reset(width=600, height=400, background_color=(30, 20, 20, 255))
        self.renderer.add_layer("map_background_layer", z_index=0)  # Слой для фона BaseSprite
        self.renderer.add_layer("tokens_layer", z_index=10)
        # Слой map_tiles_layer больше не нужен, если не используем тайловую карту

        self._ensure_temp_arrow_layer()

    def on_canvas_resize_or_configure(self, event=None):
        self.display_rendered_image()

    def load_map_image_action(self):
        filepath = filedialog.askopenfilename(
                title="Выберите фоновое изображение карты",
                filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("Все файлы", "*.*")]
                )
        if filepath:
            try:
                original_map_image = Image.open(filepath).convert("RGBA")

                img_w, img_h = original_map_image.size
                # Используем MAX_RENDER_WIDTH/HEIGHT из рендерера для ограничения
                scale_factor = 1.0
                if img_w > SpriteRenderer.MAX_RENDER_WIDTH or img_h > SpriteRenderer.MAX_RENDER_HEIGHT:
                    scale_w = SpriteRenderer.MAX_RENDER_WIDTH / img_w
                    scale_h = SpriteRenderer.MAX_RENDER_HEIGHT / img_h
                    scale_factor = min(scale_w, scale_h)

                processed_map_image = original_map_image.resize(
                        (int(img_w * scale_factor), int(img_h * scale_factor)), Image.Resampling.LANCZOS
                        ) if scale_factor < 1.0 else original_map_image

                # 1. Создаем BaseSprite для фона
                self.map_background_sprite = BaseSprite(processed_map_image, x=0, y=0, name="loaded_map_background")
                self.map_label.config(
                        text=f"{filepath.split('/')[-1]} ({processed_map_image.width}x{processed_map_image.height})"
                        )

                # 2. Создаем ЛОГИЧЕСКИЙ BattleMap на основе размеров фона
                map_w = processed_map_image.width
                map_h = processed_map_image.height
                tile_w = MapTileSprite.TILE_WIDTH
                tile_h = MapTileSprite.TILE_HEIGHT
                grid_w = map_w // tile_w
                grid_h = map_h // tile_h

                if grid_w > 0 and grid_h > 0:
                    self.battle_map_instance = BattleMap(
                            map_width_tiles=grid_w,
                            map_height_tiles=grid_h
                            # default_tile_image=None - нам не нужны его тайлы для рендера
                            )
                    self.map_info_label.config(text=f"Размер сетки: {grid_w}x{grid_h}")
                else:
                    self.battle_map_instance = None  # Слишком маленькая карта для сетки
                    self.map_info_label.config(text="Размер сетки: - (карта мала)")

                # 3. Обновляем рендерер
                self.renderer.reset(
                        width=map_w,
                        height=map_h,
                        background_color=(0, 0, 0, 0)
                        )  # Фон рендерера может быть прозрачным
                self.renderer.add_layer("map_background_layer", z_index=0)
                self.renderer.add_layer("tokens_layer", z_index=10)

                # 4. Сбрасываем вид и перерисовываем
                self.display_scale = 1.0
                self.canvas_view_x = 0.0
                self.canvas_view_y = 0.0
                self.prepare_and_render_scene()

            except Exception as e:
                self.map_label.config(text="Ошибка загрузки фона")
                print(f"DebugUI: Ошибка загрузки фона: {e}")
                self.map_background_sprite = None
                self.battle_map_instance = None
                self.reset_and_setup()
                self.prepare_and_render_scene()

    def load_token_image_action(self):
        # Теперь не требует BattleMap, но использует его для позиционирования, если он есть
        filepath = filedialog.askopenfilename(
                title="Выберите токен",
                filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif"), ("Все файлы", "*.*")]
                )
        if filepath:
            try:
                token_pil_image = Image.open(filepath)
                token_size = TokenSize[self.token_size_var.get()]
                token_id = TokenId(len(self.loaded_tokens) + 1)
                name_stem = filepath.split('/')[-1].rsplit('.', 1)[0][:20]
                new_token = Token(token_pil_image, token_size, token_id, name=f"{name_stem}_{token_id}")

                # Позиционируем новый токен по сетке, если BattleMap доступен
                if self.battle_map_instance:
                    grid_w = self.battle_map_instance.map_width_tiles
                    grid_h = self.battle_map_instance.map_height_tiles
                    tile_pw = self.battle_map_instance.tile_pixel_width
                    tile_ph = self.battle_map_instance.tile_pixel_height

                    # Простая логика размещения
                    col = (len(self.loaded_tokens) * 2) % max(1, grid_w - new_token.token_size_enum.tiles_width + 1)
                    row = (len(self.loaded_tokens) // max(1, (grid_w // 2) + 1)) % max(
                            1,
                            grid_h - new_token.token_size_enum.tiles_height + 1
                            )

                    new_token.set_grid_position(col, row, tile_pw, tile_ph)
                else:  # Если карты нет, ставим в угол
                    new_token.set_position(10, 10)

                self.loaded_tokens.append(new_token)
                self.tokens_listbox.insert(tk.END, new_token.name)
                self.tokens_listbox.selection_clear(0, tk.END)
                self.tokens_listbox.selection_set(tk.END)
                self.on_token_listbox_select(None)
                self.prepare_and_render_scene()
            except Exception as e:
                print(f"DebugUI: Ошибка загрузки токена: {e}")

    def remove_selected_token_action(self):
        # ... (как раньше) ...
        if not self.selected_token:
            return
        try:
            self.loaded_tokens.remove(self.selected_token)
            listbox_items = self.tokens_listbox.get(0, tk.END)
            if self.selected_token.name in listbox_items:
                self.tokens_listbox.delete(listbox_items.index(self.selected_token.name))
            self.update_selected_token_display(None)
            self.prepare_and_render_scene()
        except ValueError:
            pass

    def prepare_and_render_scene(self, include_preview_arrow: bool = True):
        self.renderer.clear_all_layers_sprites()

        # Добавляем фон, если он есть
        if self.map_background_sprite:
            try:
                self.renderer.add_sprite("map_background_layer", self.map_background_sprite)
            except ValueError as e:
                print(f"DebugUI (prepare): Ошибка добавления фона: {e}.")

        # Добавляем токены
        for token in self.loaded_tokens:
            try:
                self.renderer.add_sprite("tokens_layer", token)
            except ValueError:
                pass

        if include_preview_arrow and self.preview_arrow_sprite:
            try:
                self.renderer.add_sprite(self.temp_arrow_layer, self.preview_arrow_sprite)
            except ValueError:
                pass  # Слой мог исчезнуть, _ensure_temp_arrow_layer должен помочь

        self.display_rendered_image()

    def clear_all_action(self):
        self.reset_and_setup()
        self.prepare_and_render_scene()

    def display_rendered_image(self):
        # ... (Без изменений в логике рендеринга и отображения) ...
        if not self.renderer or not self.tk_canvas.winfo_exists():
            return
        try:
            full_rendered_image = self.renderer.render(draw_grid=self.draw_grid_var.get())
            canvas_width = self.tk_canvas.winfo_width()
            canvas_height = self.tk_canvas.winfo_height()
            if canvas_width < 1 or canvas_height < 1:
                return
            world_img_w, world_img_h = full_rendered_image.size
            if world_img_w == 0 or world_img_h == 0:
                self.tk_canvas.delete("all"); return
            view_world_x1 = self.canvas_view_x
            view_world_y1 = self.canvas_view_y
            view_world_x2 = self.canvas_view_x + (canvas_width / self.display_scale)
            view_world_y2 = self.canvas_view_y + (canvas_height / self.display_scale)
            crop_x1 = max(0, math.floor(view_world_x1))
            crop_y1 = max(0, math.floor(view_world_y1))
            crop_x2 = min(world_img_w, math.ceil(view_world_x2))
            crop_y2 = min(world_img_h, math.ceil(view_world_y2))
            if crop_x1 >= crop_x2 or crop_y1 >= crop_y2:
                self.tk_canvas.delete("all"); return
            visible_part_world_img = full_rendered_image.crop((crop_x1, crop_y1, crop_x2, crop_y2))
            display_part_w = int(visible_part_world_img.width * self.display_scale)
            display_part_h = int(visible_part_world_img.height * self.display_scale)
            if display_part_w <= 0 or display_part_h <= 0:
                self.tk_canvas.delete("all"); return
            resampling_filter = Image.Resampling.BILINEAR
            if self.display_scale < 0.75:
                resampling_filter = Image.Resampling.NEAREST
            image_for_canvas_display = visible_part_world_img.resize(
                    (display_part_w, display_part_h),
                    resampling_filter
                    ) if (
                    display_part_w != visible_part_world_img.width or display_part_h != visible_part_world_img.height) else visible_part_world_img
            self.tk_image_ref = ImageTk.PhotoImage(image_for_canvas_display)
            self.tk_canvas.delete("all")
            draw_on_canvas_x = int(-view_world_x1 * self.display_scale) if view_world_x1 < 0 else 0
            draw_on_canvas_y = int(-view_world_y1 * self.display_scale) if view_world_y1 < 0 else 0
            self.tk_canvas.create_image(draw_on_canvas_x, draw_on_canvas_y, anchor=tk.NW, image=self.tk_image_ref)
        except Exception as e:
            print(f"DebugUI: Ошибка display_rendered_image: {e}")
            import traceback
            traceback.print_exc()

    def canvas_to_world_coords(self, canvas_x: int, canvas_y: int) -> tuple[float, float]:
        return (canvas_x / self.display_scale) + self.canvas_view_x, (
                canvas_y / self.display_scale) + self.canvas_view_y

    def on_mouse_left_press(self, event):
        self.last_mouse_x_canvas, self.last_mouse_y_canvas = event.x, event.y
        world_x, world_y = self.canvas_to_world_coords(event.x, event.y)
        clicked_token_found: Token | None = None
        for token_obj in reversed(self.loaded_tokens):
            if not token_obj.visible:
                continue
            if token_obj.x <= world_x < (token_obj.x + token_obj.logical_pixel_width) and \
                    token_obj.y <= world_y < (token_obj.y + token_obj.logical_pixel_height):
                clicked_token_found = token_obj
                break
        self.update_selected_token_display(clicked_token_found)
        if self.selected_token:
            self.dragging_token = True
        else:
            self.dragging_token = False

    def on_mouse_left_motion(self, event):
        if self.dragging_token and self.selected_token:
            dx_canvas = event.x - self.last_mouse_x_canvas
            dy_canvas = event.y - self.last_mouse_y_canvas
            dx_world = dx_canvas / self.display_scale
            dy_world = dy_canvas / self.display_scale

            # Запоминаем старую позицию для стрелки
            start_x, start_y = self.selected_token.x, self.selected_token.y

            # Вычисляем новую позицию (пиксельную)
            new_world_x = self.selected_token.x + dx_world
            new_world_y = self.selected_token.y + dy_world

            # --- Логика стрелки предпросмотра ---
            target_x, target_y = round(new_world_x), round(new_world_y)

            # Если включена привязка к сетке, вычисляем целевую ячейку сетки
            if self.snap_to_grid_var.get() and self.battle_map_instance:
                tile_w = self.battle_map_instance.tile_pixel_width
                tile_h = self.battle_map_instance.tile_pixel_height
                # Определяем целевую ячейку по новой пиксельной позиции
                target_grid_col = round(new_world_x / tile_w)
                target_grid_row = round(new_world_y / tile_h)
                # Ограничиваем
                target_grid_col = max(
                    0,
                    min(target_grid_col, self.battle_map_instance.map_width_tiles - self.selected_token.token_size_enum.tiles_width)
                    )
                target_grid_row = max(
                    0,
                    min(target_grid_row, self.battle_map_instance.map_height_tiles - self.selected_token.token_size_enum.tiles_height)
                    )
                # Пересчитываем целевые пиксельные координаты из сеточных
                target_x = target_grid_col * tile_w
                target_y = target_grid_row * tile_h

            # Создаем или обновляем спрайт стрелки
            # Центр старой позиции токена
            center_start_x = start_x + self.selected_token.logical_pixel_width // 2
            center_start_y = start_y + self.selected_token.logical_pixel_height // 2
            # Центр новой (возможно, привязанной к сетке) позиции
            center_target_x = target_x + self.selected_token.logical_pixel_width // 2
            center_target_y = target_y + self.selected_token.logical_pixel_height // 2

            arrow_img, arrow_pos = create_arrow_image(
                    (center_start_x, center_start_y),
                    (center_target_x, center_target_y)
                    )

            if arrow_img:
                if self.preview_arrow_sprite:
                    # Обновляем существующий спрайт стрелки
                    self.preview_arrow_sprite.image = arrow_img
                    self.preview_arrow_sprite.set_position(arrow_pos[0], arrow_pos[1])
                else:
                    # Создаем новый спрайт стрелки
                    self.preview_arrow_sprite = BaseSprite(arrow_img, arrow_pos[0], arrow_pos[1], name="_preview_arrow")
            else:  # Если стрелка не нужна (точки совпадают)
                self.preview_arrow_sprite = None
            # --- Конец логики стрелки ---

            self.selected_token.move(round(dx_world), round(dy_world))
            self.last_mouse_x_canvas, self.last_mouse_y_canvas = event.x, event.y
            self.update_selected_token_display(self.selected_token)
            self.prepare_and_render_scene(include_preview_arrow=True)

    def on_mouse_left_release(self, event):
        arrow_needs_redraw = False
        if self.preview_arrow_sprite:
            self.preview_arrow_sprite = None  # Сбрасываем спрайт
            arrow_needs_redraw = True  # Нужно перерисовать сцену без стрелки

        if self.dragging_token:
            self.dragging_token = False
            # Привязка к сетке теперь использует self.battle_map_instance, если он есть
            if self.selected_token and self.snap_to_grid_var.get() and self.battle_map_instance:
                grid_col, grid_row = self.selected_token.get_grid_position(
                        self.battle_map_instance.tile_pixel_width,
                        self.battle_map_instance.tile_pixel_height
                        )
                # Ограничиваем по размеру логической карты BattleMap
                grid_col = max(
                        0,
                        min(grid_col, self.battle_map_instance.map_width_tiles - self.selected_token.token_size_enum.tiles_width)
                        )
                grid_row = max(
                        0,
                        min(grid_row, self.battle_map_instance.map_height_tiles - self.selected_token.token_size_enum.tiles_height)
                        )

                pixel_x_at_grid = grid_col * self.battle_map_instance.tile_pixel_width
                pixel_y_at_grid = grid_row * self.battle_map_instance.tile_pixel_height

                if self.selected_token.x != pixel_x_at_grid or self.selected_token.y != pixel_y_at_grid or arrow_needs_redraw:
                    self.selected_token.set_grid_position(
                            grid_col, grid_row,
                            self.battle_map_instance.tile_pixel_width,
                            self.battle_map_instance.tile_pixel_height
                            )
                    self.update_selected_token_display(self.selected_token)
                    self.prepare_and_render_scene(include_preview_arrow=False)  # Рисуем без стрелки

                elif arrow_needs_redraw:  # Если не было привязки, но стрелка была
                    self.prepare_and_render_scene(include_preview_arrow=False)  # Рисуем без стрелки

    def on_mouse_middle_press(self, event):
        self.last_mouse_x_canvas, self.last_mouse_y_canvas = event.x, event.y;
        self.panning_canvas = True
        self.tk_canvas.config(
                cursor="fleur"
                )

    def on_mouse_middle_motion(self, event):
        if self.panning_canvas:
            dx_canvas = event.x - self.last_mouse_x_canvas
            dy_canvas = event.y - self.last_mouse_y_canvas
            self.canvas_view_x -= dx_canvas / self.display_scale
            self.canvas_view_y -= dy_canvas / self.display_scale
            self.last_mouse_x_canvas, self.last_mouse_y_canvas = event.x, event.y
            self.display_rendered_image()

    def on_mouse_middle_release(self, event):
        self.panning_canvas = False
        self.tk_canvas.config(cursor="")

    def _zoom(self, factor: float, pivot_x_canvas: int, pivot_y_canvas: int):
        world_pivot_x_before, world_pivot_y_before = self.canvas_to_world_coords(pivot_x_canvas, pivot_y_canvas)
        old_scale = self.display_scale
        new_scale = self.display_scale * factor
        min_scale, max_scale = 0.05, 10.0
        self.display_scale = max(min_scale, min(new_scale, max_scale))
        if abs(self.display_scale - old_scale) < 0.001:
            return
        self.canvas_view_x = world_pivot_x_before - (pivot_x_canvas / self.display_scale)
        self.canvas_view_y = world_pivot_y_before - (pivot_y_canvas / self.display_scale)
        self.display_rendered_image()

    def on_mouse_wheel_windows_linux(self, event):
        self._zoom(1.1 if event.delta > 0 else (1 / 1.1), event.x, event.y)

    def on_mouse_wheel_macos_up(self, event):
        self._zoom(1.1, event.x, event.y)

    def on_mouse_wheel_macos_down(self, event):
        self._zoom(1 / 1.1, event.x, event.y)

    def on_token_listbox_select(self, event):
        selection = self.tokens_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.loaded_tokens):
                self.update_selected_token_display(self.loaded_tokens[index])
            else:
                self.update_selected_token_display(None)

    def update_selected_token_display(self, token_obj: Token | None):
        self.selected_token = token_obj
        if token_obj:
            self.selected_token_label.config(text=token_obj.name)
            self.token_x_var.set(str(token_obj.x))
            self.token_y_var.set(str(token_obj.y))
            # Используем battle_map_instance для получения сеточных координат
            if self.battle_map_instance:
                grid_col, grid_row = token_obj.get_grid_position(
                        self.battle_map_instance.tile_pixel_width, self.battle_map_instance.tile_pixel_height
                        )
                self.token_grid_col_var.set(str(grid_col))
                self.token_grid_row_var.set(str(grid_row))
            else:  # Карты нет, сетка не определена
                self.token_grid_col_var.set("-")
                self.token_grid_row_var.set("-")
            # Синхронизация с Listbox
            try:
                idx = self.loaded_tokens.index(token_obj)
                current_selection = self.tokens_listbox.curselection()
                if not current_selection or current_selection[0] != idx:
                    self.tokens_listbox.selection_clear(0, tk.END)
                    self.tokens_listbox.selection_set(idx)
                    self.tokens_listbox.activate(idx)
            except (ValueError, tk.TclError):
                pass
        else:  # Сброс UI если токен не выбран
            self.selected_token_label.config(text="Нет")
            self.token_x_var.set("")
            self.token_y_var.set("")
            self.token_grid_col_var.set("")
            self.token_grid_row_var.set("")
            current_selection = self.tokens_listbox.curselection()
            if current_selection:
                self.tokens_listbox.selection_clear(current_selection[0])

    def apply_token_pixel_position_from_entry(self):
        if self.selected_token:
            try:
                new_x = int(self.token_x_var.get())
                new_y = int(self.token_y_var.get())
                if self.selected_token.x != new_x or self.selected_token.y != new_y:
                    self.selected_token.set_position(new_x, new_y)
                    self.update_selected_token_display(self.selected_token)
                    self.prepare_and_render_scene()
            except ValueError:
                print("DebugUI: Неверный формат пиксельных координат.")
        else:
            print("DebugUI: Токен не выбран.")

    def apply_token_grid_position_from_entry(self):
        if not self.selected_token:
            print("DebugUI: Токен не выбран."); return
        if not self.battle_map_instance:
            print("DebugUI: Логическая карта (BattleMap) не создана."); return
        token = self.selected_token
        try:
            grid_col = int(self.token_grid_col_var.get())
            grid_row = int(self.token_grid_row_var.get())
            max_col = self.battle_map_instance.map_width_tiles - token.token_size_enum.tiles_width
            max_row = self.battle_map_instance.map_height_tiles - token.token_size_enum.tiles_height
            final_grid_col = max(0, min(grid_col, max_col))
            final_grid_row = max(0, min(grid_row, max_row))
            # Используем параметры из battle_map_instance
            token.set_grid_position(
                    final_grid_col, final_grid_row,
                    self.battle_map_instance.tile_pixel_width,
                    self.battle_map_instance.tile_pixel_height
                    )
            self.update_selected_token_display(token)
            self.prepare_and_render_scene()
        except ValueError:
            print("DebugUI: Неверный формат сеточных координат.")
        except AttributeError:
            print("DebugUI: Экземпляр BattleMap отсутствует.")

    def run(self):
        self.tk_root.mainloop()
