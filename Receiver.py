from machine import Pin, PWM, SPI
import utime
import struct
from nrf24l01 import NRF24L01


spi = SPI(0, baudrate=4000000, polarity=0, phase=0,
          sck=Pin(6), mosi=Pin(7), miso=Pin(4))
csn = Pin(5, mode=Pin.OUT, value=1)
ce = Pin(3, mode=Pin.OUT, value=0)
radio = NRF24L01(spi, csn, ce, payload_size=16)
radio.open_rx_pipe(1, b'\xe1\xf0\xf0\xf0\xf0')
radio.start_listening()

#turns transmitted values into pwm inputs for servos
def cleanedtopwm(value):
    return 1500 + (value * 500)

def throttletopwm(value):
    return 1000 + (value * 1000)

aileronL = PWM(Pin(2))
aileronL.freq(50)

aileronR = PWM(Pin(8))
aileronR.freq(50)

elevator_servo = PWM(Pin(9))
elevator_servo.freq(50)

rudder_servo = PWM(Pin(10))
rudder_servo.freq(50)

motor = PWM(Pin(11))
motor.freq(50)


last_packet_time = utime.ticks_ms()

while True:

    if radio.any():
        packet = radio.recv()
        aileron, elevator, rudder, throttle = struct.unpack('ffff', packet)
        last_packet_time = utime.ticks_ms()
    
    time_since_last_packet = utime.ticks_ms() - last_packet_time

    if time_since_last_packet > 250:
        aileronL.duty_ns(1500000)
        aileronR.duty_ns(1500000)
        elevator_servo.duty_ns(1500000)
        rudder_servo.duty_ns(1500000)
        motor.duty_ns(1000000)
    else: 
        aileronL.duty_ns(int(cleanedtopwm(aileron) * 1000))
        aileronR.duty_ns(int(cleanedtopwm(-aileron) * 1000))
        elevator_servo.duty_ns(int(cleanedtopwm(elevator)*1000))
        rudder_servo.duty_ns(int(cleanedtopwm(rudder) * 1000))
        motor.duty_ns(int(throttletopwm(throttle) * 1000))

    utime.sleep_ms(20)

