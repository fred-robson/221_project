from databaseUtil import databaseAccess
from collections import defaultdict
from datetime import date
import cPickle as pickle
import numpy
PICKLE_DIRECTORY = "data/"
YEARS = ["2011","2012","2013","2014","2015"]
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

class kMeans():
	def __init__(self, db, table, usePickle=True):

		def calculate_group_cov():
			'''
			Builds covariance map in the form:
				{loangroup1: {loangroup1: cov(1,1), loangroup2: cov(1,2)}, loangroup2: {etc}}
			Requires numpy.
			'''
			covariances = {}
			for k, v in self.cluster_variances.iteritems():
				covariances[k] = {}
			# covariances = defaultdict(lambda: defaultdict(int))

			# for k1, v1 in tqdm(self.cluster_variances.iteritems(),total=len(self.cluster_variances)):
			for k1, v1 in self.cluster_variances.iteritems():
				for k2, v2 in self.cluster_variances.iteritems():
					# print k1, k2
					print v1, v2
					cov = numpy.cov(v1, v2)
					print cov
					covariances[k1][k1] = cov[0][0]
					covariances[k1][k2] = cov[0][1] 
					covariances [k2][k1] = cov[1][0]
					covariances[k2][k2] = cov[1][1]
			return covariances


		def contribution_to_month(l, curr_date):
			'''
			Determines if loan is active during given month/year. Takes in a loan
			and a date to compare it against in the form 'Jan-2015'.  

			It extracts the issue date, last payment date, term length, and then 'add_months'
			to generate what the last payment date should be given there is no default.  So if 
			last payment date and this projected date do not align, we know we have default so 
			we are actually losing money in those months.
			'''
			def add_months(d, months_to_add):
				month = d.month - 1 + months_to_add
				year = int(d.year + month / 12)
				month = month % 12 + 1
				return date(year, month, 1)


			loan_term = int(l[self.columns.index('term')].split()[0])
			loan_issue_date = l[self.columns.index('issue_d')]
			loan_last_pymnt_date = l[self.columns.index('last_pymnt_d')]
			# print loan_issue_date, loan_last_pymnt_date
			if loan_last_pymnt_date == "None": return l[self.columns.index('installment')]

			issue_month = MONTHS.index(loan_issue_date[: loan_issue_date.index('-')]) + 1
			issue_year = int(loan_issue_date[loan_issue_date.index('-') + 1:])
			issue_date = date(issue_year, issue_month, 1)

			last_month = MONTHS.index(loan_last_pymnt_date[: loan_last_pymnt_date.index('-')]) + 1
			last_year = int(loan_last_pymnt_date[loan_last_pymnt_date.index('-') + 1:])
			last_date = date(last_year, last_month, 1)
			projected_end_date = add_months(issue_date, loan_term)
			if issue_date < curr_date and curr_date < last_date:
				return l[self.columns.index('installment')] # installment
			if issue_date < curr_date and curr_date == last_date:
				return l[self.columns.index('last_pymnt_amnt')] # last_pymnt_amnt instead of installment.
			if last_date < curr_date and curr_date <= projected_end_date:
				return -l[self.columns.index('installment')] # -installment because default
			return 0 # loan not active

		def generate_cash_flow_vectors():
			'''
			For each cluster: 
				Creates a vector of cash flows for every month by adding up all of the installments of
				the loans in group.
			Returns a map of cluster => cash_flow_vector[] 
			'''
			d = defaultdict(list)
			for k, v in self.clusters.iteritems():
				cash_flow = []
				for year in YEARS:
					for month in range(1, len(MONTHS) + 1):
						monthly_cash_flow = 0
						for loan in v:
							monthly_cash_flow += contribution_to_month(loan, date(int(year), month, 1)) # if contributing to monthly cash flow.
						cash_flow.append(monthly_cash_flow)
				d[k] = cash_flow				
			return d

		# variance = sum((x/row["funded_amnt"] - expReturn)**2 for x in allReturns)/(len(allReturns)-1)
		def cluster_variance():
			def months_paid(l):
				def add_months(d, months_to_add):
					month = d.month - 1 + months_to_add
					year = int(d.year + month / 12)
					month = month % 12 + 1
					return date(year, month, 1)


				loan_term = int(l[self.columns.index('term')].split()[0])
				loan_issue_date = l[self.columns.index('issue_d')]
				loan_last_pymnt_date = l[self.columns.index('last_pymnt_d')]
				# print loan_issue_date, loan_last_pymnt_date
				if loan_last_pymnt_date == "None": loan_last_pymnt_date = 'Jun-2016'

				issue_month = MONTHS.index(loan_issue_date[: loan_issue_date.index('-')]) + 1
				issue_year = int(loan_issue_date[loan_issue_date.index('-') + 1:])
				issue_date = date(issue_year, issue_month, 1)

				last_month = MONTHS.index(loan_last_pymnt_date[: loan_last_pymnt_date.index('-')]) + 1
				last_year = int(loan_last_pymnt_date[loan_last_pymnt_date.index('-') + 1:])
				last_date = date(last_year, last_month, 1)
				projected_end_date = add_months(issue_date, loan_term)

				if last_date < projected_end_date:
					return self.db.monthsDifference((last_date.month, last_date.year), (issue_date.month, issue_date.year))
				return loan_term

			d = {}
			for k,v in self.clusters.iteritems():
				clusterReturns = []
				total_funded_amt = 0
				for loan in v:
					issue_date = self.db.stringToDate(loan[self.columns.index('issue_d')])
					loan_term = int(loan[self.columns.index('term')].split()[0])
					loanMonthsCompleted = months_paid(loan)
					total_funded_amt += loan[self.columns.index('installment')] * min(loan_term, self.db.monthsDifference((5, 2015), issue_date))
					clusterReturns.append(loanMonthsCompleted * loan[self.columns.index('installment')])

				expReturn = (sum(clusterReturns)/total_funded_amt)/len(clusterReturns)
				if len(clusterReturns) > 1:
					variance = sum((x/total_funded_amt - expReturn)**2 for x in clusterReturns)/(len(clusterReturns)-1) #-1 for sample
					d[k] = variance
			return d

		'''
		Partitions loans based on first two numbers of zip_code. 
		Returns map of cluster_id (zip_code) => a vector of all loans assigned.
		'''
		def cluster_loans():
			# clustering by zip_code
			d = defaultdict(list)
			for l in self.loans:
				zip_code = l[self.columns.index('zip_code')]
				z = list(zip_code)
				z[2] = 'x'
				zip_code = "".join(z)
				if zip_code in d:
					d[zip_code].append(l)
				else:                                            
					d[zip_code] = [l]

			return d

		def extract_term_length(table):
			if table.find("Sixty") > -1:
				return 60
			else:
				return 36

		self.db = db
		self.termLength = extract_term_length(table)
		if usePickle:
			self.covariances = pickle.load(open(PICKLE_DIRECTORY+str(self.termLength)+"covariances.p",'rb'))
		else:
			self.loans = db.extract_table_loans(table)
			self.columns = db.getColumnNames(table)
			self.clusters = cluster_loans()
			# self.cash_flow_dict = generate_cash_flow_vectors()
			self.cluster_variances = cluster_variance()
			self.covariances = calculate_group_cov()
			pickle.dump(self.covariances, open(PICKLE_DIRECTORY+str(self.termLength)+"covariances.p","wb"))

db = databaseAccess()
kmeans = kMeans(db, "TrainSixty", False)


