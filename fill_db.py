import redis
import os
from dotenv import load_dotenv


"""Внутри скрипта создадим 20 пользователей, 10 из которых спикеры, у 5 будет назначено выступление."""




def create_users(redis_con, amount_of_users=20):
    for user in range(amount_of_users):
        user_id = user
        user_firstname = f'first_name of {user_id}'
        user_age = 20 + user_id
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
        redis_con.hset(
            f'{user_id}_questionnaire',
            'age',
            user_age,
        )
        redis_con.hset(
            f'{user_id}_questionnaire',
            'language',
            'python',
        )
        redis_con.sadd(
            'python',
            user_id,
        )


def create_speakers(redis_con, amount_of_speakers=10):
    awailable_time = [
        '10:00:00',
        '11:00:00',
        '15:00:00',
        '16:00:00',
        '18:00:00',
    ]
    for user_id in range(amount_of_speakers):
        redis_con.sadd(
            'speakers',
            user_id,
        )
    for user_id, time in enumerate(awailable_time):
        speach_info = f'выступление пользователя  про python c id -'
        if user_id == 0:
            redis_con.set(
                'current_speach',
                time,
            )
        redis_con.sadd(
            'scheduled_speakers',
            user_id,
        )
        redis_con.hset(
            'speach_time',
            time,
            user_id,
        )
        redis_con.set(
            f'{time}_info',
            f'{user_id}: {speach_info}',
        )




def main():
    load_dotenv()
    tg_bot_token = os.getenv('TG_BOT_TOKEN')
    r = redis.Redis(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        db=os.getenv('DB_NUMBER'),
    )
    create_users(redis_con=r)
    create_speakers(redis_con=r)

if __name__ == '__main__':
    main()
    
    