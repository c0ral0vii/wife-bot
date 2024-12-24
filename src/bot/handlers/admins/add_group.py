from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.bot.middlewares.admin_middleware import AdminMiddleware


router = Router()
router.message.middleware(AdminMiddleware())