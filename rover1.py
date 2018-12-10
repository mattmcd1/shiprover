import fnmatch
import serial
from queue import Queue
import threading
import time


def detect_serial_devices():
    """ Function to detect FTDI USB-to-serial converters
    Returns:
      A list of serial device paths
    """
    
    import glob
    glist = glob.glob('/dev/serial/by-path/platform-3f980000.usb-usb-0:1.*')
    ret = []
    
    for d in glist:
        ret.append(d)
    return ret


def serial_device(device, deviceID, message_queue, device_status):
    """ Listens on a serial port, encapsulates data in a frame
    with a RoverID (Raspberry Pi serial number) and DeviceID.
    
    Args:
      device: An instance of a Serial object.
      deviceID: An integer ID for that device
    Returns:
      Nothing.
    """
    
    head = 0x5a
    tail = 0xa5
    
    while True:
        line = device.read(100)
        
        if len(line) > 0:
            device_status[deviceID] = 10        # will be decremented by heartbeat
            
            # Construct the frame
            frame = bytearray()
            frame.append(head)
            frame.append(head)
            frame.extend(get_serial()[-4:].encode())
            frame+=(int(deviceID).to_bytes(2, byteorder='big'))
            frame+=(len(line).to_bytes(4, byteorder='big'))
            frame+=(line)
            frame.append(tail)
            frame.append(tail)
            
            # Add the frame to the queue for uplink
            message_queue.put(frame)
    
    return

def get_serial():
    """ Extract serial from cpuinfo file.
    Used as the RoverID.
    
    Returns:
      Raspberry Pi serial number.
    """
    
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


def beat(pulse_queue, period=1):
    """ Heartbeat function. Used to generate an "alive" pulse.
    """
    
    while True:
        time.sleep(period)
        pulse_queue.put(1)
    
    return

def print_status(device_status):
    """ Generates a status frame to be sent on the heartbeat pulse.
    """
    
    head = 0x5a
    tail = 0xa5
    
    frame = bytearray()
    frame.append(head)
    frame.append(head)
    frame.extend(get_serial()[-4:].encode())
    frame.append(0xFF)
    frame+=(int(device_status[1]).to_bytes(1, byteorder='big'))
    frame+=(int(device_status[2]).to_bytes(1, byteorder='big'))
    frame+=(int(device_status[3]).to_bytes(1, byteorder='big'))
    frame+=(int(device_status[4]).to_bytes(1, byteorder='big'))
    frame.append(tail)
    frame.append(tail)
    
    return frame

def main():
    devices = []                            # list of connected serial devices
    radio_port = ''                         # serial port that radio is connected to
    gnss_correction_port = ''               # serial port that GNSS corrections should be forwarded to
    device_status = [0, 0, 0, 0, 0]         # device "time to live" counter (set to 10 when data received, decremented by heartbeat)
    device_msg_queue = Queue(1000)          # threadsafe queue for device data
    pulse = Queue(1)                        # threadsafe heartbeat signal
    
    serial_devices = detect_serial_devices()
    for port in serial_devices:
        if port == '/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.2:1.0-port0':
            radio_port = port
        else:
            devices.append(port)
    
    # Debug code - to be deleted
    
    if radio_port != '':
        print('Radio connected on USB2.')
        radio_serial = serial.Serial(radio_port, 115200, timeout=1)
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
    
    # End debug
    
    # Spawn a thread to listen to each connected serial device
    if len(devices) > 0:
        serial1 = serial.Serial(devices[0], 115200, timeout=1)
        thread1 = threading.Thread(target=serial_device, args=(serial1,1,device_msg_queue,device_status,),).start()
        if devices[0] == '/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.3:1.0-port0':
            gnss_correction_port = serial1
    if len(devices) > 1:
        serial2 = serial.Serial(devices[1], 115200, timeout=1)
        thread2 = threading.Thread(target=serial_device, args=(serial2,2,device_msg_queue,device_status,),).start()
        if devices[1] == '/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.3:1.0-port0':
            gnss_correction_port = serial2
    if len(devices) > 2:
        serial3 = serial.Serial(devices[2], 115200, timeout=1)
        thread3 = threading.Thread(target=serial_device, args=(serial3,3,device_msg_queue,device_status,),).start()
        if devices[2] == '/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.3:1.0-port0':
            gnss_correction_port = serial3
    if len(devices) > 3:
        serial4 = serial.Serial(devices[3], 115200, timeout=1)
        thread4 = threading.Thread(target=serial_device, args=(serial4,4,device_msg_queue,device_status,),).start()
        if devices[3] == '/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.3:1.0-port0':
            gnss_correction_port = serial4
    
    # Spawn the heartbeat thread
    heartbeat = threading.Thread(target=beat, args=(pulse, 5,),).start()
    
    # Run forever...
    while True:
        # Process/uplink device data in the queue
        if not device_msg_queue.empty():
            data = device_msg_queue.get()
            radio_serial.write(data)
            print(len(data))                # DEBUG
            print(data)                     # DEBUG
            
        # Heartbeat actions
        if not pulse.empty():
            pulse.get()
            for i in range(len(device_status)):
                if device_status[i] > 0:
                    device_status[i] -= 1
            
            print([hex(c) for c in print_status(device_status)])
    
    return 0

if __name__ == '__main__':
    main()
