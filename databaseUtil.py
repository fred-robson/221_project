#Series of classes/functions for being used 
import sqlite3 as lite
import sys,csv

TABLE = 'loan'
DB_NAME = 'data/database.sqlite'

def set_up_db():
	'''
	
	'''
	con = None
	try:
	    con = lite.connect(DB_NAME)    
	    cur = con.cursor()
	    return cur
	except lite.Error, e:	    
	    print "Error %s:" % e.args[0]
	    sys.exit(1)	    

class databaseAccess():
	#Class that allows easy access to database functionality 
	def __init__(self):
		self.cur = set_up_db()
		self.columns=[]
		with open("data/columns.txt") as file:
			for x in file: self.columns.append(x.strip())

	def get_loans_issued_in(self, month):
		'''
		Returns a list of all the loans issued in @month
		@params: 
			month: The month the loan was issued in eg "Mar-2011"
			return: a list of tuples, where each tuple is a single loan
		'''
		execute_string = ("SELECT * FROM {} WHERE issue_d = '{}'").format(TABLE,month)
		self.cur.execute(execute_string)
		return self.cur.fetchall()


