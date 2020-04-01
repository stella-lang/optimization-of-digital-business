import csv
import re
import os
from collections import namedtuple
from io import StringIO

Datum = namedtuple('Datum', ['cpc', 'clicks', 'impressions', 'cost'])

def parse_scrape_log(filename):
	lines = []
	with open(filename, newline='', encoding='utf-8') as f:
		for line in f:
			line = line.strip()
			if re.match(r'\d+(?:\.\d+)?\s*,\s*\d+(?:\.\d+)?\s*,\s*\d+(?:\.\d+)?\s*,\s*\d+(?:\.\d+)?', line):
				lines.append(line)
	#print('CSV read, {0} lines'.format(len(lines)))
	csvlines = StringIO('\n'.join(lines), newline='')
	csvreader = csv.reader(csvlines, delimiter=",")
	scrape = [Datum(*(float(x) for x in row)) for row in csvreader if len(row) > 0]
	scrape = list(set(scrape)) #remove duplicates
	scrape.sort(key=lambda x: x.cpc)
	return scrape
