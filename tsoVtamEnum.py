from py3270 import Emulator
import sys
import time

if len(sys.argv) <= 3:
	print("Usage: tsoUserEnum.py <host> <port> <path to VTAM subsystem list>")
	sys.exit()

host = sys.argv[1]
port = sys.argv[2]
vtam_list_location = sys.argv[3]

delay_time = 1

def file2list(filename):
	lines = []
	with open(filename) as file:
    		lines = file.readlines()
    		lines = [line.rstrip() for line in lines]
	return lines
	
def user_enum(count, subsystems, number_of_subsystems):
	# use x3270 so you can see what is going on
	#em = Emulator(visible=True)

	# or not (uses s3270)
	em = Emulator()

	# connect to host
	em.connect('%s:%d' % (host, int(port)))
	em.wait_for_field()
	time.sleep(delay_time)
	#print("[i] Connected to host")
	
	# vtam enumeration loop
	while count < number_of_subsystems:
		# enter subsystem name at the VTAM prompt
		em.fill_field(21, 22, subsystems[count], len(subsystems[count]))
		em.send_enter()
		em.wait_for_field()
		time.sleep(delay_time)

		#message = em.string_get(22,1, 15)
		#print("[i] Message: ", message)
		if em.string_found(22, 1, 'Invalid Command'):
			#print("[-] Subsystem: " + subsystems[count] + " is not valid")
			None
		else:
			print("["+str(count)+"] Subsytem: " + subsystems[count] + " may be valid")
			None
			em.terminate()
			count += 1
			return count
		count += 1
		#print("["+str(count)+"]")
	# disconnect from host and kill subprocess
	em.terminate()
	return count

# define a list of subsystems
subsystems = file2list(vtam_list_location)
number_of_subsystems = len(subsystems)

progress = 0

print("[i] Attempting to enumerate " + str(number_of_subsystems) + " subsystems")

while progress < number_of_subsystems:
	progress = user_enum(progress, subsystems, number_of_subsystems)

