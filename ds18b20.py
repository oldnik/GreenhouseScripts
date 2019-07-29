import os
import time

FILE_PATH = '/sys/bus/w1/devices/'
SENSOR_NAMES = os.listdir(FILE_PATH)[1:]

def tempRaw(sensors = SENSOR_NAMES):
    lines = []
    for s in sensors:
        f = open(FILE_PATH + s + '/w1_slave', 'r')
        lines.append(f.readlines())
        f.close()
    return lines

def getReadings():
    lines = tempRaw()
    temperatures = []
    for l in lines:
        if(l[0][:-3] != 'YES'):
            index = l[1].find('t=')
            if index != -1:
                temperatures.append(float(l[1].strip()[index+2:])/1000)
    return temperatures
