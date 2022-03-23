import json
import os
import pathlib
import smtplib
import sys
from email.mime.application import MIMEApplication

import telepot
import time
from telepot.loop import MessageLoop
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

__FILEPATH__ = ""
__SETTINGS__ = {}
dfn = "fileCache"


def setup_enviroment():
    try:
        global __FILEPATH__
        __FILEPATH__ = pathlib.Path(__file__).parent.resolve()
        os.chdir(__FILEPATH__)
        os.mkdir(dfn)
    except:
        pass


def load_settings():
    """
    requires the creation of a jsonObject file in the folder containing this python script
    the json must have 4 properties:
    {
    "email": "example@example.exp", # email account from where to send emails
    "password": "password",
    "authorizedUsers": ["TelegramUsername1", "TelegramUsername2"], # telegram names autorized from which a messagge can be redirected
    "targets": ["target1@example.exp", "target2@example.exp"], # email destination where to send the messagges to redirect
    "token": "PutHereYourTelegram'sTokenApi" # your telegram bot token got from BotFather
    }
    """
    try:
        with open(f'{__FILEPATH__}/settings.json', "r") as jsonObject:
            jsonString = ""
            for setting in jsonObject:
                jsonString += setting
            global __SETTINGS__
            __SETTINGS__ = json.loads(jsonString)
    except FileNotFoundError:
        print("Impossibile trovare il file di impostazioni!")
        sys.exit(1)
    except json.decoder.JSONDecodeError:
        print("Errore nella struttura del file settings.json!")
        sys.exit(2)


def setup_email():
    email = smtplib.SMTP("smtp.gmail.com", 587)
    email.ehlo()
    email.starttls()
    email.login(__SETTINGS__["email"], __SETTINGS__["password"])
    return email


def setup_bot():
    try:
        return telepot.Bot(__SETTINGS__["token"])
    except:
        print("Il token fornito non funziona, fornirne uno funzionante!")
        sys.exit(3)


def handle_message(msg):
    user = msg["from"]["id"]
    if msg["from"]["username"] not in __SETTINGS__["authorizedUsers"]:
        bot.sendMessage(user, "Utente non autorizzato!")
        return
    print(msg)
    try:
        document = msg["document"]

        print("INFO: Scarico il file ricevuto.")
        bot.sendMessage(user, "Sto scaricando il file")
        try:
            os.remove(f'{__FILEPATH__}/{dfn}/{document["file_name"]}')
        except:
            pass
        bot.download_file(document["file_id"], f'{__FILEPATH__}/{dfn}/{document["file_name"]}')
        print("INFO: Download terminato.")
        bot.sendMessage(user, "Scaricamento terminato!")

        print("INFO: Iniziato l'inoltro a tutti i destinatari.")
        try:
            email = setup_email()
            attachment = MIMEApplication(open(f'{__FILEPATH__}/{dfn}/{document["file_name"]}', 'rb').read())
            attachment.add_header('Content-Disposition', 'attachment', filename=document["file_name"])
            for destinatario in __SETTINGS__["targets"]:
                print("INFO: Invio a " + destinatario)
                emailMsg = MIMEMultipart()
                emailMsg["Subject"] = document["file_name"]
                emailMsg["From"] = __SETTINGS__["email"]
                emailMsg["To"] = destinatario
                emailMsg.attach(attachment)
                email.sendmail(__SETTINGS__["email"], destinatario, emailMsg.as_string())
                print("INFO: Invio completato a " + destinatario)
                bot.sendMessage(user, "File inviato a " + destinatario + "!")
            os.remove(f'{__FILEPATH__}/{dfn}/{document["file_name"]}')
            email.quit()
            print("INFO: Operazione completata.")
            bot.sendMessage(user, "OK: Operazione completata, controlla tua casella di posta!")
        except BaseException as e:
            print("ERROR: Problema nella configurazione della mail mittente!")
            bot.sendMessage(user, "ERRORE! Chiedi di controllare la configurazione!")
        return
    except KeyError as e:
        print("INFO: Arrivato un messaggio di testo, non lo inoltro agli indirizzi email.")
        bot.sendMessage(user, "Non inoltro i messaggi di testo!")

    pass


if __name__ == '__main__':
    setup_enviroment()
    load_settings()
    email = setup_email()
    bot = setup_bot()
    MessageLoop(bot, handle_message).run_as_thread()
    print('Aspettando richieste ...')
    while 1:
        time.sleep(1000)
