from machine import ADC, Pin, SPI
import utime
import struct
from nrf24l01 import NRF24L01 


spi = SPI(0, baudrate=4000000, polarity=0, phase=0,
          sck=Pin(6), mosi=Pin(7), miso=Pin(4))
csn = Pin(5, mode=Pin.OUT, value=1)
ce = Pin(3, mode=Pin.OUT, value=0)
radio = NRF24L01(spi, csn, ce, payload_size=16)
radio.open_tx_pipe(b'\xe1\xf0\xf0\xf0\xf0')


#maps each axis to a pin on the microcontroller, ADC reads values
# throttle via ADS1115 on I2C - to be implemented with hardware
roll = ADC(Pin(26))
pitch = ADC(Pin(27))
yaw = ADC(Pin(28))
throttle_raw = 0  # placeholder until ADS1115 is wired


#converts the ADC values into values between -1 and 1
def normalize(raw):
    result = (raw / 32767.5) - 1.0  
    return result


#converts throttle ADC to values between 0 and 1
def normalize_throttle(raw):
    result = raw / 65535
    return result


#gets rid of small imperfections in readings    
def deadband(value, threshold):
    if abs(value) < threshold:
        return 0.0
    return value


#makes response less sensitive when close to the center
def expo(value, amount):
    return value**3 * amount + value * (1-amount)





#read and printed adjusted values from controller
while True:
    valueroll = roll.read_u16()
    valuepitch = pitch.read_u16()
    valueyaw = yaw.read_u16()
    
    normalizedroll = normalize(valueroll)
    normalizedpitch = normalize(valuepitch)  
    normalizedyaw = normalize(valueyaw)
    normalizedthrottle = normalize_throttle(throttle_raw)

    cleanedroll = deadband(normalizedroll, 0.05)
    cleanedpitch = deadband(normalizedpitch, 0.05)
    cleanedyaw = deadband(normalizedyaw, 0.05)
    cleanedthrottle = deadband(normalizedthrottle, 0.02)

    exporoll = expo(cleanedroll, 0.5)
    expopitch = expo(cleanedpitch, 0.5)
    expoyaw = expo(cleanedyaw, 0.5)

    #mixes some rudder input into ailerons to automatically roll while turning
    aileron_mixed = max(-1.0, min(1.0, exporoll + (expoyaw * 0.3)))

    packet = struct.pack('ffff', aileron_mixed, expopitch, expoyaw, cleanedthrottle)

    radio.send(packet)

    print(aileron_mixed, expopitch, expoyaw, cleanedthrottle)
    utime.sleep_ms(20)
