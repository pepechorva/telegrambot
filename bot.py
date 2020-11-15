#! /usr/bin/python3

#https://maker.pro/raspberry-pi/projects/how-to-create-a-telegram-bot-with-a-raspberry-pi
#bot de telegram que responde gifs a determinados comandos dados en un JSON montado como comando:gif
#para facilitar su posible ampliación/mantenimiento
#
#también responde a comandos de texto


import os
from subprocess import call
import urllib
import requests
import datetime  # Importing the datetime library
import telepot   # Importing the telepot library
from telepot.loop import MessageLoop  # Library function to communicate with telegram bot
from time import sleep    # Importing the time library to provide the delays in program

# Insert your telegram token below
TOKEN = 'TOKEN'
MYGROUP = 00000000
BOTNAME = 'botname'



urls = {
 "/lodije":"http://i.giphy.com/13IC4LVeP5NGNi.gif",
 "/zasca":"https://media.giphy.com/media/JrMgGbXmucW6ccgave/giphy.gif",
  "/blablabla":"https://media.giphy.com/media/NgNSBCBwIELDi/giphy.gif",
 "/bliblibli":"https://media.giphy.com/media/3o6UB2MSoh7z6Gw3fO/giphy.gif",
 "/jijiji":"https://media.giphy.com/media/XEIfzDne3lA2sY9qyR/giphy.gif",
 "/osquiero":"https://media.giphy.com/media/2dQ3FMaMFccpi/giphy.gif",
 "/excusas":"https://media.giphy.com/media/szlSwLwiXBEeQ/giphy.gif",
 "/byebye":"http://giphygifs.s3.amazonaws.com/media/GB7AfEnRyAPcI/giphy.gif",
 "/din":"https://media.giphy.com/media/j06A7M6HlkFPO/giphy.gif",
 "/don":"https://media.giphy.com/media/sHV6YMsVFTQD6/giphy.gif",
 "/amen":"https://media.giphy.com/media/doUu2ByZDbPYQ/giphy.gif",
 "/hide":"http://giphygifs.s3.amazonaws.com/media/jUwpNzg9IcyrK/giphy.gif",
 "/patxaran":"https://media1.tenor.com/images/4656f258352e28f023d7109c3135c90f/tenor.gif?itemid=11817205",
 "/queosfollen":"https://media.giphy.com/media/143cE5FtVmKrNC/giphy.gif",
 "/dindindin":"https://media.giphy.com/media/j06A7M6HlkFPO/giphy.gif",
 "/fail":"http://giphygifs.s3.amazonaws.com/media/li0dswKqIZNpm/giphy.gif",
 "/carajillo":"https://cookpad.com/es/recetas/2123613-carajillo-de-3-colorets-de-castellon",
 "/chof":"https://media.giphy.com/media/KHJw9NRFDMom487qyo/giphy.gif",
 "/epicfail":"https://media.giphy.com/media/FewMZauWeGB0IpNpVO/giphy.gif",
 }

messages = {
 "/hi":"Jelouuu!!",
 "/bye":"chauuu!!",
 }

def handle(msg):
	chat_id = msg['chat']['id'] # Receiving the message from telegram
	command = msg['text']   # Getting text from the message
	now = datetime.datetime.now() # Getting date and time
	print ('Received: ', command, " in ", chat_id)
	command2 = command
	if "@"+BOTNAME in command:
		aux = command.split('@', 1 )
		command = aux[0]
	# Comparing the incoming message to send a reply according to it
	if command in urls.keys():
		bot.sendDocument(chat_id, urls[command])
	elif command in messages.keys():
		bot.sendMessage(chat_id, str(messages[command]))
	elif command == '/List' or command == '/list':
		lista = ["/List"]
		lista.extend(list(messages.keys()))
		lista.extend(list(urls.keys()))
		bot.sendMessage(chat_id, str(lista))
	elif command == '/ip' or command == '/IP':
		ip = urllib.request.urlopen('https://api.ipify.org').read() # esta URL puede ser reemplazada con otra que preste similar servicio
		bot.sendMessage(MYGROUP, str(ip, 'utf-8'))
bot = telepot.Bot(TOKEN)
bot.deleteWebhook()
print (bot.getMe())

# Start listening to the telegram bot and whenever a message is  received, the handle function will be called.
MessageLoop(bot, handle).run_as_thread()
print ('Listening....')
while 1:
	sleep(10)
