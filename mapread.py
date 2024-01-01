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
c.timeout = 3

readError = None
regs = [0] * 0x100 * 6

def bbin(bVal):
	return bin(bVal)[2:]

def readRs(reg_addr, reg_nb=1):
	# Читает из RS485 нужное кол-во байт. не слов а именно байт т.к. RS485 читает словами, а в каждом слове по 2 байта
	global readError
	global regs
	try:
		reg_nbL = reg_nb // 2;
		if reg_nb > (reg_nbL * 2):
			reg_nbL += 1;

		regsL = c.read_holding_registers(reg_addr, reg_nbL)
		if regsL:
			if len(regsL) == reg_nbL:
				cntr = 0
				for regCur in regsL:
					regs[reg_addr+cntr] = (regCur & 0b1111111100000000)>>8
					cntr += 1
					if cntr < reg_nb:
						regs[reg_addr+cntr] = (regCur & 0b0000000011111111)
						cntr += 1
			else:		
				readError = "Incorrect count List from read_holding_registers " + hex(reg_addr) + " need " + str(reg_nbL) + " received " + str(len(regsL))
		else:
			readError = "None List from read_holding_registers " + hex(reg_addr)
	except Exception as e:
		readError = str(e) + " on addr " + hex(reg_addr)


try:
	# open or reconnect TCP to server
	if not c.is_open:
		if not c.open():
			print("unable to connect to "+SERVER_HOST+":"+str(SERVER_PORT))

	if c.is_open:
		# read 10 bits at address 0, store result in regs list
		readError = None

		jsq = "{\"ObjType\":\"MAP\""
		
		current_datetime = datetime.now()
		
		dCur = current_datetime
		jsq = jsq + "\n," + "\"timestamp\":\"" + str(int(dCur.strftime("%s"))) + "\""

		if not readError:
			#readRs(0x1B6, 1)
			#readRs(0x18, 2)
			#readRs(0x400, 0x4B + 1)
			
			#readRs(0x000, 0x80)
			#readRs(0x080, 0x80)
			#readRs(0x100, 0x80)
			#readRs(0x180, 0x80)
			#readRs(0x400, 0x80)
			#readRs(0x480, 0x80)
			#readRs(0x500, 0x80)
			#readRs(0x580, 0x80)

			# 1B6
			# 44B
			# 400 402 405 406 422 427
			# 587 59A 59B 59E 59F
			#readRs(0x400, 0x4B+1)
			#readRs(0x400, 0x80)

			readRs(0x400, 0x33+1)
			readRs(0x587, 0x18+1)
			#readRs(0x1B6, 1)

		if not readError:
			#curtimeMapH = (regs[0x1B6] & 0b11111000) >> 3 # Текущее время. Часы
			#curtimeMapD = (regs[0x1B6] & 0b00000111) # Текущее время. Десятки минут
			#curMinMapM = regs[0x44B] # Текущее время. Единицы минут

			#map_UID	= (regs[0x19] << 8) | regs[0x18] # Серийный номер
			map_UID = 51510

			map_MODE = regs[0x400]
			map_Status_Char = regs[0x402]	
			#_PLoad_L=0x409 - текущая мощность нагрузки по АКБ т.е. при генерации (или при трансляции сети в режиме подкачки в сеть).
			#Данная ячейка отображает мощность потребления блоков мощностью до 25кВт. Для блоков большей мощности необходимо задействовать
			#ячейку _PLoad_H см. ниже. Pнагруз(Вт) = PLoad*100
			#_PLoad_H=0x456 – дополнительный байт для отображения мощности нагрузки по АКБ  (или при трансляции сети в режиме подкачки в сеть)
			#для блоков мощностью более 25кВт. Pнагруз(Вт) = (PLoad_H*256 + PLoad_L)*100
			#Начиная с версии 26.6. 16-ти битные ячейки мощности аналогичные 8 битным PNET и PLoad но в 8 раз точнее:
			#PLoad_8=0x59E-0x59F - текущая мощность нагрузки в киловатах/10 и *8
			map_PLOAD = (((regs[0x59F] << 8) | regs[0x59E]) / 8 ) * 100
			

			#_IAcc_med_A_u16_L=0x432, _IAcc_med_A_u16_H=0x433 - Более точное значение тока по АКБ (аналогичное _IAcc_med_A_2), для подсчета статистики.
			#Iакб(А) = (IAcc_med_A_u16_L+ IAcc_med_A_u16_H*256)/16
			#map_IACC = regs[0x408] * 2
			map_IACC = (regs[0x432] + regs[0x433] * 256)/16


			map_UACC = (regs[0x405] * 256 + regs[0x406])/10

			#Для режима заряда - считаем через ток и напряжение по АКБ. Иначе инвертируем
			if map_MODE == 4:
				map_PLOAD = round(map_IACC * map_UACC)
			else:
				map_IACC = 0 - map_IACC;
				map_PLOAD = 0 - map_PLOAD;

			#Начиная с версии 26.6. 16-ти битные ячейки мощности аналогичные 8 битным PNET и PLoad но в 8 раз точнее:
			#PNET_8=0x59A-0x59B  - текущая мощность сети в киловатах/10 и *8, знак определяется по PNET_Sign_P=0x587.
			map_PNET = round((((regs[0x59B] << 8) | regs[0x59A]) / 8 ) * 100)

			#PNET_Sign_P=0x587 
			#знак мощности сети: 1 – положительная, 0 - отрицательная мощность (продажа)
			if regs[0x587] == 0:
				map_PNET = 0 - map_PNET

			
			map_P_MPPT = 0 #TODO Доделать как придут из ремонта MPPT контроллеры
			
			#_UNET=0x422 - Напряжение сети.
			#UNET=0 – нет сети на входе иначе Uсети(В)=UNET+100
			map_UNET = regs[0x422] + 100
			
			#_INET=0x423 - Ток отбираемый от сети, в том числе на заряд.
			#Iсети(A)= INET.
			map_INET = regs[0x423]
			map_INET_16_4 = regs[0x431]
			if map_INET < 16:
				map_INET_16_4 = map_INET_16_4 / 16
			else:
				map_INET_16_4 = map_INET_16_4 / 4

			#_UOUTmed=0x427 – Напряжение на выходе во время генерации
			#UOUTmed=0 – нет сети на входе иначе Uвыход(В)=UOUTmed +100.
			map_UOUT = regs[0x427] + 100


		if not readError:
			#jsq = jsq + "\n," + "\"time\":" + "\"" + str(curtimeMapH).zfill(2) + ":" + str(curtimeMapD) + str(curMinMapM) + ":00" + "\""
			jsq = jsq + "\n," + "\"time\":" + "\"" +dCur.strftime("%H:%M:%S")+ "\""
			
			jsq = jsq + "\n," + "\"UID\":" + "\"" + str(map_UID) + "\""
			# TODO Сделать сложный MODE как у osolemio
			jsq = jsq + "\n," + "\"MODE\":" + "\"" + str(map_MODE) + "\""
			jsq = jsq + "\n," + "\"Status_Char\":" + "\"" + str(map_Status_Char) + "\""


			jsq = jsq + "\n," + "\"PLOAD\":" + "\"" + str(map_PLOAD) + "\""
			jsq = jsq + "\n," + "\"PNET\":" + "\"" + str(map_PNET) + "\""
			jsq = jsq + "\n," + "\"P_MPPT_AVG\":" + "\"" + str(map_P_MPPT) + "\""
			jsq = jsq + "\n," + "\"UNET\":" + "\"" + str(map_UNET) + "\""
			jsq = jsq + "\n," + "\"UOUT\":" + "\"" + str(map_UOUT) + "\""
			jsq = jsq + "\n," + "\"UACC\":" + "\"" + str(map_UACC) + "\""
			jsq = jsq + "\n," + "\"IACC\":" + "\"" + str(map_IACC) + "\""
			jsq = jsq + "\n," + "\"INET\":" + "\"" + str(map_INET) + "\""
			jsq = jsq + "\n," + "\"INET_16_4\":" + "\"" + str(map_INET_16_4) + "\""

			jsq = jsq + "}"
			
			#print("jsq=" + jsq)

			jjsq = json.loads(jsq)
			#conn = http.HTTPConnection('localhost')
			conn = http.HTTPConnection('192.168.13.253')
			headers = {'Content-type': 'application/json'}
			conn.request('POST', '/gr/py.php/'+'MAP', jsq, headers)
			response = conn.getresponse()

		else:
			print("Read error: " + readError)
except Exception as e:
	print(str(e))
