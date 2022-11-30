#!/usr/bin/env python3.9

from config import *
from giflist import *
from blasphemywords import *
from mqttconf import *
import telebot
from telebot import types
import time
import os
import json
import jsonpickle
import random
from subprocess import call
from paho.mqtt import client as mqtt_client
import urllib
import requests
import datetime  # Importing the datetime library
import unicodedata

"""
MQTT connection
"""
def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def publish(client, msg):
    mqttmsg = jsonpickle.encode(msg)
    result = mqtt_client.publish(topic, mqttmsg)

def publishToTopic(client, newTopic, msg):
    mqttmsg = jsonpickle.encode(msg)
    result = mqtt_client.publish(topic + '/' + newTopic, mqttmsg.encode("utf-8"))


"""
TELEBOT
"""

# error handling if user isn't known yet 
# (obsolete once known users are saved to file, because all users
# had to use the /start command and are therefore known to the bot)
#Solved by checking by name and nick 

def user_call(m):
    name = None
    if m.from_user.username is not None:
        name = m.from_user.username
    elif m.from_user.first_name is not None:
        name = m.from_user.first_name
    return name

def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        knownUsers.append(uid)
        userStep[uid] = 0
        print("New user detected, who hasn't used \"/start\" yet")
        return 0

# only used for console output now
def listener(messages):
    """
    When new messages arrive TeleBot will call this function.
    """
    #print("received: " + str(messages))
    for m in messages:
        result = ""
        if m.content_type == 'text':
            data=m.text
            string_utf = data.encode()
            result = user_call(m)
            if(m.chat.type == 'private'):
                result += " "
            else:
                result += " [" + str(m.chat.title.encode(), 'iso8859-15') + "]: " 
            result += str(string_utf, 'iso8859-15')
            print(result)
            publish(client_id, result)

def getUrl():
    f = os.popen('curl https://api.ipify.org')
    return f.read()


bot = telebot.TeleBot(TOKEN)
bot.set_update_listener(listener) # register listener

# handle the "/start" command
@bot.message_handler(commands=['start'])
def command_start(m):
    if not isBlacklistedUser(m):
        cid = m.chat.id
        if cid not in knownUsers:
            knownUsers.append(cid)
            userStep[cid] = 0
            #print(str(knownUsers))

# Listar comandos
@bot.message_handler(commands=['list'])
def command_long_text(m):
    if not isBlacklistedUser(m):
        cid = m.chat.id
        lista = ["/list"]
        lista.extend(list(messages.keys()))
        lista.extend(list(urls.keys()))
        bot.send_message(cid, str(lista))


# Reinicia servidor
@bot.message_handler(commands=['reboot'])
def command_long_text(m):
    if not isBlacklistedUser(m):
        cid = m.chat.id
        bot.send_message(cid, "que qué?")
        bot.send_chat_action(cid, 'typing')
        time.sleep(1)
        bot.send_message(cid, "y una 💩!!!")
        bot.send_chat_action(cid, 'typing')
        time.sleep(3)
        bot.reply_to(m, "🖕")

"""
# Python program to read json file
import json
from collections import defaultdict

def getUsersInBlacklist(chatType, chatID):
    for groups in ignoredList[chatType]:
        group = groups["idGroup"]
        if group == chatID:
            users = groups["idUsers"]
            return users

def isUserInBlacklist(chatType, chatID, userID):
    users = getUsersInBlacklist(chatType, chatID)
    if users is None:
        return False
    #print(users)
    if userID in users:
        return True
    return False



def addUserToBlacklist(chatType, chatID, userID):
    if not ignoredList[chatType]: #no existe o grupo vacio
        new_key_values_dict = {"idGroup":chatID, "idUsers": [userID]}
        ignoredList[chatType].append(new_key_values_dict)
    else:
        chatList = ignoredList[chatType]
        for each in ignoredList[chatType]:
            if each["idGroup"] == chatID:
                each["idUsers"].append(userID)
                return
    new_key_values_dict = {"idGroup":chatID, "idUsers": [userID]}
    ignoredList[chatType].append(new_key_values_dict)

def removeUserFromBlackList(chatType, chatID, userID):
    if not ignoredList[chatType]: #no existe o grupo vacio
        return
    chatList = ignoredList[chatType]
    for each in ignoredList[chatType]:
        if each["idGroup"] == chatID:
            each["idUsers"].remove(userID)
            return


def test1():
    print("test1")
    print(getUsersInBlacklist("group", 111111111))
    print(getUsersInBlacklist("group", 12333334))
    print("\n")

def test2():
    print("test2")
    print(isUserInBlacklist("group", 111111111, 123))
    print(isUserInBlacklist("group", 111111111, 124))
    print("\n")

def test3():
    print("test3")
    addUserToBlacklist("group", 111111111, 1233)
    addUserToBlacklist("supergroup", -111111111, 1233)
    addUserToBlacklist("supergroup", -111111112, 1233)
    print("eeeee ", getUsersInBlacklist("group", 111111111))
    print("eeeee ", isUserInBlacklist("group", 111111111, 1233))
    print("eeeee ", getUsersInBlacklist("supergroup", -111111111))
    print("eeeee ", isUserInBlacklist("supergroup", -111111111, 1233))
    print("\n")

def test4():
    print("test4")
    addUserToBlacklist("group", 111111111, 1233)
    addUserToBlacklist("supergroup", -111111111, 1233)
    addUserToBlacklist("supergroup", -111111112, 1233)
    print("eeeee ", getUsersInBlacklist("group", 111111111))
    print("eeeee ", isUserInBlacklist("group", 111111111, 1233))
    print("eeeee ", getUsersInBlacklist("supergroup", -111111111))
    print("eeeee ", isUserInBlacklist("supergroup", -111111111, 1233))
    removeUserFromBlackList("group", 111111111, 1233)
    print("eeeee ", isUserInBlacklist("group", 111111111, 1233))
    print("eeeee ", getUsersInBlacklist("group", 111111111))
    print("eeeee ", getUsersInBlacklist("supergroup", -111111111))
    print("eeeee ", isUserInBlacklist("supergroup", -111111111, 1233))
    removeUserFromBlackList("supergroup", -111111111, 1233)
    print("eeeee ", getUsersInBlacklist("supergroup", -111111111))
    print("eeeee ", isUserInBlacklist("supergroup", -111111111, 1233))
    
    print("\n")
# Opening JSON file
f = open('json2.json')
# returns JSON object as 
# a dictionary
ignoredList = json.load(f)
# Closing file
f.close()
# Iterating through the json list
#test1()
#test2()
#test3()
test4()
# Closing file
f.close()
"""

def isBlacklistedUser(m):
    print("eeeeeeeeeee", m.chat.type)
    if(m.chat.type == 'private'):
        print("privado: ", m.from_user.id)
        return False #testing
    else:
        print("grupo: ", m.chat.type, " = ", m.chat.id)
        return False #testing
        if any(word in message.text.lower() for word in ignoredUserList):
            return True
    return False


# Envia un gif de los establecidos en el JSON urls
@bot.message_handler(commands=keys)
def send_gif(m):
    if not isBlacklistedUser(m):
        command = m.text
        cid = m.chat.id
        publishToTopic(client_id, "command", m)
        if command in urls.keys():
            bot.send_document(cid, urls[command])
        elif command in messages.keys():
            bot.send_message(cid, str(messages[command]))

# Enviarme la IP de la rasp a mi en privado
@bot.message_handler(commands=['ip'])
def command_help(m):
    if not isBlacklistedUser(m):
        bot.send_message(myID, "IP: "+ getUrl())


def extract_arg(arg):
    argument = arg.split()[1:]
    argumentstring = ' '.join(argument)
    return argumentstring

@bot.message_handler(commands=['eltiempo'])
def eltiempo(m):
    if not isBlacklistedUser(m):
        bot.send_message(m.chat.id, "Saca la cabeza por la ventana y no des por culo con tonterías.")

# Ejecuta un comando
@bot.message_handler(commands=['exec'])
def command_long_text(m):
    if not isBlacklistedUser(m):
        cid = m.chat.id
        bot.send_message(cid, "Ejecutando: "+m.text[len("/exec"):])
        bot.send_chat_action(cid, 'typing') # show the bot "typing" (max. 5 secs)
        time.sleep(2)
        if cid == myID:
            f = os.popen(m.text[len("/exec"):])
            result = f.read()
            bot.send_message(cid, "Resultado: "+result)
        else:
            bot.send_message(cid, "JA!!!")
            bot.send_chat_action(cid, 'typing')
            time.sleep(1)
            bot.send_message(cid, "tus ganas locas")
            bot.send_chat_action(cid, 'typing')
            time.sleep(3)
            bot.reply_to(m, "🖕")

def guardaUrl(m):
    file1 = open("urlsdelchat.txt", "a")  # append mode
    data=m.text
    string_utf = data.encode()
    result = ""
    if(m.chat.type == 'private'):
        result = user_call(m) + " [" + user_call(m) + "]: " + str(string_utf, 'iso8859-15')
    else:
        result = user_call(m) + " [" + str(m.chat.title.encode(), 'iso8859-15') + "]: " + str(string_utf, 'iso8859-15')
    file1.write(result)
    file1.write("\n")
    file1.close()



def string_found(string1, string2):
    string1 = " " + string1.strip() + " "
    string2 = " " + string2.strip() + " "
    return string2.find(string1)

# filter on a specific message
@bot.message_handler(func=lambda message: "mmmkk" in message.text.lower())
def command_text_kk(m):
    return
    bot.send_message(m.chat.id, "esto es mmmkk, @" + user_call(m) + "!")

@bot.message_handler(func=lambda message: any(["alfo" == word for word in message.text.lower().split()]))
def command_text_alfo(m):
    if not isBlacklistedUser(m):
        bot.reply_to(m, "Ha dicho alFo xDDD")

@bot.message_handler(func=lambda message: "buenas noches" in message.text.lower())
def command_text_nanit(m):
    if not isBlacklistedUser(m):
        bot.send_message(m.chat.id, "Buenas noches, @" + user_call(m))

saludoList = ["hola", "buenos dias", "buenos días", "wenos dias"]
respuestaSaludo = ["Yep", "Hola", "Muy buenas", "Ah, hola"]
@bot.message_handler(func=lambda message: any(saludo in message.text.lower() for saludo in saludoList))
def command_text_saludo(m):
    if not isBlacklistedUser(m):
        bot.reply_to(m, random.choice(respuestaSaludo) + ", @" + user_call(m))

@bot.message_handler(func=lambda message: any(word in message.text.lower() for word in blasphemywords))
def command_text_blasphemy(m):
    if not isBlacklistedUser(m):
        bot.reply_to(m, "ESA BOCA!!!")

@bot.message_handler(func=lambda message: "http" in message.text.lower())
def command_text_http(m):
    guardaUrl(m)



mqtt_client = connect_mqtt()
mqtt_client.loop_start()
publish(mqtt_client, "first message!")

bot.send_message(myID, "Bot iniciado en IP: "+getUrl())
bot.polling(none_stop=True, timeout=300)




"""
mmmmmmmmmmmmmmmm
"first message!"
Connected to MQTT Broker!
Sent msg to topic `python/mqtt`
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100    12  100    12    0     0     22      0 --:--:-- --:--:-- --:--:--    22
received: [<telebot.types.Message object at 0x75c73c40>]
Pepe [Xorva]: adsf
message type =  ['_Message__html_text', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', 'animation', 'audio', 'author_signature', 'caption', 'caption_entities', 'channel_chat_created', 'chat', 'check_json', 'connected_website', 'contact', 'content_type', 'date', 'de_json', 'delete_chat_photo', 'dice', 'document', 'edit_date', 'entities', 'forward_date', 'forward_from', 'forward_from_chat', 'forward_from_message_id', 'forward_sender_name', 'forward_signature', 'from_user', 'group_chat_created', 'has_protected_content', 'html_caption', 'html_text', 'id', 'invoice', 'is_automatic_forward', 'json', 'left_chat_member', 'location', 'media_group_id', 'message_id', 'migrate_from_chat_id', 'migrate_to_chat_id', 'new_chat_member', 'new_chat_members', 'new_chat_photo', 'new_chat_title', 'parse_chat', 'parse_entities', 'parse_photo', 'photo', 'pinned_message', 'reply_markup', 'reply_to_message', 'sender_chat', 'sticker', 'successful_payment', 'supergroup_chat_created', 'text', 'venue', 'via_bot', 'video', 'video_note', 'voice']
message id = 3837
from_user type =  ['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', 'can_join_groups', 'can_read_all_group_messages', 'check_json', 'de_json', 'first_name', 'full_name', 'id', 'is_bot', 'language_code', 'last_name', 'supports_inline_queries', 'to_dict', 'to_json', 'username']
from user:  Pepe at Xorva
date = 1647024788
chat = {'id': 15559765, 'type': 'private', 'title': None, 'username': 'Xorva', 'first_name': 'Pepe', 'last_name': None, 'photo': None, 'bio': None, 'has_private_forwards': None, 'description': None, 'invite_link': None, 'pinned_message': None, 'permissions': None, 'slow_mode_delay': None, 'message_auto_delete_time': None, 'has_protected_content': None, 'sticker_set_name': None, 'can_set_sticker_set': None, 'linked_chat_id': None, 'location': None}
content_type = text
text = adsf
mmmmmmmmmmmmmmmm
{"py/object": "telebot.types.Message", "content_type": "text", "id": 3837, "message_id": 3837, "from_user": {"py/object": "telebot.types.User", "id": 15559765, "is_bot": false, "first_name": "Pepe", "username": "Xorva", "last_name": null, "language_code": "es", "can_join_groups": null, "can_read_all_group_messages": null, "supports_inline_queries": null}, "date": 1647024788, "chat": {"py/object": "telebot.types.Chat", "id": 15559765, "type": "private", "title": null, "username": "Xorva", "first_name": "Pepe", "last_name": null, "photo": null, "bio": null, "has_private_forwards": null, "description": null, "invite_link": null, "pinned_message": null, "permissions": null, "slow_mode_delay": null, "message_auto_delete_time": null, "has_protected_content": null, "sticker_set_name": null, "can_set_sticker_set": null, "linked_chat_id": null, "location": null}, "sender_chat": null, "forward_from": null, "forward_from_chat": null, "forward_from_message_id": null, "forward_signature": null, "forward_sender_name": null, "forward_date": null, "is_automatic_forward": null, "reply_to_message": null, "via_bot": null, "edit_date": null, "has_protected_content": null, "media_group_id": null, "author_signature": null, "text": "adsf", "entities": null, "caption_entities": null, "audio": null, "document": null, "photo": null, "sticker": null, "video": null, "video_note": null, "voice": null, "caption": null, "contact": null, "location": null, "venue": null, "animation": null, "dice": null, "new_chat_member": null, "new_chat_members": null, "left_chat_member": null, "new_chat_title": null, "new_chat_photo": null, "delete_chat_photo": null, "group_chat_created": null, "supergroup_chat_created": null, "channel_chat_created": null, "migrate_to_chat_id": null, "migrate_from_chat_id": null, "pinned_message": null, "invoice": null, "successful_payment": null, "connected_website": null, "reply_markup": null, "json": {"message_id": 3837, "from": {"id": 15559765, "is_bot": false, "first_name": "Pepe", "username": "Xorva", "language_code": "es"}, "chat": {"id": 15559765, "first_name": "Pepe", "username": "Xorva", "type": "private"}, "date": 1647024788, "text": "adsf"}}
Sent msg to topic `python/mqtt`

"""



"""
{
    "py/object": "telebot.types.Message", 
    "content_type": "text", 
    "id": 128243, 
    "message_id": 128243, 
    "from_user": {
        "py/object": "telebot.types.User", 
        "id": ########, 
        "is_bot": false, 
        "first_name": "Pepe", 
        "username": "Xorva", 
        "last_name": null, 
        "language_code": "es", 
        "can_join_groups": null, 
        "can_read_all_group_messages": null, 
        "supports_inline_queries": null
    }, 
    "date": 1663192687, 
    "chat": 
    {
        "py/object": "telebot.types.Chat", 
        "id": ##############, 
        "type": "supergroup", 
        "title": "Cacharreando!", 
        "username": null, 
        "first_name": null, 
        "last_name": null, 
        "photo": null, 
        "bio": null, 
        "has_private_forwards": null, 
        "description": null, 
        "invite_link": null, 
        "pinned_message": null, 
        "permissions": null, 
        "slow_mode_delay": null, 
        "message_auto_delete_time": null, 
        "has_protected_content": null, 
        "sticker_set_name": null, 
        "can_set_sticker_set": null, 
        "linked_chat_id": null, 
        "location": null
    }, 
    "sender_chat": null, 
    "forward_from": null, 
    "forward_from_chat": null, 
    "forward_from_message_id": null, 
    "forward_signature": null, 
    "forward_sender_name": null, 
    "forward_date": null, 
    "is_automatic_forward": null, 
    "reply_to_message": null, 
    "via_bot": null, 
    "edit_date": null, 
    "has_protected_content": null, 
    "media_group_id": null, 
    "author_signature": null, 
    "text": "ahora podr\u00eda personalizarlo \ud83d\ude06", 
    "entities": null, 
    "caption_entities": null, 
    "audio": null, 
    "document": null, 
    "photo": null, 
    "sticker": null, 
    "video": null, 
    "video_note": null, 
    "voice": null, 
    "caption": null, 
    "contact": null, 
    "location": null, 
    "venue": null, 
    "animation": null, 
    "dice": null, 
    "new_chat_member": null, 
    "new_chat_members": null, 
    "left_chat_member": null, 
    "new_chat_title": null, 
    "new_chat_photo": null, 
    "delete_chat_photo": null, 
    "group_chat_created": null, 
    "supergroup_chat_created": null, 
    "channel_chat_created": null, 
    "migrate_to_chat_id": null, 
    "migrate_from_chat_id": null, 
    "pinned_message": null, 
    "invoice": null, 
    "successful_payment": null, 
    "connected_website": null, 
    "reply_markup": null, 
    "json": 
    {
        "message_id": 128243, 
        "from": 
        {
            "id": ########,, 
            "is_bot": false, 
            "first_name": "Pepe", 
            "username": "Xorva", 
            "language_code": "es"
        }, 
        "chat": 
        {
            "id": ##############, 
            "title": "Cacharreando!", 
            "type": "supergroup"
        }, 
        "date": 1663192687, 
        "text": "ahora podr\u00eda personalizarlo \ud83d\ude06"
    }
}
"""




"""
HunterDAce [Cacharreando!]: 😂😂
message id = 128245
from user:  HunterDAce at Cacharreando!
date = 1663192743
chat ID =  ##############
text = 😂😂
mqtt publishing message
{
	"py/object": "telebot.types.Message",
	"content_type": "text",
	"id": 128245,
	"message_id": 128245,
	"from_user": 
	{
		"py/object": "telebot.types.User",
		"id": ########,
		"is_bot": false,
		"first_name": "\ud835\udd6f.",
		"username": "HunterDAce",
		"last_name": "\ud83d\udc0c",
		"language_code": null,
		"can_join_groups": null,
		"can_read_all_group_messages": null,
		"supports_inline_queries": null
	},
	"date": 1663192743,
	"chat": 
	{
		"py/object": "telebot.types.Chat",
		"id": ##############,
		"type": "supergroup",
		"title": "Cacharreando!",
		"username": null,
		"first_name": null,
		"last_name": null,
		"photo": null,
		"bio": null,
		"has_private_forwards": null,
		"description": null,
		"invite_link": null,
		"pinned_message": null,
		"permissions": null,
		"slow_mode_delay": null,
		"message_auto_delete_time": null,
		"has_protected_content": null,
		"sticker_set_name": null,
		"can_set_sticker_set": null,
		"linked_chat_id": null,
		"location": null
	},
	"sender_chat": null,
	"forward_from": null,
	"forward_from_chat": null,
	"forward_from_message_id": null,
	"forward_signature": null,
	"forward_sender_name": null,
	"forward_date": null,
	"is_automatic_forward": null,
	"reply_to_message": null,
	"via_bot": null,
	"edit_date": null,
	"has_protected_content": null,
	"media_group_id": null,
	"author_signature": null,
	"text": "\ud83d\ude02\ud83d\ude02",
	"entities": null,
	"caption_entities": null,
	"audio": null,
	"document": null,
	"photo": null,
	"sticker": null,
	"video": null,
	"video_note": null,
	"voice": null,
	"caption": null,
	"contact": null,
	"location": null,
	"venue": null,
	"animation": null,
	"dice": null,
	"new_chat_member": null,
	"new_chat_members": null,
	"left_chat_member": null,
	"new_chat_title": null,
	"new_chat_photo": null,
	"delete_chat_photo": null,
	"group_chat_created": null,
	"supergroup_chat_created": null,
	"channel_chat_created": null,
	"migrate_to_chat_id": null,
	"migrate_from_chat_id": null,
	"pinned_message": null,
	"invoice": null,
	"successful_payment": null,
	"connected_website": null,
	"reply_markup": null,
	"json": 
	{
		"message_id": 128245,
		"from": 
		{
			"id": ########,
			"is_bot": false,
			"first_name": "\ud835\udd6f.",
			"last_name": "\ud83d\udc0c",
			"username": "HunterDAce"
		},
		"chat": 
		{
			"id": ##############,
			"title": "Cacharreando!",
			"type": "supergroup"
		},
		"date": 1663192743,
		"text": "\ud83d\ude02\ud83d\ude02"
	}
}
"""
