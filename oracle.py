import csv,sys, Queue 
import sqlite3 as lite 
import  databaseUtil

TERMS = [36,60] #Possible lengths of loans
DATA_FILE = 'data/loan.csv'



class oracle():
	db = databaseUtil.databaseAccess()

	@staticmethod 
	def choose_best_portfolio(intitial_investment, month, term):
		'''
		Chooses the optimal portfolio of loans for a chosen issue date and term
		@params: 
			initial_investment: the $value of the initial investment (float)
			issue_date: the issue date of the loans (string) eg "Mar-2011"
			term
		'''
		loans = oracle.db.get_loans_issued_in(month)
		pq = Queue.PriorityQueue()
		for l in loans:
			total_payment = l[39]
			funded_amnt = l[4]
			percent_return_td  = total_payment/funded_amnt
			pq.put(percent_return_td,loan)

oracle.choose_best_portfolio(1,"Mar-2014",36)

