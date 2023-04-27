import os
import secrets
import sys
from datetime import datetime
from uuid import uuid4

from dotenv import load_dotenv
from pymongo import MongoClient
from telebot import TeleBot
from telebot.types import Message, InlineQueryResultArticle, InputTextMessageContent, InlineQuery, \
    InlineKeyboardMarkup, InlineKeyboardButton, ChosenInlineResult, CallbackQuery

import messages
from messages import WELCOME_MESSAGE, WELCOME_BACK_MESSAGE

load_dotenv()

CELL_X = "❌"
CELL_O = "⭕️"
CELL_EMPTY = "🔳"

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TELEGRAM_TOKEN:
    print("err: TELEGRAM_TOKEN is required")
    sys.exit(1)
bot = TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")

client = MongoClient(port=int(os.getenv('MONGO_PORT', 27017)))
db = client.tictactoe


def _get_or_create_user(telegram_id) -> dict:
    user = db.users.find_one({"telegram_id": str(telegram_id)})
    if not user:
        db.users.insert_one({"telegram_id": str(telegram_id), "balance": 1000})
        user = {"telegram_id": str(telegram_id), "balance": 1000, "new": True}

    return user


def _find_winner(field: list) -> str:
    for column in range(5):
        if (field[0 + column] == field[5 + column] == field[10 + column] == field[15 + column]
                and field[0 + column] != ""):
            return field[0 + column]
        if (field[5 + column] == field[10 + column] == field[15 + column] == field[20 + column]
                and field[5 + column] != ""):
            return field[5 + column]
    for row in range(5):
        if (field[5 * row] == field[5 * row + 1] == field[5 * row + 2] == field[5 * row + 3]
                and field[5 * row] != ""):
            return field[5 * row]
        if (field[5 * row + 1] == field[5 * row + 2] == field[5 * row + 3] == field[5 * row + 4]
                and field[5 * row + 1] != ""):
            return field[5 * row + 1]
    for offset in range(2):
        if (field[0 + offset] == field[6 + offset] == field[12 + offset] == field[18 + offset]
                and field[0 + offset] != ""):
            return field[0 + offset]
    for offset in range(2):
        if (field[3 + offset] == field[7 + offset] == field[11 + offset] == field[15 + offset]
                and field[3 + offset] != ""):
            return field[3 + offset]

    return ""


def _is_draw(field: list) -> bool:
    for column in range(5):
        if not ([field[0 + column], field[5 + column], field[10 + column], field[15 + column]].count("X") >= 2
                and [field[0 + column], field[5 + column], field[10 + column], field[15 + column]].count("O") >= 2):
            return False
        if not ([field[5 + column], field[10 + column], field[15 + column], field[20 + column]].count("X") >= 2
                and [field[5 + column], field[10 + column], field[15 + column], field[20 + column]].count("O") >= 2):
            return False
    for row in range(5):
        if not ([field[5 * row], field[5 * row + 1], field[5 * row + 2], field[5 * row + 3]].count("X") >= 2
                and [field[5 * row], field[5 * row + 1], field[5 * row + 2], field[5 * row + 3]].count("O") >= 2):
            return False
        if not ([field[5 * row + 1], field[5 * row + 2], field[5 * row + 3], field[5 * row + 4]].count("X") >= 2
                and [field[5 * row + 1], field[5 * row + 2], field[5 * row + 3], field[5 * row + 4]].count("O") >= 2):
            return False
    for offset in range(2):
        if not ([field[0 + offset], field[6 + offset], field[12 + offset], field[18 + offset]].count("X") >= 2
                and [field[0 + offset], field[6 + offset], field[12 + offset], field[18 + offset]].count("O") >= 2):
            return False
    for offset in range(2):
        if not ([field[3 + offset], field[7 + offset], field[11 + offset], field[15 + offset]].count("X") >= 2
                and [field[3 + offset], field[7 + offset], field[11 + offset], field[15 + offset]].count("O") >= 2):
            return False

    return True


def _get_cell(field: list, cell_id: int) -> str:
    return CELL_EMPTY if field[cell_id] == "" else (CELL_X if field[cell_id] == "X" else CELL_O)


def _get_keyboard(field=None, game_id=None, show_surround=True) -> list:
    buttons = []
    for i in range(25):
        cell_text = _get_cell(field, i) if field is not None else CELL_EMPTY
        cell_data = f"turn_{game_id}_{i}" if game_id is not None else 'empty_data'
        buttons.append(InlineKeyboardButton(cell_text, callback_data=cell_data))

    # Group buttons by 3 [[x, x, x], [x, x, x], [x, x, x]]. Won't work if len(buttons) % 3 != 0
    result = list(zip(*[buttons[i::5] for i in range(5)]))
    if show_surround:
        result.append([
            InlineKeyboardButton("Surround", callback_data=f"surround_{game_id}")
        ])

    return result


@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def handle_reject_game(call: CallbackQuery) -> None:
    game_id = call.data.replace("reject_", "")
    game = db.games.find_one({"id": game_id, "state": "pending"})
    if not game:
        bot.answer_callback_query(call.id, messages.GAME_NOT_FOUND, show_alert=True, cache_time=0)
        return

    user = _get_or_create_user(call.from_user.id)
    if game.get("first_player") == user.get("telegram_id"):  # creator of game
        winner_id = user.get("telegram_id")
        db.games.update_one({"id": game_id}, {"$set": {"state": "canceled"}})
        callback_answer = messages.GAME_CANCELED
        actor = "organiser"
    else:
        winner_id = game.get("first_player")
        db.games.update_one({"id": game_id}, {"$set": {"state": "rejected", "second_player": user.get("telegram_id")}})
        callback_answer = messages.GAME_REJECTED
        actor = "opponent"

    bot.answer_callback_query(call.id, callback_answer, show_alert=True, cache_time=0)
    db.users.update_one({"telegram_id": winner_id}, {"$inc": {"balance": game.get("bet")}})
    bot.edit_message_text(inline_message_id=call.inline_message_id,
                          text=f"Game canceled by {actor}. Bet returned to organiser's balance.",
                          reply_markup=None)


@bot.callback_query_handler(func=lambda call: call.data.startswith('surround_'))
def handle_surround(call: CallbackQuery) -> None:
    game_id = call.data.replace("surround_", "")
    game = db.games.find_one({"id": game_id, "state": "started"})
    if not game:
        bot.answer_callback_query(call.id, messages.GAME_NOT_FOUND, show_alert=True, cache_time=0)
        return

    user = _get_or_create_user(call.from_user.id)

    if game.get("first_player") != user.get("telegram_id") and game.get("second_player") != user.get("telegram_id"):
        bot.answer_callback_query(call.id, messages.NOT_MEMBER, show_alert=True, cache_time=0)
        return

    if game.get("first_player") == user.get("telegram_id"):
        winner_id = game.get("second_player")
        username = game.get("first_player_name")
        winner = game.get("second_player_name")
    else:
        winner_id = game.get("first_player")
        username = game.get("second_player_name")
        winner = game.get("first_player_name")

    db.users.update_one({"telegram_id": winner_id}, {"$inc": {"balance": 2 * int(game.get("bet"))}})
    db.games.update_one({"id": game_id}, {"$set": {"state": "winner_first"}})
    bot.answer_callback_query(call.id, messages.GIVEN_UP_ALERT,
                              show_alert=True,
                              cache_time=0)

    bot.edit_message_text(inline_message_id=call.inline_message_id,
                          text=messages.GAME_END_GIVE_UP(username, winner, game_id),
                          reply_markup=None)


@bot.callback_query_handler(func=lambda call: call.data.startswith('turn_'))
def handle_turn(call: CallbackQuery) -> None:
    game_id, cell = call.data.replace("turn_", "").split("_")
    if int(cell) < 0 or int(cell) > 24:
        bot.answer_callback_query(call.id, messages.CELL_NOT_FOUND(cell), show_alert=True, cache_time=0)
        return

    game = db.games.find_one({"id": game_id, "state": "started"})
    if not game:
        bot.answer_callback_query(call.id, messages.GAME_NOT_FOUND, show_alert=True, cache_time=0)
        return

    user = _get_or_create_user(call.from_user.id)
    if game.get("first_player") != user.get("telegram_id") and game.get("second_player") != user.get("telegram_id"):
        bot.answer_callback_query(call.id, messages.NOT_MEMBER, show_alert=True, cache_time=0)
        return

    if game.get("turn") != user.get("telegram_id"):
        bot.answer_callback_query(call.id, messages.NOT_YOUR_TURN, show_alert=True, cache_time=0)
        return

    field = game.get("field", [])
    if not field:
        field = ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]

    if field[int(cell)] != "":
        bot.answer_callback_query(call.id, messages.CELL_CHANGED, show_alert=True, cache_time=0)
        return

    bot.answer_callback_query(call.id, "", show_alert=False, cache_time=0)
    field[int(cell)] = "X" if game.get("first_player") == user.get("telegram_id") else "O"
    new_turn = game.get("second_player") if game.get("first_player") == user.get("telegram_id") else game.get(
        "first_player")

    if "" not in field or _find_winner(field) != "" or _is_draw(field):
        winner = _find_winner(field)
        if winner == "X":
            state = "winner_first"
        elif winner == "O":
            state = "winner_second"
        else:
            state = "no_winner"

        db.games.update_one({"id": game_id}, {"$set": {"field": field, "state": state}})
        if state != "no_winner":
            winner_id = game.get('first_player') if state == "winner_first" else game.get('second_player')
            db.users.update_one({"telegram_id": winner_id}, {"$inc": {"balance": 2 * int(game.get("bet"))}})

            username = game.get("first_player_name") if state == "winner_first" else game.get("second_player_name")
            bot.edit_message_text(inline_message_id=call.inline_message_id,
                                  text=messages.GAME_END_WINNER(username, game_id),
                                  reply_markup=InlineKeyboardMarkup(_get_keyboard(field, show_surround=False)))
        else:
            db.users.update_one({"telegram_id": game.get('first_player')},
                                {"$inc": {"balance": int(game.get("bet"))}})
            db.users.update_one({"telegram_id": game.get('second_player')},
                                {"$inc": {"balance": int(game.get("bet"))}})
            bot.edit_message_text(inline_message_id=call.inline_message_id,
                                  text=messages.GAME_END_DRAW(game_id),
                                  reply_markup=InlineKeyboardMarkup(_get_keyboard(field, show_surround=False)))
        return

    db.games.update_one({"id": game_id}, {"$set": {"field": field, "turn": new_turn}})
    new_turn_name = game.get('first_player_name') if new_turn == game.get('first_player') else game.get(
        'second_player_name')
    bot.edit_message_text(inline_message_id=call.inline_message_id,
                          text=messages.GAME_YOUR_TURN(new_turn_name, 2 * game.get('bet'), game_id),
                          reply_markup=InlineKeyboardMarkup(_get_keyboard(field, game_id, True)))


@bot.callback_query_handler(func=lambda call: call.data == "show_balance")
def handle_accept_game(call: CallbackQuery) -> None:
    user = _get_or_create_user(call.from_user.id)
    bot.answer_callback_query(call.id, messages.BALANCE_REFRESHED, show_alert=False, cache_time=0)

    try:
        bot.edit_message_text(chat_id=user.get("telegram_id"),
                              message_id=call.message.id, text=WELCOME_BACK_MESSAGE(user.get('balance')),
                              reply_markup=InlineKeyboardMarkup([
                                  [
                                      InlineKeyboardButton("Refresh", callback_data="show_balance"),
                                  ]
                              ]))
    except:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_'))
def handle_accept_game(call: CallbackQuery) -> None:
    game_id = call.data.replace("accept_", "")
    game = db.games.find_one({"id": game_id, "state": "pending"})
    if not game:
        bot.answer_callback_query(call.id, messages.GAME_NOT_FOUND, show_alert=True, cache_time=0)
        return

    user = _get_or_create_user(call.from_user.id)
    if game.get("first_player") == user.get("telegram_id"):  # creator of game
        bot.answer_callback_query(call.id, messages.CANNOT_ACCEPT_OWN_GAME, show_alert=True, cache_time=0)
        return

    if user.get('balance') < int(game.get('bet')):
        bot.answer_callback_query(call.id, messages.INSUFFICIENT_BALANCE, show_alert=True, cache_time=0)
        return

    db.users.update_one({"telegram_id": user.get('telegram_id')}, {"$inc": {"balance": -1 * int(game.get("bet"))}})

    username = call.from_user.username
    if not username:
        username = ' '.join([call.from_user.first_name, call.from_user.last_name])

    if secrets.choice([0, 1]):
        new_turn = game.get("first_player")
        new_turn_name = game.get("first_player_name")
    else:
        new_turn = user.get("telegram_id")
        new_turn_name = username

    db.games.update_one({"id": game_id}, {
        "$set": {"state": "started", "second_player": user.get("telegram_id"), "second_player_name": username,
                 "field": [], "turn": new_turn}})

    bot.edit_message_text(inline_message_id=call.inline_message_id,
                          text=messages.GAME_YOUR_TURN(new_turn_name, 2 * game.get("bet"), game_id),
                          reply_markup=InlineKeyboardMarkup(_get_keyboard(None, game_id, True)))


@bot.inline_handler(lambda query: query.query != "")
def inline_handler(inline_query: InlineQuery) -> None:
    user = _get_or_create_user(inline_query.from_user.id)

    try:
        bet = inline_query.query.strip()
        if not bet.isnumeric() or int(bet) <= 0 or int(bet) > user.get("balance"):
            bot.answer_inline_query(inline_query.id,
                                    switch_pm_text=messages.BET_VALIDATION_MESSAGE(user.get("balance")),
                                    switch_pm_parameter="invalid_bet", cache_time=0, is_personal=True, results=[])
            return

        username = inline_query.from_user.username
        if not username:
            username = ' '.join([inline_query.from_user.first_name, inline_query.from_user.last_name])
        r = InlineQueryResultArticle(secrets.token_urlsafe(6), "Create new game",
                                     input_message_content=InputTextMessageContent(
                                         messages.INVITE(username, int(bet)),
                                         parse_mode="HTML"),
                                     description=messages.BET_PREVIEW(int(bet)),
                                     reply_markup=InlineKeyboardMarkup([
                                         [InlineKeyboardButton("Processing...", callback_data="empty_data")]
                                     ]))
        bot.answer_inline_query(inline_query.id, [r], cache_time=0)
    except Exception as e:
        print(e)


@bot.chosen_inline_handler(func=lambda chosen_inline_result: True)
def choose_inline_result_handler(chosen_inline_result: ChosenInlineResult) -> None:
    user = _get_or_create_user(chosen_inline_result.from_user.id)
    bet = chosen_inline_result.query
    if not bet.isnumeric() or int(bet) <= 0 or int(bet) > user.get("balance"):
        bot.edit_message_text(inline_message_id=chosen_inline_result.inline_message_id,
                              text=messages.SMTH_WRONG, reply_markup=None)
        return

    db.users.update_one({"telegram_id": user.get("telegram_id")}, {"$inc": {"balance": -1 * int(bet)}})
    game_id = uuid4().hex

    username = chosen_inline_result.from_user.username
    if not username:
        username = ' '.join([chosen_inline_result.from_user.first_name, chosen_inline_result.from_user.last_name])

    db.games.insert_one(
        {"id": game_id, "first_player": user.get("telegram_id"), "first_player_name": username, "second_player": None,
         "state": "pending",
         "bet": int(bet), "created_at": datetime.utcnow(), "turn": user.get("telegram_id")})

    bot.edit_message_reply_markup(inline_message_id=chosen_inline_result.inline_message_id,
                                  reply_markup=InlineKeyboardMarkup([
                                      [
                                          InlineKeyboardButton("Accept", callback_data="accept_" + game_id),
                                          InlineKeyboardButton("Reject", callback_data="reject_" + game_id)
                                      ]
                                  ]))


@bot.message_handler(commands=['start', 'help'])
def handle_start(message: Message) -> None:
    telegram_id = message.from_user.id
    user = _get_or_create_user(telegram_id)

    msg = WELCOME_MESSAGE(user.get('balance')) if user.get("new", False) else WELCOME_BACK_MESSAGE(user.get('balance'))
    bot.send_message(telegram_id, text=msg, reply_markup=InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Refresh", callback_data="show_balance"),
        ]
    ]))


def main() -> None:
    print(f"Started bot: {bot.get_me().username}")
    bot.infinity_polling()


if __name__ == '__main__':
    main()
