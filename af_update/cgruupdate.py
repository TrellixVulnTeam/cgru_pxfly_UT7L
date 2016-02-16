#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json

FILES = dict()


class ChangeLog:
	def __init__(self, variables= FILES, changelog= None):
		self.Files = variables
		self.load(changelog)

	def load(self, changelog):
		if not os.path.isfile(changelog):
			return

		with open(changelog, 'r') as f:
			logInfo = f.read()

		success = True
		try:
			obj = json.loads(logInfo)['cgru_changelog']
		except:  # TODO: Too broad exception clause
			success = False
			print(changelog)
			print(str(sys.exc_info()[1]))

		if not success:
			return

		self.getVars(self.Files, obj, changelog)

	def getVars(self, o_vars, i_obj, i_filename):
		for key in i_obj:
			if len(key) == 0:
				continue
			o_vars[key] = i_obj[key]