#!/usr/bin/env python
from comms import *
import serial
import sys
import time
from math import sin, cos, pi

PROTOCOL_V2 = 2

if len(sys.argv) != 5:
        print("give me a serial port, address, and duty cycle and arduino port")
        exit()

port = sys.argv[1]
arduino_port = sys.argv[4]
s = serial.Serial(port=port, baudrate=COMM_DEFAULT_BAUD_RATE, timeout=0.1)
arduino = serial.Serial(port=arduino_port, baudrate=9600, timeout=0.1)

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

    client.writeRegisters([address], [0x2006], [1], [struct.pack('<f', float(0))])
    client.writeRegisters([address], [0x2000], [1], [struct.pack('<B', 2)]) # Torque control


start_time = time.time()
count = 0
while True:
    for address in addresses:
        try:
            data_from_arduino = float(arduino.readline().decode())
            current_cmd = (data_from_arduino / 1024.0 - 0.5)
            if count % 1000 == 0:
                print(current_cmd)
                print(data_from_arduino)
            client.writeRegisters([address], [0x2006], [1], [struct.pack('<f', float(current_cmd))])

            # print(address, data)
        except Exception:
            pass

        count += 1
        if count % 1000 == 0:
            freq = count / (time.time() - start_time)
            print("{} \t {}".format(address, freq))
            sys.stdout.flush()
    time.sleep(0.01)
