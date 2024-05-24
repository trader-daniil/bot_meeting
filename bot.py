import logging

from enum import Enum
from environs import Env
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackContext)


logger = logging.getLogger(__name__)

State = Enum('State', [
    'CHOOSING',
    'ASKING_QUESTION',
    'SAVING_QUESTION',
    'STARTING_FORM',
    'ASKING_NAME',
    'ASKING_AGE',
    'ASKING_LANGUAGE',
    'CHOOSING_PERSON',
])


def start(update: Update, context: CallbackContext) -> int:
    """Send a message when the command /start is issued."""

    # через update.message.from_user.id получаем роль пользователя
    # в зависимости от этого разные приветственные сообщения и наборы кнопок

    listener_keyboard = [
        ['Текущее выступление'],
        ['Расписание'],
        ['Пообщаться'],
        ['Помощь'],
        ['Задонатить']
    ]

    speaker_keyboard = listener_keyboard + [['Список вопросов']]

    # organizer_keyboard = [
    #     ['Расписание'],
    #     ['Добавить докладчика'],
    #     ['Изменить программу'],
    #     ['Оповещение всем'],
    #     ['Донаты'],
    # ]

    global main_keyboard

    # if user.role == 'speaker':
    #     main_keyboard = listener_keyboard
    # elif user.role == 'organizer':
    #     main_keyboard = organizer_keyboard
    # else:
    #     main_keyboard = listener_keyboard

    main_keyboard = speaker_keyboard  # delete

    reply_markup = ReplyKeyboardMarkup(main_keyboard)
    update.message.reply_text(
        text='Привет! Я бот для проведения митапов! Используй команду /help '
             'или напиши "Помощь" для знакомства с моим функционалом.',
        # через f строку можно вставить название роли на русском после Привет
        reply_markup=reply_markup,
    )

    return State.CHOOSING


def now(update: Update, context: CallbackContext) -> int:
    """Show current meetup."""
    now_keyboard = [['Задать вопрос'], ['Назад'],]
    reply_markup = ReplyKeyboardMarkup(now_keyboard)
    update.message.reply_text(
        text='Название доклада - Имя докладчика',
        reply_markup=reply_markup,
    )

    return State.ASKING_QUESTION


def ask_question(update: Update, context: CallbackContext) -> int:
    context.bot.delete_message(
        update.message.chat.id,
        update.message.message_id,
    )
    update.message.reply_text(
        text='Введите вопрос',
        reply_markup=ReplyKeyboardMarkup([['Назад']]),
    )

    return State.SAVING_QUESTION


def save_question(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        text='Ваш вопрос записан',
        reply_markup=ReplyKeyboardMarkup(main_keyboard),
    )

    return State.CHOOSING


def show_main_keyboard(update: Update, context: CallbackContext) -> int:
    context.bot.delete_message(
        update.message.chat.id,
        update.message.message_id,
    )
    update.message.reply_text(
        text='Выберите из списка действий',
        reply_markup=ReplyKeyboardMarkup(main_keyboard),
    )

    return State.CHOOSING


def get_help(update: Update, context: CallbackContext) -> int:
    context.bot.delete_message(
        update.message.chat.id,
        update.message.message_id,
    )
    update.message.reply_text(
        text='/now - текущее выступление, задать вопрос\n'
             '/schedule - расписание\n'
             '/meet - пообщаться\n'
             '/help - основные команды\n'
             '/donate - сделать донат\n',
        reply_markup=ReplyKeyboardMarkup(main_keyboard),
    )

    return State.CHOOSING


def ask_meeting(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        text='Для продолжения необходимо заполнить анкету',
        reply_markup=ReplyKeyboardMarkup(
            [['Заполнить анкету'], ['Как это работает'], ['Назад']]
        ),
    )

    return State.STARTING_FORM


def ask_name(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        text='Введите имя',
        reply_markup=ReplyKeyboardMarkup([['Назад']]),
    )

    return State.ASKING_NAME


def ask_age(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        text='Введите возраст',
        reply_markup=ReplyKeyboardMarkup([['Назад']]),
    )

    return State.ASKING_AGE


def ask_language(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        text='Введите язык программирования',
        reply_markup=ReplyKeyboardMarkup([['Назад']]),
    )

    return State.ASKING_LANGUAGE


def get_person(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        text='Имя и разные данные из анкеты другого пользователя, '
             'либо сообщение что никто не найден',
        reply_markup=ReplyKeyboardMarkup(
            [['Выбрать'], ['Следующий'], ['Назад']]
        ),
    )

    return State.CHOOSING_PERSON


def get_contact(update: Update, context: CallbackContext) -> int:
    context.bot.delete_message(
        update.message.chat.id,
        update.message.message_id,
    )
    update.message.reply_text(
        text='@ник_пользователя',
        reply_markup=ReplyKeyboardMarkup(main_keyboard),
    )

    return State.CHOOSING


def get_schedule(update: Update, context: CallbackContext) -> int:
    context.bot.delete_message(
        update.message.chat.id,
        update.message.message_id,
    )
    update.message.reply_text(
        text='Тут расписание',
        reply_markup=ReplyKeyboardMarkup(main_keyboard),
    )

    return State.CHOOSING


def about_meetings(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        text='О том как знакомиться',
        reply_markup=ReplyKeyboardMarkup([['Заполнить анкету'], ['Назад']],)
    )

    return State.STARTING_FORM


def get_questions(update: Update, context: CallbackContext) -> int:
    context.bot.delete_message(
        update.message.chat.id,
        update.message.message_id,
    )
    update.message.reply_text(
        text='Тут список контактов или вопросов',
        reply_markup=ReplyKeyboardMarkup(main_keyboard),
    )

    return State.CHOOSING


def donate(update: Update, context: CallbackContext) -> int:
    pass

    return State.CHOOSING


def cancel(update: Update, context: CallbackContext) -> int:
    return ConversationHandler.END


def main() -> None:
    """Start the bot."""
    updater = Updater(env.str('TELEGRAM_BOT_TOKEN'))

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            State.CHOOSING: [
                MessageHandler(Filters.regex(r'Текущее выступление'), now),
                CommandHandler('now', now),

                MessageHandler(Filters.regex(r'Помощь'), get_help),
                CommandHandler('help', get_help),

                MessageHandler(Filters.regex(r'Пообщаться'), ask_meeting),
                CommandHandler('meet', ask_meeting),

                MessageHandler(Filters.regex(r'Расписание'), get_schedule),
                CommandHandler('schedule', get_schedule),

                MessageHandler(Filters.regex(r'Задонатить'), donate),
                CommandHandler('donate', donate),

                MessageHandler(
                    Filters.regex(r'Список вопросов'),
                    get_questions,
                ),
                CommandHandler('questions', get_questions),
            ],
            State.ASKING_QUESTION: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(Filters.regex(r'Задать вопрос'), ask_question)
            ],
            State.SAVING_QUESTION: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(Filters.text, save_question)
            ],
            State.STARTING_FORM: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(Filters.regex(r'Заполнить анкету'), ask_name),
                MessageHandler(
                    Filters.regex(r'Как это работает'), about_meetings
                ),
            ],
            State.ASKING_NAME: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(Filters.text, ask_age)
            ],
            State.ASKING_AGE: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(Filters.text, ask_language)
            ],
            State.ASKING_LANGUAGE: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(Filters.text, get_person)
            ],
            State.CHOOSING_PERSON: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(Filters.regex(r'Выбрать'), get_contact),
                MessageHandler(Filters.regex(r'Следующий'), get_person),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    logger.info('Bot started.')
    updater.idle()


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )

    env = Env()
    env.read_env()

    main()
