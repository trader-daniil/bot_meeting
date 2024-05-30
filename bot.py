import logging

from enum import Enum
from environs import Env
from telegram import ReplyKeyboardMarkup, Update, LabeledPrice
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          PreCheckoutQueryHandler, TypeHandler,
                          ConversationHandler, CallbackContext)
from data import (get_user_status, get_current_speach, create_questionnaire,
                  add_age_to_questionnaire, add_language_to_questionnaire,
                  get_users_by_language, get_schedule_db, create_question,
                  add_user_to_language, get_speaker_questions, get_speakers_without_speach,
                  get_allowed_time, add_new_speaker, get_new_speaker)
from functools import partial
import redis
import random


env = Env()
env.read_env()

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
    'GETTING_DONATE',
    'SENDING_INVOICE',
    'GOT_PAYMENT',
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
    print(user.id)

    if user_role == 'speaker':
        main_keyboard = speaker_keyboard
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


def save_question(update: Update, context: CallbackContext, redis_con) -> int:
    """Добавить возможность"""
    create_question(
        user_id=update.message.from_user,
        question=update.message.text,
        redis_con=redis_con,
    )
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
    user_id = update.message.from_user['id']
    add_language_to_questionnaire(
        user_id=user_id,
        language=update.message.text,
        redis_con=redis_con,
    )
    add_user_to_language(
        user_id=user_id,
        language=update.message.text,
        redis_con=redis_con,
    )
    users_with_same_language = get_users_by_language(
        language=update.message.text,
        redis_con=redis_con,
    )
    update.message.reply_text(
        text=random.choice(users_with_same_language),
        reply_markup=ReplyKeyboardMarkup(
            [['Выбрать'], ['Следующий'], ['Назад']]
        ),
    )

    return State.CHOOSING_PERSON


def get_contact(update: Update, context: CallbackContext, redis_con) -> int:
    context.bot.delete_message(
        update.message.chat.id,
        update.message.message_id,
    )
    users_with_same_language = get_users_by_language(
        language=update.message.text,
        redis_con=redis_con,
    )
    update.message.reply_text(
        text=users_with_same_language[random.randint(0, len(users_with_same_language) - 1)],
        reply_markup=ReplyKeyboardMarkup(main_keyboard),
    )
    return State.CHOOSING


def get_schedule(update: Update, context: CallbackContext, redis_con) -> int:
    context.bot.delete_message(
        update.message.chat.id,
        update.message.message_id,
    )
    result = ''
    schedule = get_schedule_db(redis_con=redis_con)
    print(schedule, 'in function')
    for time, theme in schedule.items():
        result += f'время начала - {time}, тема выступления - {theme}\n'

    update.message.reply_text(
        text=result,
        reply_markup=ReplyKeyboardMarkup(main_keyboard),
    )

    return State.CHOOSING


def about_meetings(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        text=('Для начала заполните анкету, после этого мы дадаим '
              'вам логины пользователей со схожими языками программирования'),
        reply_markup=ReplyKeyboardMarkup([['Заполнить анкету'], ['Назад']],)
    )

    return State.STARTING_FORM


def get_questions(update: Update, context: CallbackContext, redi_con) -> int:
    context.bot.delete_message(
        update.message.chat.id,
        update.message.message_id,
    )
    questions = get_speaker_questions(redis_con=redi_con)
    update.message.reply_text(
        text=questions,
        reply_markup=ReplyKeyboardMarkup(main_keyboard),
    )

    return State.CHOOSING


def donate(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        text='Введите сумму доната',
        reply_markup=ReplyKeyboardMarkup([['Назад']]),
    )

    ConversationHandler.END


def send_invoice(update: Update, context: CallbackContext) -> int:
    price = int(update.message.text)

    context.bot.send_invoice(
        chat_id=update.message.chat_id,
        title='Донат',
        description='Донат организатору',
        payload='invoice_payload_test',
        provider_token=env.str('PAYMENT_TG_TOKEN'),
        currency='rub',
        prices=[LabeledPrice(label='Донат', amount=price * 100)],
    )

    return State.SENDING_INVOICE


def checkout(update, context):
    query = update.pre_checkout_query
    if query.invoice_payload != "Custom-Payload":
        query.answer(ok=False, error_message="Something went wrong...")
    else:
        query.answer(ok=True)

    return State.GOT_PAYMENT


def got_payment(update, context):
    update.message.reply_text('Успешная оплата')


def choose_speaker(update: Update, context: CallbackContext, redis_con) -> int:
    allowed_speakers = get_speakers_without_speach(
        redis_con=redis_con,
    )
    update.message.reply_text(
        text='Выберите спикера',
        reply_markup=ReplyKeyboardMarkup(
            [[speaker] for speaker in allowed_speakers]
        )
    )
    return State.CHOOSING_SPEAKER


def choose_meeting_time(update: Update, context: CallbackContext, redis_con) -> int:
    allowed_time = get_allowed_time(redis_con=redis_con)
    add_new_speaker(
        redis_con=redis_con,
        speaker_id=update.message.text
    )
    update.message.reply_text(
        text='Выберите доступное время',
        #  список кнопок со свободным временем
        reply_markup=ReplyKeyboardMarkup(
            [[time] for time in allowed_time]
        ),
    )

    return State.CHOOSING_MEETING_TIME


def save_meeting(update: Update, context: CallbackContext, redis_con) -> int:
    meeting_time = update.message.text
    speaker_id = get_new_speaker(redis_con=redis_con).encode('utf-8')
    
    print(meeting_time, '-------------')
    print(speaker_id, '---------------')
    redis_con.sadd(
        'scheduled_speakers',
        speaker_id,
    )
    redis_con.hset(
        'speach_time',
        meeting_time,
        speaker_id,
    )
    redis_con.set(
        f'{meeting_time}_info',
        f'{speaker_id}: новое выступление',
    )
    update.message.reply_text(
        text='Докладчик записан',
        reply_markup=ReplyKeyboardMarkup(main_keyboard),
    )

    return State.CHOOSING


def edit_schedule(update: Update, context: CallbackContext) -> int:
    allowed_time = get_allowed_time(redis_con=redis_con)
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
    updater = Updater(env.str('TG_BOT_TOKEN'))
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

                MessageHandler(
                    Filters.regex(r'Расписание'),
                    partial(
                        get_schedule,
                        redis_con=r,
                    )),
                CommandHandler(
                    'schedule',
                    partial(
                        get_schedule,
                        redit_con=r,
                    )),

                MessageHandler(Filters.regex(r'Задонатить'), donate),
                CommandHandler('donate', donate),
                MessageHandler(
                    Filters.regex(r'Список вопросов'),
                    partial(
                        get_questions,
                        redis_con=r,
                    )
                ),
                CommandHandler(
                    'questions',
                    partial(
                        get_questions,
                        redis_con=r,
                )),
                MessageHandler(
                    Filters.regex(r'Добавить докладчика'),
                    partial(
                        choose_speaker,
                        redis_con=r
                    )
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
                MessageHandler(
                    Filters.text,
                    partial(
                        save_question,
                        redis_con=r,
                    )),
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
                MessageHandler(
                    Filters.regex(r'Выбрать'),
                    partial(
                        get_contact,
                        redis_con=r,
                )),
                MessageHandler(
                    Filters.regex(r'Следующий'),
                    partial(
                        get_person,
                        redis_con=r,
                )),
            ],
            State.CHOOSING_SPEAKER: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(
                    Filters.text,
                    partial(
                        choose_meeting_time,
                        redis_con=r,
                    ))
            ],
            State.CHOOSING_MEETING_TIME: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(
                    Filters.text,
                    partial(
                        save_meeting,
                        redis_con=r,
                    ))
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
            State.GETTING_DONATE: [
                MessageHandler(Filters.regex(r'Назад'), show_main_keyboard),
                MessageHandler(Filters.text, send_invoice)
            ],
            State.SENDING_INVOICE: [
                PreCheckoutQueryHandler(checkout),
            ],
            State.GOT_PAYMENT: [
                MessageHandler(Filters.successful_payment, got_payment),
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

    main()
