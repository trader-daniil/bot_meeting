import redis
import os
from dotenv import load_dotenv
import datetime


def get_user_status(user_id, redis_con):
    """Определяем статус учатника по его id Tg
        Используем структуру данных SET."""
    speakers_ids = redis_con.smembers('speakers')
    orginizers_ids = redis_con.smembers('organizers')
    user_id = str.encode(str(user_id))
    if user_id in speakers_ids:
        return 'speaker'
    elif user_id in orginizers_ids:
        return 'organizer'
    return 'listener'

def get_users_by_language(language, redis_con):
    """Получим всех пользователей, которые используют выбранных язык
        Используем тип данных SET."""
    users = []
    users_ids = redis_con.smembers(language.lower())
    for user_id in users_ids:
        users.append(user_id.decode('utf-8'))
    return users


def add_user_to_language(user_id, language, redis_con):
    """Добавим пользователя в список программистов с указанным ЯП
        Используем тип данных SET."""
    users_ids = get_users_by_language(
        language=language,
        redis_con=redis_con,
    )
    if str.encode(user_id) in users_ids:
        return 'Вы уже состоите в списке'
    redis_con.sadd(language.lower(), user_id) 


def add_speaker(speaker_name, speach_time, speach_info, redis_con):
    """Добавляем пользователя по его ID в TG как списка
        Используем тип данных HASH ключ - время в формате HH:MM:SS значение - id спикера"""
    redis_con.hset(
        'speach_time',
        speach_time,
        speaker_name,
    )
    redis_con.set(
        f'{speach_time}_info',
        f'{speaker_name}: {speach_info}',
    )


def get_speaker_questions(speaker_name, redis_con):
    """Получим все контакты тех, кто хочет задать вопрос докладчику
        Используем тип данных SET."""
    contacts = redis_con.smembers(f'{speaker_name}_contacts')
    return contacts


def get_speach_data(redis_con, speach_time):
    """Получим подробную информацию о выступлении
        Используем тип key value, где key время начала выступления
        и value это подробная информация о выступлении."""
    speach_info = redis_con.get(f'{speach_time}_info')
    return speach_info.decode('utf-8')


def get_current_speach(redis_con):
    """Получим текущее выступление
        Используем тип данных key-value, где value это время начала выступления
        Затем обращаемся к этому времени и получаем подробную информацию о выступлении."""
    speach_start_time = redis_con.get('current_speach')
    current_speach = redis_con.hget(
        'speach_time',
        speach_start_time,
    )
    info = get_speach_data(
        redis_con=redis_con,
        speach_time=speach_start_time.decode('utf-8'),
    )
    speach_info = {
        'speaker': current_speach.decode('utf-8'),
        'speach_info': info
    }
    return speach_info



def create_question(user_id, question, redis_con):
    """Получим текущее выступление и зададим вопрос спикеру
        Используем тип данных SET, ключ это <username спикера>_questions
        и значение это перечисление вопросов."""
    current_speaker = get_current_speach(redis_con=redis_con)['speaker']
    redis_con.sadd(
        f'{current_speaker}_questions',
        f'{user_id}: {question}',
    )


def get_speaker_questions(speaker_id, redis_con):
    """Получим текущие вопросы к спикеру, вернем в формате
        id задающего в ТГ: текст вопроса."""
    questions = {}
    contacts = redis_con.smembers(f'{speaker_id}_questions')
    for question in contacts:
        username, question = question.decode('utf-8').split(': ')
        questions[username] = question
    return questions


def create_questionnaire(user_id, redis_con, user_firstname):
    """Создадим анкеты пользовтеля
        Испольщуем тип данных HASH."""
    redis_con.hset(
        f'{user_id}_questionnaire',
        'tg_id',
        user_id,
    )
    redis_con.hset(
        f'{user_id}_questionnaire',
        'user_firstname',
        user_firstname,
    )


def add_age_to_questionnaire(user_id, user_age, redis_con):
    redis_con.hset(
        f'{user_id}_questionnaire',
        'age',
        user_age,
    )


def add_language_to_questionnaire(user_id, language, redis_con):
    redis_con.hset(
        f'{user_id}_questionnaire',
        'language',
        language,
    )


def get_user_questionnaire(user_id, redis_con):
    """Получим анкету пользователя."""
    if not redis_con.exists(f'{user_id}_questionnaire'):
        return None
    return {
        'tg_id': user_id,
        'user_info': redis_con.hget(
            f'{user_id}_questionnaire',
            'info',
        ).decode('utf-8')
    }


def get_schedule_db(redis_con):
    """Получим время начала текущего доклада, затем следующие доклады."""
    current_speach_time = redis_con.get('current_speach').decode('utf-8')
    next_speach = {}
    current_speach_time = datetime.datetime.strptime(
        current_speach_time,
        '%H:%M:%S'
    ).time()
    schedule = redis_con.hgetall('speach_time')
    for speach_time, speaker in schedule.items():
        speach_time_formated = datetime.datetime.strptime(
            speach_time.decode('utf-8'),
            '%H:%M:%S'
        ).time()
        if speach_time_formated> current_speach_time:
            next_speach[speach_time.decode('utf-8')] = speaker.decode('utf-8')
    
    return next_speach


def remove_speaker(time_to_delete, redis_con):
    redis_con.hdel(
        'speach_time',
        time_to_delete,
    )


def main():
    load_dotenv()
    tg_bot_token = os.getenv('TG_BOT_TOKEN')
    r = redis.Redis(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        db=os.getenv('DB_NUMBER'),
    )

    
    print(
        get_users_by_language(
            language='Python',
            redis_con=r,
        )
    )

    
if __name__ == '__main__':
    main()