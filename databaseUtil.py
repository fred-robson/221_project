#Series of classes/functions for accesing the database
import sqlite3 as lite
import sys,csv
import random
TABLE = 'loan'
DB_NAME = 'database.sqlite'
STR_TYPES = ['CHARACTER(20)', 'VARCHAR(255)', 'VARYING CHARACTER(255)', 'NCHAR(55)', 'NATIVE CHARACTER(70)', 'NVARCHAR(100)', 'TEXT']
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
	# Class that allows easy access to database functionality 
	def __init__(self):
		self.cur, self.con = set_up_db()
		res = self.con.execute("select * from loan")
		self.col_name_list = {t[0]:i for i,t in enumerate(res.description)}
		self.tables = ["TestThirtySix", "TrainThirtySix", "TestSixty", "TrainSixty"]

	def extract_table_loans(self, table_name):
		execute_string = ("SELECT * FROM {}").format(table_name)
		self.cur.execute(execute_string)
		return self.cur.fetchall()

	# Extracting loans based on term -- 36 or 60.
	def extract_term_loans(self, term):
		execute_string = ("SELECT * FROM {} WHERE term = ' {} months'").format(TABLE, term)
		self.cur.execute(execute_string)
		return self.cur.fetchall()

	# Randomly distributes data amongst the test and train data.
	def partition_data(self, features):
		def populate_table(table_name, loan_set):
			for loan in loan_set:
				query = "INSERT OR IGNORE INTO {} VALUES ({},".format(table_name, loan[0])
				for k in features.keys():
					if features[k] in STR_TYPES: query += '\''
					query += "{}".format(loan[self.col_name_list[k]])
					if features[k] in STR_TYPES: query += '\''
					query += ","
				query = query[:-1] + ")"
				self.cur.execute(query)
				self.con.commit()


		loans = self.extract_term_loans(36)
		n = len(loans) / 2
		random.shuffle(loans)
		populate_table("TestThirtySix", loans[:n])
		print "finished thirty six test loans"
		populate_table("TrainThirtySix", loans[n:])
		print "finished thirty six loans"

		loans = self.extract_term_loans(60)
		n = len(loans) / 2
		random.shuffle(loans)
		populate_table("TestSixty", loans[:n])
		print "finished sixty test loans"
		populate_table("TrainSixty", loans[n:])
		print "finished sixty loans"

	# Features dict => { "column_name": DATA_TYPE } 
	# Refer to data/data_types.txt.
	def add_columns(self, features):
		for i in self.tables:
			for k, v in features.items():
				query = "ALTER TABLE {} ADD COLUMN {} {}".format(i, k, v)
				self.cur.execute(query)
				self.con.commit()

	# Features dict => { "column_name": DATA_TYPE } 
	# Refer to data/data_types.txt.
	def update_table_features(self, features):
		for i in self.tables:
			self.cur.execute("DROP TABLE IF EXISTS {}".format(i))
			self.cur.execute("CREATE TABLE {} (id INT PRIMARY KEY)".format(i))
		self.add_columns(features)
		self.partition_data(features)

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

#db = databaseAccess()
flist = {}
flist["term"] = "TEXT"
flist["funded_amnt"] = "INT" 
flist["installment"] = "FLOAT"
flist["total_pymnt"] = "INT"
flist["issue_d"] = "VARCHAR(255)" 
flist["zip_code"] = "TEXT" 
flist["last_pymnt_d"] = "TEXT" 
flist["last_pymnt_amnt"] = "FLOAT"
 
#db = databaseAccess()
#db.update_table_features(flist)
# db.update_table_features(flist)
# db.partition_data({"total_pymnt": "INT", "funded_amnt": "INT"})
#db.add_columns()

