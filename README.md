# telegrambot

Bot de Telegram que responde gifs a determinados comandos dados en un JSON montado como "comando:gif" para facilitar su posible ampliación y mantenimiento. También responde a comandos de texto


Para instalar este bot necesitarás instalar previamente:
```
sudo python3 -m pip install telebot
sudo python3 -m pip install jsonpickle
sudo python3 -m pip install paho-mqtt
```

Además de configurar un archivo en /etc/botconfig.ini con tus datos:
```
[Telebot]
TOKEN=TU_TOKEN
myID=tu_ID_de_Telegram
knownUsers=[tu_ID_de_Telegram]

[Paths]
commandJsonsFile=path_de_commands.json
ignoreUsersFile=path_de_ignoreUsers.json
URLsFromChat=path_de_urlsfromchat.txt

[IP]
getIPList= https://icanhazip.com,https://ifconfig.me,https://api.ipify.org,https://bot.whatismyipaddress.com,https://ipinfo.io/ip,https://i>


[MQTT]
host=localhost
broker=localhost
port=1883
topic=telegram/bot
; generate client ID with pub prefix randomly
client_id= f'python-mqtt-{random.randint(0, 1000)}'
username= ''
password= ''
```





También puedes crearte un servicio (daemon) en /lib/systemd/system/tubot.service:
```
[Unit]
Description=Bot Service
After=multi-user.target

[Service]
Type=idle
ExecStart=/usr/bin/python path_a_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Y arrancarlo con:
systemclt enable tubot.service
systemctl start tubot.service