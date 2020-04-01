import os
import argparse
import re
from scrape_tools import parse_scrape_log, Datum
import matplotlib.pyplot as plt

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="View scrape file.")
	parser.add_argument("filename")
	args = parser.parse_args()
	filename = args.filename
	scrape = parse_scrape_log(filename)

	cpc = [x.cpc for x in scrape]
	clicks = [x.clicks for x in scrape]
	cost = [x.cost for x in scrape]

	fig = plt.figure()
	ax1 = fig.add_subplot(211)
	ax2 = fig.add_subplot(212)

	ax1.plot(cpc, clicks)
	ax2.plot(cpc, cost)

	ax1.set_xlabel('Bid')
	ax1.set_ylabel('Clicks')
	ax2.set_xlabel('Bid')
	ax2.set_ylabel('Cost')
	plt.show()


