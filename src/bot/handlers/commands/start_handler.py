from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder  

from src.logger import setup_logger
from src.bot.keyboards.reply import start_kb
from src.database.orm.users import check_vip, create_user
from src.database.orm.promo import get_promo
from src.utils.create_file import create_file_profile
from src.database.orm.users import add_balance
from decimal import Decimal
from src.bot.fsm.promo import Promo


router = Router(name='start_router')
logger = setup_logger(__name__)


@router.message(CommandStart())
async def start_command(message: types.Message):
    if message.chat.type == "private":

        user = await create_user(data={
            "user_id": message.from_user.id,
            "username": message.from_user.username,
        })

        await create_file_profile(
            file_name=message.from_user.id
        )

        await message.answer(text="""Привет, с помошью меня, вы можете собрать множество wife из самых различных манг/аниме/игр.\nВы можете продавать или обменивать их на глобальном рынке или в своем локальном""", reply_markup=await start_kb.start_kb())
    else:
        await message.answer("Перейдите в бота для использования комманд, актуальные команды можете увидеть в /help")

@router.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        text="""<b>Список команд:</b>
                    
            <b>Main Commands:</b>
            /start - Начать работу с ботом
            /help - Показать список команд
            /promo - Ввести промокод
            /vip - Купить VIP статус
            /top - Показать топ пользователей
            /profile - Просмотреть свой профиль
            /shop - Открыть рынок
            /bonus - Получить ежечасный бонус

            <b>Profile Management:</b>
            /profile - Просмотр своего профиля

            <b>Marketplace:</b>
            /shop - Глобальный и локальный рынки

            <b>Игры:</b>
            /tictactoe - Игра "Крестики-нолики"
            /findball - Игра "Найди шарик"
            /guessnumber - Игра "Угадай число"
            /rps - Игра "Камень, ножницы, бумага"

            <b>Вип и бонусы:</b>
            /vip - Покупка VIP статуса
            /bonus - Получить ежечасный бонус

            <b>Примечание:</b>
            Для некоторых команд требуется баланс или специальный статус.
            """,
        parse_mode="HTML"
    )


@router.message(Command("promo"))
async def promo_command(message: types.Message, state: FSMContext):
    await state.set_state(Promo.promo)
    await message.answer("""Введите промокод""")


@router.message(F.text, Promo.promo)
async def check_promo(message: types.Message, state: FSMContext):

    result = await get_promo(promocode=message.text)

    if result is None:
        await message.answer("Такого промокода не существует")
    else:
        added = await add_balance(add_to=Decimal(result), user_id=message.from_user.id)
        await message.answer(f"Вы ввели промокод на {added["value"]} бонусов")
        
    await state.clear()


@router.message(Command("vip", "VIP"))
async def buy_vip(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text=f"Оплатить с помощью ⭐️stars⭐️", callback_data="vip_stars")
    builder.button(text=f"Банковский перевод", callback_data="card")

    await message.answer("Выберите метод оплаты:", reply_markup=builder.as_markup())

@router.callback_query(F.data == "card")
async def card_pay(callback: types.CallbackQuery):
    await callback.message.answer("Для оплаты отправьте сумму в 100/159/200 рублей в зависимости от уровня VIP\nРеквизиты - 2200152319651066 (альфа банк)\nОтправьте ваш чек сюда @c0ral0vii")


@router.callback_query(F.data == "vip_stars")
async def payment_keyboard(callback: types.CallbackQuery):  
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Оплатить VIP-1 уровня 50 ⭐️", callback_data="donate_50"))
    builder.row(types.InlineKeyboardButton(text="Оплатить VIP-2 уровня 100 ⭐️", callback_data="donate_100"))
    builder.row(types.InlineKeyboardButton(text="Оплатить VIP-3 уровня 150 ⭐️", callback_data="donate_150"))

    await callback.message.answer(text="Выберит какой VIP вы хотите купить:", reply_markup=builder.as_markup())


@router.pre_checkout_query()
async def on_pre_checkout_query(
    pre_checkout_query: types.PreCheckoutQuery,
):
    await pre_checkout_query.answer(ok=True)


@router.callback_query(F.data == "donate_50")
@router.callback_query(F.data == "donate_100")
@router.callback_query(F.data == "donate_150")
async def send_invoice_handler(callback: types.CallbackQuery):  
    callback_data = callback.data.split("_")[-1]

    prices = [types.LabeledPrice(label="Оплатить Vip", amount=callback_data)]
    
    await callback.message.answer_invoice(  
        title="Донат",  
        description="После покупки вы получите статус випа на месяц",  
        prices=prices,  
        provider_token="",  
        payload="donate",  
        currency="XTR",  
    )


@router.message(F.successful_payment)
async def on_successful_payment(message: types.Message):
    logger.debug(message.successful_payment.order_info)