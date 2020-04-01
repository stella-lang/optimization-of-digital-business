import csv
import sys
import os.path
import argparse
import sqlite3
import re
import datetime
from collections import Counter


def split_into_words(query):
	return query.lower().replace("+","").replace("/"," ").replace("."," ").split()


def determine_intent(row):
	words = split_into_words(row['Search keyword'])
	conservative = 0  #politically convervative-leaning
	privacy = 0       #privacy-conscious
	email = 0         #email-related

	if "com" in words and "reagan" in words:
		return "targeted" #already knows about reagan.com but is too lazy to type it

	for w in words:
		if w in {"reagan", "conservative", "regan", "reagen", "regean", "ronald", "republican"}:
			conservative += 1
		if w in {"private", "secure", "encrypted", "privacy", "provate", "encryption", "encrypted", "security", "confidential"}:
			privacy += 1
		if w in {"mail", "email", "address"}:
			email += 1

	if conservative > 0 and privacy == 0:
		if email:
			return "conservative-mail"
		else:
			return "conservative"
	if conservative == 0 and privacy > 0:
		if email:
			return "privacy-mail"
		else:
			return "privacy"

	#print the searches we can't classify
	#print(words)
	return "unknown"


def determine_brand(row):
	from adgroup_brand import adgroup_brand
	return adgroup_brand[row['Ad group']]

def to_sqlite_date(month):
	d = datetime.datetime.strptime(month, '%b %Y')
	return d.strftime('%Y-%m-%d %H:%M:%S')


def databasename(name):
	"""Given a filename, return the filename that the database should be written to."""
	base, ext = os.path.splitext(name)
	dbname = base + ".sqlite"
	n = 0
	while os.path.exists(dbname):
		dbname = base + "(" + str(n) + ")" + ".sqlite"
		n += 1
	return dbname


def create_brand_table(cursor, name):
	cursor.execute('''CREATE TABLE ''' + name + '''
		         (id integer primary key, adgroup text, intent text, keyword text, matchtype text,
		         device text, month datetime, impressions integer,
		         clicks integer, conversions integer, convclicks integer, cost real)''')


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Process CSV report from Google Adwords.")
	parser.add_argument("filename")
	args = parser.parse_args()
	fname = args.filename
	
	print("Reading {0}...".format(fname), end='')
	sys.stdout.flush()
	with open(fname, newline='', encoding='utf-8') as fin:
		csvreader = csv.DictReader(fin, delimiter=",")
		fieldnames = csvreader.fieldnames
		table = []
		for row in csvreader:
			table.append(row)
	print(" done.")
	print("Columns:")
	for h in fieldnames:
		print("    " + h)
	print("Row count:\n    {0}".format(len(table)))
	print("")

	dbname = databasename(fname)
	print("Creating database {0}...".format(dbname), end='')
	sys.stdout.flush()
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	print(" done.")

	print("Writing brand search tables to database file {0}...".format(dbname), end='')
	sys.stdout.flush()
	for b in ["reagan", "mymailconfidential", "brand1791", "faithbasedemail"]:
		create_brand_table(c, b)
		c.executemany('''INSERT INTO ''' + b + ''' (adgroup, intent, keyword, matchtype, device,
		             month, impressions, clicks, conversions, convclicks, cost)
		             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
		             [(row['Ad group'],
		             	determine_intent(row),
		             	row['Search keyword'],
		             	row['Search term match type'],
		             	row['Device'],
		             	to_sqlite_date(row['Month']),
		             	re.sub(r',', '', row['Impressions']),
		             	re.sub(r',', '', row['Clicks']),
		             	re.sub(r',', '', row['Conversions']),
		             	re.sub(r',', '', row['Converted clicks']),
		             	re.sub(r'[^\d.-]', '', row['Cost']))
		             for row in table if determine_brand(row) == b])
	print(" done.")

	print("Creating table of words...".format(dbname), end='')
	sys.stdout.flush()
	#TODO: this should be a set, not a counter
	keywords = Counter()
	for row in table:
		if determine_brand(row) == "reagan":
			keywords.update(split_into_words(row['Search keyword']))
	c.execute('''CREATE TABLE reagan_words (word text)''')
	c.executemany('''INSERT INTO reagan_words (word) VALUES (?)''',
		[(w,) for w,c in keywords.most_common()])
	print(" done.")

	print("Creating table of words vs searches...".format(dbname), end='')
	sys.stdout.flush()
	c.execute('''CREATE TABLE reagan_words_searches
		         (word text, searchid integer)''')
	c.execute('''SELECT id, keyword FROM reagan''')
	for row in c.fetchall():
		index, search = row
		words = split_into_words(search)
		for w in words:
			c.execute('''INSERT INTO reagan_words_searches (word, searchid) VALUES (?,?)''', (w, index))
	print(" done.")

	print("Adding interestings views to database...".format(dbname), end='')
	sys.stdout.flush()
	c.execute('''CREATE VIEW reagan_words_statistics AS
		SELECT w.word AS word, SUM(r.impressions) as impressions,
		    SUM(r.clicks) as clicks, SUM(r.conversions) as conversions, SUM(r.cost) as cost
		FROM reagan_words as w
		LEFT JOIN reagan_words_searches as rws
		ON w.word = rws.word
		LEFT JOIN reagan as r
		ON rws.searchid = r.id
		GROUP BY w.word
		''')
	print(" done.")
	
	print("Closing database file...", end='')
	sys.stdout.flush()
	conn.commit()
	conn.close()
	print(" done.")

