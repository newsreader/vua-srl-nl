#!/usr/bin/python 

# This script reads in a NAF file that contains Alpino dependencies
# and creates a feature vector for the SoNaR Semantic Role Labeller
# It is a reimplementation of the SSRL package by Orphee DeClerq using 
# python and the NAF serialisation of the Alpino output
# Term ids of the predicates and the arguments were added to the output
# to facilitate reinserting the SRL predictions into the NAF
# 
# v1.0
# Only the argcatpattern feature does not behave quite like the original
# feature in passive sentences. Maybe this will be fixed in a future version
#
# Author: Marieke van Erp (marieke.van.erp@vu.nl)
# Date: 27 September 2014
#
# Update 23 February 2015: better constituent extraction for feature generation
# with help from Ruben Izquierdo


from KafNafParserPy import KafNafParser
import re
import sys 
from collections import OrderedDict
import codecs

input = sys.stdin

my_parser = KafNafParser(input)
	 
### We first need a list of the predicates that we want to create feature vectors for
predicates = {} 
for term_obj in my_parser.get_terms():
	predicate = re.match("WW", term_obj.get_morphofeat())
	if predicate is not None:
		predicates[term_obj.get_id()] = term_obj.get_pos()
		#print term_obj.get_id(), term_obj.get_morphofeat(), term_obj.get_lemma()

# We need the dependencies to find out the structure of the argument patterns
# and also to know which verbs are auxiliary verbs and which ones are main verbs
dependencies = {} 
for dep_obj in my_parser.get_dependencies():
	relparts = dep_obj.get_function().split('/')
	rel_from = relparts[0]
	rel_to = relparts[1]
	dep_id = dep_obj.get_from() + '-' + dep_obj.get_to() 
	dependencies[dep_id] = dep_obj.get_function()

# We also want to distinguish between main verbs and auxiliary verbs
# for this we first gather all dependency patterns and store those 
dep_patterns = {} 		
for deps in dependencies:
	dep_parts = deps.split('-')
	#dep_patterns[dep_parts[0]] = [] 
	func_parts = dependencies[deps].split('/')
	if predicates.get(dep_parts[0]) is not None:
		if dependencies[deps] != '-- / --':
			if dep_patterns.get(dep_parts[0]) is None:
				dep_patterns[dep_parts[0]] = []
				dep_patterns[dep_parts[0]].append(dep_parts[1].strip('t_'))
			else:
				dep_patterns[dep_parts[0]].append(dep_parts[1].strip('t_'))

# Then we find the dependencies between two predicates
# we store the main verb as the key and the auxiliary verb as the value 
auxiliary_verbs = {}
for pattern in dep_patterns:
	sorted_dep_patterns = list(set(dep_patterns[pattern]))
	sorted_dep_patterns.sort(key=int)
	for sorted in sorted_dep_patterns:
		if predicates.get(('t_' + str(sorted))) is not None:
			pattern_term_number = int(pattern.strip('t_'))
			if int(sorted) != int(pattern_term_number):
				if my_parser.get_term(pattern).get_lemma() == 'zijn':
					auxiliary_verbs['t_' + str(pattern_term_number)] = 't_'+ str(sorted)
				else:
					auxiliary_verbs['t_'+ str(sorted)] = 't_' + str(pattern_term_number)

# The pos tags are actually the first part of the morphofeat attributes 
# Here they are rewritten to that format 
def rewrite_postag(term):
	morphofeat = my_parser.get_term(term).get_morphofeat()
	parts = morphofeat.split(',')
	postag = (parts[0] + ')')
	postag = postag.replace('))', ')')
	return(postag)		
	
# The argument categories are pulled out of the constituency trees
non_terminals = {}
terminals = {}
for tree in my_parser.get_trees():
	for terminal in tree.get_terminals():
		for span in terminal.get_span(): 
			#print terminal.get_id(), span.get_id()
			terminals[terminal.get_id()] = span.get_id()
	for nt in tree.get_non_terminals():
		non_terminals[nt.get_id()] = nt.get_label()
	
argument_category_head = {} 
argument_category_term = {}
argument_category_deep = {} 			
for tree in my_parser.get_trees():
	for edge in tree.get_edges():
		for head_edge in tree.get_edges():
			if terminals.get(edge.get_from()) is not None:
				terminal_id = terminals[edge.get_from()]
				argument_category_term[terminal_id] = non_terminals[edge.get_to()]
				if edge.get_to() == head_edge.get_from() and head_edge.get_head() is not None:
					argument_category_head[my_parser.get_term(terminal_id).get_id()] =  non_terminals[head_edge.get_to()]
			elif edge.get_to() == head_edge.get_from() and non_terminals[edge.get_to()] == 'smain':
					for deeper in tree.get_edges():
						if edge.get_from() == deeper.get_to() and terminals.get(deeper.get_from()) is not None:
					#		print 'test', edge.get_from(), terminals[deeper.get_from()], non_terminals[deeper.get_to()]
							if argument_category_deep.get(terminals[deeper.get_from()]) is None:
								argument_category_deep[terminals[deeper.get_from()]] = non_terminals[deeper.get_to()]
			#	elif non_terminals[edge.get_to()] == 'smain':
			#		print "hell yeah", edge.get_to(), edge.get_from()
		#	terminal_id = terminals[edge.get_from()]
		#	if argument_category_head.get(my_parser.get_term(terminal_id).get_id()) is None:	
		#		print "head doesn't exist yet", my_parser.get_term(terminal_id).get_id()	

								
# For each predicate, you want to get a list of the predicate arguments 
predicate_arguments = {}
head_dependency = {} 
for head_obj in my_parser.get_dependencies():
	if predicates.get(head_obj.get_from()) is not None and head_obj.get_function() != '-- / --':
	#if head_obj.get_from() == id_parts[0].get_to():
		head_function_parts = head_obj.get_function().split('/')
		head_function = head_function_parts[1]
		head_dependency[head_obj.get_to()] = head_function
	# TEST 
		#print head_obj.get_from(), head_obj.get_to(), my_parser.get_term(head_obj.get_from()).get_lemma(), my_parser.get_term(head_obj.get_to()).get_lemma(), head_obj.get_function()
		id_parts = head_obj.get_to().split('_')
		to_id = id_parts[1]
		if predicate_arguments.get(head_obj.get_from()) is not None:
			predicate_arguments[head_obj.get_from()].append(int(to_id))
		else:
			predicate_arguments[head_obj.get_from()] = []
			predicate_arguments[head_obj.get_from()].append(int(to_id))	
		# make sure the arguments list contains no duplicates and is sorted 
		list2 = list(set(predicate_arguments[head_obj.get_from()]))		
		list2.sort(key=int)	
		predicate_arguments[head_obj.get_from()] = list2
	
# For each argument head, you also want to know which other tokens are part of the argument 
predicate_argument_spans = {} 
for id in predicate_arguments:
	for item in predicate_arguments[id]:
		try:
			for chunk in my_parser.get_constituency_extractor().get_all_chunks_for_term("t_" + str(item)):
				#print id, "t_",item, chunk[0], chunk
				if chunk[0] != 'smain' and chunk[0] != 'top' and chunk[0] != 'inf':
					if chunk[1].count(id) == 1:
						break
				#	print id, "t_",item, chunk[0], chunk
					#predicate_argument_spans[id][item] = chunk[0]
					if id not in predicate_argument_spans:
						predicate_argument_spans[id] = {}
					if item not in predicate_argument_spans[id]:
						predicate_argument_spans[id][item] = []
						predicate_argument_spans[id][item].append(chunk[1])
					elif len(predicate_argument_spans[id][item]) < len(chunk[1]):
						predicate_argument_spans[id][item] = chunk[1]
		except KeyError:
			continue  	
	
arguments = {} 	
argument_text = {}				
for predicate in predicate_argument_spans:
	#print predicate, predicate_argument_spans[predicate]
	for item in predicate_argument_spans[predicate]:
		templist = []
		text = "" 
		for term in predicate_argument_spans[predicate][item]:
			if isinstance(term, str):
				term_id = term[2:]
			elif isinstance(term, list):
				term_id = term[0][2:]
			templist.append(int(term_id))
		templist.sort(key=int)
		predicate_argument_spans[predicate][item] =  templist 
		for index in templist:
			text = text + " " +  my_parser.get_term("t_" + str(index)).get_lemma() 
		arguments["t_" + str(item)] = predicate_argument_spans[predicate][item]
		argument_text["t_" + str(item)] = text
		#print predicate, item, term, arguments["t_" + str(item)], predicate_argument_spans[predicate][item] 

arg_cat_patterns = {}
arg_dep_patterns = {} 
for pred in predicate_arguments:
 	for arg in predicate_arguments[pred]:
 		verb = pred
 		if auxiliary_verbs.get(pred) is not None:
 			arg_aux_combo = auxiliary_verbs[pred] + '-t_' + str(arg)
 			if dependencies.get(arg_aux_combo) is not None:
 				verb = auxiliary_verbs[pred]
 		verb_pos = verb.strip('t_')		
 		pred_arg_id = pred + '-t_' + str(arg)
 		arg_id = 't_' + str(arg)
 		arg_cat_pattern = ''
 		arg_cat_pattern_ids = []
 		arg_cat_pattern_ids.append(int(verb_pos))
 		arg_dep_pattern = ''
 		for d_arg in predicate_arguments[verb]:
 			d_arg_id = 't_' + str(d_arg)
# 		#	print argument_category_head[d_arg_id]
 			arg_cat_pattern_ids.append(int(d_arg))
 
 		pattern_list = list(set(arg_cat_pattern_ids))
 		pattern_list.sort(key=int)
 		for part in pattern_list:
 			part_id = 't_' + str(part)
 			if str(part_id) == str(verb):
 				arg_cat_pattern = arg_cat_pattern + '*' + argument_category_term[verb]
 				arg_dep_pattern = arg_dep_pattern + '*' + 'hd'
 			elif d_arg == arg:
 				if argument_category_head.get(part_id) is None:
 					if argument_category_deep.get(part_id) is not None:
 						arg_cat_pattern = arg_cat_pattern + '*' + argument_category_deep[part_id]
 					else:
 						arg_cat_pattern = arg_cat_pattern + '*' + '#'
 				else:
 					arg_cat_pattern = arg_cat_pattern + '*' + argument_category_head[part_id]
 				arg_dep_pattern = arg_dep_pattern + '*' + head_dependency[part_id]
 			elif arguments.get(d_arg_id) is not None and len(arguments[d_arg_id]) > 1:
 				if argument_category_head.get(part_id) is None:
 					if argument_category_deep.get(part_id) is not None:
 						arg_cat_pattern = arg_cat_pattern + '*' + argument_category_deep[part_id]
 					else:
 						arg_cat_pattern = arg_cat_pattern + '*' + '#'
 				else:
 					arg_cat_pattern = arg_cat_pattern + '*' + argument_category_head[part_id]
 				arg_dep_pattern = arg_dep_pattern + '*' + head_dependency[part_id]
 			else:
# 		#		print 'arg_part', part_id
 				arg_cat_pattern = arg_cat_pattern + '*' + argument_category_term[part_id]
 				arg_dep_pattern = arg_dep_pattern + '*' + head_dependency[part_id]
 		arg_cat_pattern = arg_cat_pattern.strip('*')
 		arg_dep_pattern = arg_dep_pattern.strip('*')
 		arg_cat_patterns[pred_arg_id] = arg_cat_pattern
 		arg_dep_patterns[pred_arg_id] = arg_dep_pattern
 			
# Remove the auxiliary verbs from the predicate dictionary 
# because you're only making feature vectors for the main verbs 
# also use this info to assign the voice
voice = {}					
for verb in auxiliary_verbs:
 	if predicates.get(auxiliary_verbs[verb]) is not None:
 		del predicates[auxiliary_verbs[verb]]
 	if my_parser.get_term(auxiliary_verbs[verb]).get_lemma() == 'worden' or my_parser.get_term(auxiliary_verbs[verb]).get_lemma() == 'zijn':
 		voice[verb] = 'passive'
 	else:
 		voice[verb] = 'active'
 
 	
# Loop through the predicates and create the feature vectors 
vectors = {}  		
for predicate in predicates:
 	if voice.get(predicate) is None:
 		voice[predicate] = 'active'
 	pos = rewrite_postag(predicate)
# 	print predicate, my_parser.get_term(predicate).get_lemma(), pos.lower()
 	if predicate_arguments.get(predicate) is not None:
 		for arg in predicate_arguments[predicate]:
 			argument_head = ('t_' + str(arg))
 			vector_id = predicate + ',t_' + str(arg)
 			vectors[vector_id] = vector_id 
# 			# check if there is an argument category for the argument head
# 			# otherwise, set value to '#'
 			if argument_category_head.get(argument_head) is None:
 				argument_category_head[argument_head] = '#'
# 			# Get the predicate position and compare it to the argument position to obtain
# 			# the argument position feature
 			position = 'before'  
 			predicate_pos = predicate.strip('t_')
 			if int(predicate_pos) < int(arg):
 				position = 'after'
# 			# rewrite the pos tag of the argument 
 			argpos = rewrite_postag(argument_head)
# 			# get the first and last tokens and their POS tags of the argument
# 			# if the argument contains more than one token, otherwise, the value is '#'
 			arg_start_lemma = '#'
 			arg_start_pos = '#'
 			arg_end_lemma = '#'
  			arg_end_pos = '#'
 			if arguments.get(argument_head) is not None and len(arguments[argument_head]) > 1:
 				arg_start = ("t_" + str(arguments[argument_head][0]))
 				arg_start_lemma = my_parser.get_term(arg_start).get_lemma()
 				arg_start_pos = rewrite_postag(arg_start)
 				arg_end = ("t_" + str(arguments[argument_head][-1]))
 				arg_end_lemma = my_parser.get_term(arg_end).get_lemma()
 				arg_end_pos = rewrite_postag(arg_end)
 			elif arguments.get(argument_head) is None:
 				arguments[arg] = '#'	
# 			# This is to make sure no extra commas get added to the feature vector 
 			if arg_start_lemma == ',':
 				arg_start_lemma = '#' 
 				arg_start_pos = '#'
 			if arg_end_lemma == ',':
 				arg_end_lemma = '#'
 				arg_end_pos = '#' 
# 			# You also don't want commas inside numbers 
 			arg_start_lemma = arg_start_lemma.replace(',', '.')
 			arg_end_lemma = arg_end_lemma.replace(',', '.')
# 				 
 			pred_arg_id = predicate + '-' + argument_head
# 			# The arg cat+relpattern consists of the arg_cat and the arg_dep
# 			# if argcat is '#', then the second part is left open
 			arg_cat_rel = str(head_dependency[argument_head]) + '*'
 			if argument_category_head[argument_head] != '#':
 				arg_cat_rel = arg_cat_rel + argument_category_head[argument_head]
# 			# Add features to the vector 
			# Insert + argument_text[argument_head] + ',' somewhere to check if the argument was chosen correctly. 
 			vectors[vector_id] = vector_id + ',t_' + str(arguments[argument_head][0]) + ',t_' + str(arguments[argument_head][-1]) + ',' +  my_parser.get_term(predicate).get_lemma() + ',' + pos.lower() + ',' + voice[predicate] + ',' + argument_category_head[argument_head] + ',' + str(head_dependency[argument_head]) + ',' + position + ',' + my_parser.get_term(argument_head).get_lemma() + ',' + argpos.lower() + ',' + arg_start_lemma + ',' + arg_start_pos + ',' + arg_end_lemma + ',' + arg_end_pos +',' +  arg_cat_patterns[pred_arg_id] + ',' + arg_dep_patterns[pred_arg_id] + ',' + arg_cat_rel + ',' + '#' 
# 		
# # Print vectors 
for vector in vectors:
	print vectors[vector].encode('utf-8')
# 	
# 	
# 
# 	
# 					