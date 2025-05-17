# /project/main.py
# Убедитесь, что пути импорта соответствуют вашей структуре проекта

# from battlemap.sprites.token_tile import TokenSize # Не нужны для простого запуска UI
# from battlemap.types.token import OwnerId, Token, TokenId

# Импортируем только то, что нужно для создания рендерера и UI
from battlemap.render.sprite import SpriteRenderer
from debug_ui import DebugUI # Если debug_ui.py в той же папке, что и main.py
                             # или from project.debug_ui import DebugUI, если main.py в корне project

if __name__ == '__main__':
    # 1. Создаем экземпляр рендерера с начальными размерами
    # Эти размеры будут перезаписаны при показе карты, но нужны для инициализации Canvas
    initial_renderer_width = 300
    initial_renderer_height = 200
    main_renderer = SpriteRenderer(
        width=initial_renderer_width,
        height=initial_renderer_height,
        background_color=(50, 50, 50, 255)
    )

    # 2. Создаем и запускаем DebugUI
    debug_app = DebugUI(main_renderer)
    debug_app.run()

    print("DebugUI закрыт.")