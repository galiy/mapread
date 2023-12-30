#!/usr/bin/python3

from pyModbusTCP.client import ModbusClient
import json
import http.client as http
import time
from datetime import datetime

def toSigned(n, byte_count): 
	return int.from_bytes(n.to_bytes(byte_count, 'little'), 'little', signed=True)

SERVER_HOST = "192.168.13.77"
SERVER_PORT = 502
SERVER_U_ID = 2

c = ModbusClient()

c.host = SERVER_HOST
c.port = SERVER_PORT
c.unit_id = SERVER_U_ID

try:
	# open or reconnect TCP to server
	if not c.is_open:
		if not c.open():
			print("unable to connect to "+SERVER_HOST+":"+str(SERVER_PORT))

		# if open() is ok, read coils (modbus function 0x01)

	if c.is_open:
		# read 10 bits at address 0, store result in regs list
		readError = False

		jsq = "{"
		
		current_datetime = datetime.now()
		jsq = jsq + "\"timestamp\":\"" + str(int(current_datetime.strftime("%s"))) + "\""

		curtimeMapH = 0;
		curtimeMapD = 0;
		curtimeMapM = 0;

		regsA = []

		for bpart in range(6):
			for mpart in range(4):
				if bpart > 1 and bpart < 4:
					regsA.extend([0] * 0x40)
				else:
					if not readError:
						regs = c.read_holding_registers(0x0 + (bpart*mpart*0x40), 0x40)
						if regs:
							regsA.extend(regs)
						else:
							readError = True

		print(regsA)


		if not readError:
			regs = c.read_holding_registers(0x1B6, 1)
			if regs:
				# Текущее время. Часы и десятки минут
				curtimeMap= (regs[0] & 0b1111111100000000)  >> 8
				curtimeMapH = (curtimeMap & 0b11111000) >> 3
				curtimeMapD = (curtimeMap & 0b00000111)
			else:
				readError = True

		if not readError:
			regs = c.read_holding_registers(0x44B, 1)
			if regs:
				# Текущее время. Единицы минут минут
				curMinMapM = (regs[0] & 0b1111111100000000) >> 8
			else:
				readError = True

		#if not readError:
		#	regs = c.read_holding_registers(0x18, 6)
		#	if regs:
		#		# Серийный номер, ID МАП "_UID":"0" д.б. 51510
		mapUID = 51510 # Пока костылим это т.к. непонятно, как получить из этих регистров нужное значение
		#	else:
		#		readError = True


		if not readError:
				#print( str(regs) )


			jsq = jsq + "\n," + "\"time\":" + "\"" + str(curtimeMapH).zfill(2) + ":" + str(curtimeMapD) + str(curMinMapM) + ":00" + "\""
			jsq = jsq + "\n," + "\"_UID\":" + "\"" + str(mapUID) + "\""

			jsq = jsq + "}"
			
			print("jsq=" + jsq)

			#jjsq = json.loads(jsq)
			#conn = http.HTTPConnection('localhost')
			#headers = {'Content-type': 'application/json'}
			#conn.request('POST', '/gr/py.php/'+'dds238-2', jsq, headers)
			#response = conn.getresponse()
		else:
			print("read error, regs is null")


except Exception as e:
	print(str(e))

				#v_TotalEnergy   = ((regs[0]*65536) + regs[1])/100
				#v_ExportEnergy  = ((regs[8]*65536) + regs[9])/100
				#v_ImportEnergy  = ((regs[10]*65536) + regs[11])/100
				#v_Voltage       = (regs[12])/10
				#v_Current       = (regs[13])/100
				#v_ActivePower   = toSigned(regs[14],2)
				#v_ReActivePower = toSigned(regs[15],2)
				#v_PowerFactor   = regs[16]/1000
				#v_Frequency     = regs[17]/100
				
				#jsq = jsq + "," + "\"ObjType\":\"EnergyMeter\""
				#jsq = jsq + "," + "\"TotalEnergy\":" +    str(v_TotalEnergy)
				#jsq = jsq + "," + "\"ExportEnergy\":" +   str(v_ExportEnergy)
				#jsq = jsq + "," + "\"ImportEnergy\":" +   str(v_ImportEnergy)
				#jsq = jsq + "," + "\"Voltage\":" +        str(v_Voltage)
				#jsq = jsq + "," + "\"Current\":" +        str(v_Current)
				#jsq = jsq + "," + "\"ActibePower\":" +    str(v_ActivePower)
				#jsq = jsq + "," + "\"ReActibePower\":" +  str(v_ReActivePower)
				#jsq = jsq + "," + "\"PowerFactor\":" +    str(v_PowerFactor)
				#jsq = jsq + "," + "\"Frequency\":" +      str(v_Frequency)
