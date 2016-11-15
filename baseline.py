from databaseUtil import databaseAccess

class Baseline():

	def __init__(self, month):
		self.db = databaseAccess()
		self.loans = self.db.get_loans_issued_in(month)

	def percentReturn(self):
		numLoans = len(self.loans)
		total_pymnt = self.db.col_name_list["total_pymnt"]
		funded_amnt = self.db.col_name_list["funded_amnt"]

		return sum(map(lambda l : (l[total_pymnt] / l[funded_amnt]) / numLoans, self.loans))
		# return totalPayments / totalFunded

for year in ["2011","2012","2013","2014","2015"]:
	for month in ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]: 
		date = "{}-{}".format(month,year)
		
		for term in [36,60]:
			b = Baseline(date)
			print date, term, b.percentReturn()





