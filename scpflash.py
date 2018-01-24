#!/usr/bin/env python

# SCP Flash by Bailey Seymour (@atomikpanda)
# Install zips on a jailbroken device via scp

import zipfile
import sys
import tempfile
import shutil
import os
import getopt
import stat

device_ip = None
device_port = "22"
package_root = None

def uninstall_script_path(package_id):
	return "/var/mobile/Library/scpflash/uninstall_"+package_id+".sh"

def find_bootstrap_dir(base_dir):
	for root, dirs, files in os.walk(base_dir):
		path = root.split(os.sep)
		for adir in dirs:
			if adir == "bootstrap":
				current_bootsrap = os.sep.join(path)+os.sep+adir
				# print "found bootstrap dir at " + current_bootsrap
				return current_bootsrap
	return None

def find_flash_dir(base_dir):
	for root, dirs, files in os.walk(base_dir):
		path = root.split(os.sep)
		for adir in dirs:
			if adir == "FLASH":
				current_flash = os.sep.join(path)+os.sep+adir
				# print "found FLASH dir at " + current_flash
				return current_flash
	return None

def create_file_list(package_root):
	liststr = ""

	for root, dirs, files in os.walk(package_root):
		path = root.split(os.sep)
		for file in files:
			current_path = os.sep.join(path)+os.sep+file

			# verify that we do not add a directory for removal
			if os.path.isdir(current_path) == False:
				on_device_path = current_path.replace(package_root, "")
				liststr += on_device_path.strip()+"\n"	

	return liststr

def remove_ds_store_recursive(at_path):
	for root, dirs, files in os.walk(at_path):
		for file in files:
			if file.endswith('.DS_Store'):
				path = os.path.join(root, file)
				os.remove(path)
	pass

def fatal(msg):
	print "*** FATAL ERR: "+msg
	exit(1)
	pass

def parse_control(control_filepath):

	with open(control_filepath, 'r') as content_file:
		control_file = content_file.read()

		lines = control_file.split("\n")
		control = {}

		for line in lines:

			if len(line) == 0:
				continue

			components = line.split(":")
			field = components[0]
			components.pop(0)
			value = ":".join(components)
			control[field.strip()] = value.strip()

			pass

		return control
	return None

def has_key_and_val(list, key):

	if list.has_key(key) and len(list[key]) != 0:
		return True

	return False

def short_description(control):
	desc = ""

	if has_key_and_val(control, "Name"):
		desc = control["Name"] + " (" + control["Package"]+")" + " (v"+control["Version"]+")"
	else:
		desc = control["Package"] + " (v"+control["Version"]+")"

	if has_key_and_val(control, "Description"):
		desc += "\n" + control["Description"]

	return desc

def extract_zip(path, target_dir):
	with zipfile.ZipFile(path,"r") as zip_ref:
		zip_ref.extractall(target_dir)

		MACOSX_DIR = target_dir+"/__MACOSX"

		if os.path.isdir(MACOSX_DIR) == True:
			shutil.rmtree(MACOSX_DIR)

		return target_dir

	return None

def get_flash_dir(extracted_dir):
	global package_root;

	local_flash_dir = find_flash_dir(extracted_dir)

	if local_flash_dir == None:
		shutil.rmtree(extracted_dir)
		fatal("Failed to find FLASH directory in zip contents.")

	# Save package root dir
	package_root = os.path.dirname(local_flash_dir);

	# Move flash dir somewhere else
	shutil.move(local_flash_dir, extracted_dir)
	local_flash_dir = extracted_dir+os.sep+"FLASH"

	remove_ds_store_recursive(package_root)

	return local_flash_dir

def install_zip(path, device_ip, device_port):
	
	tmpdir = tempfile.mkdtemp()

	extract_zip(path, tmpdir)
	
	local_flash_dir = get_flash_dir(tmpdir)

	control = parse_control(local_flash_dir+os.sep+"control")

	if control.has_key("Package") == False:
		shutil.rmtree(tmpdir)
		fatal("No Package field in FLASH/control")

	# print str(control) + "\n"
	print "------------------------------------------"
	print short_description(control)

	print "------------------------------------------"
	# print "installing "+control["Name"]+" ("+control["Package"]+")"

	# print create_file_list(package_root) + "\n"

	list_to_uninstall = create_file_list(package_root)
	uninstall_loc_pkg = package_root+uninstall_script_path(control["Package"])
	os.system("mkdir -p \""+os.path.dirname(uninstall_loc_pkg)+'"')
	# remove ourself
	list_to_uninstall += uninstall_script_path(control["Package"])
	
	# generate script
	removal_script = uninstall_sh_from_liststr(list_to_uninstall)
	# add finished uninstalling
	removal_script += "echo finished uninstalling "+control["Package"]

	uninstall_sh = open(uninstall_loc_pkg, "w")
	uninstall_sh.write(removal_script)
	uninstall_sh.close()

	st = os.stat(uninstall_loc_pkg)
	os.chmod(uninstall_loc_pkg, st.st_mode | 0111)

	print("installing "+control["Package"]+" on "+device_ip+":"+device_port)
	scp_cmd = "scp -r -P "+device_port+" "+package_root+"/. root@"+device_ip+":/"
	#print scp_cmd # useful for debugging the scp command

	# fatal("DISABLED SCP") #DEBUG
	os.system(scp_cmd)

	# clean up tmp dir
	shutil.rmtree(tmpdir)
	pass

def uninstall_sh_from_liststr(liststr):
	script = ""#"#!/bin/bash\n\n"

	lines = liststr.split("\n")

	for line in lines:
		if len(line) != 0:
			script += "rm \"" + line + "\"; "

	return script

def uninstall_zip(path, device_ip, device_port):
	tmpdir = tempfile.mkdtemp()

	extract_zip(path, tmpdir)
	
	local_flash_dir = get_flash_dir(tmpdir)

	control = parse_control(local_flash_dir+os.sep+"control")

	if control.has_key("Package") == False:
		shutil.rmtree(tmpdir)
		fatal("No Package field in FLASH/control")

	list_to_uninstall = create_file_list(package_root)
	removal_script = uninstall_sh_from_liststr(list_to_uninstall)

	# add finished uninstalling
	removal_script += "echo finished uninstalling "+control["Package"]

	print("uninstalling "+control["Package"]+" on "+device_ip+":"+device_port)

	# ssh a removal script from our list
	ssh_cmd = "ssh -p "+ device_port +" root@"+device_ip+" '"+removal_script+"'";

	# print ssh_cmd
	os.system(ssh_cmd)
	# clean up tmp dir
	shutil.rmtree(tmpdir)
	pass

def uninstall_id(id, device_ip, device_port):

	script = "source "+uninstall_script_path(id)

	print("uninstalling "+id+" on "+device_ip+":"+device_port)
	# ssh a removal script from our list
	ssh_cmd = "ssh -p "+ device_port +" root@"+device_ip+" '"+script+"'";

	# print ssh_cmd
	os.system(ssh_cmd)
	
	pass

def usage(exit_code):
	print "\nUsage: ./scpflash.py --ip <ip_addr> --port <device_port> --zip <path_to_archive> [--theos] [--uninstall=pkg_identifier]\n"
	print "Install From Zip: ./scpflash.py --ip 127.0.0.1 --port 2222 --zip mypackage.zip"
	print "Uninstall Package Id: ./scpflash.py --ip 127.0.0.1 --port 2222 --uninstall com.yourpackage.id"
	print "Uninstall From Zip: ./scpflash.py --ip 127.0.0.1 --port 2222 --zip mypackage.zip --uninstall-zip"
	print "Theos Example: ./scpflash.py --zip tweak.zip --theos"
	exit(exit_code)
	pass

def theos_mode():
	global device_ip
	global device_port

	if os.environ.has_key("THEOS_DEVICE_IP") == True:
		device_ip = os.environ["THEOS_DEVICE_IP"]

	if os.environ.has_key("THEOS_DEVICE_PORT") == True:
		device_port = os.environ["THEOS_DEVICE_PORT"]

	if device_ip == None:
		print "Device IP cannot be nothing. Try changing THEOS_DEVICE_IP to the IP address of your iOS device."
		usage(1)

	pass

def main():
	global device_ip
	global device_port
	input_file = None
	use_theos = False
	uninstall = False

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'i:p:hz:tu:', ['ip=', 'port=', 'help', 'zip=', 'theos', 'uninstall=', 'uninstall-zip'])
	except getopt.GetoptError:
		usage(2)

	uni_id = None
	uninstall_using_zip = False

	for opt, arg in opts:
		if opt in ('-h', '--help'):
			usage(2)
		elif opt in ('-i', '--ip'):
			device_ip = arg
		elif opt in ('-p', '--port'):
			device_port = arg
		elif opt in ('-z', '--zip'):
			input_file = arg
		elif opt in ('-t', '--theos'):
			use_theos = True
		elif opt in ('-u', '--uninstall'):
			uninstall = True
			uni_id = arg
		elif opt in ('--uninstall-zip'):
			uninstall = True
			uninstall_using_zip = True
		else:
			usage(2)

	

	if input_file == None and uninstall == True and uninstall_using_zip == True:
		print "No input zip file -z or --zip not specified."
		usage(1)

	if use_theos == True:
		theos_mode()
	
	if device_ip == None:
		print "Device IP cannot be nothing. Try specifying --ip or --theos."
		usage(1)

	if uninstall == True and uninstall_using_zip == True:
		uninstall_zip(input_file, device_ip, device_port)
	elif uninstall == True and uninstall_using_zip == False:
		uninstall_id(uni_id, device_ip, device_port)
	else:
		install_zip(input_file, device_ip, device_port)

	return 0


exit(main())