from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.database.models import Wife, Slot


async def pagination_kb(list_requests: List[Wife] = None, list_slots: List[Slot] = None, trade: bool = False, page: int = 1, max_page = "..", user_id: int = None, my_slots=False):
    wifes = []

    if not list_requests is None:
        for wife in list_requests:
            wifes.append([InlineKeyboardButton(text=f"Имя:{wife.name}-Аниме:{wife.from_}-Редкость:{wife.rare.value}", callback_data=f"select_{user_id}_{wife.id}")])
        refresh = InlineKeyboardButton(text='⏳Перезагрузить', callback_data=f'refresh_{user_id}')
        left_button = InlineKeyboardButton(text='<', callback_data=f'left_pagination_{user_id}')
        page_button = InlineKeyboardButton(text=f'{page}/{max_page}', callback_data='page_pagination')
        right_button = InlineKeyboardButton(text='>', callback_data=f'right_pagination_{user_id}')
        
    elif trade:
        for slot in list_slots:
            if not slot.closed and not slot.selled:
                if not my_slots:
                    wifes.append([InlineKeyboardButton(text=f"ID:{slot.id}, {slot.wife.name}({slot.wife.rare.value})->{slot.price}", callback_data=f"trade_{user_id}_{slot.id}")])
                else:
                    wifes.append([InlineKeyboardButton(text=f"ID:{slot.id}, {slot.wife.name}({slot.wife.rare.value})->{slot.price}", callback_data=f"trade_{user_id}_{slot.id}")])

        refresh = InlineKeyboardButton(text='⏳Перезагрузить', callback_data=f'trade_refresh_{user_id}')
        left_button = InlineKeyboardButton(text='<', callback_data=f'trade_left_pagination_{user_id}')
        page_button = InlineKeyboardButton(text=f'{page}/{max_page}', callback_data='page_pagination')
        right_button = InlineKeyboardButton(text='>', callback_data=f'trade_right_pagination_{user_id}')

    else:
        for slot in list_slots:
            if not slot.closed and not slot.selled:
                if not my_slots:
                    wifes.append([InlineKeyboardButton(text=f"ID:{slot.id}, {slot.wife.name}({slot.wife.rare.value})->{slot.price}", callback_data=f"buy_{user_id}_{slot.id}")])
                else:
                    wifes.append([InlineKeyboardButton(text=f"ID:{slot.id}, {slot.wife.name}({slot.wife.rare.value})->{slot.price}", callback_data=f"stop_select_{user_id}_{slot.id}")])

        refresh = InlineKeyboardButton(text='⏳Перезагрузить', callback_data=f'shop_refresh_{user_id}')
        left_button = InlineKeyboardButton(text='<', callback_data=f'shop_left_pagination_{user_id}')
        page_button = InlineKeyboardButton(text=f'{page}/{max_page}', callback_data='page_pagination')
        right_button = InlineKeyboardButton(text='>', callback_data=f'shop_right_pagination_{user_id}')
    

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        *wifes,
        [left_button, page_button, right_button],
        [refresh],
    ])

    return keyboard