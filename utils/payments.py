import logging
import aiohttp
from aiogram import html
from aiogram.types import CallbackQuery
import datetime
from settings.base import PAGE_SIZE, DATE_FORMAT

        

def format_payment(curr_payment: dict):
    payment_id = curr_payment['id']
    type = curr_payment['type']
    user_id = curr_payment['user_id']
    wallet_address = curr_payment['address']
    amount = curr_payment['amount']
    updated_at = datetime.datetime.fromisoformat(curr_payment['updated_at']).strftime(DATE_FORMAT)
    return (
        f'Payment ID: {html.bold(payment_id)}\n'
        f'Payment type: {html.bold('Withdraw' if type == 0 else 'Deposit')}\n'
        f'User ID: {html.bold(user_id)}\n'
        f'Wallet address: {html.bold(wallet_address)}\n'
        f'Amount: {html.bold(f'{amount}$')}\n'
        f'Verdict time: {html.bold(updated_at)}'
    )
