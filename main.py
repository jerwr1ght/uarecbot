# -*- coding: utf8 -*-
import telebot
import random
from telebot import types
import config as ct
from threading import Thread
import psycopg2
import os
from configparser import ConfigParser
from time import sleep
global db
global sql
db = psycopg2.connect(database='dbir1kfgtc2gr', user='wgqusjxghdknsd', port="5432", password='9e0dfc871e76a775b7df2f9b8f732994ec3d0aed806485f11b5366893e8027a7', host='ec2-23-20-208-173.compute-1.amazonaws.com', sslmode='require')
sql=db.cursor()
sql.execute("""CREATE TABLE IF NOT EXISTS clangs (chatid TEXT, language TEXT)""")
db.commit()
sql.execute("""CREATE TABLE IF NOT EXISTS versions (num TEXT)""")
db.commit()

bot=telebot.TeleBot(ct.TOKEN)

global config
file = 'loc.ini'
config = ConfigParser()
config.read(file, encoding="utf-8")

def sending_updates():
    sql.execute(f"SELECT * FROM clangs")
    rows = sql.fetchall()
    c = 0
    prefix = '&#8226;'
    #bot.send_message(703934578, msg, parse_mode='html')
    for row in rows:
        chat_id, loc_lang = row[0], row[1]
        upd_items = [f"{prefix} {row.lower()}\n" for row in config[f"{loc_lang}"]["upd"].split(prefix)]
        msg = f'<b>New {config[f"{loc_lang}"]["cv"].lower()} {ct.VERSION}</b>\n\n<b>{config[f"{loc_lang}"]["upd_word"]}</b>:\n'
        for item in upd_items:
            msg += f'{item}'
        try:
            bot.send_message(chat_id, msg, parse_mode='html')
            c += 1
        except Exception as ex:
            print(ex)
        finally:
            sleep(1)
    print(f'Message about new version was sent to {c}/{len(rows)} chats')
    bot.send_message(703934578, f'Message about new version was sent to <b>{c}/{len(rows)}</b> chats', parse_mode='html')

sql.execute(f"SELECT * FROM versions")
res = sql.fetchone()
if res is None:
    sql.execute(f"INSERT INTO versions VALUES ('{ct.VERSION}')")
    db.commit()
    sending_updates()
else: 
    if res[0] != ct.VERSION:
        sql.execute(f"UPDATE versions SET num = '{ct.VERSION}'")
        db.commit()
        sending_updates()
 



def get_user(user):
    mention = user.first_name
    #mention = f'<a href="tg://user?id={user.id}">{user.first_name}'
    if user.last_name != None:
        mention = f'{mention} {user.last_name}'
    return mention

def mention_user(user):
    mention = f'<a href="tg://user?id={user.id}">{user.first_name}'
    if user.last_name != None:
        mention = f'{mention} {user.last_name}'
    mention=mention+'</a>'
    return mention

def set_commands(message, loc_lang):
    commands = [types.BotCommand(command='clang', description=config[f"{loc_lang}"]["clang"])]
    bot.set_my_commands(commands=commands, scope=types.BotCommandScopeChat(chat_id=message.chat.id))

def working_with_sql(message):
    sql.execute(f"SELECT language FROM clangs WHERE chatid = '{message.chat.id}'")
    res = sql.fetchone()

    if res is None:
        sql.execute("INSERT INTO clangs VALUES (%s, %s)", (message.chat.id, 'en-US'))
        db.commit()
        msg = ''
        for row in config.sections():
            msg += f'<b>{config[f"{row}"]["true_name"]}</b>: {config[f"{row}"]["first_1"]} @{bot.get_me().username}{config[f"{row}"]["first_2"]} /clang{config[f"{row}"]["first_3"]}\n\n'
        msg += f'<b>Version</b>: {ct.VERSION}'
        bot.send_message(message.chat.id, msg, parse_mode='html')
        return 'en-US'
    else:
        return res[0]

def editing_lang(message, loc_lang):
    sql.execute(f"UPDATE clangs SET language = '{loc_lang}' WHERE chatid = '{message.chat.id}'")
    db.commit()

def is_user_admin(message, user, loc_lang):
    if message.chat.type != 'private' and bot.get_chat_member(message.chat.id, user.id).status.lower() not in ['administrator', 'owner', 'creator']:
        bot.send_message(message.chat.id, f'⚠️ {mention_user(user)}, {config[f"{loc_lang}"]["noadmin"][0].lower()}{config[f"{loc_lang}"]["noadmin"][1:]}', parse_mode='html')
        return False
    else:
        return True

def is_bot_admin(message):
    if message.chat.type != 'private' and bot.get_chat_member(message.chat.id, bot.get_me().id).status.lower() not in ['administrator', 'owner', 'creator']:
        loc_lang = working_with_sql(message)
        return False, loc_lang
    else:
        loc_lang = working_with_sql(message)
        return True, loc_lang

def recoginze_your_language(file_name, lang, loc_lang):
    #Подключаем Speech Recognition
    import speech_recognition as sr
    engine = sr.Recognizer()

    with sr.AudioFile(file_name) as source:
        print(f'Log: file {file_name} is being recorded')
        audio = engine.record(source)

    try:
        print(f'Log: file {file_name} is being analized')
        text = engine.recognize_google(audio, language=lang)
    except Exception as ex:
        text = f'{config[f"{loc_lang}"]["r_error"]} 😣'
        print({ex})

    print(f'Log: file {file_name} is recognized with {lang} language')
    return text

@bot.message_handler(content_types=['new_chat_members'])
def checking_members(message):
    for member in message.new_chat_members:
        if member.username == bot.get_me().username:
            is_admin, loc_lang = is_bot_admin(message)
            set_commands(message, loc_lang)

@bot.message_handler(content_types=['left_chat_member'])
def bot_removed(message):
    if message.left_chat_member.username == bot.get_me().username:
        sql.execute(f"DELETE FROM clangs WHERE chatid = '{message.chat.id}'")
        db.commit()

@bot.message_handler(content_types=['voice', 'video_note'])
def voice_processing(message):
    loc_lang = working_with_sql(message)
    set_commands(message, loc_lang)
    #Сохраняем файл wav
    if message.video_note != None:
        file_info = bot.get_file(message.video_note.file_id)
        pr = 'mp4'
    else:
        file_info = bot.get_file(message.voice.file_id)
        pr = 'ogg'

    downloaded_file = bot.download_file(file_info.file_path)
    rn = random.randint(1, 99999)
    file_name = f'{rn}_{message.chat.id}.{pr}'
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)
    #Конвертация в wav
    from pydub import AudioSegment
    wav_audio = AudioSegment.from_file(file_name, file_name.split('.')[1])
    wav_audio.export(file_name.replace(file_name.split('.')[1], 'wav'), format = "wav")
    os.remove(file_name)
    file_name = file_name.replace(file_name.split('.')[1], 'wav')

    msg = bot.send_message(message.chat.id, f'{config[f"{loc_lang}"]["trying"]}...', parse_mode='html')
    text = ''
    for row in config.sections():
        text += f'<b>{config[f"{row}"]["true_name"]}</b> - {recoginze_your_language(file_name, row, loc_lang)}\n'

    os.remove(file_name)
    print(f'Log: file {file_name} is deleted')
    
    if message.forward_from !=None: 
        user = get_user(message.forward_from)
    else:
        user = get_user(message.from_user)
    bot.edit_message_text(chat_id = msg.chat.id, message_id = msg.message_id, text = f'{config[f"{loc_lang}"]["from"]} <b>{user}</b>:\n\n{text[0].upper()}{text[1:]}\n<code>P.S. {config[f"{loc_lang}"]["bv"]} 🧑‍💻</code>', parse_mode='html')
    #bot.send_message(message.chat.id, f'{config[f"{loc_lang}"]["from"]} <b>{user}</b>:\n{text[0].upper()}{text[1:]}\n\n<code>P.S. {config[f"{loc_lang}"]["bv"]} 🧑‍💻</code>', parse_mode='html')

@bot.message_handler(commands=['clang', 'cl'])
def changing_language(message):
    loc_lang = working_with_sql(message)
    set_commands(message, loc_lang)
    if is_user_admin(message, message.from_user, loc_lang)==False:
        return
    lang_reply = types.InlineKeyboardMarkup()
    for row in config.sections():
        if row == loc_lang:
            continue
        lang_reply.add(types.InlineKeyboardButton(f'{config[f"{row}"]["true_name"]}', callback_data=row))
    bot.send_message(message.chat.id, f'<b>{config[f"{loc_lang}"]["tn_r"]}</b> {config[f"{loc_lang}"]["lnow"]}', parse_mode='html', reply_markup=lang_reply)
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        msg = call.message
        loc_lang = call.data
        if is_user_admin(msg, call.from_user, loc_lang)==False:
            return
        editing_lang(msg, loc_lang)
        bot.edit_message_text(chat_id = msg.chat.id, message_id = msg.message_id, text=f'✅ <b>{config[f"{loc_lang}"]["tn_r"]}</b> {config[f"{loc_lang}"]["lset"]}', parse_mode='html', reply_markup=None)
        set_commands(msg, loc_lang)
#working_with_sql(message)

bot.polling(none_stop=True)