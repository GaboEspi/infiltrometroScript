"""
#   
#
    pin 40    led de avisos varios
    pin 37    boton 
    
#
"""

import RPi.GPIO as GPIO
from datetime import datetime, timedelta
import time
import serial
import subprocess
import threading

#################################################################
#                           Settings   
#################################################################
ser = serial.Serial('/dev/ttyS0',
                    baudrate=115200,
                    bytesize=8,
                    parity='N',
                    stopbits=1)

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
PIN_BOTON = 35
PIN_LED = 40
GPIO.setup(PIN_BOTON, GPIO.IN)
GPIO.setup(PIN_LED, GPIO.OUT)

###################################################
#      verificar usb
###################################################
def verificarUsb():
    estadoLed = True
    while True:
        comando = subprocess.run(['ls /media/pi'], stdout=subprocess.PIPE, shell=True)
        print (comando.stdout)
        if str(comando.stdout) == "b''":
            print("usb no insertada")
            GPIO.output(PIN_LED, estadoLed)
            estadoLed = not estadoLed
            time.sleep(0.5)
        else:
            rutaUSB = "/media/pi/"+str(comando.stdout)[2:len(str(comando.stdout))-3]
            print(rutaUSB)
            GPIO.output(PIN_LED, False)
            return rutaUSB
        
#             guardarArchivo(rutaUSB, "archivo.txt")
            
#################################################################
                #nombre prueba Hora GSM
#################################################33
def nombrePruebaHoraGsm():
    ser.write(b'AT+cclk?\r\n')
    
    while True:
        hora = ser.readline()
        horaSTR=""
        
        if(hora.decode() != ''):            
            if hora.decode()[0:6] == '+CCLK:':
                horaSTR=hora.decode()
                horaSTR=horaSTR[8:25]
                horaSTR="prueba_"+horaSTR[6:8]+"-"+horaSTR[3:5]+"-20"+horaSTR[0:2]+"_"+horaSTR[9:11]+"-"+horaSTR[12:14]
                return horaSTR
            
#################################################################
#     toma de dato

def tomaDato():
    distance = -1
    try:
        GPIO.output(PIN_LED, True)
        PIN_TRIGGER = 7
        PIN_ECHO = 11

        GPIO.setup(PIN_TRIGGER, GPIO.OUT)
        GPIO.setup(PIN_ECHO, GPIO.IN)

        GPIO.output(PIN_TRIGGER, GPIO.LOW)  
        print ("Waiting for sensor to settle")
        time.sleep(0.1)
        print ("Calculating distance")
        GPIO.output(PIN_TRIGGER, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(PIN_TRIGGER, GPIO.LOW)

        timeError = time.time()
        while GPIO.input(PIN_ECHO)==0:
            pulse_start_time = time.time()
            if time.time()-timeError >0.2:
                print("Error en la toma de distancia: t>0.2\n")
                return -1
        while GPIO.input(PIN_ECHO)==1:
            pulse_end_time = time.time()

        pulse_duration = pulse_end_time - pulse_start_time
#         distance = round(pulse_duration * 17150, 2)
        distance = round(pulse_duration * 19047, 2)
        """
            Se resta la supuesta distancia del sensor al suelo.
            Por los general es de 25 cm o 30.
            está por definirse
        """
        distance = 25 - distance 
        print ("Distance:",distance,"cm")
        
    finally:
#         GPIO.cleanup()        
        time.sleep(0.1)
        GPIO.output(PIN_LED, False)
        return distance
################################################################
#    publicar mensaje
################################################################
def publicar(mensaje):
    publicado = False
    try:
        ser.write(b'AT+SAPBR=3,1,Contype,GPRS\r\n')
        s = ser.readline()
        print(s)
        time.sleep(0.1)

        ser.write(b'AT+SAPBR=3,1,APN,"web.colombiamovil.com.co"\r\n')
        s = ser.readline()
        print(s)
        time.sleep(0.1)

        ser.write(b'AT+SAPBR=3,1,USER,"Tigo Web"\r\n')
        s = ser.readline()
        print(s)
        time.sleep(0.1)

        ser.write(b'AT+SAPBR=1,1\r\n')
        s = ser.readline()
        print(s)
        time.sleep(1)#1.5 seg

        ser.write(b'AT+HTTPINIT\r\n')
        s = ser.readline()
        print(s)
        time.sleep(0.1)#0.1 seg

        ser.write(b'AT+HTTPPARA="CID",1\r\n')
        s = ser.readline()
        print(s)
        time.sleep(0.4)

        ser.write(b'AT+HTTPPARA="URL","http://104.197.33.56/infiltrometrounicor/controller/listenerpost.php"\r\n')
        s = ser.readline()
        print(s)
        time.sleep(0.1)

        ser.write(b'AT+HTTPPARA="CONTENT","application/x-www-form-urlencoded"\r\n')
        s = ser.readline()
        print(s)
        time.sleep(0.1)

        #datos=("n=6&p=hacer la prueba de nuevo con post con un texto mas largo, no tan largo pero si largo. POST\r\n").encode('ascii')
        mensaje=(identificacion+"&m="+mensaje+"\r\n").encode('ascii')#dispositivo, prueba, mensaje (tiempo, dato)
        ###
        #   servidor recibe: POST
        #   $_POST['d'] : dispositivo
        #   $_POST['p'] : nombre de prueba
        #   $_POST['m'] : mensaje (tiempo y dato) 10;12.2;20;12.1;...
        ###
        lenth=len(mensaje)-2
        print(lenth)
        HTTPdata=("AT+HTTPDATA="+str(lenth)+",1000\r\n").encode('ascii')

        #ser.write(b'AT+HTTPDATA=12,5000\r\n')
        ser.write(HTTPdata)
        s = ser.readline()
        print(s)
        time.sleep(0.1)

        #ser.write(b'n=6&p="POST"\r\n')
        ser.write(mensaje)
        s = ser.readline()
        print(s)
        time.sleep(0.1)

        ser.write(b'AT+HTTPACTION=1\r\n')
        s = ser.readline()
        print(s)
        time.sleep(1)

    #     ser.write(b'AT+HTTPREAD\r\n')
    #     s = ser.readline()
    #     print(s)
    #     time.sleep(0.1)

        ser.write(b'AT+HTTPTERM\r\n')
        s = ser.readline()
        print(s)
        time.sleep(0.1)

        ser.write(b'AT+SAPBR=0,1\r\n')
        s = ser.readline()
        print(s)
        time.sleep(0.1)
        
        publicado = True
    
    finally:
        return publicado
    
##############################################################
#      guardar mensaje en USB    
##############################################################
def crearArchivoUsb(nombreArchivo, rutaUSB):
    f = open (rutaUSB+'/'+nombreArchivo,'w')        
    f.write('')
    f.close()
    
def guardarMensajeUsb(mensaje, nombreArchivo, rutaUSB):    
    f = open (rutaUSB+'/'+nombreArchivo,'a')        
    f.write(mensaje+'\n')
    f.close()
    print("archivo guardado")

##########################################################################
                            # MAIN
                    
if __name__ == '__main__':
    rutaUsb = verificarUsb()
    #Hace falta definir la hora del dispositivo mediante red. Va aquí
    print( "A la espera")
    while True:
        if GPIO.input(PIN_BOTON) == 0:
            print("boton pulsado")
            break 
    nombreDispositivo='0x1831bf156f44'
    date = datetime.now()
    date = date.strftime("%d-%m-%Y_%H-%M")
#     nombrePrueba="prueba_" + date
    nombrePrueba = nombrePruebaHoraGsm()#La hora para el nombre de la prueba se obtiene de la red mediante el GSM

    identificacion = "d=" + nombreDispositivo + "&p=" + nombrePrueba  #debe enviar MAC, id_prueba, tiempo, dato
    
    crearArchivoUsb(nombrePrueba, rutaUsb)
    
    inicio = datetime.now()
    intervalos10 = inicio #+ datetime.timedelta(seconds=0)
    intervalos30 = inicio + timedelta(seconds=35)
    segundo = 0
    
    
    mensaje = ""
    mensajePublicar = ""
    distancia=0
    distanciaAnt=100000
                      
    while True:
        if datetime.now() > intervalos10:
            intervalos10 += timedelta(seconds=10)
            
            """Tomar la distancia 10 veces"""
            distancia=0
            count=0
            for i in range(10):
                if tomaDato==-1:
                    distancia += 0
                else:
                    distancia += tomaDato()
                    count+=1
                time.sleep(0.05)
                
            if count != 0:
                distancia = distancia/count
            else:
                distancia = distanciaAnt
                
            """verificar que la distancia no se mayor a la distancia anterior"""
            if distancia>distanciaAnt and distancia-distanciaAnt<=2:
                distancia = distanciaAnt
                
            """Guardar mensaje en memoria"""
            mensaje += str(segundo) + ";" + str(distancia)
            distanciaAnt = distancia
            guardarMensajeUsb(mensaje, nombrePrueba, rutaUsb)
            mensajePublicar += mensaje + ";"
            segundo += 10            
            print(mensaje+"\n")            
            mensaje=""
            """enviar mensaje despues de 30 segundos"""
        if datetime.now() > intervalos30:
            try:
                mensajePublicar=mensajePublicar[:len(mensajePublicar)-1]
                thread = threading.Thread(target=publicar, args=(mensajePublicar,))
                thread.start()
#                 publicar(mensajePublicar)
                mensajePublicar = ""
            except:
                print("mensaje no publicado\n")
                
            intervalos30 += timedelta(seconds=30)
            
