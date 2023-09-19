

# FuzzDeep by Ryan Armstrong 2023

import os
import sys
import argparse
import time
import datetime

import pyradamsa
from adb_shell.adb_device import AdbDeviceTcp, AdbDeviceUsb
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.auth.keygen import keygen

# Load the appropriate keys to connect to the target device with adb.
def load_keys(adb_key_location):
    home_dir = os.getenv("HOME")
    adb_key_location = adb_key_location.replace("HOME", home_dir)
    
    private_key_location = adb_key_location + '/adbkey'
    public_key_location = adb_key_location + '/adbkey.pub'
    
    if (os.path.isfile(public_key_location) and os.path.isfile(private_key_location)):
        with open(public_key_location) as f:
            public_key = f.read()   
    
        with open(private_key_location) as f:
            private_key = f.read()
    
        return PythonRSASigner(public_key, private_key)

    else:
        sys.exit("adb key was not found")

# Connect to device
def connect_device(signer):
    # Connect via USB
    device = AdbDeviceUsb()
    device.connect(rsa_keys=[signer], auth_timeout_s=0.1)
    
    # Confirm connection
    try:
        device.shell('pwd')
    except:
        sys.exit('Error connecting to device')

    return device

def send_payload(payload, sleep, package, device):
    activity_manager_call = "am start -a android.intent.action.VIEW -d 'PAYLOAD'" # Added single quotes around payload
    
    # Payload filtering/encoding
    payload = payload.replace(" ", "%20") # Replace spaces with %20
        
    device.shell(activity_manager_call.replace("PAYLOAD", payload))
    print(str(datetime.datetime.now()) + '  Trying payload: ' + payload, end='')
    print('Waiting for: ' + str(sleep))
    time.sleep(sleep)
    # Close the activity
    device.shell('am force-stop ' + package)


def fuzz(target, fuzz_base, sleep, iterations, device, package):
    # Get interface to Radamsa
    rad = pyradamsa.Radamsa()
    
    # Ensure FUZZ appears in target string
    if ("FUZZ" not in target):
    	sys.exit('No FUZZ position specified')
    # Convert string to bytes for Radamsa
    byte_payload = bytes(fuzz_base, 'utf-8')
    
    for i in range(iterations):
        # Create paylaod
        fuzz_payload_bytes = rad.fuzz(byte_payload) # Note, a second, optional param can specify seed (see docs)
        fuzz_payload_string = fuzz_payload_bytes.decode('utf-8', errors='ignore') # Note: may want to instead use 'replace' - https://www.w3docs.com/snippets/python/unicodedecodeerror-utf8-codec-cant-decode-byte-0xa5-in-position-0-invalid-start-byte.html
        #fuzz_payload_string = unicode(fuzz_payload_bytes, errors='replace')
        
        # Create crafted URL
        test_url = target.replace("FUZZ", fuzz_payload_string)
        
        # Send payload
        send_payload(test_url, sleep, package, device)
               
    return
    
    
def wordlist(target, wordlist_file_name, sleep, device, package):

    wordlist_file = open(wordlist_file_name, 'r')

    for word in wordlist_file:
        test_url = target.replace("FUZZ", word)
        
        # Send payload
        send_payload(test_url, sleep, package, device)

    return


def main(arguments):
    # Define Parser and arguments
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-p','--package', help="Specify the Android package name", type=str)
    parser.add_argument('-t','--target', help="Specify a deep link target. Use FUZZ to indicate payload positioning.", default='https://app?FUZZ', type=str)
    parser.add_argument('-f', '--fuzz', help="Use fuzz mode (radamsa) with the specified payload base. If a wordlist is also specified, it will be used first.", default='', type=str)
    parser.add_argument('-i', '--iterations', help="In Fuzz mode, set a maximum number of iterations. ", default=1000, type=int)
    parser.add_argument('-w', '--wordlist', help="Use wordlist mode with the specified wordlist. If fuzzing (radamsa) is also specified, it will occur second.", default='', type=str)
    parser.add_argument('-s', '--sleep', help="Set the sleep time between payloads. The default is 3 seconds. Time should be set based on observed behavior.", default=3, type=int)
    parser.add_argument('-k', '--keys', help="Specify the folder that contains your adb keys (default is chosen for Linux: $HOME/.android)", default='HOME/.android', type=str)

    args = parser.parse_args(arguments)
    
    # Prepare adb connection
    signer = load_keys(args.keys)
    device = connect_device(signer)    
    
    ## Wordlist attack
    if (args.wordlist):
        wordlist(args.target, args.wordlist, args.sleep, device, args.package)
    
    ## Fuzz with Radamsa attack
    if (args.fuzz):
        fuzz(args.target, args.fuzz, args.sleep, args.iterations, device, args.package)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
