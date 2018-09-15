#
#!/usr/bin/env python
from comms import *
import serial
import csv
import datetime
import sys
import time
from math import sin, cos, pi


intervals = 0.0002




if len(sys.argv) != 5:
        print("give me a serial port, address, duty cycle, and data_title")
        exit()

title = sys.argv[4]


####################################################################################################################

PROTOCOL_V2 = 2

port = sys.argv[1]
s = serial.Serial(port=port, baudrate=COMM_DEFAULT_BAUD_RATE, timeout=0.1)

try:
    addresses = [int(sys.argv[2])]
    duty_cycles = [float(sys.argv[3])]
except ValueError:
    addresses = [int(address_str) for address_str in sys.argv[2].split(',')]
    duty_cycles = [float(duty_cycle_str) for duty_cycle_str in sys.argv[3].split(',')]

client = BLDCControllerClient(s)

for address, duty_cycle in zip(addresses, duty_cycles):
    client.leaveBootloader([address])
    time.sleep(0.2)
    s.reset_input_buffer()

    calibration_obj = client.readCalibration([address])

    client.setZeroAngle([address], [calibration_obj['angle']])
    client.setInvertPhases([address], [calibration_obj['inv']])
    client.setERevsPerMRev([address], [calibration_obj['epm']])
    client.setTorqueConstant([address], [calibration_obj['torque']])
    client.setPositionOffset([address], [calibration_obj['zero']])
    if 'eac_type' in calibration_obj and calibration_obj['eac_type'] == 'int8':
        print('EAC calibration available')
        try:
            client.writeRegisters([address], [0x1100], [1], [struct.pack('<f', calibration_obj['eac_scale'])])
            client.writeRegisters([address], [0x1101], [1], [struct.pack('<f', calibration_obj['eac_offset'])])
            client.writeRegisters([address], [0x1011], [1], [struct.pack('<f', 100.00)])
            eac_table_len = len(calibration_obj['eac_table'])
            slice_len = 64
            for i in range(0, eac_table_len, slice_len):
                table_slice = calibration_obj['eac_table'][i:i+slice_len]
                client.writeRegisters([address], [0x1200+i], [len(table_slice)], [struct.pack('<{}b'.format(len(table_slice)), *table_slice)])
        except ProtocolError:
            print('WARNING: Motor driver board does not support encoder angle compensation, try updating the firmware.')
    client.setCurrentControlMode([address])
    client.writeRegisters([address], [0x1030], [1], [struct.pack('<H', 1000)])
    # print("Motor %d ready: supply voltage=%fV", address, client.getVoltage(address))

    client.writeRegisters([address], [0x2006], [1], [struct.pack('<f', 0.0)])
    client.writeRegisters([address], [0x2000], [1], [struct.pack('<B', 2)]) # Torque control
    # client.writeRegisters([address], [0x1011], [1], [struct.pack('<f', 10.0)])


for i in range(100):
    client.writeRegisters([address], [0x2006], [1], [struct.pack('<f', 0.0)])
    time.sleep(0.05)

count = 0


rows = []
is_done = False
sent = []
strain_gague = []

ser = serial.Serial('/dev/ttyACM0')
start_time = time.time()
while not is_done:
    for address in addresses:
        send = float(count) * intervals
        sent.append(send)
        rows.append([time.time() - start_time, send])
        try:
            # data = struct.unpack('<ff', client.readRegisters([address], [0x3000], [2])[0])
            client.writeRegisters([address], [0x2006], [1], [struct.pack('<f', send)])
            # print(address, data)
            print(send)
        except IOError:
            pass

        count += 1
        if count % 100 == 0:
            freq = count / (time.time() - start_time)
            print("{} \t {}".format(address, freq))
            print("hello!")
            sys.stdout.flush()

        if duty_cycle == send:
            is_done = True
        count += 1
    ser_bytes = ser.readline()
    decoded_bytes = str((ser_bytes[0:len(ser_bytes)-2].decode("utf-8")))
    lst = decoded_bytes.split(',');
    try:
        strain_gague.append([float(lst[0]), float(lst[1])])
    except:
        strain_gague.append([float(0), float(0)])

is_done = False
for x in (sent[::-1] + [-x for x in sent][0:200]) :
    count = 0
    for address in addresses:
        send = x
        print(send)
        rows.append([time.time() - start_time, send])
        try:
            # data = struct.unpack('<ff', client.readRegisters([address], [0x3000], [2])[0])
            client.writeRegisters([address], [0x2006], [1], [struct.pack('<f', send)])
            # print(address, data)
        except:
            print(error)
            pass

        count += 1
        if count % 100 == 0:
            freq = count / (time.time() - start_time)
            print("{} \t {}".format(address, freq))
            print("hello!")
            sys.stdout.flush()

        if -duty_cycle < 0:
            is_done = True
        count += 1

    ser_bytes = ser.readline()
    decoded_bytes = str((ser_bytes[0:len(ser_bytes)-2].decode("utf-8")))
    lst = decoded_bytes.split(',');
    strain_gague.append([float(lst[0]), float(lst[1])])

    try:
        strain_gague.append([float(lst[0]), float(lst[1])])
    except:
        strain_gague.append([float(0), float(0)])


with open( title + "_{}".format(duty_cycle) +  '.csv', mode='w') as file:
    writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["time", "command", "strain1", "strain2"])
    for i, r in enumerate(rows):
        writer.writerow(r + strain_gague[i])
