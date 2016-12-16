from databaseUtil import databaseAccess
from collections import defaultdict
from datetime import date
import cPickle as pickle
from util.zipDist import Zip_Codes
from util.pyzipcode import ZipCodeDatabase
import numpy
import random
PICKLE_DIRECTORY = "data/"
YEARS = ["2011","2012","2013","2014","2015"]
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
NUM_CLUSTERS = 10
MAX_ITERS = 5

class kMeans():
	def __init__(self, db, table, usePickle=True):

		def calculate_group_cov():
			'''
			Builds covariance map in the form:
				{loangroup1: {loangroup1: cov(1,1), loangroup2: cov(1,2)}, loangroup2: {etc}}
			Requires numpy.
			'''

			for k1, v1 in self.cash_flow_dict.iteritems():
				for k2, v2 in self.cash_flow_dict.iteritems():
					cov = numpy.cov(numpy.vstack(v1, v2))
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

		# want normalize home ownership (0, 1) with regards to miles otherwise wont do anything or have big effect.
			def cluster_points(loans, mu):
				
				def clusterAssignment(zc, zipCodeSet, ownBool):
					bestmukey = None
					bestmukeyDist = float("inf")
					for l in mu:
						iterZC = l[self.columns.index('zip_code')]
						if iterZC == zc:
							bestmukey = l
							break
						else:
							iZipCodeSet = [k for k in zipcodes if iterZC[:3] in k.zip]
							dist = 0
							for x in zipCodeSet:
								for y in iZipCodeSet:
									dist += zipDist.get_distance(x.zip, y.zip)
							length1 = len(zipCodeSet)
							length2 = len(iZipCodeSet)
							if length1 == 0: length1 = 1
							if length2 == 0: length2 = 1
							computedAvgDist = dist/(length1 * length2)
		 					if computedAvgDist < bestmukeyDist:
								bestmukey = l
								bestmukeyDist = computedAvgDist
					cache[zc] = bestmukey
					return bestmukey

				clusters  = {}
				cache = {}
				for l in loans:
					zc = l[self.columns.index('zip_code')]
					ho = l[self.columns.index('home_ownership')]
					if zc in cache:
						assignment = cache[zc]
					else:
						zipCodeSet = [k for k in zipcodes if zc[:3] in k.zip]
						assignment = clusterAssignment(zc, zipCodeSet, ho == "OWN")
						cache[zc] = assignment
					if assignment not in clusters: clusters[assignment] = []
					clusters[assignment].append(l)
				return clusters

			def reevaluate_centers(mu, clusters):
				def findClosestLoanWithZip(orig_zip):
					print orig_zip
					validNewMus = self.db.extract_loans_with_zip(orig_zip+"xx")
					mileRadiusCounter = 1
					while len(validNewMus) == 0:
						formattedZips = [z for z in zipcodes if orig_zip in z.zip]
						for i in formattedZips:
							closeZips = zipDist.close_zips(i, mileRadiusCounter)
							for cz in closeZips:
								validNewMus = self.db.extract_loans_with_zip(str(cz[:3]))
								if len(validNewMus) > 0: return validNewMus[0]
						mileRadiusCounter += 1
					print orig_zip, validNewMus[0]
					return validNewMus[0]

				newmu = []
				keys = sorted(clusters.keys(), key=lambda loan: loan[self.columns.index('zip_code')])
				for k in keys:
					zipCodeMean = 0
					for l in clusters[k]:
						print int(l[self.columns.index('zip_code')][:3])
						zipCodeMean += int(l[self.columns.index('zip_code')][:3])
					zipCodeMean /= len(clusters[k])
					newmu.append(findClosestLoanWithZip(str(zipCodeMean)))
				return newmu

			def has_converged(mu, oldmu):
				return set(mu) == set(oldmu)

			def find_centers(loans, K):
			# Initialize to K random centers
				oldmu = random.sample(loans, K)
				mu = random.sample(loans, K)
				i = 0
				while not has_converged(mu, oldmu) or i >= MAX_ITERS:
					oldmu = mu
					# Assign all points in loans to clusters
					clusters = cluster_points(loans, mu)
					# Reevaluate centers
					mu = reevaluate_centers(oldmu, clusters)
					i += 1
				return(mu, clusters)

			zcdb = ZipCodeDatabase()
			zipcodes = zcdb.find_zip()
			zipDist = Zip_Codes()
			return find_centers(self.loans, NUM_CLUSTERS)[1]

		def update_table_clusters(table):
			sorted_clusters = sorted(self.clusters.keys(), key=lambda loan: loan[self.columns.index('zip_code')])
			for i in range(len(sorted_clusters.keys())):
				for loan in sorted_clusters.keys()[i]:
					self.db.updateTableValue(table, {id: loan[self.columns.index("id")]}, "cluster", i)

		def extract_term_length(table):
			if table.find("Sixty") > -1: return 60
			return 36

		self.db = db
		self.termLength = extract_term_length(table)
		if usePickle:
			self.clusters = pickle.load(open(PICKLE_DIRECTORY+table+"clusters.p", 'rb'))
			self.covariances = pickle.load(open(PICKLE_DIRECTORY+table+"covariances.p",'rb'))
		else:
			self.loans = db.extract_table_loans(table)
			self.columns = db.getColumnNames(table)
			self.clusters = cluster_loans()
			update_table_clusters(table)
			pickle.dump(self.clusters, open(PICKLE_DIRECTORY+table+"clusters.p","wb"))

			self.cash_flow_dict = generate_cash_flow_vectors()
			# self.cluster_variances = cluster_variance()
			self.covariances = calculate_group_cov()
			pickle.dump(self.covariances, open(PICKLE_DIRECTORY+table+"covariances.p","wb"))

<<<<<<< HEAD
db = databaseAccess()
kmeans = kMeans(db, "TrainSixty", False)
		
=======
<<<<<<< HEAD
=======
if __name__ == "__main__":
	db = databaseAccess()
	kmeans = kMeans(db, "TrainSixty", False)

>>>>>>> 87423e9bc4469bbccf3c24933296f08af2007f46

if __name__ == "__main__":
	db = databaseAccess()
	kmeans = kMeans(db, "TrainSixty")
>>>>>>> abd97ce543bcea3920a8c90a42bd12377ea6c061
