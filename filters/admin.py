from aiogram import F
from settings.base import ADMINS

ADMIN_FILTER = F.from_user.id.in_(ADMINS)
