import win32api
import os
from datetime import datetime

drives = win32api.GetLogicalDriveStrings()
drives = drives.split('\000')[:-1]
print(drives)

for drive in drives:
    print(drive)
    for dir in os.listdir(drive):
        if os.path.isdir(os.path.join(drive, dir)):
            if str(datetime.now().year) in dir:
                print(dir)
