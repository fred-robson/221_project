import csv,sys
import sqlite3 as lite 

TERMS = [36,60] #Possible lengths of loans
DATA_FILE = 'data/loan.csv'

def set_up_db():
	try:
	    con = lite.connect('data/database.sqlite')    
	    cur = con.cursor()
	    return cur
    
	except lite.Error, e:	    
	    print "Error %s:" % e.args[0]
	    sys.exit(1)
	    
	finally:
	    if con:
	        con.close()

def choose_best_portfolio(intitial_investment, issue_date, term):
	'''
	Chooses the optimal portfolio of loans for a chosen issue date and term
	@params: 
		initial_investment: the $value of the initial investment (float)
		issue_date: the issue date of the loans (string)
		term

	'''
	pass

set_up_db()