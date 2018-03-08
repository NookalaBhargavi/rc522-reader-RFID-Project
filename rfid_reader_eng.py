#!/opt/python3/bin/python3
import shlex
import subprocess
import sys
import time
import pymysql
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.OUT) //Green LED
GPIO.setup(8, GPIO.OUT) //Red LED


#############################################################################################
#                                 Copyright 2014 (BSD License)                              #
#                           Credits:  Florian Otto(Solider) and hadara                      #
#                           Contact me at: otti96@t-online.de                               #
#                           I may can help you to customize your code                       #
#                                                                                           #
#############################################################################################

#be sure to put the file in the same directory as "rc522_reader" !!! If not, you can edit in line 73
# IMPORTANT!!!: Edit the Database properties in line 77


###############################################################

preis=2.0 #keep it with the decimal point!

###############################################################


class RFIDReaderWrapper(object):
    """runs rfid reader as a subprocess & parses tag serials
    from its output
    """
    def __init__(self, cmd):
        self._cmd_list = shlex.split(cmd)
        self._subprocess = None
        self._init_subprocess()

    def _init_subprocess(self):
        self._subprocess = subprocess.Popen(self._cmd_list,
            stderr=subprocess.PIPE)

    def read_tag_serial(self):
        """blocks until new tag is read
        returns serial of the tag once the read happens
        """
        if not self._subprocess:
            self._init_subprocess()

        while 1:
            line = self._subprocess.stderr.readline()
            if isinstance(line, bytes):
                # python3 compat
                line = line.decode("utf-8")

            if line == '':
                # EOF
                return None

            if not line.startswith("New tag"):
                continue

            serial = line.split()[-1].split("=", 1)[1]
            return serial


try:
    if __name__ == '__main__':
        GPIO.output(8, 1)
        reader = RFIDReaderWrapper("./rc522_reader -d")
        name=""
        while 1:

            connection = pymysql.connect(host='127.0.0.1',unix_socket='/var/run/mysqld/mysqld.sock', user='USER', passwd='PASS', db='rfid') # Edit host, user, pass and/or db as it fit to your server
            cursor = connection.cursor()
            fobj = open("/root/status.txt","r+")
            serial = reader.read_tag_serial()
            cursor.execute("""SELECT name,money,counter,access FROM rfid_cards WHERE ID=(%s)""", (serial)) 	
            for row in cursor.fetchall():
                name = str(row[0])
                money = float(row[1])
                counter = int(row[2])
                access = int(row[3])
            GPIO.output(8, 1)
            if not name=="":
                if access == 1 and money>=preis:
                    cursor.execute("""UPDATE rfid_cards SET money = money - (%s) WHERE ID = (%s)""", (preis,serial));
                    cursor.execute("""UPDATE rfid_cards SET counter = counter + 1 WHERE ID = (%s)""", (serial));
                    cursor.execute("""SELECT name,money,counter,access FROM rfid_cards WHERE ID=(%s)""", (serial))
                    for row in cursor.fetchall():
                        name = str(row[0])
                        money = float(row[1])
                        counter = int(row[2])
                        access = int(row[3])			
                    print("Card recognized!")
                    print("Name:",name,"| Card ID:",serial)
                    print("credit: ",money)
                    print("accesses: ",counter)
                    GPIO.output(8, 0)
                    GPIO.output(7, 1)
                    time.sleep(4)
                    GPIO.output(7, 0)
                    GPIO.output(8, 1)
                elif money<preis:
                    print("credit too low! your credit: ",money)
                    print("price: ",preis)
                    GPIO.output(8, 0)
                    time.sleep(.5)
                    GPIO.output(8, 1)
                    time.sleep(.5)
                    GPIO.output(8, 0)
                    time.sleep(.5)
                    GPIO.output(8, 1)
                elif access == 0:
                    print("Access denied! Banned Serial!")
                    GPIO.output(8, 0)
                    time.sleep(.5)
                    GPIO.output(8, 1)
                    time.sleep(.5)
                    GPIO.output(8, 0)
                    time.sleep(.5)
                    GPIO.output(8, 1)
            else:
                print("Not known! Card ID:",serial)
                GPIO.output(8, 0)
                time.sleep(.5)
                GPIO.output(8, 1)
                time.sleep(.5)
                GPIO.output(8, 0)
                time.sleep(.5)
                GPIO.output(8, 1)           
            fobj.close()
            cursor.close()
            connection.commit()
            connection.close ()
            name=""
except KeyboardInterrupt:
    print("Exit!")
    GPIO.output(8, 0)
    GPIO.output(7, 0)
    cursor.close()
    connection.commit()
    connection.close ()  
    sys.exit(0)		