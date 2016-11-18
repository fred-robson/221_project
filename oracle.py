import csv,sys, Queue
import sqlite3 as lite 
import  databaseUtil
from tqdm import tqdm

TERMS = [36,60] #Possible lengths of loans

class oracle():
	db = databaseUtil.databaseAccess()

	@staticmethod 
	def choose_best_portfolio(initial_investment, month, term):
		'''
		Chooses the optimal portfolio of loans for a chosen issue date and term
		@params: 
			initial_investment: the $value of the initial investment (float)
			issue_date: the issue date of the loans (string) eg "Mar-2011"
			term: how long the loan is (36 or 60) in months
			return: a list of the loans invested in. [(return to date, funded amount, loan row)]
		'''
		loans = oracle.db.get_loans_issued_in(month,term)
		pq = Queue.PriorityQueue()
		for l in loans:
			total_payment = l[39]
			funded_amnt = l[4]
			percent_return_td  = total_payment/funded_amnt
			pq.put((-percent_return_td,l)) #negative to put highest returns at front of queue
		
		invested_loans = []
		invested = 0
		while invested<initial_investment:
			
			percent_return_td,l = pq.get()
			funded_amnt = l[4]
			#invest in part of loan to reach initial investment
			if funded_amnt+invested>initial_investment:
				funded_amnt = initial_investment - invested
			invested+=funded_amnt
			invested_loans.append((-percent_return_td,funded_amnt, l))
			if pq.qsize == 0: return None
		return invested_loans

	@staticmethod
	def average_return(investments):
		#Works out the overall return to date of a portfolio in the form [(return to date, funded amount, loan)] 
		return sum(x[0]*x[1] for x in investments)/sum(x[1] for x in investments)


for year in ["2011","2012","2013","2014","2015"]:
	for month in ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]: 
		date = "{}-{}".format(month,year)
		for term in [36,60]:
			portfolio = oracle.choose_best_portfolio(100000,date,term)
			print date,term,oracle.average_return(portfolio)

