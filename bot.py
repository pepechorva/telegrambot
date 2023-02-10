#!/usr/bin/env python3.9

import configparser
import io
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
from inspect import currentframe, getframeinfo

import logging

#DEBUGGING
logging.basicConfig(format='%(lineno)d %(message)s', level=logging.DEBUG)


logging.info("Loading config from file...")
config = configparser.ConfigParser()
config.read("/etc/botconfig.ini")

#TELEBOT
myID = config.getint('Telebot', 'myID')

#MQTT
client_id   = config["MQTT"]["client_id"]


salutes = ["hola", "buenos dias", "buenos días", "wenos dias"]
saluteResponses = ["Yep", "Hola", "Muy buenas", "Ah, hola"]
blasphemywords = ['zorra', 'capullo', 'joputa', 'gilipollas', 'mierda', 'gilipo', 'puta ']

def readCommandJsonsFile():
    f = open(config["Paths"]["commandJsonsFile"], "r")
    commandListJson = json.load(f)
    f.close()
    ch = '/'
    commandKeysList = [elem.replace(ch, '') for elem in commandListJson.keys()]
    return commandListJson, commandKeysList

commandList, commandKeys = readCommandJsonsFile()

f = open(config["Paths"]["ignoreUsersFile"], "r")
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
    file1 = open(config["Paths"]["URLsFromChat"], "a")
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
    for url in config["IP"]["getIPList"].split(','):
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
    with open(config["Paths"]["ignoreUsersFile"], "w") as outfile:
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
        connection = ""
        if rc == 0:
            connection = "Connected to MQTT Broker!\n"
        else:
            connection = "Failed to connect, return code " + rc + "\n"
        logging.info(connection)
        print(connection)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(config["MQTT"]["username"], config["MQTT"]["password"])
    client.on_connect = on_connect
    client.connect(config.get("MQTT", "broker"), config.getint("MQTT", "port"))
    return client

def publish(client, msg):
    mqttmsg = jsonpickle.encode(msg)
    result = mqtt_client.publish(config["MQTT"]["topic"], mqttmsg)

def publishToTopic(client, newTopic, msg):
    mqttmsg = jsonpickle.encode(msg)
    result = mqtt_client.publish(config["MQTT"]["topic"] + '/' + newTopic, mqttmsg.encode("utf-8"))


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
            publish(client_id, result)

bot = telebot.TeleBot(config.get("Telebot", "TOKEN"))
bot.set_update_listener(listener) # register listener

# List commands
@bot.message_handler(commands=['list'])
def command_long_text(m):
    cid = m.chat.id
    response = ""
    if not isBlacklistedUser(m):
        response = ', '.join(list(commandList.keys())) + " /ruleta, " + " /ignoramebot, "
    bot.send_message(cid, response + "/hazmecasitobot")

@bot.message_handler(commands=["ignoramebot"])
def blacklistUser(m):
    addUserToBlacklist(m.chat.type, m.chat.id, m.from_user.id)

@bot.message_handler(commands=["hazmecasitobot"])
def whitelistUser(m):
    removeUserFromBlacklist(m.chat.type, m.chat.id, m.from_user.id)

# List commands
@bot.message_handler(commands=['ruleta'])
def command_long_text(m):
    cid = m.chat.id
    if not isBlacklistedUser(m):
        trigger = random.randint(0, 5)
        logging.info("Ruleta, trigger == %d", trigger)
        #logging.info("chat_id = %d, user_id = %d, myID = %d", m.chat.id, m.from_user.id, myID)
        #logging.info(m)
        if trigger < 5:
            bot.send_document(cid, 'https://media.giphy.com/media/s9Y0czwWdTtB7U6d5I/giphy.gif')
        else:
            bot.send_document(cid, 'https://media.giphy.com/media/fe4dDMD2cAU5RfEaCU/giphy.gif')
            bot.send_chat_action(cid, 'typing')
            time.sleep(3)
            bot.send_message(cid, "BANNED!!")
            time.sleep(3)
            try:
                bot.ban_chat_member(m.chat.id, m.from_user.id)
            except:
                bot.send_message(cid, "Emmm... mejor no, que me me baneas tu 😅")





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
        if "sendDocument" in commandList[command]["typeSend"]:
            bot.send_document(cid, commandList[command]["response"])
        elif "sendMessage" in commandList[command]["typeSend"]:
            response = str(commandList[command]["response"])
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
    if not isBlacklistedUser(m):
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
