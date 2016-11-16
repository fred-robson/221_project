#Series of classes/functions for accesing the database
import sqlite3 as lite
import sys,csv

TABLE = 'loan'
DB_NAME = 'data/database.sqlite'

def set_up_db():
	'''
	Accesses the sql database
	@return: 
		- returns cursor and connection 
	'''
	con = None
	try:
	    con = lite.connect(DB_NAME)    
	    cur = con.cursor()
	    return cur,con
	except lite.Error, e:	    
	    print "Error %s:" % e.args[0]
	    sys.exit(1)	    

class databaseAccess():
	#Class that allows easy access to database functionality 
	def __init__(self):
		self.cur, self.con = set_up_db()
		res = self.con.execute("select * from loan")
		self.col_name_list = {t[0]:i for i,t in enumerate(res.description)}

	def get_loans_issued_in(self, month, term=36):
		'''
		Returns a list of all the loans issued in @month
		@params: 
			month: The month the loan was issued in eg "Mar-2011"
			return: a list of tuples, where each tuple is a single loan
		'''
		execute_string = ("SELECT * FROM {} WHERE issue_d = '{}' AND term = ' {} months'").format(TABLE,month,term)
		self.cur.execute(execute_string)
		return self.cur.fetchall()


#For testing the data...
if __name__ == "__main__":
	with open(data)
