import settings
import os
import sys
import pickle

class DataView:
	
	def __init__(self, symbol, date, ftype):
		#self.symbol = symbol
		self.symbol = "AMZN"
		self.date = date
		self.ftype = ftype
		self.data = None
		self.load_data()
	
	def load_data(self):
		fpath_no_p = "{0}/{1}/{2}/xml/{3}/".format(settings.EXTRACTED_DATA_PATH,
							   self.symbol,
							   self.ftype,
							   self.date)
		fpath_file = os.listdir(fpath_no_p)[0]
		fpath = "{0}/{1}".format(fpath_no_p, fpath_file)
		self.data = pickle.load(open(fpath, 'rb'))
	
	def get_all_roles(self, cat='pre'):
		"""Returns list of all roles."""
		
		return self.data[cat]['roles'].keys()
	
	def traverse_print_tree(self, base, role_keys, tabs=0):
		"""Traverse cal tree and print."""

		for rk in role_keys:
			if rk == 'sub':
				continue
			tab_str = '   ' * tabs
			try:
				lab_str = tab_str + str(rk)
			except KeyError:
				lab_str = rk
			try:
				base_keys = base[rk]['val'].keys()
				if len(base_keys) == 0:
					if len(base[rk]['sub']) == 0:
						continue
					else:
						print('\033[1m' + lab_str + '\033[0m')
				else:
					date_str = ''
					val_str = ''
					for i in base_keys:
						date_str += str(i)
						date_str += '\t\t'
					for bk in base_keys:
						if base[rk]['val'][bk] == None:
							continue
						if isinstance(base[rk]['val'][bk], float):
							val_str += str(base[rk]['val'][bk])
						else:
							val_str += base[rk]['val'][bk].encode('utf-8')
						val_str += '\t\t'
					print(lab_str)
					print(tab_str + '\t' + date_str)
					print(tab_str + '\t' + val_str)
			except KeyError:
				pass
			if len(base[rk]['sub']) > 0:
				rk_base = base[rk]['sub']
				rk_base_keys = rk_base.keys()
				self.traverse_print_tree(rk_base, rk_base_keys, tabs=tabs+1)
				
	def traverse_tree(self, name, cat='pre'):
		base = self.data[cat]['roles'][name]
		base_tree = base['tree']
		role_keys = base_tree.keys()
		self.traverse_print_tree(base_tree, role_keys)
	
	def traverse_all_trees(self):
		base = self.data['pre']['roles']
		base_keys = base.keys()
		for bk in base_keys:
			print('\033[1m' + 'Title:' + ' ' + bk + '\033[0m')
			self.traverse_tree(bk)
			print('\n\n')
				
	def find_fact_in_role(self, fact, cat='pre'):
		"""Returns list of roles with fact in them."""
		
		all_role_keys = self.data[cat]['roles'].keys()
		roles_with_fact = []
		for i in all_role_keys:
			base = self.data[cat]['roles'][i]['unique']
			for b in base:
				if fact == b[1]:
					roles_with_fact.append(i)
		roles_with_fact = list(set(roles_with_fact))
		return roles_with_fact
