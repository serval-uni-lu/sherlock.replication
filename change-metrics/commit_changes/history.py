"""
Collect two types of commit change information:
	1. Unique changes: the number of prior changes (i.e., commit) to the modified files
	2. Developers: a list of developers who have changed the modified files in the past
"""
import git
import utils

class History(object):
	"""docstring for History"""
	def __init__(self, repo, file_postfix = ".java"):
		super(History, self).__init__()
		self.repo = repo
		self.g = git.Git(repo)
		self.file_postfix = file_postfix

	def num_unique_changes(self, commit, target_files, 
		file_renamed = None,
		commits_in_range = None, 
		files_and_author_per_commit = None):
		"""
		the number of prior changes to the modified files 
		Ret: (int, dictionary)
			int: the number of prior changes made to the modified files
			dictionary: per file      
		"""
		if commits_in_range is None:
			commits_in_range = utils.get_previous_commits(commit, self.repo, g = self.g)

		num_counts_per_file = {target_file:0 for target_file in target_files}
		file_rename_history = {target_file:[target_file] for target_file in target_files}
		current_commit = commit
		for _commit in commits_in_range:
			if files_and_author_per_commit is None:
				showinfo = self.g.show("--name-only", "--oneline", _commit)
				show_lines = [line for line in showinfo.split("\n") if bool(line.strip())]
				modified_files = show_lines[1:]
			else:
				modified_files = files_and_author_per_commit[_commit]['files']
		
			renamed = utils.get_renamed_files(current_commit, 
				_commit,
				file_rename_history = file_renamed, 
				repo = self.repo, 
				g = self.g)
			
			# rename update
			utils.update_renamed_files(file_rename_history, renamed)
			the_last_ver_target_files = [file_rename_history[target_file][-1] for target_file in target_files]

			# get common files 
			paired_files = utils.get_common_files(the_last_ver_target_files, 
				modified_files,
				sim_threshold = 1.0)
	
			# afile is the file that is considered to be the same file with target_file in the _commit
			for the_last_ver_target_file, afile in paired_files:
				idx_to_target_file = the_last_ver_target_files.index(the_last_ver_target_file)
				num_counts_per_file[target_files[idx_to_target_file]] += 1

			# update for the next operation
			current_commit = _commit

		return sum(list(num_counts_per_file.values())), num_counts_per_file


	def num_developers(self, commit, target_files, #start_and_end_nums, 
		file_renamed = None, 
		commits_in_range = None, 
		files_and_author_per_commit = None):
		"""
		We do not consider the case whern a developer has more than one author name
		"""
		# use git blame on the target (a set of modified lines ) &
		participated_authors = []
		participated_authors_per_file = {target_file:[] for target_file in target_files}

		# need to look through all past commits
		if commits_in_range is None:
			commits_in_range = utils.get_previous_commits(commit, self.repo, g = self.g)

		#flag = True
		current_commit = commit
		for _commit in commits_in_range:
			if files_and_author_per_commit is None:
				record = utils.record_modfied_files_and_author_per_commit([_commit], 
					self.repo, 
					g = self.g, 
					postfix = self.file_postfix)
				author_name = record[_commit]['author']
				modified_files = record[_commit]['files']
			else:
				author_name = files_and_author_per_commit[_commit]['author']
				modified_files = files_and_author_per_commit[_commit]['files']

			# this is requried, as sometimes, the file doesn't exist in the commit 
			file_rename_history = {target_file:[target_file] for target_file in target_files}
			# get renamed files
			# renamed(dict): key = filename in current_commit, value: filename in _commit
			renamed = utils.get_renamed_files(current_commit,
				_commit,  
				file_rename_history = file_renamed,
				repo = self.repo, 
				g = self.g)

			# rename update
			utils.update_renamed_files(file_rename_history, renamed)
			the_last_ver_target_files = [file_rename_history[target_file][-1] for target_file in target_files]

			# get common files 
			files_to_check = utils.get_common_files(the_last_ver_target_files, 
				modified_files,
				sim_threshold = 1.0)
			#########

			if len(files_to_check) > 0:
				participated_authors.append(author_name)

			for _target_file, afile in files_to_check:
				target_file = target_files[the_last_ver_target_files.index(_target_file)]
				participated_authors_per_file[target_file].append(author_name)

			# update 
			current_commit = _commit

		uniq_authors = list(set(participated_authors))
		return len(uniq_authors), participated_authors, participated_authors_per_file
