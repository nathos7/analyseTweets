#! /usr/bin/python3

import got3
import sys
import re
from french_lefff_lemmatizer.french_lefff_lemmatizer import FrenchLefffLemmatizer
import pickle
import argparse
from p_tqdm import p_umap 

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument("-f", "--file", 	dest='areArgsFiles', action='store_const', const=True,	help="arguments are file(s) in wich we look at twitter accounts")
group.add_argument("-a", "--account", dest='areArgsFiles', action='store_const', const=False, help="arguments are twitter accounts")
parser.set_defaults(areArgsFiles=True)
parser.add_argument("-o", "--out", type=str, default="output", help="name of file for output")
parser.add_argument("-n", "--number", type=int, default=100, help="number of tweets to analyse per account")
parser.add_argument('argList', metavar='L', type=str, nargs='+', help='list of twitter accounts or file with them into.')
args = parser.parse_args()



users = []
if args.areArgsFiles:
	for i in args.argList:
		users += open(i).read().split()
else:
	users += args.argList



TWEET_BY_USER = args.number
# TWEET_BY_USER = 20


lemmatizer = FrenchLefffLemmatizer()


# On recupere le texte brut des tweets, on affine le "lavage" et la lemmatisation plus tard.
def getTweetsAsTxt(usr):
	tweetsCriteria = got3.manager.TweetCriteria().setUsername(usr).setMaxTweets(TWEET_BY_USER)
	tweets = got3.manager.TweetManager.getTweets(tweetsCriteria)
	return '\n '.join([t.text for t in tweets])


def clean(twtTxt):
	return ''.join([i if i.isalpha() else " " for i in re.sub(r'((https?://)?[.\w\-_]*.(com|biz|fr|net|org)(/?[\w_-]+)*(\.\w{2,4})?)|(@\w+)', '', twtTxt.lower()) ])


def _lemmatize(m):
	tmp = lemmatizer.lemmatize(m, 'all')
	if type(tmp) != list: tmp=[tmp]			# petite correction de la lib; à arranger là-bas en théorie
	return tmp

def mLemmatizer(m):
	D = dict([i[::-1] for i in _lemmatize(m)])
	return D['nc'] if 'nc' in D else D['v'] if 'v' in D else D['adj'] if 'adj' in D else m

def getTweetsAsDict(usr):
	d = dict()
	for m in clean(getTweetsAsTxt(usr)).split():
		m = mLemmatizer(m)
		d[m] = d.get(m, 0)+1
	return d

###############################################################

def handleUser(usr):
	return [usr, getTweetsAsDict(usr)]

usersTweets = p_umap(handleUser, users) # download tweets from all users, in concurential mode, showing a progressbar

glob = dict(usersTweets)

allWords = {}




print(glob.keys())

for i in users:
	for mot in glob[i]:
		allWords[mot] = allWords.get(mot, 0) + glob[i][mot]



pickle.dump({"users": glob, "allWords": allWords}, open(args.out, 'wb'))

"""
import tweepy
tweepy.api
auth = tweepy.OAuthHandler("_", "_")
auth.set_access_token("_", "_")
api = tweepy.API(auth)

def getFollNumb(u):
	try:
		return api.get_user(u).followers_count
	except:
		return -1

"""
