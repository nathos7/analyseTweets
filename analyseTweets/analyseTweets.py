#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import networkx as nx
import matplotlib.pyplot as plt
from os import listdir
from os.path import isfile, join
from pickle import load 
import operator
import argparse
import sys
from pprint import pprint

# Parsing des arguments de l'utilisateur
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dict", dest='TweetsDictFile', default="tweets.dict", 
	action='store_const', const=True, help="Dict file with words")
parser.add_argument("-o", "--output-graph", dest='save_graph', default="graph.gml", help="name of file for output")
parser.add_argument("-s", "--stopListSize", type=int, dest='stopListSize', default=220, help="size of stoplist")
parser.add_argument("-m", "--minOccurences", type=int, dest='minOccurences', default=6, 
	help="minimum number of occurence for a word to be noted")
parser.add_argument("-p", "--percentage-threshold", type=float, dest='seuil', default=62, 
	help="Percentage of closeness necessary to keep the edge")

parser.set_defaults(areArgsFiles=True)
parser.add_argument("-v", "--verbose", dest='TEST_MODE', action='store_const', const=True, default=False, 
	help="Put on the verbose mode")
args = parser.parse_args()

# Variables globales
TweetsDictFile = args.TweetsDictFile
TweetsDict = {}
stopListSize = args.stopListSize
minOccurences = args.minOccurences
seuil = args.seuil
seuil = (seuil/20+30)/100
stopList=["Monsieur"]
TEST_MODE=args.TEST_MODE
wordsDicts={}
proxTab=[]
totalWord = dict()

# Open and load file
def pickeLoad(filePath) :
	file = open(filePath, 'rb')
	obj = load(file)
	file.close()
	return obj

def createStopList(NFirstWords=stopListSize) :
	global stopList
	wordsDict = TweetsDict["allWords"]
	sorted_words = sorted(wordsDict.items(), key=operator.itemgetter(1))
	for (w, oc) in sorted_words[-NFirstWords:] : stopList.append(w)

# Fonction chargeant un fichier dict, en supprimant les mots trop peu présents, et les mots qui le sont trop
def loadDict(userName, minOccurences=minOccurences, deleteNFirst=20, stopList=[]) :
	wordsDict = TweetsDict['users'][userName]
	# Delete rare words, stop-listed words, and 3 letters long or less words
	#if TEST_MODE : print("*** Mots rares supprimés ***") #Test empirique: supprime-t-on trop de mots?
	for w in list(wordsDict.keys()).copy() :
		if wordsDict[w] <= minOccurences : 
			if TEST_MODE and wordsDict[w] > minOccurences-2 : print(w, "->", wordsDict[w])
			wordsDict.pop(w)
		elif w in stopList or len(w) <= 3 : wordsDict.pop(w)
	# Delete over-occuring words
	#if TEST_MODE : print("\n\n*** Mots trop présents supprimés ***")		# idem
	sorted_words = sorted(wordsDict.items(), key=operator.itemgetter(1))
	for (w, oc) in sorted_words[-deleteNFirst:] :
		wordsDict.pop(w,-1)
		#if TEST_MODE : print(w)
	#if TEST_MODE : print()
	#return sorted(wordsDict.items(), key=operator.itemgetter(1))  # to visualize easily
	for w in list(wordsDict.keys()).copy() :
		totalWord[userName] = totalWord.get(userName, 0) + wordsDict[w] 
	return wordsDict

# Récupère tous les fichiers tweets et les chargent dans le tableau wordsDicts
def getAllDicts() :
	for n in TweetsDict['users'].keys() : 
		wordsDicts[n] = loadDict(n)
	deleteEmptyDicts()
	return wordsDicts

def deleteEmptyDicts(minMots=10) :
	for p in list(wordsDicts.keys()).copy() :
		if len(wordsDicts[p]) < minMots : wordsDicts.pop(p)

# Première méthode : on calcule la différence de fréquences de chaque mot
def proximiteLinguistique1(t1, t2) :
	dictT1 = wordsDicts[t1] ; dictT2 = wordsDicts[t2]
	total1 = totalWord[t1] ; total2 = totalWord[t2]
	s = 0
	for w in dictT1.keys() :
		s += min(dictT1[w]/total1, dictT2.get(w, 0)/total2)
	return s

# Deuxième méthode : on prend le nb d'occurences le plus bas pour chaque mot commun, 
# et on divise par la moyenne d'occurences totales
def proximiteLinguistique2(t1, t2) :
	dictT1 = wordsDicts[t1] ; dictT2 = wordsDicts[t2]
	s = 0
	for w in dictT1.keys() :
		s += min(dictT1[w], dictT2.get(w, 0))
	return s/((totalWord[t1]+totalWord[t2])/2)

# Troisième méthode : multiplier les fréquences pour chaque mot
def proximiteLinguistique3(t1, t2) :
	dictT1 = wordsDicts[t1] ; dictT2 = wordsDicts[t2]
	s = 0
	for w in dictT1.keys() :
		s += dictT1[w] * dictT2.get(w, 0)
	return s/((totalWord[t1]+totalWord[t2])/6)


def keepSignificantEdges(s=seuil) :
	while(proxTab[-1][2] < s) : proxTab.pop()

# Outil d'analyse
# Fonction, qui, pour une liste de comptes donnée, fournit les N mots les plus communéments fréquents
def findNcommonWords(tList, n=5) :
	listeMots = [] ; mots_scores = []
	for t in tList : 
		listeMots.extend(list(wordsDicts[t].keys()))
	listeMots = set(listeMots)
	for w in listeMots :
		if w in stopList : continue
		s=0
		for t in tList :
			s += wordsDicts[t].get(w,0)/max(totalWord[t],1)*100
		mots_scores.append((w, s))
	mots_scores = sorted(mots_scores, key=operator.itemgetter(1), reverse=True)
	for (w,sc) in mots_scores[:n] : 
		print(w,":",'%.2f'%sc)
	print()


PROX_FUNCTION = proximiteLinguistique1
TweetsDict = pickeLoad(TweetsDictFile)
createStopList()
getAllDicts()

if TEST_MODE : 
	for p in wordsDicts.keys() : print(p, "|", len(wordsDicts[p]))

wordsDicts2 = list(wordsDicts.keys()).copy()
for t1 in wordsDicts.keys() :
	wordsDicts2.remove(t1) # Ne pas repasser sur t2 t1 plus tard
	for t2 in wordsDicts2 : proxTab.append((t1,t2, PROX_FUNCTION(t1, t2)))

proxTab = sorted(proxTab, key=operator.itemgetter(2), reverse=True)

# Save the entire Graph
Gall = nx.Graph()
Gall.add_weighted_edges_from(proxTab)
nx.write_gml(Gall, args.save_graph)

# Draw the restricted graph
keepSignificantEdges()
G = nx.Graph()
G.add_weighted_edges_from(proxTab)

if TEST_MODE :
	for edge in proxTab : 
		print(edge[0], "-", edge[1])
		findNcommonWords([edge[0], edge[1]]) 

# Draw Graph
nx.draw(G, with_labels=True, font_weight='bold')
plt.show()

"""
# Fonction test pour visualiser les dictionnaires d'occurences
def visualizeDict(t) :
	wordsDict = wordsDicts[t]
	sorted_words = sorted(wordsDict.items(), key=operator.itemgetter(1))
	for (w,oc) in sorted_words : print(w,':',oc)
	print("***********\n")
print('\n\n')
print(proxTab)
visualizeDict('@AChristine_Lang')
visualizeDict('@AbadieCaroline')
visualizeDict('@AdrienMorenas')

findNcommonWords(["@RNational_off", "@J_Bardella", "@NicolasBay_", 
	"@ericcoquerel", "@MLP_officiel", "@fxbellamy", "@david_rachline"], 6)

findNcommonWords(["@JLMelenchon", "@Francois_Ruffin", "@jclagarde", 
	"@FranceInsoumise", "@GenerationsMvt", "@benoithamon", "@partisocialiste"], 10)

findNcommonWords(["@faureolivier", "@GenerationsMvt", "@benoithamon", "@partisocialiste"], 10)

findNcommonWords(["@JLMelenchon", "@Francois_Ruffin", "@jclagarde", 
	"@FranceInsoumise"], 10)


"""