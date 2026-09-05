import os
import sys
from time import sleep

# usato quando Discord blocca i bot per rate limit: aspetta e riavvia main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sleep(20)
os.system(f'"{sys.executable}" "{os.path.join(BASE_DIR, "main.py")}"')
sys.exit(0)
