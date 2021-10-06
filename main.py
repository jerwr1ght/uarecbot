# -*- coding: utf8 -*-
import telebot
import random
from telebot import types
import config as ct
from threading import Thread
import psycopg2
import os
from configparser import ConfigParser
import time
from time import sleep
global db
global sql
db = psycopg2.connect(database='dbir1kfgtc2gr', user='wgqusjxghdknsd', port="5432", password='9e0dfc871e76a775b7df2f9b8f732994ec3d0aed806485f11b5366893e8027a7', host='ec2-23-20-208-173.compute-1.amazonaws.com', sslmode='require')
sql=db.cursor()
sql.execute("""CREATE TABLE IF NOT EXISTS clangs (chatid TEXT, language TEXT)""")
db.commit()
sql.execute("""CREATE TABLE IF NOT EXISTS versions (num TEXT)""")
db.commit()
sql.execute("""CREATE TABLE IF NOT EXISTS fstats (chatid TEXT, voice INT, video_note INT, video INT, audio INT)""")
db.commit()
#sql.execute("DELETE FROM clangs WHERE chatid = '703934578'")

bot=telebot.TeleBot(ct.TOKEN)

global config
file = 'loc.ini'
config = ConfigParser()
config.read(file, encoding="utf-8")

global flags
flags = {'en-US': '🇺🇸', 'uk-UA': '🇺🇦', 'ru-RU': '🇷🇺'}

#Устанавливаем команды
def set_commands(chat_id, loc_lang):
    commands = [types.BotCommand(command='start', description=config[f"{loc_lang}"]["start"]),
    types.BotCommand(command='clang', description=config[f"{loc_lang}"]["clang"]),
    types.BotCommand(command='stats', description=config[f"{loc_lang}"]["stats"]),
    types.BotCommand(command='gstats', description=config[f"{loc_lang}"]["gstats"]),
    types.BotCommand(command='invite', description=config[f"{loc_lang}"]["invite"]),
    types.BotCommand(command='tts', description=config[f"{loc_lang}"]["tts"]),
    types.BotCommand(command='extract', description=config[f"{loc_lang}"]["extract"])]
    bot.set_my_commands(commands=commands, scope=types.BotCommandScopeChat(chat_id=chat_id))

#Отправляем информацию об обнове
def sending_updates():
    sql.execute(f"SELECT * FROM clangs")
    rows = sql.fetchall()
    c = 0
    prefix = '&#8226;'
    #bot.send_message(703934578, msg, parse_mode='html')
    for row in rows:
        chat_id, loc_lang = row[0], row[1]
        upd_items = [f"{prefix} {row.lower()}\n" for row in config[f"{loc_lang}"]["upd"].split(prefix)]
        msg = f'<b>{config[f"{loc_lang}"]["new"]} {config[f"{loc_lang}"]["cv"].lower()} {ct.VERSION}</b>\n\n<b>{config[f"{loc_lang}"]["upd_word"]}:</b>\n'
        for item in upd_items:
            msg += f'{item}'
        if 'https' not in ct.UPD_LINK.lower():
            link_reply = None
        else:
            link_reply = types.InlineKeyboardMarkup()
            link_reply.add(types.InlineKeyboardButton(f'🌐 {config[f"{loc_lang}"]["upd_link"]}', url = ct.UPD_LINK))

        try:
            bot.send_message(chat_id, msg, parse_mode='html', reply_markup=link_reply)
            c += 1
            set_commands(chat_id, loc_lang)
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


#Имена пользователей и отметки
def get_user(message):
    if message.forward_from !=None: 
        user = message.forward_from
    else:
        user = message.from_user

    mention = user.first_name
    #mention = f'<a href="tg://user?id={user.id}">{user.first_name}'
    if user.last_name != None:
        mention = f'{mention} {user.last_name}'
    if len(user.first_name) == 0 and len(user.last_name) == 0:
        return 'Unknown user'
    return mention

def mention_user(user):
    mention = f'<a href="tg://user?id={user.id}">{user.first_name}'
    if len(user.first_name) == 0 and len(user.last_name) == 0:
        mention=mention+'Unknown user'
    elif user.last_name != None:
        mention = f'{mention} {user.last_name}'
    mention=mention+'</a>'
    return mention

def command_duration(loc_lang, start_time):
    return f'<b>{round(time.time() - start_time, 2)}{config[f"{loc_lang}"]["seconds"]}</b>'

#Чекаем язык
def working_with_sql(message):
    sleep(1)
    #Удаляем лишние
    sql.execute(f"SELECT language FROM clangs WHERE chatid = '{message.chat.id}'")
    rows = sql.fetchall()
    if len(rows)>1:
        sql.execute(f"DELETE FROM clangs WHERE chatid = '{message.chat.id}' AND language = 'en-US'")
        db.commit()

    sleep(1)
    sql.execute(f"SELECT language FROM clangs WHERE chatid = '{message.chat.id}'")
    res = sql.fetchone()

    if res == None:
        sql.execute("INSERT INTO clangs VALUES (%s, %s)", (message.chat.id, 'en-US'))
        db.commit()
        msg = ''
        all_add_reply = types.InlineKeyboardMarkup()
        all_add_reply_text = ''
        for row in config.sections():
            all_add_reply_text += config[f"{row}"]["add"].split()[0] + ' / '
            msg += f'<b>{config[f"{row}"]["true_name"]}:</b> {config[f"{row}"]["first_1"]} @{bot.get_me().username}{config[f"{row}"]["first_2"]} /clang{config[f"{row}"]["first_3"]}\n\n'
        all_add_reply.add(types.InlineKeyboardButton(f'💬 {all_add_reply_text[:-2]}', url = f'https://t.me/{bot.get_me().username}?startgroup=true'))
        msg += f'<b>Version:</b> {ct.VERSION}'

        bot.send_message(message.chat.id, msg, parse_mode='html', reply_markup=all_add_reply)
        set_commands(message.chat.id, 'en-US')
        return 'en-US'
    else:
        set_commands(message.chat.id, res[0])
        return res[0]

#Обновляем статистику
def working_with_stats(message, file_type):
    sql.execute(f"SELECT * FROM fstats WHERE chatid = '{message.chat.id}'")
    res = sql.fetchone()

    if res is None:
        sql.execute("INSERT INTO fstats VALUES (%s, %s, %s, %s, %s)", (message.chat.id, 0, 0, 0, 0))
        db.commit()

    sql.execute(f"UPDATE fstats SET {file_type} = {file_type} + 1 WHERE chatid = '{message.chat.id}'")
    db.commit()

#Подсчитываем статистические данные
def count_all(message, loc_lang, is_full):
    sql.execute(f"SELECT * FROM fstats")
    rows = sql.fetchall()
    voices, video_notes, videos, audios = 0,0,0,0
    local_voices, local_video_notes, local_videos, local_audios = 0, 0, 0, 0
    
    for row in rows:
        chat_id = row[0]

        voices += row[1]
        video_notes += row[2]
        videos += row[3]
        audios += row[4]
        if chat_id == str(message.chat.id):
            local_voices, local_video_notes, local_videos, local_audios = row[1], row[2], row[3], row[4]
    total = voices + video_notes + videos + audios
    msg = ''
    if is_full == True:
        msg = f'🗣 <b>{config[f"{loc_lang}"]["recognized"]}</b> 🗣\n\n'
        msg += f'<b>{config[f"{loc_lang}"]["voices"]}</b> - {local_voices}\n'
        msg += f'<b>{config[f"{loc_lang}"]["video_notes"]}</b> - {local_video_notes}\n'
        msg += f'<b>{config[f"{loc_lang}"]["videos"]}</b> - {local_videos}\n'
        msg += f'<b>{config[f"{loc_lang}"]["audios"]}</b> - {local_audios}\n\n'
        msg += f'<b>{config[f"{loc_lang}"]["vvv"]}</b> - {local_voices+local_video_notes+local_videos+local_audios}\n'
    else:
        msg = f'{config[f"{loc_lang}"]["recognized"]} {config[f"{loc_lang}"]["all"]}: <b>{total}</b>'
    return msg


@bot.message_handler(commands=['start'])
def welcome(message):
    loc_lang = working_with_sql(message)

@bot.message_handler(commands=['clang', 'cl'])
def change_lang(message):
    loc_lang, lang_reply = changing_language(message)
    bot.send_message(message.chat.id, f'{flags[loc_lang]} <b>{config[f"{loc_lang}"]["tn_r"]}</b> {config[f"{loc_lang}"]["lnow"]}', parse_mode='html', reply_markup=lang_reply)

def changing_language(message):
    loc_lang = working_with_sql(message)
    set_commands(message.chat.id, loc_lang)
    if is_user_admin(message, message.from_user, loc_lang)==False:
        return
    lang_reply = types.InlineKeyboardMarkup()
    for row in config.sections():
        if row == loc_lang:
            continue
        lang_reply.add(types.InlineKeyboardButton(f'{flags[row]} {config[f"{row}"]["true_name"]}', callback_data=row))
    return loc_lang, lang_reply

@bot.message_handler(commands=['stats', 'gstats'])
def welcome(message):
    loc_lang = working_with_sql(message)
    if 'gstats' in message.text.lower():
        msg = '🗣 '+count_all(message, loc_lang, False)
    else:
        msg = count_all(message, loc_lang, True)
    bot.send_message(message.chat.id, msg, parse_mode='html')

@bot.message_handler(commands=['invite', 'inv'])
def inviting(message):
    loc_lang = working_with_sql(message)
    add_reply = types.InlineKeyboardMarkup()
    add_reply.add(types.InlineKeyboardButton(f'💬 {config[f"{loc_lang}"]["add"]}', url = f'https://t.me/{bot.get_me().username}?startgroup=true'))
    bot.send_message(message.chat.id, f'😉 {config[f"{loc_lang}"]["add_msg"]}', parse_mode='html', reply_markup=add_reply)

def add_example(text, loc_lang, command, needed_arguments, supported_list=None):
    supported_list = ['mp3', 'wav', 'ogg', 'mp2', 'flac']

    text += f'<b>{config[f"{loc_lang}"]["example"].capitalize()}:</b>\n/{command}'
    descriptions = ''
    for row in needed_arguments:
        text += f' <b><i>{config[f"{loc_lang}"][f"{row}"]}</i></b>'
        descriptions += f'&#8226; <b><i>{config[f"{loc_lang}"][f"{row}"]}</i></b> - {config[f"{loc_lang}"][f"{row}_description"]}'
        if row == "type":
            descriptions += f' (<b>{config[f"{loc_lang}"]["supported"].lower()}:</b> {", ".join(supported_list)})' 
        descriptions += '\n'
    text += f'\n\n{descriptions}'
    return text


@bot.message_handler(commands=['tts'])
def text_to_speech(message):
    loc_lang = working_with_sql(message)
    set_commands(message.chat.id, loc_lang)
    msg = f'{config[f"{loc_lang}"]["tts_trying"]}...'
    bot_msg = bot.send_message(message.chat.id, msg, parse_mode='html')

    start_time = time.time()
    arguments = message.text.replace('/tts', '').strip().split(' ', 1)

    local_langauages = {}
    for row in config.sections():
        l_code = row.split('-')[0]
        local_langauages.update({config[f"{row}"]["true_name"].lower(): l_code})
        if arguments[0].lower() in config[f"{row}"]["true_name"].lower():
            arguments[0] = config[f"{row}"]["true_name"].lower()

    supported_list = ['mp3', 'wav', 'ogg', 'mp2', 'flac']
    if len(arguments)!=2 or arguments[0].lower() not in local_langauages:
        msg = f'⚠️ {mention_user(message.from_user)}, {config[f"{loc_lang}"]["arg_error"].lower()}\n\n'
        msg = add_example(msg, loc_lang, "tts", ['lang', 'text'])
        return bot.send_message(message.chat.id, msg, parse_mode='html')


    from gtts import gTTS as tts
    output = tts(text=arguments[1], lang = local_langauages[arguments[0]], slow = False)

    rn = random.randint(1, 99999)
    pr = 'ogg'
    file_name = f'tts_{rn}_{message.chat.id}.{pr}'
    output.save(file_name)
    

    if is_more_limit(message, os.path.getsize(file_name), loc_lang, "tts_error") == True:
        return os.remove(file_name)

    user = get_user(message)

    f = open(file_name,"rb")


    msg = f'{config[f"{loc_lang}"]["tts_done"]} <b>{user}</b>\n{config[f"{loc_lang}"]["done_for"]} {command_duration(loc_lang, start_time)} ⏳'
    bot.send_voice(message.chat.id, f, caption=msg, parse_mode='html')
    bot.delete_message(message.chat.id, message.message_id)
    bot.delete_message(bot_msg.chat.id, bot_msg.message_id)
    f.close()

    os.remove(file_name)

def convert_to(msg, file_name, file_type, loc_lang):
    from pydub import AudioSegment
    try:
        wav_audio = AudioSegment.from_file(file_name, file_name.split('.')[1])
    except Exception as ex:
        print(ex)
        text = f'⚠️ {config[f"{loc_lang}"]["f_error"]}'
        bot.edit_message_text(chat_id = msg.chat.id, message_id = msg.message_id, text=text, parse_mode='html', reply_markup=None)
        print('first')
        return os.remove(file_name)
    
    try:
        os.remove(file_name)
        file_name = file_name.replace(file_name.split('.')[1], file_type).replace(f"_{msg.chat.id}", "")
        wav_audio.export(file_name, format = file_type)
        return file_name
    except Exception as ex:
        print(ex)
        text = f'⚠️ {config[f"{loc_lang}"]["f_error"]}'
        bot.edit_message_text(chat_id = msg.chat.id, message_id = msg.message_id, text=text, parse_mode='html', reply_markup=None)
        print('second')
        return None

@bot.message_handler(commands=['extract'])
def extract_audio(message):
    loc_lang = working_with_sql(message)
    set_commands(message.chat.id, loc_lang)
    arguments = message.text.replace('/extract', '').lower().strip().split(' ', 1)
    file_type = arguments[0]
    if (len(arguments)>1 and len(arguments[1].strip())>0): 
        file_title = arguments[1]
    else:
        file_title = None

    supported_list = ['mp3', 'wav', 'ogg', 'mp2', 'flac']
    if file_type not in supported_list:
        text = f'⚠️ {mention_user(message.from_user)}, {config[f"{loc_lang}"]["arg_error"].lower()}\n\n'
        text = add_example(text, loc_lang, "extract", ['type', 'title'], supported_list)
        bot.send_message(chat_id = message.chat.id, text=text, parse_mode='html', reply_markup=None)
        return


    msg = f'{config[f"{loc_lang}"]["extr_trying"]}...'
    bot_msg = bot.send_message(message.chat.id, msg, parse_mode='html')
    if message.reply_to_message != None:
        current_msg = message.reply_to_message
    else:
        current_msg = message



    start_time = time.time()
    file_name = voice_processing(current_msg, extract=True, file_title = file_title)
    if file_name == None:
        bot.delete_message(chat_id = bot_msg.chat.id, message_id=bot_msg.message_id)
        return
    file_name = convert_to(bot_msg, file_name, file_type, loc_lang)
    if file_name==None:
        return

    f = open(file_name, "rb")
    user = get_user(message)

    msg = f'{config[f"{loc_lang}"]["extr_done"]} <b>{user}</b>\n{config[f"{loc_lang}"]["done_for"]} {command_duration(loc_lang, start_time)} ⏳'
    bot.send_audio(message.chat.id, f, caption=msg, parse_mode='html')
    bot.delete_message(message.chat.id, message.message_id)
    bot.delete_message(bot_msg.chat.id, bot_msg.message_id)
    f.close()
    os.remove(file_name)







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

def is_more_limit(message, file_size, loc_lang, error):
    limit = 50
    if round(file_size/(10**6))>limit:
        bot.send_message(message.chat.id, f'⚠️ {config[f"{loc_lang}"][f"{error}"]}{config[f"{loc_lang}"]["limit"]}', parse_mode='html')
        return True
    else:
        return False

def recognize_your_language(engine, audio, file_name, lang, loc_lang, file_type, message, r_c):
    
    try:
        print(f'Log: file {file_name} is being analized')
        text = engine.recognize_google(audio, language=lang)
        r_c += 1
        if r_c == 1:
            working_with_stats(message, file_type)
    except Exception as ex:
        text = f'{config[f"{loc_lang}"]["r_error"]} 😣'
        print(ex)
    print(f'Log: file {file_name} is recognized with {lang} language')
    return text, r_c

@bot.message_handler(content_types=['new_chat_members'])
def checking_members(message):
    for member in message.new_chat_members:
        if member.username == bot.get_me().username:
            is_admin, loc_lang = is_bot_admin(message)
            set_commands(message.chat.id, loc_lang)

@bot.message_handler(content_types=['left_chat_member'])
def bot_removed(message):
    if message.left_chat_member.username == bot.get_me().username:
        sql.execute(f"DELETE FROM clangs WHERE chatid = '{message.chat.id}'")
        db.commit()




@bot.message_handler(content_types=['voice', 'video_note', 'video', 'audio'])
def voice_processing(message, extract = False, file_title=None):
    loc_lang = working_with_sql(message)
    set_commands(message.chat.id, loc_lang)
    if extract==False:
        msg = bot.send_message(message.chat.id, f'{config[f"{loc_lang}"]["trying"]}...', parse_mode='html')
    
    start_time = time.time()
    #Проверка на тип файла
    if message.video_note != None:
        file_info = bot.get_file(message.video_note.file_id)
        pr = 'mp4'
        file_type = 'video_note'
    elif message.video != None:
        file_info = bot.get_file(message.video.file_id)
        if message.video.file_name==None:
            pr = 'mp4'
        else:
            pr = message.video.file_name.split('.')[1]
        file_type = 'video'
    elif message.audio != None:
        file_info = bot.get_file(message.audio.file_id)
        pr = message.audio.file_name.split('.')[1]
        file_type = 'audio'
    else:
        if message.voice == None:
            msg = f'⚠️ {config[f"{loc_lang}"]["no_media"]}'
            bot.send_message(message.chat.id, msg, parse_mode='html')
            return None
        file_info = bot.get_file(message.voice.file_id)
        pr = 'ogg'
        file_type = 'voice'

    #Проверка на лимит
    if is_more_limit(message, file_info.file_size, loc_lang, "r_error") == True:
        return

    #Скачиваем файл в нужном формате
    downloaded_file = bot.download_file(file_info.file_path)
    rn = random.randint(1, 99999)
    file_name = f'{rn}_{message.chat.id}.{pr}'
    print(file_name)
    if extract==True:
        if file_title!=None:
            file_name=f"{file_title}.{pr}"
        else:
            file_name=f'extr_{file_name}'
        print(file_name)
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)
        return file_name
    else:
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)



    #Конвертация в wav
    file_name = convert_to(msg, file_name, "wav", loc_lang)
    if file_name==None:
        return

    text = ''
    r_c = 0

    #Подключаем Speech Recognition
    import speech_recognition as sr
    engine = sr.Recognizer()

    with sr.AudioFile(file_name) as source:
        print(f'Log: file {file_name} is being recorded')
        audio = engine.record(source)

    for row in config.sections():
        recognized, r_c = recognize_your_language(engine, audio, file_name, row, loc_lang, file_type, message, r_c)
        text += f'<b>{config[f"{row}"]["true_name"]}</b> - {recognized}\n'

    os.remove(file_name)
    print(f'Log: file {file_name} is deleted')
    
    user = get_user(message)

    c_all = count_all(message, loc_lang, False)
    bot.edit_message_text(chat_id = msg.chat.id, message_id = msg.message_id, text = f'{config[f"{loc_lang}"]["from"]} <b>{user}:</b>\n\n{text[0].upper()}{text[1:]}\n{config[f"{loc_lang}"]["done_for"]} {command_duration(loc_lang, start_time)} ⏳\n{c_all} 🗣\n<b>{config[f"{loc_lang}"]["cv"]} {ct.VERSION} 🧑‍💻</b>', parse_mode='html')
    #bot.send_message(message.chat.id, f'{config[f"{loc_lang}"]["from"]} <b>{user}</b>:\n{text[0].upper()}{text[1:]}\n\n<code>P.S. {config[f"{loc_lang}"]["bv"]} 🧑‍💻</code>', parse_mode='html')

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        msg = call.message
        loc_lang = call.data
        if is_user_admin(msg, call.from_user, loc_lang)==False:
            return
        editing_lang(msg, loc_lang)
        bot.edit_message_text(chat_id = msg.chat.id, message_id = msg.message_id, text=f'✅ <b>{config[f"{loc_lang}"]["tn_r"]}</b> {config[f"{loc_lang}"]["lset"]}', parse_mode='html', reply_markup=None)
        set_commands(msg.chat.id, loc_lang)
#working_with_sql(message)

bot.polling(none_stop=True)