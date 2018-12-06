import fnmatch
import serial
import queue
import threading

device_msg_queue = queue.Queue(1000)

def detect_serial_devices():
    
    import glob
    glist = glob.glob('/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.*')
    ret = []
    
    for d in glist:
        ret.append(d)
    return ret

def serial_device(device, deviceID):
    head = 0x5a
    tail = 0xa5
    
    while True:
        line = device.read(100)
        # print(line.decode('utf-8'))
        if len(line) > 0:
            # print('Received: ' + str(len(line)) + ' characters.')
            frame = bytearray()
            frame.append(head)
            frame.append(head)
            frame.extend(get_serial()[-4:].encode())
            frame+=(int(deviceID).to_bytes(2, byteorder='big'))
            frame+=(len(line).to_bytes(4, byteorder='big'))
            frame+=(line)
            frame.append(tail)
            frame.append(tail)
            device_msg_queue.put(frame)

def get_serial():
  # Extract serial from cpuinfo file
  cpuserial = "0000000000000000"
  try:
    f = open('/proc/cpuinfo','r')
    for line in f:
      if line[0:6]=='Serial':
        cpuserial = line[10:26]
    f.close()
  except:
    cpuserial = "ERROR000000000"

  return cpuserial

def main():
    radio_port = ''
    gnss_correction_port = ''
    devices = []
    
    serial_devices = detect_serial_devices()
    for port in serial_devices:
        # print(port)
        if port == '/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.2:1.0-port0':
            radio_port = port
        else:
            devices.append(port)
            if port == '/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.3:1.0-port0':
                gnss_correction_port = port
    
    if radio_port != '':
        print('Radio connected on USB2.')
    else:
        print('Radio not connected.')
    
    if gnss_correction_port != '':
        print('GNSS corrections being sent on USB3.')
    else:
        print('GNSS corrections device not found.')
    
    if len(devices) == 1:
        print(str(len(devices)) + ' device connected.')
    else:
        print(str(len(devices)) + ' devices connected.')
    
    # radio_serial = serial.Serial(radio_port, 115200, timeout=1)
    # gnss_correction_serial = serial.Serial(gnss_correction_port, 115200, timeout=1)
    
    if len(devices) > 0:
        serial1 = serial.Serial(devices[0], 115200, timeout=1)
        thread1 = threading.Thread(target=serial_device, args=(serial1,1,),).start()
    if len(devices) > 1:
        serial1 = serial.Serial(devices[1], 115200, timeout=1)
        thread1 = threading.Thread(target=serial_device, args=(serial2,2,),).start()
    if len(devices) > 2:
        serial1 = serial.Serial(devices[2], 115200, timeout=1)
        thread1 = threading.Thread(target=serial_device, args=(serial3,3,),).start()
    if len(devices) > 3:
        serial1 = serial.Serial(devices[3], 115200, timeout=1)
        thread1 = threading.Thread(target=serial_device, args=(serial4,4,),).start()
    
    
    while True:
        if not device_msg_queue.empty():
            data = device_msg_queue.get()
            # radio_serial.write(data)
            print(len(data))
            print(data)
    
    return 0

if __name__ == '__main__':
    main()
    
test