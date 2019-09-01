import json
import ask_lex

# Credentials.json contains account/bot information
with open('credentials.json', 'r') as config_file:
    bot_credentials = json.load(config_file) 

while True:
    message = input()
    if (message.lower() == 'done'):
        break
    print(ask_lex.ask_lex(message, bot_credentials)[1])
