import smbus
from time import sleep
import sqlite3
from datetime import datetime


bus = smbus.SMBus(1)
i2c_address = 0x4B


def soil():
    rd = bus.read_word_data(i2c_address, 0)
    data = ((rd & 0xFF) << 8) | ((rd & 0xFF00) >> 8)
    data = data >> 2
    wet_x1 = 330
    dry_x2 = 740
    y1 = 0
    y2 = 100
    a = (y2-y1) / (wet_x1-dry_x2)
    b = y1 - (a * dry_x2)
    procent = a * data + b  #f(y) = ax+b
    if procent > 100:
        procent = 100
    if procent < 0:
        procent = 0
    return data, procent

while True:
    #data, procent = soil()
    rd = bus.read_word_data(i2c_address, 0)
    data = ((rd & 0xFF) << 8) | ((rd & 0xFF00) >> 8)
    data = data >> 2
    wet_x1 = 330
    dry_x2 = 740
    y1 = 0
    y2 = 100
    a = (y2-y1) / (wet_x1-dry_x2)
    b = y1 - (a * dry_x2)
    procent = a * data + b  #f(y) = ax+b
    if procent > 100:
        procent = 100
    if procent < 0:
        procent = 0
    print("Raw_Data: ", data)
    print(int(procent), "%")
    sleep(1)
#330 wet - 780 dry air /700 dry cloth - dry 740

def SQL_insert():
    date_time = datetime.now()
    timestamp = f"{date_time.strftime('%d-%m-%Y-%H:%M:%S')}"
    con = sqlite3.connect('greenhouse.db')
    curr = con.cursor()
    procent = soil()
    moisture_percentage = procent
    params = (timestamp, moisture_percentage)
    sql = """INSERT INTO Soilmoisture (timestamp, moisture_percentage) VALUES(?,?)"""
    curr.execute(sql, params)
    print("Saved data")
    con.commit()
    con.close()




    


