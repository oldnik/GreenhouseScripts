import time
import datetime
import MySQLdb
import bh
import ds18b20 as temperatures
import DHT as dht
import gleba as soil 
import RPi.GPIO as GPIO
from multiprocessing import Process, Pool
import os


'''_____________________USTAWIENIA GPIO_____________________'''

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(0)

#OSWIETLENIE
GPIO.setup(37, GPIO.OUT)
GPIO.output(37, GPIO.HIGH)
GPIO.setup(35, GPIO.OUT)
GPIO.output(35, GPIO.HIGH)
GPIO.setup(33, GPIO.OUT)
GPIO.output(33, GPIO.HIGH)
GPIO.setup(31, GPIO.OUT)
GPIO.output(31, GPIO.HIGH)


#WENTYLATORY
GPIO.setup(32, GPIO.OUT)
went = GPIO.PWM(32, 50)
went.start(0)

#SERWOMECHANIZM
GPIO.setup(12, GPIO.OUT)
serwo = GPIO.PWM(12, 50)
serwo.start(0)

#GRZALKA

GPIO.setup(38, GPIO.OUT)
GPIO.output(38, GPIO.HIGH)


#POMPA

GPIO.setup(36, GPIO.OUT)
GPIO.output(36, GPIO.HIGH)

'''___________________________________________________________'''

lightDictionary = {
    650 : [1],
    880 : [4],
    1000: [3],
    1060: [2],
    1460: [1,4],
    1620: [1,2],
    1650: [2,4],
    1690: [1,3],
    1750: [3,4],
    1850: [2,3],
    2350: [1,2,4],
    2380: [2,3,4],
    2500: [1,3,4],
    2600: [1,2,3],
    3500: [1,2,3,4]
    }

bulb = [False] * 4
    

#daneList = []
#sterowanieList = []
#ustawieniaList = []
    
    
def selectAll(name):
    db = MySQLdb.connect(host="127.0.0.1", user="szklarnia123", passwd="qwe123", db="szklarnia")
    cur = db.cursor()
    sql = "SELECT * FROM %s" %(name)
    cur.execute(sql)
    data = cur.fetchone()
    db.close()
    return data
    
    
def select(sql):
    db = MySQLdb.connect(host="127.0.0.1", user="szklarnia123", passwd="qwe123", db="szklarnia")
    cur = db.cursor()
    cur.execute(sql)
    data = cur.fetchone()
    db.close()
    return data


def getColumnName(tableName):
    db = MySQLdb.connect(host="127.0.0.1", user="szklarnia123", passwd="qwe123", db="szklarnia")
    temp = []
    columnNames = []
    cur = db.cursor()
    sql = "SELECT column_name FROM information_schema.columns WHERE table_schema = 'szklarnia' AND table_name = '%s';" %(tableName)
    cur.execute(sql)
    temp = cur.fetchall()
    for v in temp:
        columnNames.append(v[0])
    db.close()
    return columnNames


def getTypeString(variable):
    if isinstance(variable, int):
        return 'd'
    elif isinstance(variable, float):
        return 'f'
    elif isinstance(variable, str):
        return 's'
    else:
        return 0


def updateParams(fromTable, toTable):
    db = MySQLdb.connect(host="127.0.0.1", user="szklarnia123", passwd="qwe123", db="szklarnia")
    cur = db.cursor()
    sql = "UPDATE %s SET " %(toTable)
    fromTableDict = dict(zip(getColumnName(fromTable), selectAll(fromTable)))
    toTableDict = dict(zip(getColumnName(toTable), selectAll(toTable)))
    for key, value in toTableDict.items():
        for k ,v in fromTableDict.items():
            if key == k:
                toTableDict[key] = fromTableDict[k]
    for k, v in toTableDict.items():
        sql += "%s = " %(k)
        sql += str(v) + ", "
    sql = sql[:-2]
    cur.execute(sql)
    db.commit()
    db.close()
    

def updateReadings():
    
    db = MySQLdb.connect(host="localhost", user="szklarnia123", passwd="qwe123", db="szklarnia")
    cur = db.cursor()
    tempList = temperatures.getReadings()
    dhtList = dht.getReadings()
    bhList = bh.getReadings()
    soilList = soil.getReadings()
    sql = "UPDATE biezace_parametry SET a_temp = %f, b_temp = %f, c_temp = %f, d_temp = %f, d_wilg = %d, e_wilg_gleba = %d, f_swiatlo = %d, g_swiatlo = %d" %(float(tempList[2]), float(tempList[0]), float(tempList[1]), float(dhtList[1]), int(dhtList[0]), int(soilList), int(bhList[1]), int(bhList[0]))
    cur.execute(sql)
    db.commit()
    db.close()
    print("Readings Updated")



def setDevices(gpioSet):
    if(gpioSet[10] == 0):
        GPIO.output(37, GPIO.HIGH)
    elif(gpioSet[10] == 1):
        GPIO.output(37, GPIO.LOW)
    if(gpioSet[11] == 0):
        GPIO.output(35, GPIO.HIGH)
    elif(gpioSet[11] == 1):
        GPIO.output(35, GPIO.LOW)
    if(gpioSet[12] == 0):
        GPIO.output(33, GPIO.HIGH)
    elif(gpioSet[12] == 1):
        GPIO.output(33, GPIO.LOW)
    if(gpioSet[13] == 0):
        GPIO.output(31, GPIO.HIGH)
    elif(gpioSet[13] == 1):
        GPIO.output(31, GPIO.LOW)
    if(gpioSet[14] == 0):
        GPIO.output(38, GPIO.HIGH)
    elif(gpioSet[14] == 1):
        GPIO.output(38, GPIO.LOW)
    if(gpioSet[15] == 0):
        GPIO.output(36, GPIO.HIGH)
    elif(gpioSet[15] == 1):
        GPIO.output(36, GPIO.LOW)
    if(gpioSet[8]>30 and gpioSet[8]<=100):
        went.ChangeDutyCycle(gpioSet[8])
    else:
        went.ChangeDutyCycle(0)
    time.sleep(0.5)


def setSerwo(gpioSet):

    if(gpioSet == 1):
        print("Serwo open")
        serwo.ChangeDutyCycle(12.5)
    elif(gpioSet == 0):
        print("Serwo close")
        serwo.ChangeDutyCycle(2.5)

    
def openSerwo():
    autoUpdate("serwo", 1)
    serwo.ChangeDutyCycle(12.5)
    time.sleep(8)


def closeSerwo():
    autoUpdate("serwo", 0)
    serwo.ChangeDutyCycle(2.5)
    time.sleep(8)
    

def autoUpdate(columnName, value):
    db = MySQLdb.connect(host="127.0.0.1", user="szklarnia123", passwd="qwe123", db="szklarnia")
    cur = db.cursor()
    sql = "UPDATE biezace_parametry SET %s = %d" %(str(columnName), int(value))
    cur.execute(sql)
    db.commit()
    db.close()
    
    
def saveToHistory(period):
    lastHistorySaving = select("SELECT * FROM historia_pomiarow ORDER BY id DESC LIMIT 1")[9]
    now = datetime.datetime.now()
    delta = now - lastHistorySaving
    if(delta.total_seconds() >= period):
        print("Saving to history")
        data = selectAll("biezace_parametry")
        db = MySQLdb.connect(host="127.0.0.1", user="szklarnia123", passwd="qwe123", db="szklarnia")
        cur = db.cursor()
        now = datetime.datetime.now()
        sql = "INSERT INTO historia_pomiarow (a_temp, b_temp, c_temp, d_temp, d_wilg, e_gleba_wilg, f_swiatlo, g_swiatlo, data_pomiaru) VALUES (%f, %f, %f, %f, %d, %d, %d, %d, '%s')" %(float(data[0]), float(data[1]), float(data[2]), float(data[3]), int(data[4]), int(data[5]), int(data[6]), int(data[7]), now)    
        cur.execute(sql)
        db.commit()
        db.close()
        
        
def lightCheck(light, bulb):
    bulbList = lightDictionary.get(light, lightDictionary[min(lightDictionary.keys(), key = lambda k:abs(k-light))])
    if 1 in bulbList and bulb[0] == False:
        autoUpdate("zarowka1", 1)
        bulb1 = True
    elif 1 not in bulbList and bulb[0] == True:
        autoUpdate("zarowka1", 0)
        bulb1 = False
    if 2 in bulbList and bulb[1] == False:
        autoUpdate("zarowka2", 1)
        bulb2 = True
    elif 2 not in bulbList and bulb[1] == True:
        autoUpdate("zarowka2", 0)
        bulb2 = False
    if 3 in bulbList and bulb[2] == False:
        autoUpdate("zarowka3", 1)
        bulb3 = True
    elif 3 not in bulbList and bulb[2] == True:
        autoUpdate("zarowka3", 0)
        bulb3 = False
    if 4 in bulbList and bulb[3] == False:
        autoUpdate("zarowka4", 1)
        bulb4 = True
    elif 4 not in bulbList and bulb[3] == True:
        autoUpdate("zarowka4", 0)
        bulb4 = False
    return bulb
    
def lightOff(bulb):
    autoUpdate("zarowka1", 0)
    autoUpdate("zarowka2", 0)
    autoUpdate("zarowka3", 0)
    autoUpdate("zarowka4", 0)
    for i in bulb:
        bulb[i] = False
    print bulb
 
    
def main():
    
    heaterOn = False
    histereza = 0.3
    margin = 10
    
    while True:
        
        tryb = selectAll("ustawienia")
        serwo.start(0)
        lastSerwoParam = selectAll("biezace_parametry")[9]
        
        #GLOWNA PETLA TRYBU MANUALNEGO
        
        while(tryb[0] == '0' or tryb[0] == 'm'):
            print("TRYB MANUALNY")
            saveToHistory(tryb[1])
            updateParams("manual", "biezace_parametry")
            gpioSet = selectAll("biezace_parametry")
            updateReadings()
            if(lastSerwoParam != gpioSet[9]):
                setSerwo(gpioSet[9])
                lastSerwoParam = gpioSet[9]
            print(selectAll("biezace_parametry"))
            setDevices(gpioSet)
            tryb = selectAll("ustawienia")
        
        #GLOWNA PETLA TRYBU AUTOMATYCZNEGO 
            
        while(tryb[0] == '1' or tryb[0] == 'a'):
            print("TRYB AUTOMATYCZNY")
            
            saveToHistory(tryb[1])
            updateReadings()
            sensorReadings = selectAll("biezace_parametry")
            settings = selectAll("auto")
            t = datetime.datetime.now()
            temperature = settings[0] 
            humidity = settings[1] #skrypt dazy do uzyskania zadanego parametru dla wilgotnosci
            light = settings[2] #skrypt dazy do uzyskania zadanego parametru dla swiatla
            lightMode = settings[3] #tryb doswietlania
            lightOutside = settings[4] #
            lightFromHour = settings[5] #
            lightToHour = settings[6] #
            soilHumidity = settings[7] # wartosc do ktorej dazy skrypt dla wilgotnosci gleby
            waterFromHour = settings[8] #godzina od ktorej moze pracowac pompa wody
            waterToHour = settings[9] #godzina do ktorej moze pracowac pompa wody
            
            #STEROWANIE TEMPERATURA PRZY POMOCY GRZALKI
            
            tempAverage = (sensorReadings[0] + sensorReadings[1])/2
            if(tempAverage <= temperature - histereza and heaterOn == False):
                autoUpdate("grzalka", 1)
                heaterOn = True
                print("heater ON")
            if(tempAverage >= temperature + histereza and heaterOn == True):
                autoUpdate("grzalka", 0)
                print("heater OFF")
                heaterOn = False
            
            print(sensorReadings[7], lightOutside, lightMode)
            
            if lightMode == 0:
                lightCheck(light, bulb)
            if lightMode == 1:
                if(sensorReadings[7] < lightOutside):
                    lightCheck(light, bulb)
                else:
                    lightOff(bulb)
            if lightMode == 2:
                if(lightFromHour <= t.hour <= lightToHour):
                    lightCheck(light, bulb)
                else:
                    lightOff(bulb)
            
            #STEROWANIE WILGOTNOSCIA POWIETRZA
            
            if(humidity > sensorReadings[4] + margin):
                closeSerwo()
                autoUpdate("went", 0)
                went.ChangeDutyCycle(0)
                time.sleep(0.5)
            elif(humidity < sensorReadings[4] - margin):
                openSerwo()
                autoUpdate("went", 100)
                went.ChangeDutyCycle(100)
                time.sleep(0.5)
            
            #STEROWANIE NAWODNIENIEM GLEBY PRZY POMOCY POMPY    
                
            if(soilHumidity > sensorReadings[5] and (waterFromHour <= t.hour <= waterToHour)):
                autoUpdate("pompa", 1)
                gpioSet = selectAll("biezace_parametry")
                setDevices(gpioSet)
                time.sleep(7)
                autoUpdate("pompa", 0)
                gpioSet = selectAll("biezace_parametry")
                setDevices(gpioSet)
                
            gpioSet = selectAll("biezace_parametry")
            setDevices(gpioSet)

            tryb = selectAll("ustawienia")
        
main()
    
    
