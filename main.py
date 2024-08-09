from threading import Thread
from lo_zozzone import main as m
from la_zozzona import main as ma
from keep_alive import keep_alive

if __name__ == "__main__":
    keep_alive()
    lo_zozzone_bot = Thread(target=m)
    la_zozzona_bot = Thread(target=ma)
    lo_zozzone_bot.start()
    la_zozzona_bot.start()