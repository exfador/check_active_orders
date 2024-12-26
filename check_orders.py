from __future__ import annotations

from os.path import exists
from typing import TYPE_CHECKING

import telebot

if TYPE_CHECKING:
    from exfa import exfa

import os
import FunPayAPI.types
from FunPayAPI.account import Account
from logging import getLogger
from telebot.types import Message
from tg_bot import static_keyboards as skb
import time
import json

NAME = "Lots Active"
VERSION = "0.1"
DESCRIPTION = """
Этот плагин позволяет оперативно получать список активных заказов, которые еще не закрыты. 
Он значительно упрощает процесс работы, позволяя быстро отправлять в техническую поддержку (ТП) идентификаторы заказов (#id), без необходимости каждый раз вручную искать их в системе. 
Это экономит время и повышает эффективность обработки запросов."""
CREDITS = "@exfador"
UUID = "14e34e59-0939-45b0-8748-f2ba008c075b"
SETTINGS_PAGE = False

logger = getLogger("FPC.lots_active")

def get_active_orders(exfa: exfa, tg_msg: Message) -> None:
    bot = exfa.telegram.bot

    try:
        next_order_id, orders = exfa.account.get_sells(include_closed=False, include_refunded=False)

        if not orders:
            bot.send_message(tg_msg.chat.id, "🟢 Нет активных заказов.")
            return

        message = "🟢 Активные заказы:\n\n"
        active_order_ids = []

        for order_shortcut in orders:
            try:
                order = exfa.account.get_order(order_shortcut.id)
                message += f"🔹 ID заказа: #{order.id}\n"
                message += f"🔹 Покупатель: {order.buyer_username}\n"
                message += f"🔹 Статус: {order.status}\n"
                message += f"🔹 Товар: {order.short_description}\n"
                message += f"🔹 Цена: {order.sum} руб.\n"
                message += f"🔹 Ссылка: https://funpay.com/orders/{order.id}/\n\n"
                active_order_ids.append(order.id)
            except Exception as e:
                logger.error(f"[ACTIVE ORDERS] Не удалось получить информацию о заказе {order_shortcut.id}. Ошибка: {e}")
                message += f"🔹 ID заказа: #{order_shortcut.id}\n"
                message += f"🔹 Ошибка: Не удалось получить полную информацию о заказе.\n\n"
                active_order_ids.append(order_shortcut.id)

        file_path = os.path.join("storage", "plugins", "active_orders.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(active_order_ids, file, ensure_ascii=False, indent=4)

        bot.send_message(tg_msg.chat.id, message)

        active_orders_formatted = " ".join([f"<code>#{order_id}</code>" for order_id in active_order_ids])
        bot.send_message(tg_msg.chat.id, f"Список активных заказов: {active_orders_formatted}", parse_mode="HTML")

        with open(file_path, "rb") as file:
            bot.send_document(tg_msg.chat.id, file, caption="Файл с активными заказами (active_orders.json)")

    except Exception as e:
        logger.error(f"[ACTIVE ORDERS] Не удалось получить активные заказы. Ошибка: {e}")
        bot.send_message(tg_msg.chat.id, "❌ Не удалось получить активные заказы. Попробуйте позже.")

def init_commands(exfa: exfa):
    if not exfa.telegram:
        return
    tg = exfa.telegram
    bot = exfa.telegram.bot

    def active_orders(m: Message):
        get_active_orders(exfa, m)

    exfa.add_telegram_commands(UUID, [
        ("active_orders", "показывает активные заказы", True),
    ])

    tg.msg_handler(active_orders, commands=["active_orders"])

BIND_TO_PRE_INIT = [init_commands]
BIND_TO_DELETE = None