
# todo: clean up these imports
from collections import namedtuple
from collections import deque
import numpy as np
from scipy.interpolate import interp1d
from scrape_tools import parse_scrape_log, Datum
import argparse
import re
import random
import time

# Suppose f is a non-decreasing
# function on [0,1] with f(0) <= 0
# and f(1) >= 0.
# Let x be the largest number in [0,1] with f(x)=0.
# This function returns a number in the interval
# [x-precision, x]
def findzero(f, precision=0.00000001):
	a = 0.0
	b = 1.0
	fa = f(a)
	fb = f(b)
	while fb != 0 and b-a >= precision:
		c = (a+b)/2
		fc = f(c)
		if fc > 0:
			b = c
			fb = fc
		else:
			a = c
			fa = fc
	return a

def project_to_budget(cost, budget, bids):
	t = findzero(lambda t: cost([t*bid for bid in bids])-budget)
	return np.array([t*bid for bid in bids]), t

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Predict revenue and profit for Google Adwords keywords, under a limited budget.\
 Predictions are based on projected click value and traffic scrapes.')
	parser.add_argument("budget", type=float)
	parser.add_argument("valuefile")
	args = parser.parse_args()

	budget = args.budget
	valuefile = args.valuefile
	values = []
	scrapes = []
	scrapefilenames = []
	with open(valuefile) as vf:
		for line in vf:
			line = line.strip()
			if len(line) < 1:
				continue
			m = re.match(r'(\d+(?:\.\d+)?)\s+(.+)', line)
			if not m:
				print('Unable to parse line')
				print('>  ' + line)
				continue
			values.append(float(m.group(1)))
			scrapes.append(parse_scrape_log(m.group(2)))
			scrapefilenames.append(m.group(2))

	N = len(values)
	print('Budget: ${0:.2f}'.format(budget))
	print('')
	print('Read {0} files:'.format(N))
	for i in range(N):
		print('> {0: <15}  ${1:.2f} -- ${2:.2f}   value ${3:.2f}'.format(scrapefilenames[i],\
			min(x.cpc for x in scrapes[i]),\
			max(x.cpc for x in scrapes[i]),\
			values[i]))
	print('')

	costs = [interp1d([x.cpc for x in scrapes[i]], [x.cost for x in scrapes[i]]) for i in range(len(scrapes))]
	clicks = [interp1d([x.cpc for x in scrapes[i]], [x.clicks for x in scrapes[i]]) for i in range(len(scrapes))]
	impressions = [interp1d([x.cpc for x in scrapes[i]], [x.impressions for x in scrapes[i]]) for i in range(len(scrapes))]

	def cost(bids):
		return sum([costs[i](bids[i]) for i in range(N)])
	def revenue(bids):
		return sum([values[i]*clicks[i](bids[i]) for i in range(N)])
	def profit(bids):
		return revenue(bids) - cost(bids)

	bids = np.array(values)
	c = cost(bids)
	r = revenue(bids)
	p = profit(bids)
	print('If you bid the full value for each click:')
	print('    ' + 'Bids: ' + '   '.join('${0:.2f}'.format(bid) for bid in bids))
	print('    ' + 'Cost: ${0:.2f}   Revenue: ${1:.2f}   Profit: ${2:.2f}'.format(c, r, p))

	if c <= budget:
		print('This fits in the budget.')
		sys.exit(0)

	print('')
	bids, t = project_to_budget(cost, budget, values)
	print('To fit this into the budget, we have to multiply all the bids by {0:.1f}%.'.format(100*t))
	print('')

	c = cost(bids)
	r = revenue(bids)
	p = profit(bids)
	print('New results:')
	print('    ' + 'Bids: ' + '   '.join('${0:.2f}'.format(bid) for bid in bids))
	print('    ' + 'Cost: ${0:.2f}   Revenue: ${1:.2f}   Profit: ${2:.2f}'.format(c, r, p))


