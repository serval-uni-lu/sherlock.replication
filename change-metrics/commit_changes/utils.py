"""
"""
import git
from tqdm import tqdm
import numpy as np

def get_previous_commits(commit, 
	repo, 
	g = None, 
	with_author_and_date = False,
	parse_date = False,
	before_date = None,
	with_strip = False):
	"""
	return a list of commits before a given commit
	"""
	if g is None:
		import git
		g = git.Git(repo)

	entire_commits = [] # will be the latest to the oldest
	if not with_author_and_date:
		if before_date is None:
			loginfo = g.log("--pretty=oneline", "-w")
		else:
			loginfo = g.log("--pretty=oneline", "-w", '--before=\"{}\"'.format(before_date)) # e.g., 2015-7-3

		for logline in loginfo.split("\n"):
			_commit = logline.split(" ")[0]
			entire_commits.append(_commit)
	else:
		if before_date is None:
			loginfo = g.log("--pretty=\"**COMMIT**%H %aN\n%ad\n%s\n%b\"", '-w')
		else:
			loginfo = g.log("--pretty=\"**COMMIT**%H %aN\n%ad\n%s\n%b\"", '-w','--before=\"{}\"'.format(before_date))
			
		loglines = loginfo.split("\n")
		for i, logline in enumerate(loglines):
			if logline.startswith('"'):
				logline = logline[1:]
			if logline.endswith('"'):
				logline = logline[:-1]

			if logline.startswith("**COMMIT**"): # start of new commit
				cnt = 0
			else:
				cnt += 1

			if cnt == 0:
				logline = logline[10:]
				_commit = logline.split(" ")[0]
				_author = " ".join(logline.split(" ")[1:])
				entire_commits.append([_commit, _author])
			elif cnt == 1: # the second line
				date_in_str = logline
				if parse_date:
					from dateutil import parser as dateparser
					_commit_time = dateparser.parse(date_in_str)
					entire_commits[-1].append(_commit_time)
				else:
					entire_commits[-1].append(date_in_str)
			elif cnt == 2: # the third
				commit_msg = logline.strip() if not with_strip else logline
				entire_commits[-1].append(commit_msg)
			else: # remaining
				commit_body = logline.strip() if not with_strip else logline
				entire_commits[-1][-1] += commit_body

	if commit is not None:
		if not with_author_and_date:
			idx_to_target_commit = entire_commits.index(commit)
		else:
			idx_to_target_commit = [v[0] for v in entire_commits].index(commit)
		commits_in_range = entire_commits[idx_to_target_commit+1:]
	else:
		commits_in_range = entire_commits

	return commits_in_range

	
def get_root(filename, 
	only_src_file = True, 
	postfix = ".java",
	project_id = None):
	"""
	return a root directory of a givne file (filename)
	e.g., commons-lang: lang, commons-math: math, joda-time: time, 
		closure compiler: goolgle (...;), jfreechart: chart, mockito: mockito
	"""
	import os

	if only_src_file and not filename.endswith(postfix):
		print ("The given file is not a source file: %s <-> %s" % (filename, postfix))
		import sys; sys.exit()

	# a list of directoruy sorted based on their level
	dirs_in_order = os.path.dirname(filename).split("/")
	if project_id is None:
		root_dir = dirs_in_order[0] # start with the top directory as the root directory
		for sub_dir in dirs_in_order[1:]:
			root_dir = os.path.join(root_dir, sub_dir)
			contained_lst = os.listdir(root_dir)
			if len(contained_lst) > 1: # more than one file (or directory)
				return root_dir
		
		return root_dir # will be same with the directory of the file filename
	else:
		#project_id = project_id.lower() 
		dirs_in_order = os.path.dirname(filename).split("/")
		root_dir = None
		for i, sub_dir in enumerate(dirs_in_order):
			if sub_dir.startswith(project_id): # e.g., lang3
				root_dir = "/".join(dirs_in_order[:i + 1]) # e.g., src/main/java/org/apache/commons/lang3
				break

		if root_dir is None:
			print ("Wheter the current give file is in our traget is not certain: %s vs %s" % (filename, project_id))
			import sys; sys.exit()

		return root_dir


def get_modified(commit, 
	repo, g = None, 
	file_postfix = None):
	"""
	return commit extracted from the git show operation and a list fo files 
	"""
	if g is None:
		g = git.Git(repo)

	#showinfo = g.show("--name-only", "--pretty=oneline", commit)
	loginfo = g.log("-r", commit, '--name-only', '--pretty=oneline', '-n 1', '-w')
	#show_lines = [line for line in showinfo.split("\n") if bool(line.strip())]
	log_lines = [line for line in loginfo.split("\n") if bool(line.strip())]
	#_commit = show_lines[0].split(" ")[0]
	_commit = log_lines[0].split(" ")[0]

	assert _commit == commit, "%s vs %s" % (_commit, commit)
	if file_postfix is not None:
		#files = [line.strip() for line in show_lines[1:] if line.endswith(file_postfix)]
		files = [line.strip() for line in log_lines[1:] if line.endswith(file_postfix)]
	else:
		#files = [line.strip() for line in show_lines[1:]]
		files = [line.strip() for line in log_lines[1:]]

	return _commit, files


def get_modified_ignore_whitespace(commit, 
	repo, g = None, 
	file_postfix = None):
	"""
	return commit extracted from the git show operation and a list fo files 
	"""
	import re

	if g is None:
		g = git.Git(repo)

	start_of_new_file_pat = "^diff --git a/.* b/(.*)$"
	#c_START_OF_NEW_FILE_FORMAT = "^diff --combined {}" # cc version

	showinfo = g.show("-w", commit)
	show_lines = [line for line in showinfo.split("\n") if bool(line.strip())]

	_commit = show_lines[0].split(" ")[1] # commit commit_sha
	#_commit = log_lines[0].split(" ")[0] 

	assert _commit == commit, "%s vs %s" % (_commit, commit)

	#print (start_of_new_file_pat)
	files = []
	for line in show_lines:
		#print (line)
		matcheds = re.match(start_of_new_file_pat, line)
		#print ("\tmatched", matcheds)
		if bool(matcheds):
			#print ("\t===", matcheds.groups())
			processed_file = matcheds.groups()[0]
			if file_postfix is None or processed_file.endswith(file_postfix):
				files.append(processed_file)

	return _commit, files


def get_common_files(filelst_1, filelst_2, sim_threshold = 0.9):
	"""
	return a list of files in filelst_1 that are in filelst_2
	"""
	import os
	common = []
	paired_and_sim = {} # key = (file_1, file_2), value = a similarity value between them

#	print ("Files 1", filelst_1)
#	print ("Files 2", filelst_2)
	i = 0
	for file_1 in filelst_1:
		for file_2 in filelst_2:
			i += 1
			key = os.path.basename(file_1)
			if file_1 == file_2:
#				print ("\t perfect", i, file_1, file_2)
				#if key in paired_and_sim.keys():
				#	common.remove(paired_and_sim[key][0])
				try:
					_ = paired_and_sim[key]
					common.remove(paired_and_sim[key][0])
				except Exception:
					pass 
				common.append([file_1, file_2])
				paired_and_sim[key] = ([file_1, file_2], 1.)
			elif sim_threshold < 1.0 and os.path.basename(file_1) == os.path.basename(file_2):
#				print ("\t cand", i, file_1, file_2)
				dir_1 = os.path.dirname(file_1)
				dir_2 = os.path.dirname(file_2)
				
				import difflib
				sim_btwn_files = difflib.SequenceMatcher(a = dir_1, b = dir_2).ratio()
				if sim_btwn_files >= sim_threshold:
					## org
					#if key not in paired_and_sim.keys():
##						print ("\t in", i, file_1, file_2, sim_btwn_files)
						#common.append([file_1, file_2])
						#paired_and_sim[key] = ([file_1, file_2], sim_btwn_files)
					#else:
						#_sim = paired_and_sim[key][1]
						#if _sim < sim_btwn_files: # current one has a higher similarity
##							print ("\t in", i, file_1, file_2, sim_btwn_files, _sim)
							#common.remove(paired_and_sim[key][0])
							#common.append([file_1, file_2]) # add new
							## update paired_and_sim to a new one
							#paired_and_sim[key] = ([file_1, file_2], sim_btwn_files)
					## org end
					###
					try:
						_ = paired_and_sim[key]
#						print ("\t in", i, file_1, file_2, sim_btwn_files)
						common.append([file_1, file_2])
						paired_and_sim[key] = ([file_1, file_2], sim_btwn_files)
					except Exception:
						_sim = paired_and_sim[key][1]
						if _sim < sim_btwn_files: # current one has a higher similarity
#							print ("\t in", i, file_1, file_2, sim_btwn_files, _sim)
							common.remove(paired_and_sim[key][0])
							common.append([file_1, file_2]) # add new
							# update paired_and_sim to a new one
							paired_and_sim[key] = ([file_1, file_2], sim_btwn_files)

	return common 


def update_renamed_files(file_rename_history, renamed):
	"""
	file_rename_history: key = initial file, value: a history of file-rename (list)
	renamed: 
		key: initial file, value: renamed-to-file
	"""
	# update file_rename_history
	for target_file, renamed_history in file_rename_history.items():
		# the target_file has been renamed -> update
		if renamed_history[-1] in renamed.keys():
			file_rename_history[target_file].append(renamed[renamed_history[-1]])

	return file_rename_history


def get_renamed_files(target_commit, 
	comp_commit,
	file_rename_history = None, 
	repo = None, 
	g = None):
	"""
	"""
	if file_rename_history is None and g is None:
		assert repo is not None
		g = git.Git(repo)

	if file_rename_history is None:
		#diffinfo = g.diff("--name-status", "-C", target_commit, comp_commit)
		#diffinfo = g.diff("--name-status", "-C80", target_commit, comp_commit)
		diffinfo = g.diff("--name-status", "-M95", target_commit, comp_commit)
		diff_lines = [line for line in diffinfo.split("\n") if bool(line.strip())]
		renamed = {}
		for diff_line in diff_lines:
			if diff_line.startswith("R") or diff_line.startswith("C"): # rename-edit
				target_file, comp_file = diff_line.split("\t")[1:]
				renamed[target_file] = comp_file
	else:
		if target_commit in file_rename_history.keys():
			renamed = file_rename_history[target_commit]
		else:
			renamed = {}

	return renamed


#def get_modified_with_stat(commit, 
#	repo, g = None, 
#	file_postfix = None):
#	"""
#	return commit extracted from the git show operation and a list fo files 
#	"""
#	if g is None:
#		import git
#		g = git.Git(repo)#

#	showinfo = g.show("--oneline", "--numstat", commit)
#	show_lines = showinfo.split("\n")
#	_commit = show_lines[0].split("\t")[0]#

#	assert _commit == commit, "%s vs %s" % (_commit, commit)
#	if file_postfix is not None:
#		files = [line.strip() for line in show_lines[1:] if line.endswith(file_postfix)]
#	else:
#		files = [line.strip() for line in show_lines[1:]]
#	return _commit, files


def check_merge_commit(commit, repo, g = None):
	"""
	Chech whether a given commit is a merge commit
		-> since 'git show' shows nothing other than the commit message without using 
		an option "name-only" when the commit is a merge commit, we use git-show without
		name-only option to check
	"""
	if g is None:
		g = git.Git(repo)

	showinfo = g.show("--pretty=oneline", "-w", commit)
	show_lines = [line for line in showinfo.split("\n") if bool(line.strip())]
	
	if len(show_lines) == 1 and show_lines[0].startswith(commit): # since we use pretty & oneline
		return True
	else:
		return False


def list_existing_files(commit, repo, postfix = ".java"):
	"""
	"""
	import subprocess
	import os

	cwd = os.getcwd()
	os.chdir(repo)

	cmd = "git ls-tree --name-only -r %s" % (commit)

	result = subprocess.run([cmd], stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
	
	files = result.stdout.decode('ascii').split("\n")
	if postfix is None:
		target_files = files
	else:
		target_files = [file for file in files if file.endswith(postfix)]

	os.chdir(cwd)

	return target_files


def get_modfied_files_and_author(commit, repo, g = None, postfix = ".java"):
	"""
	"""
	if g is None:
		g = git.Git(repo)

	showinfo = g.show("--name-only", "--format=%aN", "-w", commit) # one run is fast, but if there are multiples(3596) of them,...
	show_lines = [line for line in showinfo.split("\n") if bool(line.strip())]

	author_name = show_lines[0]
	modified_files = show_lines[1:]

	return author_name, modified_files


def record_modfied_files_and_author_per_commit(commits_in_range, repo, g = None, postfix = ".java"):
	"""
	"""
	if g is None:
		g = git.Git(repo)

	recorded = {}
#	for commit in commits_in_range:
#		author_name, modified_files = get_modfied_files_and_author(commit, 
#			repo, 
#			g = g, 
#			postfix = postfix)
#		recorded[commit] = {'author':author_name, 'files':modified_files}
	the_first_commit = commits_in_range[0]
	loginfo = g.log("--format=%aN", "-w", the_first_commit) # one run is fast, but if there are multiples(3596) of them,...
	author_names = [author_name for author_name in loginfo.split("\n")]
	
	assert len(author_names) >= len(commits_in_range), "{} vs {}".format(len(author_names), len(commits_in_range))
	
	author_names = author_names[:len(commits_in_range)]

	for commit, author_name in tqdm(zip(commits_in_range, author_names)):
		_, modified_files = get_modified_ignore_whitespace(commit, 
			repo, 
			g = g, 
			file_postfix = postfix)
		recorded[commit] = {'author':author_name, 'files':modified_files}

	return recorded


def update_diff(added, deleted, modifieds, based_on_ED = False, line_no_and_context = None):
	"""
	"""
	if len(added) > 0 and len(deleted) > 0: # modified
		#print ("Modification!")
		if not based_on_ED:
			if len(added) > len(deleted):
				for i in range(len(deleted)):
					new_lineno = added[i]
					past_lineno = deleted[i]		
					modifieds['modified'].append([new_lineno, past_lineno])			

				for i in range(len(added) - len(deleted)):
					new_lineno = added[len(deleted) + i]
					past_lineno = deleted[-1] 	
					modifieds['modified'].append([new_lineno, past_lineno])		

			elif len(added) < len(deleted):
				for i in range(len(added)):
					new_lineno = added[i] 
					past_lineno = deleted[i]		
					modifieds['modified'].append([new_lineno, past_lineno])			

				for i in range(len(deleted) - len(added)):
					new_lineno = added[-1]
					past_lineno = deleted[len(added) + i]		
					modifieds['modified'].append([new_lineno, past_lineno])		

			else: # the same -> modification
				for new_lineno, past_lineno in zip(added, deleted):
					modifieds['modified'].append([new_lineno, past_lineno])	
		else:
			assert line_no_and_context is not None
			"""
			Use edit-distance to match deleted and added lines
			"""
			pass

	elif len(added) == 0: # deleted
		modifieds['deleted'].extend([(None, del_line) for del_line in deleted])
	else: # added
		modifieds['added'].extend([add_line, None] for add_line in added)

	# reset as it has been updatec
	added = []; deleted = []
	return added, deleted, modifieds



def get_modified_lines(commit, 
	repo, 
	g = None, 
	filename = None, 
	postfix = ".java"):
	"""
	For a given commit, return a list of file name and 

	Ret (dict): modified_lines
		key = filename, value: a dictionary of past and current line number of modified lines grouped
		by added, deleted, and modified: (lineno_in_current_commit, lineno_in_past_commit)
										None -> if only added or only deleted
	"""
	import re
	if g is None:
		g = git.Git(repo)

	if filename is None:
		#output = g.show('-c', commit)
		output = g.show('-w', commit) # WE WILL IGNORE THE MERGE COMMIT as the merge commit is an act of merging itself
		# retrive a list of modified files that ends with postfix
		#_, modified_files = get_modified(commit, repo, g = g, file_postfix = postfix)
		_, modified_files = get_modified_ignore_whitespace(commit, 
			repo, 
			g = g, 
			file_postfix = postfix)
		#print ("Modified files", modified_files)
		if len(modified_files) == 0: # does not contain any target source file
			return {}
	else:
		#output = g.show('-c', commit, "--", filename)
		output = g.show('-w', commit, "--", filename)
		modified_files = [filename]
	#print (modified_files); import sys; sys.exit()
	output_lines = output.split("\n")
	
	START_OF_NEW_FILE_FORMAT = "^diff --git a/.* b/{}"
	#cc_START_OF_NEW_FILE_FORMAT = "^diff --cc {}" # cc version
	c_START_OF_NEW_FILE_FORMAT = "^diff --combined {}" # cc version

	START_OF_NEW_FILES = [START_OF_NEW_FILE_FORMAT.format(mod_file) 
							for mod_file in modified_files]
	START_OF_NEW_FILES.extend([c_START_OF_NEW_FILE_FORMAT.format(mod_file) 
							for mod_file in modified_files])

	LINE_RANGE_START = "@@ -" # will be used with startswith
	cc_LINE_RANGE_START = "@@@ -" # cc version

	ADDED_LINE_RANGE = "^@@ .*\+([0-9]+),([0-9]+) @@"
	DELETED_LINE_RANGE = "^@@ -([0-9]+),([0-9]+) "
	cc_ADDED_LINE_RANGE = "^@@@ .*\+([0-9]+),([0-9]+) @@@"
	# take the last matched one => to cover the merge case
	cc_DELETED_LINE_RANGE = "^@@@ .*-([0-9]+),([0-9]+) \+"#"^@@@ -([0-9]+),([0-9]+) "

	modified_lines = {} # key = a path to the files, value: a list of 
	start_and_end_indices = {} 
	num_processed_files = 0 # the number of processed files so far
	curr_processing_file = None 
	added = []; deleted = []

	is_diff_cc = False

	#indices = np.arange(0, len(modified_files))
	indices = np.arange(0, 2 * len(modified_files)) # as we should consider cc version

	is_our_target = False
	#print (START_OF_NEW_FILES)
	for output_line in output_lines:
		#print ("===\t %s" % (output_line))
		if output_line.startswith("diff --git") or output_line.startswith("diff --combined"): # or output_line.startswith("diff --cc"):#--cc"):
			if any([re.search(PAT, output_line) for PAT in START_OF_NEW_FILES]):
				if output_line.startswith("diff --combined"): # or output_line.startswith("diff --cc"):#--cc"):
					is_diff_cc = True
				else:
					is_diff_cc = False

				#print ("===\t %s" % output_line, is_diff_cc)
				#import sys; sys.exit()
				#and num_processed_files > :
				num_processed_files += 1
				#print ('Matched', output_line, num_processed_files)
				indices_to_file_lst = indices[[bool(re.search(PAT, output_line)) for PAT in START_OF_NEW_FILES]]
				#print (indices_to_file_lst, len(modified_files))
				assert len(indices_to_file_lst) == 1, indices_to_file_lst # should be matched with no more than a single file
				idx_to_target_file = indices_to_file_lst[0] % len(modified_files)
				#print (idx_to_target_file)
				#print (modified_files)

				# check diff update for the previous file before settting a new curr_processing_file
				if num_processed_files >= 1 \
					and (len(added) > 0 or len(deleted) > 0): # if there remains diff that has not been updated
#					print ("Herre", curr_processing_file)
					added, deleted, modified_lines[curr_processing_file] = update_diff(
						added, 
						deleted, 
						modified_lines[curr_processing_file])

				# set 
				curr_processing_file = modified_files[idx_to_target_file] # e.g., src/main/java/org/...
				mod_lines_w_context = {'added':[], 'deleted':[]}

				#print ("Currently processing", curr_processing_file)
				is_our_target = True
			else: # not our range
				is_our_target = False
				#curr_processing_file = None
				#added = []; deleted = []
				pnt_curr = None; pnt_prev = None
				dist_curr = 0; dist_prev = 0
		else:
			if num_processed_files > 0 and is_our_target and curr_processing_file is not None: # in any of the file diff
				#print ("===\t %s" % (output_line))
				# can be eithrer in the actural diff part or the line where diff are started
				#if curr_processing_file not in start_and_end_indices.keys()
				#	or (curr_processing_file in start_and_end_indices.keys() and bool(output_line.startswith(LINE_RANGE_START))):
				if bool(output_line.startswith(LINE_RANGE_START))\
					or bool(output_line.startswith(cc_LINE_RANGE_START)): # @@ -5737,7 +5737,7 @@
					#print ("In line range", output_line)
					# check the last update if it exists
					if curr_processing_file in start_and_end_indices.keys():
						processed_curr = pnt_curr + dist_curr - 1 
						processed_prev = pnt_prev + dist_prev - 1

						add_last_line = sum(start_and_end_indices[curr_processing_file]['added'][-1]) - 1
						assert processed_curr == add_last_line, "Added line %s,%s: %d + %d vs %d" % (commit, curr_processing_file, pnt_curr, dist_curr, add_last_line)

						del_last_line = sum(start_and_end_indices[curr_processing_file]['deleted'][-1]) - 1
						#print (processed_prev, del_last_line)
						assert processed_prev == del_last_line, "Deleted line %s,%s: %d + %d vs %d" % (commit, curr_processing_file, pnt_prev, dist_prev, del_last_line)


					ADDED_LINE_RANGE_PAT = ADDED_LINE_RANGE if not is_diff_cc else cc_ADDED_LINE_RANGE

					#print ("ADDED_LINE_RANGE: %s vs %s"% (ADDED_LINE_RANGE_PAT, output_line))
					matched = re.match(ADDED_LINE_RANGE_PAT, output_line)
					### Temporary disabled => SHOULD HANDLE MERGE COMMIT... -> e.g., ignite  & 33079fc9c6fb6970ff24e88466e5edbf41ff1a28
					#assert bool(matched), output_line
					if not bool(matched): continue
					#################################

					add_start_num, num_added = [int(v) for v in matched.groups()]

					DELETED_LINE_RANGE_PAT = DELETED_LINE_RANGE if not is_diff_cc else cc_DELETED_LINE_RANGE

					#print ("DELETED_LINE_RANGE: %s vs %s"% (DELETED_LINE_RANGE_PAT, output_line))
					matched = re.match(DELETED_LINE_RANGE_PAT, output_line)
					assert bool(matched), output_line
					deleted_start_num, num_deleted = [int(v) for v in matched.groups()]
					#print ("Pointer", deleted_start_num, num_deleted)

					if curr_processing_file not in start_and_end_indices.keys():
						start_and_end_indices[curr_processing_file] = {'added':[], 'deleted':[]}
					
					start_and_end_indices[curr_processing_file]['added'].append((add_start_num, num_added))
					start_and_end_indices[curr_processing_file]['deleted'].append((deleted_start_num, num_deleted))
					
					if curr_processing_file not in modified_lines.keys():
						modified_lines[curr_processing_file] = {'added':[], 'deleted':[], 'modified':[]}
					
					# will store local ones -> modification is not considered here
					added = []; deleted = []
					
					# set a pointer that keep pointing the line examined now for the current and previous commit
					pnt_curr = add_start_num; dist_curr = 0 
					pnt_prev = deleted_start_num; dist_prev = 0

				elif curr_processing_file in start_and_end_indices.keys():
					# curr_processing_file in start_and_end_indices.keys() and 
					#		bool(output_line.startswith(LINE_RANGE_START) is False) 
					# will look at the main body of the diff since we are in the diff range
					# for deleted lines, the line after it will be collected if it is immediately followed by
					# the added lines, and if not (either followed by the another deleted line or unchanged lines),
					if output_line.startswith("+"):
						added.append(pnt_curr + dist_curr)
						mod_lines_w_context['added'].append([added[-1], output_line])
						dist_curr += 1
#						print ("in add", pnt_curr, dist_curr, len(added))
					elif output_line.startswith("-"):
						deleted.append(pnt_prev + dist_prev)
						mod_lines_w_context['deleted'].append([deleted[-1], output_line])
						dist_prev += 1
#						print ("in del", pnt_prev, dist_prev, len(deleted))
					else:
						# please keep in mind, if the diff does not contain any common line, then added and deleted 
						# will not be updated by here
						dist_prev += 1; dist_curr += 1
#						print ("in neural", added, deleted, pnt_prev, dist_prev, pnt_curr, dist_curr)
						if len(added) > 0 or len(deleted) > 0: # any line is added or deleted:
							added, deleted, modified_lines[curr_processing_file] = update_diff(
								added, 
								deleted, 
								modified_lines[curr_processing_file])
						else:
							pass
				else: # not our target
					pass

	# check whether the update of the last processed file has been completed
	if num_processed_files >= 1 and (len(added) > 0 or len(deleted) > 0):

		added, deleted, modified_lines[curr_processing_file] = update_diff(
			added, 
			deleted, 
			modified_lines[curr_processing_file])

	# if the merge commit contain a file that has been 
	assert num_processed_files == len(modified_files) or (
		num_processed_files == 0 and check_merge_commit(commit,repo,g=g)), "{} vs {} ({})".format(
			num_processed_files, len(modified_files), ",".join(modified_files))

	return modified_lines#, fail_to_process_files


def is_without_added(commit, repo, g = None, file_postfix = None):
	"""
	return True if it is without any added line
	"""
	if g is None:
		g = git.Git(repo)

	showinfo = g.show("--numstat", "--oneline", '-w', commit)
	show_lines = [line for line in showinfo.split("\n") if bool(line.strip())]

	for line in show_lines[1:]:
		vals = [v for v in line.split("\t") if bool(v)]
		assert len(vals) == 3, vals

		if vals[-1].endswith(file_postfix)\
			and vals[0].isdigit() and int(vals[0]) > 0:
			return False # contain addition

	return True



def is_commit_too_large(commit, repo, g = None):#, file_postfix = None):
	"""
	If commit is too large, skip it as it is most likely related to the maintence.
	-> "We ignore large commits—those that change at least 10,000 lines or 
		at least 100 files (F5b)—" (Are fix-indcuing...)
	"""
	if g is None:
		import git
		g = git.Git(repo)

	showinfo = g.show("--numstat", "--oneline", '-w', commit)
	show_lines = [line for line in showinfo.split("\n") if bool(line.strip())]
	#print (show_lines)
	if len(show_lines) - 1 >= 100:
		print ("The commit {} has too-many files: {}".format(commit, len(show_lines) - 1))
		return True
	else:
		num_added = 0; num_deleted = 0
		for line in show_lines[1:]:
			vals = [v for v in line.split("\t") if bool(v)]
			assert len(vals) == 3, vals
			#print (vals, line)

			num_added += int(vals[0]) if vals[0].isdigit() else 0
			num_deleted += int(vals[1]) if vals[1].isdigit() else 0

		if num_added + num_deleted > 10000:
			print ("The commit {} has too-many lines: {}".format(commit, num_added + num_deleted))
			return True
		else:
			return False


def get_fix_inducing_commit_lst(fix_induc_commit_file):
	"""
	Return a list of fix(or bug)-inducing commits (from the results of SZZUnlased)
	"""
	import json
	with open(fix_induc_commit_file) as f:
		fix_and_inducers = json.load(f)
	fix_inducing_commits = list(set(map(lambda v:v[1], fix_and_inducers)))
	return fix_inducing_commits


def categorise_commits(repo, g = None, commits = None):
	"""
	Categorise commits that have been maded on the given repo by general or pr
	it is a internal commit (e.g., by the author-> the number of maximum parents is 1) or 
	merged commits (e.g., PR type -> the number of minimum parents is 2)
	"""
	if g is None:
		g = git.Git(repo)

	pr_commits = []
	internal_commits = []
	# git log --min-parents=2 --oneline
	loginfo = g.log("--min-parents=2", "--pretty=oneline", "-w")
	loglines = [line for line in loginfo.split("\n") if bool(line.strip())]
	for line in loglines:
		_commit = line.split(" ")[0]
		pr_commits.append(_commit)

	loginfo = g.log("--max-parents=1", "--pretty=oneline", "-w")
	loglines = [line for line in loginfo.split("\n") if bool(line.strip())]
	for line in loglines:
		_commit = line.split(" ")[0]
		internal_commits.append(_commit)

	categorised = {'pr':pr_commits, 'internal':internal_commits}

	return categorised

def get_match_faulty_commit(key_to_issue, bug_fixes, entire_commits, from_jira):
	"""
	If a given issue is related to bug, return a commit that contains a bug, which is the commit right before the fix-commit.
	Otherwise, return None
	"""

	if from_jira:
		key = key_to_issue
	else:
		key = key_to_issue.split("-")[-1][:-5]

	if key in list(bug_fixes.keys()): # whether the current issue was a bug and has been fixed
		fix_commit = bug_fixes[key]['hash']
		idx_to_fix_commit = entire_commits.index(fix_commit)
		matched_buggy_commit = entire_commits[idx_to_fix_commit + 1] # commit right before the fix-commit
	else:
		matched_buggy_commit = None
	return matched_buggy_commit


def match_commit_to_commit(acommit, 
	bcommmit,
	perfect_match = True, 
	printout = False,
	_attr_keys = None):
	"""
	Match commit from one repository to the another
	(sha information differs because of the ...)
	acommit (dict):
		key: sha, author, date, msg
		value: values to the matching ones
	perfect_match:
		True: -> the commits are matached if and only if 
			all the information, sha, author, date, msg, are the same
		False: -> allow submatch
			all the information match except for msg.
			For the msg, if the similarity between the msgs is over
			0.9, then True
	"""
	attr_keys = ['author', 'date', 'msg'] if _attr_keys is None else _attr_keys
	if perfect_match:
		for key in attr_keys:
			value_from_a = acommit[key]
			value_from_b = bcommmit[key]
			if value_from_a == value_from_b:
				continue
			else:
				if printout:
					print ("Mismatch between {} for {} and {}: {} vs {}".format(
						key,
						acommit['sha'],
						bcommmit['sha'],
						value_from_a, 
						value_from_b))
				return False
		return True
	else:
		for key in set(attr_keys) - set(['msg']):
			value_from_a = acommit[key]
			value_from_b = bcommmit[key]
			if value_from_a == value_from_b:
				continue
			else:
				if printout:
					print ("Mismatch between {} for {} and {}: {} vs {}".format(
						key,
						acommit['sha'],
						bcommmit['sha'],
						value_from_a, 
						value_from_b))
				return False

		if acommit['msg'] == bcommmit['msg']:
			return True
		else:
			import nltk
			# levenshtein distance
			dist = nltk.edit_distance(acommit['msg'], bcommmit['msg'])
			normed_dist = dist / np.max(acommit['msg'], bcommmit['msg'])
			if normed_dist > 0.9:
				return True
			else:
				return False

def convert_to_arr(data, labels):
	"""
	Convert a given raw format of ccm data.
	data => key: commit, data: collected data
	labels => key: commit, data: lable of commit (1: fix-inducing, 0:non-inducing)
	"""

	COMMON_FEATURE_TYPES = ['size', 'diffusion', 'history', 'authored_experience']
	COMMON_FEATURES = {'size':['added', 'deleted'],
		'diffusion':['dir', 'file', 'entropy', 'subsystem'],
		'history':['uniq_changes', 'developers', 'age'],
		'authored_experience':['prior', 'recent', 'subsystem', 'awareness']}
	SIM_FEATURES = ['sim2ir_sum','sim2ir_max','sim2ir_mean']
	ALL_FEATURES = [cft for cfty in COMMON_FEATURE_TYPES for cft in COMMON_FEATURES[cfty]] + SIM_FEATURES

	commits = list(data.keys())
	num_features = len(ALL_FEATURES)
	feature_arr = np.zeros((len(commits), num_features))
	for i,commit in enumerate(commits):
		idx = 0
		for cfty in COMMON_FEATURE_TYPES:
			for cft in COMMON_FEATURES[cfty]:
				if cft == 'age':
					feature_arr[i,idx] = data[commit][cfty][cft]['mean']
				elif cft == 'entropy':
					if data[commit][cfty][cft] is None:
						feature_arr[i,idx] = 0. # entropy has been set to zero when none of the source files has been modified
					else:
						feature_arr[i,idx] = data[commit][cfty][cft]
				else:
					feature_arr[i,idx] = data[commit][cfty][cft]
				idx += 1
		
		for ft in SIM_FEATURES:
			feature_arr[i,idx] = data[commit][ft]
			idx +=1 

	commits_and_labels = [[c,labels[c]] for c in commits]
	headers = ALL_FEATURES 
	return {'headers':headers, 'commits_and_labels':commits_and_labels, 'features':feature_arr}
