#!/usr/bin/python 

# This script takes the timbl srl predictions and inserts them into the 
# original naf file. 
#
# Author: Marieke van Erp (marieke.van.erp@vu.nl) 
# Date: 27 September 2014

#
# Update 20 February 2015:
# It seems there was a bug in writing the correct term_ids, 
# namely the last term_id wasn't copied over to the role span
# This is fixed in this version

from KafNafParserPy import *
import sys 
import datetime
import time
import pprint
import re

# Make sure you get the order of the input files right 
nafinput = sys.argv[1]
timblpredictions = sys.argv[2]

my_parser = KafNafParser(nafinput)
		
## Create header info
lp = Clp()
lp.set_name('SoNaR-News-trained-SRL')
lp.set_version('1.1')
lp.set_timestamp()
my_parser.add_linguistic_processor('srl', lp)

# If the naf file already contains predicates, store those to make sure 
# you don't overwrite them or create new predicate elements for existing predicates
roles = []
predicate_spans = []
for predicate in my_parser.get_predicates():
	for role in predicate.get_roles():
		role_id = role.get_id()
		role_id = re.sub("r","",role_id)
		roles.append(int(role_id))
	for span in predicate.get_span():
		span_id = predicate.get_id()
		span_id = re.sub("pr","",span_id)
		predicate_spans.append(int(span_id))
		
predicate = ''
if len(predicate_spans) > 0:
	pred_counter = max(predicate_spans)
else:
	pred_counter = 0 
if len(roles) > 0:		
	role_counter = max(roles)
else:
	role_counter = 0 

# Go through the timbl output file 
# get the first 4 elements and the last element		
with open(timblpredictions) as f:
	for line in f:
		line = re.sub('\n', '',line) 
		predicate_switch = 0
		items = line.split(',')
		# the first element is the predicate id, 
		# if the predicate id is not the same as the last one, start a new predicate element 
		pred_span = items[0]
		arg_head = str(items[1])
		arg_head = re.sub("t_","",arg_head)
		arg_start = items[2]
		arg_start = re.sub("t_","",arg_start)
		arg_end = items[3]
		arg_end = re.sub("t_","",arg_end)
		prediction = items[-1]
		# start a new role element for each argument 
		role = Crole()
		role_counter = role_counter + 1
		role.set_id('r' + str(role_counter))
		role.set_sem_role(prediction)
		role_span = Cspan()
		if arg_start == arg_end:
			target_term_id = arg_start
			head_target = Ctarget()
			head_target.set_id(items[1])
			head_target.set_head('yes')
			role_span.add_target(head_target)
		else:
			for arg_token in range (int(arg_start), int(arg_end)+1):
				target_term_id = ('t_' + str(arg_token))
				if target_term_id == items[1]:
					head_target = Ctarget()
					head_target.set_id(target_term_id)
					head_target.set_head('yes')
					role_span.add_target(head_target)
				else:
					role_span.add_target_id('t_' + str(arg_token))
		role.set_span(role_span)
		
		# Here you add a role to an existing predicate 		
		for predicate in my_parser.get_predicates():
			for span in predicate.get_span():
				#print items[4], 'test',span.get_id(), items[0]
				if span.get_id() == items[0]:
					predicate.add_role(role)
					predicate_switch = 1
					break
		# or you create a new predicate 
		if predicate_switch == 0:
			new_predicate = Cpredicate()
			pred_counter = pred_counter + 1 
			new_predicate.set_id('pr' + str(pred_counter))	
			predicate = pred_span
			predicate_span = Cspan()
			target = Ctarget()
			target.set_id(items[0])
			predicate_span.add_target(target)
			new_predicate.set_span(predicate_span)
			new_predicate.add_role(role)	
			my_parser.add_predicate(new_predicate)
			
# and you print the whole thing to a file 
my_parser.dump()
