import time
from machine import Pin
from machine import ADC, PWM
import mq135
import umail
import network
import esp
import socket
esp.osdebug(None)

import gc
gc.collect()

ssid = 'Honor 50+'
password = '12345678'
air_quality = 0
sendmail=0
humedad=0
green_led_pin = Pin(18, Pin.OUT)  # El LED verde será una salida del ESP32
red_led_pin = Pin(19, Pin.OUT)  # El LED rojo será una salida del ESP32
gas_sensor_pin = Pin(34, Pin.IN)  # El sensor de gas será una entrada del ESP32



green_led_pin.on()
red_led_pin.on()

#Detalles del correo
sender_email = 'senderesp07@gmail.com'
sender_name = 'ESP32' #sender name
sender_app_password = 'fxrymdbxdeqyutxd'
recipient_email ='juan_agudelo82201@elpoli.edu.co'
email_subject ='Hola desde ESP32 los niveles son alarmados'

def get_air_quality():
    adc = ADC(Pin(34))
    adc.atten(ADC.ATTN_11DB)
    adc_width = 4095
    adc_value = adc.read()
    voltage = adc_value / adc_width * 3.3
    return voltage

def read_humidity():
    adc = ADC(Pin(35)) # Conecta el pin analógico del sensor FC-28 al pin ADC adecuado
    adc.atten(ADC.ATTN_11DB)
    value = adc.read()
    voltage = value / 4095 * 3.3  # Ajusta el valor máximo de ADC (4095) y la tensión de referencia (3.3)
    humidity = (voltage - 0.88) / 0.032  # Ajusta los valores de compensación del sensor según la especificación del FC-28
    return humidity

def connect_wifi(ssid, password):
  #Connect to your network
  station = network.WLAN(network.STA_IF)
  station.active(True)
  station.connect(ssid, password)
  while station.isconnected() == False:
    pass
  print('Connection successful')
  print(station.ifconfig())

connect_wifi(ssid, password)
humedad=100-read_humidity()
def web_page():

    html = """<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" href="data:,"><style>body { text-align: center; font-family: "Trebuchet MS", Arial;}
    table { border-collapse: collapse; width:35%; margin-left:auto; margin-right:auto; }
    th { padding: 12px; background-color: #0043af; color: white; }
    tr { border: 1px solid #ddd; padding: 12px; }
    tr:hover { background-color: #bcbcbc; }
    td { border: none; padding: 12px; }
    .sensor { color:white; font-weight: bold; background-color: #bcbcbc; padding: 1px;
    </style></head><body><h1>Control Agricola ESP32</h1>
    <table><tr><th>MEDIDAS</th><th>VALUE</th></tr>
    <tr><td>Humedad</td><td><span class="sensor">""" + str(humedad) + "%"+"""</span></td></tr>
    <tr><td>Contaminacion</td><td><span class="sensor">""" + str(air_quality) + "PPU"+"""</span></td></tr></body></html>"""
    return html

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(2)

for i in range(60):
    air_quality = get_air_quality()*1000
    humedad=100-read_humidity()

    if air_quality == 3300 :
        air_quality=0
        print("Calidad del aire:  0 PPU")
    else :
        print("Calidad del aire:", air_quality, "PPU")

    print("Humedad relativa: ", humedad,"%")

    if air_quality > 800 and air_quality!= 3300 or humedad<25 or humedad >90:
        red_led_pin.on()  # El LED rojo está ENCENDIDO
        green_led_pin.off()  # El LED verde está APAGADO
        time.sleep(1)
        sendmail=sendmail+1
        if sendmail==2 :
            # Send the email
            smtp = umail.SMTP('smtp.gmail.com', 465, ssl=True) # Gmail's SSL port
            smtp.login(sender_email, sender_app_password)
            smtp.to(recipient_email)
            smtp.write("From:" + sender_name + "<"+ sender_email+">\n")
            smtp.write("Subject:" + email_subject + "\n")
            smtp.write("Niveles alarmantes, requiere de tu intervención")
            smtp.send()
            smtp.quit()
            print("Email enviado")
    elif 600 <= air_quality <= 800 and air_quality!= 3300  or 40<= humedad >60:

        red_led_pin.off()  # El LED rojo está ENCENDIDO
        green_led_pin.on()  # El LED verde está APAGADO
        time.sleep(1)


    elif air_quality < 600 or air_quality == 3300 or 40<= humedad <=60:

        green_led_pin.on()  # El LED verde está ENCENDIDO
        red_led_pin.off()  # El LED rojo está APAGADO
    
    try:
        if gc.mem_free() < 102000:
            gc.collect()
        conn, addr = s.accept()
        conn.settimeout(3.0)
        print('Got a connection from %s' % str(addr))
        request = conn.recv(1024)
        conn.settimeout(None)
        request = str(request)
        print('Content = %s' % request)
        response = web_page()
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.sendall(response)
        conn.close()
    except OSError as e:
        conn.close()
        print('Connection closed')
    
#By_Juan_Camilo_Agudelo_and_Eric_Joan_Angulo