#!/usr/bin/env python3.9

from config import *
from mqttconf import *
from telebot import *
from time import sleep
import os
import json
import jsonpickle
import random
from collections import defaultdict
from subprocess import call
from paho.mqtt import client as mqtt_client
import urllib
import requests
import datetime
import unicodedata
from concurrent.futures import ThreadPoolExecutor
import requests 


salutes = ["hola", "buenos dias", "buenos días", "wenos dias"]
saluteResponses = ["Yep", "Hola", "Muy buenas", "Ah, hola"]
blasphemywords = ['zorra', 'capullo', 'joputa', 'gilipollas', 'mierda', 'gilipo', 'puta ']

def readCommandJsonsFile():
    f = open(commandJsonsFile, "r")
    commandList = json.load(f)
    f.close()
    ch = '/'
    commandKeys = [elem.replace(ch, '') for elem in commandList.keys()]
    return commandList, commandKeys

commandList, commandKeys = readCommandJsonsFile()

f = open(ignoreUsersFile, "r")
ignoredList = json.load(f)
f.close()

def extract_arg(arg):
    argument = arg.split()[1:]
    argumentstring = ' '.join(argument)
    return argumentstring

def user_call(m):
    name = None
    if m.from_user.username is not None:
        name = m.from_user.username
    elif m.from_user.first_name is not None:
        name = m.from_user.first_name
    return name

#stores any URL sent to chats
def storeURL(m):
    file1 = open(URLsFromChat, "a")
    string_utf = m.text.encode()
    result = ""
    if(m.chat.type == 'private'):
        result = user_call(m) + " [" + user_call(m) + "]: " + str(string_utf, 'utf-8')
    else:
        result = user_call(m) + " [" + str(m.chat.title.encode(), 'utf-8') + "]: " + str(string_utf, 'utf-8')
    file1.write(result + "\n")
    file1.close()

def string_found(string1, string2):
    string1 = " " + string1.strip() + " "
    string2 = " " + string2.strip() + " "
    return string2.find(string1)

def getPublicIP():
    for url in getIPList:
        s = requests.get(url,timeout=5)
        if s.status_code == 200:
            return s.content.decode()
    return "no obtenida"


#Ignore users block

def isBlacklistedUser(m):
    return isUserInBlacklist(m.chat.type, m.chat.id, m.from_user.id)

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
    if userID in users:
        return True
    return False

def writeBlacklist():
    json_object = json.dumps(ignoredList, indent=4)    
    with open(ignoreUsersFile, "w") as outfile:
        outfile.write(json_object)

def addUserToBlacklist(chatType, chatID, userID):
    if isUserInBlacklist(chatType, chatID, userID):
        return
    if not ignoredList[chatType]: 
        new_key_values_dict = {"idGroup":chatID, "idUsers": [userID]}
        ignoredList[chatType].append(new_key_values_dict)
    else:
        chatList = ignoredList[chatType]
        for each in chatList:
            if each["idGroup"] == chatID:
                if userID not in each["idUsers"]:
                    each["idUsers"].append(userID)
                    writeBlacklist()
                    return
        new_key_values_dict = {"idGroup":chatID, "idUsers": [userID]}
        ignoredList[chatType].append(new_key_values_dict)
    writeBlacklist()

def removeUserFromBlacklist(chatType, chatID, userID):
    if not isUserInBlacklist(chatType, chatID, userID):
        return
    if not ignoredList[chatType]:
        return
    for each in ignoredList[chatType]:
        if each["idGroup"] == chatID:
            if userID in each["idUsers"]:
                each["idUsers"].remove(userID)
            writeBlacklist()
            return


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

# only used for console output now
def listener(messages):
    """
    When new messages arrive TeleBot will call this function.
    """
    for m in messages:
        result = ""
        if m.content_type == 'text':
            data=m.text
            string_utf = data.encode()
            result = user_call(m)
            if(m.chat.type == 'private'):
                result += " "
            else:
                result += " [" + str(m.chat.title.encode(), 'utf-8') + "]: " 
            result += str(string_utf, 'utf-8')
            print(result)
            publish(client_id, result)

bot = telebot.TeleBot(TOKEN)
bot.set_update_listener(listener) # register listener

# List commands
@bot.message_handler(commands=['list'])
def command_long_text(m):
    cid = m.chat.id
    if not isBlacklistedUser(m):
        bot.send_message(cid, str(list(commandList.keys())))
    print("/ignoramebot", "/hazmecasitobot")
    bot.send_message(cid, "/ignoramebot, /hazmecasitobot")

@bot.message_handler(commands=["ignoramebot"])
def blacklistUser(m):
    addUserToBlacklist(m.chat.type, m.chat.id, m.from_user.id)

@bot.message_handler(commands=["hazmecasitobot"])
def whitelistUser(m):
    removeUserFromBlacklist(m.chat.type, m.chat.id, m.from_user.id)


# Reboot server joke
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

# Send a response message from commands.json
@bot.message_handler(commands=commandKeys)
def send_response_message(m):
    if not isBlacklistedUser(m):
        command = m.text
        cid = m.chat.id
        if "@" in command:
            command = command.split('@')
            command = command[0]
        print("command = ", command, " cid = ", cid, " sendDocument = ", commandList[command]["typeSend"])
        if "sendDocument" in commandList[command]["typeSend"]:
            bot.send_document(cid, commandList[command]["response"])
        elif "sendMessage" in commandList[command]["typeSend"]:
            response = str(commandList[command]["response"])
            print(response)
            bot.send_message(cid, response)
            publish(client_id, response)



# Send RaspBerry public IP to mi priate chat
@bot.message_handler(commands=['ip'])
def command_ip(m):
    if m.chat.id == myID:
        r= getPublicIP()
        bot.send_message(m.chat.id, "ip = " + r)

# Delete, change and create gif command
@bot.message_handler(commands=['gif'])
def command_gif(m):
    cid = m.chat.id
    if not cid == myID:
        bot.send_chat_action(cid, 'typing')
        time.sleep(3)
        bot.reply_to(m, "🖕")
        return
    bot.reply_to(m, "Vamos a ello!")
    bot.send_message(cid, "Pillando args de: "+m.text[len("/gif"):])
    gifActionList = m.text.split(" ")
    print("GifAction elements = " + str(len(gifActionList)))
    if not len(gifActionList) == 5:
        bot.send_message(cid, "gif command:  action + name + typeSend + response")
        bot.send_message(cid, "ejemplo:\n /gif add unbesin sendMessage 😘")
        return
    ##crear el elemento en el json
    bot.send_message(cid, "gif command: " + gifActionList[1] + " " + gifActionList[2] + " " + gifActionList[3] + " " + gifActionList[4] + " " )
    return

@bot.message_handler(commands=['eltiempo'])
def weatherConsult(m):
    if not isBlacklistedUser(m):
        bot.send_message(m.chat.id, "Saca la cabeza por la ventana y no des por culo con tonterías.")

# Execute a command from Rasp
@bot.message_handler(commands=['exec'])
def command_long_text(m):
    if not isBlacklistedUser(m):
        cid = m.chat.id
        bot.send_message(cid, "Ejecutando: "+m.text[len("/exec"):])
        bot.send_chat_action(cid, 'typing')
        if cid == myID:
            f = os.popen(m.text[len("/exec"):])
            result = f.read()
            bot.send_message(cid, "Resultado: "+result)

@bot.message_handler(func=lambda message: "buenas noches" in message.text.lower())
def command_text_goodnight(m):
    if not isBlacklistedUser(m):
        bot.send_message(m.chat.id, "Buenas noches, @" + user_call(m))

@bot.message_handler(func=lambda message: any(salute in message.text.lower() for salute in salutes))
def command_text_salute(m):
    if not isBlacklistedUser(m):
        bot.reply_to(m, random.choice(saluteResponses) + ", @" + user_call(m))

@bot.message_handler(func=lambda message: any(word in message.text.lower() for word in blasphemywords))
def command_text_blasphemy(m):
    if not isBlacklistedUser(m):
        bot.reply_to(m, "ESA BOCA!!!")

@bot.message_handler(func=lambda message: "http" in message.text.lower())
def command_text_http(m):
    storeURL(m)


mqtt_client = connect_mqtt()
mqtt_client.loop_start()
publish(mqtt_client, "first message!")

bot.send_message(myID, "Bot iniciado!")
bot.polling(none_stop=True, timeout=300)
