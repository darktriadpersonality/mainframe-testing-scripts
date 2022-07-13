import py3270
from py3270 import Emulator,CommandError,FieldTruncateError,TerminatedError,WaitError,KeyboardStateError,FieldTruncateError,x3270App,s3270App
import sys
import time
import signal

if len(sys.argv) <= 3:
	print("Usage: cicsEnum.py <host> <port> <path to CICS transaction list>")
	sys.exit()

host = sys.argv[1]
port = sys.argv[2]
trans_list_location = sys.argv[3]

delay_time = 0.2
cracking_loop_delay_time = 0.1

def file2list(filename):
	lines = []
	with open(filename) as file:
    		lines = file.readlines()
    		lines = [line.rstrip() for line in lines]
	return lines

######################################################
#     THIS CODE TAKEN FROM THE AWESOME CICSPWN       #
#       https://github.com/ayoul3/cicspwn            #
#     Thankyou Ayoul3 for sharing your knowledge     #
######################################################

# Override some behaviour of py3270 library 
class EmulatorIntermediate(Emulator):
	def __init__(self, visible=True, delay=0):
		Emulator.__init__(self, visible)
		self.delay = delay

	def send_enter(self): # Allow a delay to be configured
		self.exec_command('Enter')
		if self.delay > 0:
			sleep(self.delay)
    
	def send_clear(self): # Allow a delay to be configured
		self.exec_command('Clear')
		if self.delay > 0:
			sleep(self.delay)
            
	def send_eraseEOF(self): # Allow a delay to be configured
		self.exec_command('EraseEOF')
		if self.delay > 0:
			sleep(self.delay)
      
	def send_pf11(self):
		self.exec_command('PF(11)')
            
	def screen_get(self):
		response = self.exec_command('Ascii()')
		if ''.join(response.data).strip() == "":
		    sleep(0.5)
		    return self.screen_get()
		return response.data

	# Send text without triggering field protection
	def safe_send(self, text):
		for i in xrange(0, len(text)):
			self.send_string(text[i])
			if self.status.field_protection == 'P':
				return False # We triggered field protection, stop
		return True # Safe

	# Fill fields in carefully, checking for triggering field protections
	def safe_fieldfill(self, ypos, xpos, tosend, length):
		if length - len(tosend) < 0:
			raise FieldTruncateError('length limit %d, but got "%s"' % (length, tosend))
		if xpos is not None and ypos is not None:
			self.move_to(ypos, xpos)
		try:
			self.delete_field()
			if self.safe_send(tosend):
				return True # Hah, we win, take that mainframe
			else:
				return False # we entered what we could, bailing
		except CommandError, e:
			# We hit an error, get mad
			return False
			# if str(e) == 'Keyboard locked':

	# Search the screen for text when we don't know exactly where it is, checking for read errors
	def find_response(self, response):
		for rows in xrange(1,int(self.status.row_number)+1):
			for cols in xrange(1, int(self.status.col_number)+1-len(response)):
				try:
					if self.string_found(rows, cols, response):
						return True
				except CommandError, e:
					# We hit a read error, usually because the screen hasn't returned
					# increasing the delay works
					sleep(self.delay)
					self.delay += 1
					whine('Read error encountered, assuming host is slow, increasing delay by 1s to: ' + str(self.delay),kind='warn')
					return False
		return False
	
	def find_field_start_on_row(self,row):
		# This is as usual a horrible hack
		# rows start at 1 (not 0)
		# from what I can tell - if you get a SF(c0=c*) it means a start of field.
		# This is then what we are looking for
		
		for _ in xrange(0,2):
			response = self.exec_command('ReadBuffer(Ascii)')
			if ''.join(response.data).strip()=="":
				sleep(0.3)
			else:
				break
		else:
			if ''.join(response.data).strip()=="":
				raise Exception("Unable to retrieve buffer data")
		for counter, char in enumerate(response.data[row-1].split()):
			if char.startswith("SF(c0=c"):
				return counter+2 # +1 to convert the 0 based index to 1 based
								 # +1 to move to actual field
    
    # Get the current x3270 cursor position
	def get_pos(self):
		results = self.exec_command('Query(Cursor)')
		row = int(results.data[0].split(' ')[0])
		col = int(results.data[0].split(' ')[1])
		return (row,col)

	def get_hostinfo(self):
		return self.exec_command('Query(Host)').data[0].split(' ')
#######################################################
#     END OF CODE TAKEN FROM THE AWESOME CICSPWN      #
#          https://github.com/ayoul3/cicspwn          #
#######################################################
	
############################################################################
#                THIS CODE TAKEN FROM THE AWESOME GRUTE                    #
#       https://github.com/incendiary/Grute_pub/blob/master/Grute.py       #
#               Thankyou incendiary for sharing your knowledge             #
############################################################################	
# Buggy transactions that hang or crash CICS
cicsexceptions = ['AORQ', 'CEJR','CJMJ','CPCT','CKTI','CPSS','CPIR','CRSY','CSFU','CRTP','CSZI','CXCU','CXRE','CMPX','CKAM','CEX2','CEHP','CEHS','CSFR','CSFE']	
############################################################################
#                END OF CODE TAKEN FROM THE AWESOME GRUTE                  #
#       https://github.com/incendiary/Grute_pub/blob/master/Grute.py       #
############################################################################
	
def transaction_enum(count, transactions, number_of_transactions):
	class WrappedEmulator(EmulatorIntermediate):
	        x3270App.executable = 'x3270'
	        s3270App.executable = 's3270'  
	 
	# use the cicspwn modified emulator:
	em = WrappedEmulator(True) 

	# connect to host
	em.connect('%s:%d' % (host, int(port)))
	#em.wait_for_field()
	time.sleep(delay_time)
	#print("[i] Connected to host")
	
	em.send_string("CICS")
	em.send_enter()
	em.wait_for_field()
	time.sleep(delay_time)
	
	em.exec_command(b"Clear")
	#em.wait_for_field()
	time.sleep(delay_time)	
	
	# transaction enumeration loop
	while count < number_of_transactions:
		skip_transaction = False # by default, we will not skip the transaction
		# check to see if transaction is buggy - if it is, skip it:
		for buggy_transaction in cicsexceptions:
			if transactions[count] == buggy_transaction:
				 print("[" + str(count) + "] " + transactions[count] + " skipped as it could be buggy")
				 skip_transaction = True
		if not skip_transaction:
			# enter subsystem name at the VTAM prompt
			em.send_string(transactions[count])
			em.send_enter()
			time.sleep(cracking_loop_delay_time)

			#print(em.string_get(23,02,10))

			if em.string_found(24, 3, 'Check that the transaction name is correct'): # this message is returned when trans ID is not recognised
				print("[" + str(count) + "] " + transactions[count] + " is not valid")

			elif em.string_found(23, 02, 'DFHAC2206'): # this message is returned when the transaction ABENDs

				print("[" + str(count) + "] " + transactions[count] + " failed with ABEND")
				
			elif em.string_found(23, 02, 'DFHAC2001'): # this message is returned when trans ID is not recognised

				print("[" + str(count) + "] " + transactions[count] + " is not valid")	
				
			elif em.string_found(23, 02, 'DFHAC2016'): # this message is returned when transaction cannot run

				print("[" + str(count) + "] " + transactions[count] + " cannot run - missing program")
								
			elif em.string_found(23, 02, 'DFHRT4415'): # this message is returned when transaction forbidden from terminal invocation

				print("[" + str(count) + "] " + transactions[count] + " terminal invocation was forbidden")

			elif em.string_found(23, 02, 'DFHAC2028'): # this message is returned when transaction cannot be used

				print("[" + str(count) + "] " + transactions[count] + " cannot be used and has been ignored")
			else:
				print("[+] " + transactions[count] + " is valid")		
				#time.sleep(delay_time)
				# we have found a transaction now we need to escape from it
				em.send_pf3()
				time.sleep(delay_time)
				em.move_to(1,2)
				
				em.exec_command(b"Clear")
				time.sleep(delay_time)
								
			em.exec_command(b"Clear")
			time.sleep(cracking_loop_delay_time)
			
		count += 1
		
	return count

# define a list of transactions
transactions = file2list(trans_list_location)
number_of_transactions = len(transactions)

progress = 0

print("[i] Attempting to enumerate " + str(number_of_transactions) + " transactions")


while progress < number_of_transactions:
	progress = transaction_enum(progress, transactions, number_of_transactions)



