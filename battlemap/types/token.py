"""
Модуль определяет класс игрового Токена и связанные типы ID.
"""
from typing import List, NewType, Optional, Sequence # Добавил Sequence для owner_ids
from PIL import Image
from battlemap.sprites.token_tile import TokenSize, TokenTileSprite

TokenId = NewType("TokenId", int)
OwnerId = NewType("OwnerId", int) # Можно сделать более сложным, если нужно (например, UUID)

class Token(TokenTileSprite):
    """
    Представляет игровой токен с уникальным ID, размером и списком владельцев.
    Наследуется от TokenTileSprite, получая его свойства управления текстурой
    и логическим размером.

    Атрибуты:
        token_id (TokenId): Уникальный идентификатор токена.
        owner_ids (List[OwnerId]): Список идентификаторов владельцев токена.
    """
    # TODO: Нужны child токены, следующие за родителем
    def __init__(
            self,
            pillow_image: Image.Image,
            token_size: TokenSize,
            token_id: TokenId,
            owner_ids: Optional[Sequence[OwnerId]] = None, # Используем Sequence для большей гибкости
            initially_visible: bool = True,
            x: int = 0,
            y: int = 0,
            name: str = "token" # Имя по умолчанию, может быть переопределено
            ):
        """
        Инициализирует объект Token.

        Args:
            pillow_image (Image.Image): Изображение для текстуры токена.
            token_size (TokenSize): Логический размер токена на карте.
            token_id (TokenId): Уникальный ID токена.
            owner_ids (Optional[Sequence[OwnerId]], optional): Список ID владельцев.
                                                              По умолчанию None (пустой список).
            initially_visible (bool, optional): Начальная видимость. По умолчанию True.
            x (int, optional): Начальная X-координата. По умолчанию 0.
            y (int, optional): Начальная Y-координата. По умолчанию 0.
            name (str, optional): Имя токена. Если "token", будет сгенерировано имя
                                  на основе ID. По умолчанию "token".
        """
        # Генерируем более осмысленное имя по умолчанию, если стандартное
        resolved_name = name
        if name == "token" or not name: # Если имя не задано или стандартное
            resolved_name = f"Token_{token_id}"

        super().__init__(pillow_image, token_size, initially_visible, x, y, resolved_name)

        self.token_id: TokenId = token_id
        self.owner_ids: List[OwnerId] = list(owner_ids) if owner_ids is not None else []

    def add_owner(self, owner_id: OwnerId):
        """Добавляет ID владельца в список, если его там еще нет."""
        if owner_id not in self.owner_ids:
            self.owner_ids.append(owner_id)

    def remove_owner(self, owner_id: OwnerId):
        """Удаляет ID владельца из списка, если он там есть."""
        try:
            self.owner_ids.remove(owner_id)
        except ValueError:
            # Владелец не найден, можно проигнорировать или залогировать
            pass

    def __repr__(self) -> str:
        """Возвращает строковое представление объекта Token."""
        # Используем self.name, который уже определен в BaseSprite
        return (f"<Token(id={self.token_id}, name='{self.name}', "
                f"texture_size={self.size}, "
                f"logical_tiles={self.token_size_enum}, "
                f"logical_px={self.logical_pixel_width}x{self.logical_pixel_height}, "
                f"pos=({self.x},{self.y}), owners={self.owner_ids}, visible={self.visible})>")