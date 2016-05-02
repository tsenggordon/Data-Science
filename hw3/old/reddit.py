import csv
import numpy as np
from collections import defaultdict
from multiprocessing import Pool
import pickle
import os
import networkx as nx
from scipy.sparse import csr_matrix
FILE = "reddit_50000.csv"

def build_dict():
	post_dict = {}
	author_dict = {}
	comment_dict = defaultdict(set)
	post_author_dict = defaultdict(int)
	post_subauthor_dict = defaultdict(set)
	post_count = 0
	author_count = 0
	with open(FILE) as f:
		reader = csv.reader(f)
		reader.next()
		for row in reader:
			author, po_id= row[0], row[1]
			head, post_id = po_id.split("_")
			if post_id not in post_dict:
				post_dict[post_id] = post_count
				post_count+=1
			if author not in author_dict:
				author_dict[author] = author_count
				author_count+=1
			comment_dict[author_dict[author]].add(post_dict[post_id])
			if head == "t3": #means it is the top post
				post_author_dict[post_dict[post_id]] = author_dict[author]
			else:
				post_subauthor_dict[post_dict[post_id]].add(author_dict[author])
	return post_dict, author_dict, comment_dict, post_author_dict, post_subauthor_dict

def doWork(x):
	edgelist = defaultdict(set)
	start_idx, end_idx= x
	work = end_idx - start_idx
	work_100 = work/100
	print "doWork start from", start_idx
	for i in xrange(start_idx, end_idx):
		#print i, start_idx,work/100
		if i % work_100 == 0:
			print i ,(i-start_idx+1)/ work_100, "%"
		for j in xrange(len(author_dict)):
			#if len(comment_dict[i] & comment_dict[j]) >0 and i!= j:
				#print float(len(comment_dict[i] & comment_dict[j])) / len(comment_dict[i] | comment_dict[j])
			#print len(comment_dict[i] & comment_dict[j]), len(comment_dict[i] | comment_dict[j])
			jacc_score[i, j] = float(len(comment_dict[i] & comment_dict[j])) / len(comment_dict[i] | comment_dict[j])
			if jacc_score[i, j] > 0 and i!= j:
				#print "gj"
				edgelist[i].add(j)
				#print edgelist
	print edgelist
	return edgelist
def build_diredge_and_pagerank():
	dirG = nx.DiGraph()
	totalkey = post_author_dict.keys() + post_subauthor_dict.keys()
	for key in totalkey:
		if (key not in post_author_dict) or (key not in post_subauthor_dict):
			continue
		actor1 = rev_author_dict[post_author_dict[key]]
		actor2 = rev_author_dict[post_subauthor_dict[key]]
		dirG.add_edge(actor1, actor2)
	pr = nx.pagerank(G)
	sort_pr = sorted(pr.keys(), key = lambda x :pr[x], reverse=True)
	print sort_pr[:10]
	return pr


def pagerank(edgelist):
	G = nx.Graph()
	for actor1 in edgelist.keys():
		for actor2 in edgelist[actor1]:
			G.add_edge(rev_author_dict[actor1], rev_author_dict[actor2])
	pr = nx.pagerank(G)
	sort_pr = sorted(pr.keys(), key = lambda x :pr[x], reverse=True)
	print sort_pr[:10]
	return pr
def build_rev_dict(target):
	rev_dict = {}
	for key in target.keys():
		rev_dict[target[key]] = key
	return rev_dict
def joinDict(dictlist):
	totalkey = []
	for dictionay in dictlist:
		totalkey += dictionay.keys()
	totaldict = {}
	print totalkey
	for key in totalkey:
		newSet = set()
		for dictionay in dictlist:
			newSet = newSet | dictionay[key]
		totaldict[key] = newSet
	return totaldict
if not os.path.exists("dict.pickle"):
	print "building dict"
	post_dict, author_dict, comment_dict, post_author_dict, post_subauthor_dict = build_dict()
	rev_author_dict = build_rev_dict(author_dict)
	with open("dict.pickle", "w") as f:
		pickle.dump( (post_dict, author_dict, comment_dict, post_author_dict, post_subauthor_dict, rev_author_dict), f)
	print "buiding dict: finished"
else:
	print "loading dict"
	with open("dict.pickle") as f:
		post_dict, author_dict, comment_dict, post_author_dict, post_subauthor_dict, rev_author_dict = pickle.load(f)
	print "loading dict:finished"

if not os.path.exists("jacc_score.pickle"):
	print "compute jacc_score"
	jacc_score = np.zeros((len(author_dict), len(author_dict))).astype(np.float32)
	
	pool = Pool(5)
	print "build pool"
	edgelist_list = pool.map(doWork, [(0,int(len(author_dict)/4) ), \
						(int(len(author_dict)/4),int(len(author_dict)/4)*2 ), \
						(int(len(author_dict)/4)*2,int(len(author_dict)/4)*3 ), \
						(int(len(author_dict)/4)*3,len(author_dict) )])
	print "Dict joining"
	edgelist = joinDict(edgelist_list)
	pool.close()
	pool.join()

	jacc_score_s = csr_matrix(jacc_score)
	print "compute jacc_score:saving pickle"
	with open("jacc_score.pickle", "w") as f:
		pickle.dump((jacc_score_s,edgelist) , f)
	print edgelist
	print "compute jacc_score:finished"
else:
	print "loading jacc_score"
	with open("jacc_score.pickle") as f:
		jacc_score_s, edgelist = pickle.load(f)
	jacc_score = jacc_score_s.todense()
	print "loading jacc_score:finished"
	for i in xrange(jacc_score.shape[0]):
		for j in xrange(jacc_score.shape[1]):
			if jacc_score[i,j] >0:
				print "great"
pr_un = pagerank(edgelist)
pr_dir = build_diredge_and_pagerank





'''
maxlen = 0
maxset = None
for key in comment_dict.keys():
	if len(comment_dict[key])> maxlen:
		maxlen =len(comment_dict[key])
		maxset = comment_dict[key]
#print comment_dict
print maxlen
print maxset
'''

		
