from flask import Flask
from threading import Thread
import requests
import time

app = Flask('')


@app.route('/')
def home():
    return "Hello. I am alive!"


def server():
    app.run(host='0.0.0.0', port=8080)


def client():
    while True:
        url = 'http://0.0.0.0:8080'
        try:
            response = requests.get(url)
            # if response.status_code == 200:
            #     print("Richiesta eseguita con successo!")
            #     print("Contenuto della risposta:", response.text)
            # else:
            #     print(
            #         "Si è verificato un problema durante la richiesta. Codice di stato:",
            #         response.status_code)
        except requests.exceptions.RequestException as e:
            print("Si è verificato un errore durante la richiesta:", e)
        time.sleep(300)


def keep_alive():
    t1 = Thread(target=server)
    t1.start()
    t2 = Thread(target=client)
    t2.start()
