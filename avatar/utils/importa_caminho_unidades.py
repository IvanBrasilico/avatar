import sys
import os
from datetime import datetime

if sys.platform == 'win32':
    import win32api
    drives = win32api.GetLogicalDriveStrings()
    drives = drives.split('\000')[:-1]
else:
    drives = []

for drive in drives:
    print(drive)
    for dir in os.listdir(drive):
        if os.path.isdir(os.path.join(drive, dir)):
            if str(datetime.now().year) in dir:
                print(dir)
