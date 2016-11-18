#Class that allows you to calculate the optimal portfolio
import util.machineLearningUtil as mlUtil
import sys
class optimalPortfolio():

	def __init__(self, possibleLoans, covariances, riskFreeReturn):
		'''	
		Initializes a portfolio
		@params: 
			- possibleLoans: dictionary of the form {loan_id: {expR:1.3, var:1.2 , loanGroup: 1,....}}
			- covariances: {loanGroup1:{loanGroup1: cov(1,1), loanGroup1: cov(1,2)....}, loanGroup2:...}
			- riskFreeReturn: %return of risk free bonds
		
		'''
		self.possibleLoans = possibleLoans
		self.covariances = covariances
		self.weights = {l: 1.0/len(self.possibleLoans) for l in possibleLoans}#initialize to equally weighted
		self.riskFreeReturn = riskFreeReturn

	def expectedReturn(self): 
		#Calculates the expected return of the portfolio using the current weights
		return sum(self.weights[l]*lInfo["expR"] for l,lInfo in self.possibleLoans.iteritems())
		
	def portfolioVariance(self): 
		#Calculates the variance of the portfolio using the current weights
		from_var = sum(self.weights[l]**2 * lInfo["var"] for l,lInfo in self.possibleLoans.iteritems())
		from_covar = 0
		for li, liInfo in self.possibleLoans.iteritems():
			for lj, ljInfo in self.possibleLoans.iteritems():
				#Variances have already been included in from_var
				if(li!=lj): from_covar+=self.weights[li]*self.weights[lj]*self.covariances[liInfo["loanGroup"]][ljInfo["loanGroup"]]
		return from_var+from_covar

	def sharpesRatio(self):
		#Returns the sharpe's ratio value
		return (self.expectedReturn() - self.riskFreeReturn)/(self.portfolioVariance()**(1.0/2))

	def sharpesRatioGradient(self):
		'''
		Calculates the gradient of sharpes ratio
		delta(Sharpe)/delta(w_i) = 
		r_i/Var(Portfolio) - Sum(w_j*Cov(i,j))(E(R_portfolio) - risk_free)/Var(portfolio)^3/2 
		'''
		expectedReturn = self.expectedReturn()
		var = self.portfolioVariance()
		sd = var**(1.0/2)
		grad = {}
		for li, liInfo in self.possibleLoans.iteritems():
			ri = liInfo["expR"]
			sumWeightCov = 0
			for lj,ljInfo in self.possibleLoans.iteritems():
				if(lj==li): cov =liInfo["var"]
				else: cov = self.covariances[liInfo["loanGroup"]][ljInfo["loanGroup"]]
				sumWeightCov+=self.weights[lj]*cov
		
			grad[li] = ri/sd - (sumWeightCov*(expectedReturn-self.riskFreeReturn))/(sd**3)		
		return grad

	def normalizeWeights(self):
		#Normalizes the weights so that they sum to 1
		totalSum = sum(wVal for _,wVal in self.weights.iteritems() if wVal>0)
		normWeights = {}
		for l,wVal in self.weights.iteritems():
			if(wVal < 0): normWeights[l] = 0.0001 #Ensures that weight>0
			else: normWeights[l] = wVal/totalSum
		self.weights = normWeights
		

	def findOptimalPortfolio(self,numIters,eta):
		'''
		Uses gradient descent to find the portfolio that maxmizes Sharpes Ratio.
		Updates self.weights to that optimal porfolio
		@params: 
			- numIters: number of iterations for gradient descent
			- eta: the step size
		'''
		for step in range(numIters):
			grad = self.sharpesRatioGradient()
			updatedWeights = {li: self.weights[li] + (eta * grad[li])  for li in self.weights}
			self.weights = updatedWeights
			self.normalizeWeights()

def test(): 
	possibleLoans = {1:{"expR":1,"var":1,"loanGroup":1},2:{"expR":10,"var":2,"loanGroup":1}}
	covariances = {1:{1:-0.02}}
	p1 = optimalPortfolio(possibleLoans,covariances,0) 
	p1.weights = {1:5000,2:50000}
	p1.findOptimalPortfolio(10000,0.0001)
	print p1.weights


if __name__ == "__main__":
	test()





