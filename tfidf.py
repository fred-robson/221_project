import sqlite3 as lite
import math
from util.porter import stem
# from util.textblob import TextBlob, Word, Blobber
# from util.textblob.classifiers import NaiveBayesClassifier
# from util.textblob.taggers import NLTKTagger
# from util.textblob import TextBlob as tb
import re, string

class TFIDF_Extractor():
	def tf(self, word, doc):
		return float(doc.split().count(word)) / float(len(doc.split()))

	def n_containing(self, word, doclist):
		return sum(1 for doc in doclist if word in doc.split())

	def idf(self, word, doclist):
		return math.log(len(doclist) / float((1 + self.n_containing(word, doclist))))

	def tfidf(self, word, doc, doclist):
		return self.tf(word, doc) * self.idf(word, doclist)

	def __init__(self, db):
		'''
		Class for TF-IDF Analysis. Handles basic text sanitization across all loans.
		Creates two documents -- one for defaulted loan descriptions and one for non-defaulted
		and current loan descriptions.
		'''

		def compileDescriptions(loan_set):
		'''
		Iterates through descriptions of each loan in set, sanitizes, then compiles into a single
		document intended for tfidf analysis. 

		Sanitization includes stripping of html tags, non English words, standardizing capitalization and word length.
		Return: result_document (Compiled Loan Descriptions)
		'''
			def sanitize_desc(desc):
				clean_desc = ""
				for word in desc.split():
					word = stem(word.lower()) # lowercases word and porter-stemming algorithm.
					if len(word) >= 4 and word in self.engDict: # makes sure it's valid English.
						clean_desc += word + " "
				return clean_desc

			result_document = ""
			for loan in loan_set:
				description = loan[self.columns.index('desc')]
				if description != None: result_document += sanitize_desc(description) + " "
			return result_document

		self.db = db
		self.columns = self.db.getColumnNames("loan")
		with open("engDict.txt", "r") as f:
			self.engDict = {line.strip() for line in f}

		defaulted_loans = self.db.extract_loans_with_status("Charged Off")
		nondefaulted_loans = self.db.extract_loans_with_status("Fully Paid") + self.db.extract_loans_with_status("Current")
		documentList = [compileDescriptions(defaulted_loans), compileDescriptions(nondefaulted_loans)]

		'''
		Computes the TF-IDF score for each word in each document. 
		TF-IDF Class returns an array where array[0] is an array of the top scoring words
		for defaulted loans and array[1] is an array of top scoring words for nondefaulting loans.
		'''
		tfidf_scores = []
		wordToScoreCache = {}
		for i in range(len(documentList)):
			print("Top words in document {}".format(i + 1))
			scores = {}
			for word in documentList[i].split():
				if word not in wordToScoreCache:
					scores[word] = self.tfidf(word, documentList[i], documentList)
					wordToScoreCache[word] = scores[word]
				else:
					scores[word] = wordToScoreCache[word]
			# scores = {word: self.tfidf(word, documentList[i], documentList) for word in documentList[i].split()}
			sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
			for word, score in sorted_words[:20]:
				print("\tWord: {}, TF-IDF: {}".format(word, round(score, 5)))
			tfidf_scores += sorted_words
		return tfidf_scores

