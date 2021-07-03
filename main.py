import settings
import EdgarScrape
import XMLExtract
import os
import threading
import queue
import time
import requests
import sys
import pickle
import logs
import pandas as pd

class ScrapeAndExtract:
	
	def __init__(self):
		
		#Scrape Section
		self.stock_lists = os.listdir(settings.STOCK_EXCHANGE_LIST_PATH)
		self.symbol_keys = []
		self.scraped_keys = None
		self.finished = False
		
		#Extract Section
		self.extracted_keys = None
		self.to_extract = queue.Queue()
		
		self.populate_symbol_keys()
		self.get_all_keys()
	
	def populate_symbol_keys(self):
		for xlist in self.stock_lists:
			f = pd.read_csv('{0}/{1}'.format(settings.STOCK_EXCHANGE_LIST_PATH, xlist))
			for symbol in f[f.columns[0]]:
				if symbol not in self.symbol_keys:
					self.symbol_keys.append(symbol)
	
	def get_all_keys(self):
		scraped_data_log = pickle.load(open(settings.SCRAPE_LOG_FILE_PATH, "rb"))
		self.scraped_keys = scraped_data_log.keys()
		extracted_data_log = pickle.load(open(settings.EXTRACT_LOG_FILE_PATH, "rb"))
		self.extracted_keys = extracted_data_log.keys()
		sk_set = set(self.scraped_keys)
		ek_set = set(self.extracted_keys)
		to_extract = list(sk_set - ek_set)
		for te in to_extract:
			self.to_extract.put(te)
	
	@staticmethod
	def extract_xml(symbol):
		q_path = "{0}/{1}/xml/{2}".format(settings.RAW_DATA_PATH, symbol, '10-Q')
		k_path = "{0}/{1}/xml/{2}".format(settings.RAW_DATA_PATH, symbol, '10-K')
		q_list = os.listdir(q_path)
		k_list = os.listdir(k_path)

		#Create directories if they do not exist
		if not os.path.exists("{0}/{1}/".format(settings.EXTRACTED_DATA_PATH, symbol)):
			os.makedirs("{0}/{1}/".format(settings.EXTRACTED_DATA_PATH, symbol))

		if not os.path.exists("{0}/{1}/10-Q/".format(settings.EXTRACTED_DATA_PATH, symbol)):
			os.makedirs("{0}/{1}/10-Q/".format(settings.EXTRACTED_DATA_PATH, symbol))

		if not os.path.exists("{0}/{1}/10-Q/xml/".format(settings.EXTRACTED_DATA_PATH, symbol)):
			os.makedirs("{0}/{1}/10-Q/xml/".format(settings.EXTRACTED_DATA_PATH, symbol))

		if not os.path.exists("{0}/{1}/10-K/".format(settings.EXTRACTED_DATA_PATH, symbol)):
			os.makedirs("{0}/{1}/10-K/".format(settings.EXTRACTED_DATA_PATH, symbol))

		if not os.path.exists("{0}/{1}/10-K/".format(settings.EXTRACTED_DATA_PATH, symbol)):
			os.makedirs("{0}/{1}/10-K/xml/".format(settings.EXTRACTED_DATA_PATH, symbol))

		xml_10q_path = "{0}/{1}/10-Q/xml/".format(settings.EXTRACTED_DATA_PATH, symbol)
		xml_10k_path = "{0}/{1}/10-K/xml/".format(settings.EXTRACTED_DATA_PATH, symbol)
		
		#10-Q Extract
		for ql in q_list:
			if logs.check_if_extracted(symbol, ql):
				continue

			if not os.path.exists("{0}/{1}".format(xml_10q_path, ql)):
				os.makedirs("{0}/{1}".format(xml_10q_path, ql))
				
			ql_path = "{0}/{1}".format(xml_10q_path, ql)
			
			
			try:
				tmp_xe = XMLExtract.ExtractFilingData(symbol, ql, '10-Q')
			except:
				logs.add_extract_data(symbol, ql, False)
				continue
			
			if settings.OUTPUT_PICKLE:
				if tmp_xe.data['error'] == False:
					pickle.dump(tmp_xe.data, open("{0}/{1}.p".format(ql_path, tmp_xe.format_str), "wb"))
					logs.add_extract_data(symbol, ql, True)
					pass
				elif tmp_xe.data['error'] == True:
					print('Error Extracting: {0}|{1}|{2}'.format(symbol, ql, '10-K'))
					logs.add_extract_data(symbol, ql, False)
					pass
			if settings.OUTPUT_JSON:
				pass
			

		for kl in k_list:
			if logs.check_if_extracted(symbol, kl):
				continue
			
			if not os.path.exists("{0}/{1}".format(xml_10k_path, kl)):
				os.makedirs("{0}/{1}".format(xml_10k_path, kl))
				
			kl_path = "{0}/{1}".format(xml_10k_path, kl)

			try:
				tmp_xe = XMLExtract.ExtractFilingData(symbol, kl, '10-K')
			except:
				logs.add_extract_data(symbol, ql, False)
				continue
			
			if settings.OUTPUT_PICKLE:
				if tmp_xe.data['error'] == False:
					pickle.dump(tmp_xe.data, open("{0}/{1}.p".format(kl_path, tmp_xe.format_str), "wb"))
					logs.add_extract_data(symbol, kl, True)
					pass
				elif tmp_xe.data['error'] == True:
					print('Error Extracting: {0}|{1}|{2}'.format(symbol, kl, '10-K'))
					logs.add_extract_data(symbol, kl, False)
					pass
			if settings.OUTPUT_JSON:
				pass
	
	@staticmethod
	def scrape_symbol(symbol):
		sym_gf = EdgarScrape.GetFilings(symbol)
		if sym_gf.filings['errors']['count'] > 0:
			soe_error_data = sym_gf.filings['errors']
			logs.add_scrape_data(symbol, soe_error_data, False)
		if sym_gf.filings['success']['count'] > 0:
			soe_success_data = sym_gf.filings['success']
			logs.add_scrape_data(symbol, soe_success_data, True)
		else:
			logs.add_scrape_data(symbol, None, True)
		
	def scrape_list(self):
		"""Scrape all symbols in list."""

		for symbol in self.symbol_keys:
			if symbol in self.scraped_keys:
				continue
			self.scrape_symbol(symbol)			
			self.scraped_keys.append(symbol)
			self.to_extract.put(symbol)
		self.finished = True
	
	def extract_all(self):
		while not self.finished:
			if self.to_extract.qsize() > 0:
				sym = self.to_extract.get()
				try:
					self.extract_xml(sym)
				except OSError:
					pass


scrape_and_extract = ScrapeAndExtract()

class ScrapeThread(threading.Thread):
	
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name
	
	def run(self):
		try:
			scrape_and_extract.scrape_list()
		except (requests.exceptions.ConnectionError, OSError, IOError):
			os.execv(sys.executable, [sys.executable] + [os.path.abspath(__file__)])
			

class ExtractThread(threading.Thread):
	
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name
	
	def run(self):
		scrape_and_extract.extract_all()

def run_main():
	scrape_thread = ScrapeThread(name='Scrape Thread')
	scrape_thread.daemon = True
	extract_thread = ExtractThread(name='Extract Thread')
	extract_thread.daemon = True
	scrape_thread.start()
	extract_thread.start()
	scrape_thread.join()
	extract_thread.join()

if __name__ == '__main__':
	run_main()







