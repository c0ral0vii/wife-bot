from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, StateFilter
import random
from decimal import Decimal
from src.database.orm.users import add_balance
from src.redis.services import redis_manager
from src.logger import setup_logger
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from src.database.orm.users import add_alter_balance


router = Router()
logger = setup_logger(__name__)

class Game(StatesGroup):
    game = State()


@router.message(Command("games"))
async def mess_games(message: types.Message):
    await games_func(message=message)


@router.callback_query(F.data == "mini-games")
async def call_games(callback: types.CallbackQuery):
    await games_func(message=callback.message)


async def games_func(message: types.Message | types.CallbackQuery):
    await message.answer(f"🕹️Все доступные игры:",
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[[InlineKeyboardButton(text="❌Крестики нолики", callback_data="tictactoe")], [InlineKeyboardButton(text="🥛Найти шарик в стакане", callback_data="findball")],
                            [InlineKeyboardButton(text="🪨Камень, ножницы, бумага", callback_data="rps")], [InlineKeyboardButton(text="🔢Угадай число", callback_data="guessnumber")],
                            ],
                        ))


games = {}

def create_board():
    return [[" " for _ in range(3)] for _ in range(3)]

def check_winner(board):
    for row in board:
        if row[0] == row[1] == row[2] != " ":
            return row[0]
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] != " ":
            return board[0][col]
    if board[0][0] == board[1][1] == board[2][2] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != " ":
        return board[0][2]
    return None

def is_full(board):
    return all(cell != " " for row in board for cell in row)

def bot_move_easy(board):
    empty_cells = [(i, j) for i in range(3) for j in range(3) if board[i][j] == " "]
    return random.choice(empty_cells)

def bot_move_medium(board):
    for i in range(3):
        for j in range(3):
            if board[i][j] == " ":
                board[i][j] = "O"
                if check_winner(board) == "O":
                    return (i, j)
                board[i][j] = " "
    return bot_move_easy(board)

def minimax(board, is_maximizing):
    winner = check_winner(board)
    if winner == "O":
        return 1
    if winner == "X":
        return -1
    if is_full(board):
        return 0

    if is_maximizing:
        best_score = -float("inf")
        for i in range(3):
            for j in range(3):
                if board[i][j] == " ":
                    board[i][j] = "O"
                    score = minimax(board, False)
                    board[i][j] = " "
                    best_score = max(score, best_score)
        return best_score
    else:
        best_score = float("inf")
        for i in range(3):
            for j in range(3):
                if board[i][j] == " ":
                    board[i][j] = "X"
                    score = minimax(board, True)
                    board[i][j] = " "
                    best_score = min(score, best_score)
        return best_score

def bot_move_hard(board):
    best_score = -float("inf")
    best_move = None
    for i in range(3):
        for j in range(3):
            if board[i][j] == " ":
                board[i][j] = "O"
                score = minimax(board, False)
                board[i][j] = " "
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    return best_move


@router.callback_query(F.data == "tictactoe")
async def start_tictactoe(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Легкий", callback_data="ttt_easy"),
        InlineKeyboardButton(text="Средний", callback_data="ttt_medium"),
        InlineKeyboardButton(text="Сложный", callback_data="ttt_hard"),
    )
    await callback.message.answer("Выберите уровень сложности:", reply_markup=builder.as_markup())


@router.callback_query(lambda c: c.data.startswith("ttt_"))
async def ttt_level_selected(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    level = callback_query.data.split("_")[1]
    play_count = await redis_manager.get(f"user_plays:{user_id}")

    if play_count:
        if int(play_count) >= 5:
            await callback_query.message.edit_text("🔒Вы уже играли 5 раз сегодня. Попробуйте завтра!")
            await callback_query.answer()
            return
    else:
        await redis_manager.set_with_ttl(f"user_plays:{user_id}", "0", 86400)  # 24 hours TTL

    # Increment play count
    await redis_manager.set_with_ttl(f"user_plays:{user_id}", str(int(play_count or 0) + 1), 86400)

    games[user_id] = {"board": create_board(), "level": level, "current_player": "X", 'difficalty': level}


    await callback_query.message.edit_text("Игра началась! Ваш ход. Вы - X", reply_markup=await get_game_keyboard(user_id))
    await callback_query.answer()

async def get_game_keyboard(user_id):
    board = games[user_id]["board"]
    builder = InlineKeyboardBuilder()
    for i in range(3):
        row_buttons = []
        for j in range(3):
            row_buttons.append(InlineKeyboardButton(text=board[i][j], callback_data=f"move_{i}_{j}"))
        builder.row(*row_buttons)
    return builder.as_markup()

@router.callback_query(lambda c: c.data.startswith("move_"))
async def ttt_move(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in games:
        await callback_query.message.edit_text("Игра не начата.")
        await callback_query.answer()
        return

    move = callback_query.data.split("_")[1:]
    i, j = int(move[0]), int(move[1])
    if games[user_id]["board"][i][j] != " ":
        await callback_query.answer("Клетка занята!")
        return

    games[user_id]["board"][i][j] = "X"
    winner = check_winner(games[user_id]["board"])
    if winner:
        if games[user_id]["difficalty"] == "easy":
            value = 500
            alter_value = 1
        elif games[user_id]["difficalty"] == "medium":
            value = 750
            alter_value = 3

        elif games[user_id]["difficalty"] == "hard":
            value = 1200
            alter_value = 5

        else:
            value = 1000
            alter_value = 2


        added = await add_balance(user_id=user_id, add_to=Decimal(value))
        alter_added = await add_alter_balance(user_id=user_id, add_to=Decimal(alter_value))
        await callback_query.message.answer(f"За победу вам начислено 💠{added["value"]}, 🔰{alter_added["value"]}", 
                                            message_effect_id="5104841245755180586")
        del games[user_id]
        await callback_query.answer("Вы выйграли!", show_alert=False)
        return
    if is_full(games[user_id]["board"]):
        await callback_query.message.edit_text("Ничья!", reply_markup=None)
        del games[user_id]
        await callback_query.answer()
        return

    level = games[user_id]["level"]
    if level == "easy":
        bot_i, bot_j = bot_move_easy(games[user_id]["board"])
    elif level == "medium":
        bot_i, bot_j = bot_move_medium(games[user_id]["board"])
    elif level == "hard":
        bot_i, bot_j = bot_move_hard(games[user_id]["board"])

    games[user_id]["board"][bot_i][bot_j] = "O"
    winner = check_winner(games[user_id]["board"])

    if winner:
        if winner == "X":
            if games[user_id]["difficalty"] == "easy":
                value = 500
            elif games[user_id]["difficalty"] == "medium":
                value = 750
            elif games[user_id]["difficalty"] == "hard":
                value = 1200
            else:
                value = 1000

            added = await add_balance(user_id=user_id, add_to=Decimal(value))
            await callback_query.message.answer(f"За победу вам начислено 💰{added["value"]}", 
                                                message_effect_id="5104841245755180586")
            del games[user_id]
            await callback_query.answer("Вы выйграли!", show_alert=True)
            return
        
        await callback_query.message.edit_text(f"Победитель: {winner}!", reply_markup=None)
        del games[user_id]
        return
    if is_full(games[user_id]["board"]):
        await callback_query.message.edit_text("Ничья!", reply_markup=None)
        del games[user_id]
        await callback_query.answer()
        return

    await callback_query.message.edit_text("Ваш ход.", reply_markup=await get_game_keyboard(user_id))
    await callback_query.answer()


@router.callback_query(F.data == "findball")
async def start_find_ball(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Легкий", callback_data="ball_easy"),
        InlineKeyboardButton(text="Средний", callback_data="ball_medium"),
        InlineKeyboardButton(text="Сложный", callback_data="ball_hard"),
    )
    await callback.message.answer("Выберите уровень сложности:", reply_markup=builder.as_markup())

@router.callback_query(lambda c: c.data.startswith("ball_"))
async def ball_level_selected(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    level = callback_query.data.split("_")[1]
    if level == "easy":
        num_cups = 3
    elif level == "medium":
        num_cups = 4
    elif level == "hard":
        num_cups = 5
    else:
        num_cups = 3

    play_count = await redis_manager.get(f"user_plays:{user_id}")

    if play_count:
        if int(play_count) >= 5:
            await callback_query.message.edit_text("🔒Вы уже играли 5 раз сегодня. Попробуйте завтра!")
            await callback_query.answer()
            return
    else:
        await redis_manager.set_with_ttl(f"user_plays:{user_id}", "0", 86400)  # 24 hours TTL

    # Increment play count
    await redis_manager.set_with_ttl(f"user_plays:{user_id}", str(int(play_count or 0) + 1), 86400)

    ball_position = random.randint(1, num_cups)
    games[user_id] = {"ball_position": ball_position, "num_cups": num_cups, "difficalty": level}
    builder = InlineKeyboardBuilder()
    for i in range(1, num_cups + 1):
        builder.add(InlineKeyboardButton(text=f"->🥛<-", callback_data=f"stakan_{i}"))
    builder.adjust(num_cups)
    await callback_query.message.edit_text(f"Шарик спрятан под одним из {num_cups} 🥛стаканов. Угадай!", reply_markup=builder.as_markup())
    await callback_query.answer()

@router.callback_query(lambda c: c.data.startswith("stakan_"))
async def process_ball_guess(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in games:
        await callback_query.message.edit_text("Игра не начата. Используйте /findball, чтобы начать.")
        await callback_query.answer()
        return

    guess = int(callback_query.data.split("_")[1])
    if guess < 1 or guess > games[user_id]["num_cups"]:
        await callback_query.answer("Некорректный выбор стакана.")
        return

    if guess == games[user_id]["ball_position"]:
        if games[user_id]["difficalty"] == "easy":
            value = 750
            alter_value = 1
        elif games[user_id]["difficalty"] == "medium":
            value = 1000
            alter_value = 3

        elif games[user_id]["difficalty"] == "hard":
            value = 1500
            alter_value = 5

        else:
            value = 1000
            alter_value = 2

        alter_added = await add_alter_balance(user_id=user_id, add_to=Decimal(alter_value))
        added = await add_balance(user_id=user_id, add_to=Decimal(value))
        await callback_query.message.delete()
        await callback_query.message.answer(f"Правильно! Ты нашел шарик!Твой выигрыш - 💠{added["value"]}, 🔰{alter_added["value"]}", message_effect_id="5104841245755180586")
    else:
        await callback_query.message.edit_text(f"Неправильно. Шарик был под стаканом {games[user_id]['ball_position']}.", reply_markup=None)
    del games[user_id]
    await callback_query.answer()


@router.callback_query(F.data == "guessnumber")
async def start_guess_number(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Легкий", callback_data="guess_number_easy"),
        InlineKeyboardButton(text="Средний", callback_data="guess_number_medium"),
        InlineKeyboardButton(text="Сложный", callback_data="guess_number_hard"),
    )
    
    await callback.message.answer("Выберите уровень сложности:", reply_markup=builder.as_markup())


@router.callback_query(lambda c: c.data.startswith("guess_number_"))
async def guess_level_selected(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    level = callback_query.data.split("_")[-1]
    if level == "easy":
        max_attemps = 3
        min_num, max_num = 1, 10
    elif level == "medium":
        max_attemps = 2
        min_num, max_num = 1, 10
    elif level == "hard":
        max_attemps = 1
        min_num, max_num = 1, 10
    else:
        max_attemps = 1
        min_num, max_num = 1, 10
    
    play_count = await redis_manager.get(f"user_plays:{user_id}")

    if play_count:
        if int(play_count) >= 5:
            await callback_query.message.edit_text("🔒Вы уже играли 5 раз сегодня. Попробуйте завтра!")
            await callback_query.answer()
            return
    else:
        await redis_manager.set_with_ttl(f"user_plays:{user_id}", "0", 86400)  # 24 hours TTL

    # Increment play count
    await redis_manager.set_with_ttl(f"user_plays:{user_id}", str(int(play_count or 0) + 1), 86400)

    secret_number = random.randint(min_num, max_num)
    games[user_id] = {"secret_number": secret_number, 'difficalty': level,"min_num": min_num, "max_num": max_num, "attempts": 0, "max_attemps": max_attemps}
    await callback_query.message.edit_text(f"Угадайте число от {min_num} до {max_num}. Максимальное количество попыток: {max_attemps}", reply_markup=None)

    await state.set_state(Game.game)
    await callback_query.answer()



@router.message(lambda message: message.text.isdigit(), StateFilter(Game.game))
async def process_guess_number(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in games:
        await message.answer("Игра не начата. Используйте /guessnumber, чтобы начать.")
        return

    guess = int(message.text)
    games[user_id]["attempts"] += 1
    if games[user_id]["attempts"] == games[user_id]["max_attemps"]:
        await message.answer("Вы проиграли! Попробуйте еще раз")
        del games[user_id]
        await state.clear()    
        return
    
    if guess < games[user_id]["min_num"] or guess > games[user_id]["max_num"]:
        await message.answer(f"Введите число от {games[user_id]['min_num']} до {games[user_id]['max_num']}.")
        return

    if guess < games[user_id]["secret_number"]:
        await message.answer("Больше!")
    elif guess > games[user_id]["secret_number"]:
        await message.answer("Меньше!")
    else:
        if games[user_id]["difficalty"] == "easy":
            value = 750
            alter_value = 1
        elif games[user_id]["difficalty"] == "medium":
            value = 1000
            alter_value = 3

        elif games[user_id]["difficalty"] == "hard":
            value = 1500
            alter_value = 5

        else:
            value = 1000
            alter_value = 2

        added = await add_balance(user_id=user_id, add_to=Decimal(value))
        alter_added = await add_alter_balance(user_id=user_id, add_to=Decimal(alter_value))

        await message.answer(f"Правильно! Вы угадали число за {games[user_id]['attempts']} попыток.\nВаш выйгрыш 💠{added["value"]}, 🔰{alter_added["value"]}", message_effect_id="5104841245755180586")
        del games[user_id]
        await state.clear()    
    


@router.callback_query(F.data == "rps")
async def start_rps(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Легкий", callback_data="rps_level_easy"),
        InlineKeyboardButton(text="Средний", callback_data="rps_level_medium"),
        InlineKeyboardButton(text="Сложный", callback_data="rps_level_hard"),
    )
    await callback.message.answer("Выберите уровень сложности:", reply_markup=builder.as_markup())

@router.callback_query(lambda c: c.data.startswith("rps_level_"))
async def rps_level_selected(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    level = callback_query.data.split("_")[2]
    games[user_id] = {"level": level}
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Камень", callback_data="rps_rock"),
        InlineKeyboardButton(text="Бумага", callback_data="rps_paper"),
        InlineKeyboardButton(text="Ножницы", callback_data="rps_scissors"),
    )
    await callback_query.message.edit_text("Выберите вашу фигуру:", reply_markup=builder.as_markup())
    await callback_query.answer()

@router.callback_query(lambda c: c.data.startswith("rps_"))
async def rps_play(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_choice = callback_query.data.split("_")[1]
    bot_choice = random.choice(["rock", "paper", "scissors"])

    # Check if user has already played 5 times today
    play_count = await redis_manager.get(f"user_plays:{user_id}")
    if play_count:
        if int(play_count) >= 5:
            await callback_query.message.edit_text("🔒Вы уже играли 5 раз сегодня. Попробуйте завтра!")
            await callback_query.answer()
            return
    else:
        await redis_manager.set_with_ttl(f"user_plays:{user_id}", "0", 86400)  # 24 hours TTL

    # Increment play count
    await redis_manager.set_with_ttl(f"user_plays:{user_id}", str(int(play_count or 0) + 1), 86400)

    result = determine_winner(user_choice, bot_choice)
    if result == "user":
        level = games.get(user_id, {}).get("level", "easy")
        reward = Decimal(500) if level == "easy" else Decimal(750) if level == "medium" else Decimal(1500)
        alter_reward = Decimal(1) if level == "easy" else Decimal(3) if level == "medium" else Decimal(5)
        alter_added = await add_alter_balance(user_id=user_id, add_to=alter_reward)
        added = await add_balance(user_id=user_id, add_to=reward)
        await callback_query.message.edit_text(f"Вы выбрали {user_choice}. Вы выиграли! Баланс добавлен: {added["value"]}")
    elif result == "bot":
        await callback_query.message.edit_text(f"Вы выбрали {user_choice}. Бот выиграл!")
    else:
        await callback_query.message.edit_text(f"Вы выбрали {user_choice}. Ничья!")
    await callback_query.answer()


def determine_winner(user, bot):
    if user == bot:
        return "draw"
    if (user == "rock" and bot == "scissors") or \
       (user == "paper" and bot == "rock") or \
       (user == "scissors" and bot == "paper"):
        return "user"
    else:
        return "bot"