import logging

from enum import Enum
from environs import Env
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackContext)
from data import (get_user_status, get_current_speach, create_questionnaire,
                  add_age_to_questionnaire, add_language_to_questionnaire,
                  get_users_by_language)
from functools import partial
import redis


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
    'CHOOSING_SPEAKER',
    'CHOOSING_MEETING_TIME',
    'EDITING_MEETING',
    'EDITING_THEME',
    'EDITING_SCHEDULE',
    'SEND_NOTIFICATION',
])


def start(update: Update, context: CallbackContext, redis_con) -> int:
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

    organizer_keyboard = [
        ['Расписание'],
        ['Добавить докладчика'],
        ['Изменить программу'],
        ['Оповещение всем'],
        ['Донаты'],
    ]

    user = update.message.from_user

    global main_keyboard
    user_role = get_user_status(
        user_id=user.id,
        redis_con=redis_con,
    )

    if user_role == 'speaker':
        main_keyboard = listener_keyboard
    elif user_role == 'organizer':
        main_keyboard = organizer_keyboard
    else:
        main_keyboard = listener_keyboard
    reply_markup = ReplyKeyboardMarkup(main_keyboard)
    update.message.reply_text(
        text='Привет! Я бот для проведения митапов! Используй команду /help '
             'или напиши "Помощь" для знакомства с моим функционалом.',
        # через f строку можно вставить название роли на русском после Привет
        reply_markup=reply_markup,
    )

    return State.CHOOSING


def now(update: Update, context: CallbackContext, redis_con) -> int:
    """Show current meetup."""
    now_keyboard = [['Задать вопрос'], ['Назад'],]
    reply_markup = ReplyKeyboardMarkup(now_keyboard)
    current_speach = get_current_speach(redis_con=redis_con)
    update.message.reply_text(
        text=f'{current_speach["speach_info"]} - {current_speach["speaker"]}',
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


def ask_age(update: Update, context: CallbackContext, redis_con) -> int:
    create_questionnaire(
        user_id=update.message.from_user['id'], 
        user_firstname=update.message.text,
        redis_con=redis_con,
    )
    update.message.reply_text(
        text='Введите возраст',
        reply_markup=ReplyKeyboardMarkup([['Назад']]),
    )

    return State.ASKING_AGE


def ask_language(update: Update, context: CallbackContext, redis_con) -> int:
    add_age_to_questionnaire(
        user_id=update.message.from_user['id'],
        user_age=update.message.text,
        redis_con=redis_con,
    )

    update.message.reply_text(
        text='Введите язык программирования',
        reply_markup=ReplyKeyboardMarkup([['Назад']]),
    )


    return State.ASKING_LANGUAGE


def get_person(update: Update, context: CallbackContext, redis_con) -> int:
    add_language_to_questionnaire(
        user_id=update.message.from_user['id'],
        language=update.message.text,
        redis_con=redis_con,
    )
    users_with_same_language = get_users_by_language(
        language=update.message.text,
        redis_con=redis_con,
    )
    update.message.reply_text(
        text=users_with_same_language,
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


def choose_speaker(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        text='Выберите докладчика',
        reply_markup=ReplyKeyboardMarkup(
            [[f'speaker{i}'] for i in range(5)]
        )
    )

    return State.CHOOSING_SPEAKER


def choose_meeting_time(update: Update, context: CallbackContext) -> int:
    # username = update.message.text
    update.message.reply_text(
        text='Выберите доступное время',
        #  список кнопок со свободным временем
        reply_markup=ReplyKeyboardMarkup(
            [[f'{i}:00'] for i in range(9, 19)]
        ),
    )

    return State.CHOOSING_MEETING_TIME


def save_meeting(update: Update, context: CallbackContext) -> int:
    # meeting_time = update.message.text
    update.message.reply_text(
        text='Докладчик записан',
        reply_markup=ReplyKeyboardMarkup(main_keyboard),
    )

    return State.CHOOSING


def edit_schedule(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        text='Выберите доклад',
        # cписок докладов
        reply_markup=ReplyKeyboardMarkup(
            [[f'{i}:00 - Тема доклада'] for i in range(9, 19)]
        ),
    )

    return State.EDITING_SCHEDULE


def edit_meeting(update: Update, context: CallbackContext) -> int:
    #  перехват времени или названия доклада
    target = update.message.text
    #  сохранить например в bot_data или в redis
    context.bot_data['edit_meeting'] = target

    update.message.reply_text(
        text='Выберите редактировать или удалить докдад из расписания',
        reply_markup=ReplyKeyboardMarkup([
            ['Редактировать'],
            ['Удалить'],
        ]),
    )

    return State.EDITING_MEETING


def edit_theme(update: Update, context: CallbackContext) -> int:
    context.bot.delete_message(
        update.message.chat.id,
        update.message.message_id,
    )
    update.message.reply_text(
        text='Введите новую тему выступления',
        reply_markup=ReplyKeyboardMarkup([['Назад']]),
    )

    return State.EDITING_THEME


def save_theme(update: Update, context: CallbackContext) -> int:
    new_theme = update.message.text
    #  выступление тянем из context.bot_data
    update.message.reply_text(
        text='Тема выступления сохранена',
        reply_markup=ReplyKeyboardMarkup(main_keyboard),
    )

    return State.CHOOSING


def delete_meeting(update: Update, context: CallbackContext) -> int:
    # удаление выступления из расписания
    # выступление тянем из context.bot_data
    update.message.reply_text(
        text='Выступление удалено',
        reply_markup=ReplyKeyboardMarkup(main_keyboard),
    )

    return State.CHOOSING


def get_notification(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        text='Введите текст оповещения',
        reply_markup=ReplyKeyboardMarkup([['Назад']]),
    )

    return State.SEND_NOTIFICATION


def send_notification(update: Update, context: CallbackContext) -> int:
    #  отправка сообщения всем
    update.message.reply_text(
        text='Оповещение отправлено',
        reply_markup=ReplyKeyboardMarkup(main_keyboard),
    )

    return State.CHOOSING


def get_donations(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        text='@username - Сумма руб.',
        reply_markup=ReplyKeyboardMarkup(main_keyboard),
    )

    return State.CHOOSING


def cancel(update: Update, context: CallbackContext) -> int:
    return ConversationHandler.END


def main() -> None:
    """Start the bot."""
    updater = Updater(env.str('TELEGRAM_BOT_TOKEN'))
    r = redis.Redis(
        host=env.str('DB_HOST'),
        port=env.str('DB_PORT'),
        db=env.str('DB_NUMBER'),
    )

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler(
            'start',
            partial(
                start,
                redis_con=r,
            ),
        )],
        states={
            State.CHOOSING: [
                MessageHandler(
                    Filters.regex(r'Текущее выступление'),
                    partial(
                        now,
                        redis_con=r,
                    ),),
                CommandHandler(
                    'now',
                    partial(
                        now, 
                        redis_con=r,
                    ),
                ),
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

                MessageHandler(
                    Filters.regex(r'Добавить докладчика'),
                    choose_speaker,
                ),

                MessageHandler(
                    Filters.regex(r'Изменить программу'),
                    edit_schedule,
                ),

                MessageHandler(
                    Filters.regex(r'Оповещение всем'),
                    get_notification,
                ),

                MessageHandler(Filters.regex(r'Донаты'), get_donations),
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
                MessageHandler(
                    Filters.text,
                    partial(
                        ask_age,
                        redis_con=r,
                    ))
            ],
            State.ASKING_AGE: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(
                    Filters.text,
                    partial(
                        ask_language,
                        redis_con=r,
                    ))
            ],
            State.ASKING_LANGUAGE: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(
                    Filters.text,
                    partial(
                        get_person,
                        redis_con=r,
                    ))
            ],
            State.CHOOSING_PERSON: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(Filters.regex(r'Выбрать'), get_contact),
                MessageHandler(Filters.regex(r'Следующий'), get_person),
            ],
            State.CHOOSING_SPEAKER: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(Filters.text, choose_meeting_time)
            ],
            State.CHOOSING_MEETING_TIME: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(Filters.text, save_meeting)
            ],
            State.EDITING_SCHEDULE: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(Filters.text, edit_meeting)
            ],
            State.EDITING_MEETING: [
                MessageHandler(Filters.regex(r'Редактировать'), edit_theme),
                MessageHandler(Filters.regex(r'Удалить'), delete_meeting),
            ],
            State.EDITING_THEME: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(Filters.text, save_theme)
            ],
            State.SEND_NOTIFICATION: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(Filters.text, send_notification)
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
