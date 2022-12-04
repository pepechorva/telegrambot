#!/usr/bin/env python3.9

from config import *
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
import datetime
import unicodedata

saluteList = ["hola", "buenos dias", "buenos días", "wenos dias"]
saluteResponse = ["Yep", "Hola", "Muy buenas", "Ah, hola"]
blasphemywords = ['zorra', 'capullo', 'joputa', 'gilipollas', 'mierda', 'gilipo']

f = open('commands.json')
commandList = json.load(f)
f.close()
ch = '/'
commandKeys = [elem.replace(ch, '') for elem in commandList.keys()]


def user_call(m):
    name = None
    if m.from_user.username is not None:
        name = m.from_user.username
    elif m.from_user.first_name is not None:
        name = m.from_user.first_name
    return name

def storeURL(m):
    file1 = open("urlsfromchat.txt", "a")
    data=m.text
    string_utf = data.encode()
    result = ""
    if(m.chat.type == 'private'):
        result = user_call(m) + " [" + user_call(m) + "]: " + str(string_utf, 'utf-8')
    else:
        result = user_call(m) + " [" + str(m.chat.title.encode(), 'utf-8') + "]: " + str(string_utf, 'utf-8')
    file1.write(result)
    file1.write("\n")
    file1.close()

def string_found(string1, string2):
    string1 = " " + string1.strip() + " "
    string2 = " " + string2.strip() + " "
    return string2.find(string1)

def getUrl():
    f = os.popen('curl https://api.ipify.org')
    return f.read()

def isBlacklistedUser(m):
    #TODO
    if m.chat.type == 'group' or m.chat.type == 'supergroup':
        print("group: ", m.chat.type, " = ", m.chat.id)
        return False #testing
        if any(word in message.text.lower() for word in ignoredUserList):
            return True
    return False



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
    if not isBlacklistedUser(m):
        cid = m.chat.id
        bot.send_message(cid, str(list(commandList.keys())))

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
        if "sendDocument" in commandList[command]["typeSend"]:
            bot.send_document(cid, commandList[command]["response"])
        elif "sendMessage" in commandList[command]["typeSend"]:
            response = str(commandList[command]["response"])
            print(response)
            bot.send_message(cid, response)
            publish(client_id, response)

# Send RaspBerry public IP to mi priate chat
@bot.message_handler(commands=['ip'])
def command_help(m):
    if not isBlacklistedUser(m):
        bot.send_message(myID, "IP: "+ getUrl())

def extract_arg(arg):
    argument = arg.split()[1:]
    argumentstring = ' '.join(argument)
    return argumentstring

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
        else:
            time.sleep(2)
            bot.send_message(cid, "JA!!!")
            bot.send_chat_action(cid, 'typing')
            time.sleep(1)
            bot.send_message(cid, "tus ganas locas")
            bot.send_chat_action(cid, 'typing')
            time.sleep(3)
            bot.reply_to(m, "🖕")

@bot.message_handler(func=lambda message: "buenas noches" in message.text.lower())
def command_text_goodnight(m):
    if not isBlacklistedUser(m):
        bot.send_message(m.chat.id, "Buenas noches, @" + user_call(m))

@bot.message_handler(func=lambda message: any(salute in message.text.lower() for salute in saluteList))
def command_text_salute(m):
    if not isBlacklistedUser(m):
        bot.reply_to(m, random.choice(saluteResponse) + ", @" + user_call(m))

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

bot.send_message(myID, "Bot iniciado en IP: "+getUrl())
bot.polling(none_stop=True, timeout=300)
