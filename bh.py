import smbus
import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(0)
GPIO.setup(15,GPIO.OUT)
GPIO.output(15, GPIO.HIGH)

DEVICES     = [0x23, 0x5C] # Default device I2C address
convertedData = []

bus = smbus.SMBus(1)

def convertToNumber(data):
  result=(data[1] + (256 * data[0])) / 1.2
  return (result)

def getReadings(addr=DEVICES):
    convertedData[:] = []
    for a in addr:
        data = bus.read_i2c_block_data(a, 0x20)
        convertedData.append(round(convertToNumber(data),2))
    return (convertedData)