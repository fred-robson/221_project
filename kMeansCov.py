from databaseUtil import databaseAccess
from collections import defaultdict
from datetime import date
import numpy

YEARS = ["2011","2012","2013","2014","2015"]
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

class kMeans():
	def __init__(self, db, table):

		def calculate_group_cov():
			# builds covariance map for each cluster
			covariances = defaultdict(lambda: defaultdict(int))
			for k1, v1 in self.cash_flow_dict.iteritems():
				for k2, v2 in self.cash_flow_dict.iteritems():
					cov = numpy.cov(numpy.vstack((v1, v2)))
					covariances[k1][k1] = cov[0][0]
					covariances[k1][k2] = cov[0][1] 
					covariances [k2][k1] = cov[1][0]
					covariances[k2][k2] = cov[1][1]
			return covariances


		def contribution_to_month(l, curr_date):
			# Determines if loan is active during given month/year.
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
			d = defaultdict(list)
			# cluster => [monthly cash flow]
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

		def cluster_loans():
			# clustering by zip_code
			d = defaultdict(list)
			for l in self.loans:
				zip_code = l[self.columns.index('zip_code')]
				if zip_code in d:
					d[zip_code].append(l)
				else:                                            
					d[zip_code] = [l]
			return d

		self.db = db
		self.loans = db.extract_table_loans(table)
		self.columns = db.getColumnNames(table)
		self.clusters = cluster_loans()
		self.cash_flow_dict = generate_cash_flow_vectors()
		self.covariances = calculate_group_cov()


# db = databaseAccess()
# kmeans = kMeans(db, "TrainSixty")
