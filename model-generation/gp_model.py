"""
DP models based on MLP
"""
from deap import base, creator, tools, algorithms, gp
from tqdm import tqdm
import numpy as np
import operator
import time 

MAX_UNCHANGED = 10 

def protect_div(x, y):
	return np.divide(x, y, out = np.zeros_like(x), where = y!=0)

def protect_sqrt(x):
	return np.sqrt(np.abs(x))

def if_then_else(input, output1, output2):
	return output1 if input else output2


class GP_model(object):
	def __init__(self, 
		features,
		maxTreeDepth = 8, 
		minTreeDepth = 1, 
		initMaxTreeDepth = 6, 
		cxpb = 0.9,
		mutpb = 0.1, 
		random_state = None,
		num_pop = 40,
		ngen = 100):

		super(GP_model, self).__init__()

		np.random.seed(random_state)

		self.features = features 
		self.maxTreeDepth = maxTreeDepth
		self.minTreeDepth = minTreeDepth
		self.initMaxTreeDepth = initMaxTreeDepth
		self.ngen = ngen
		self.num_pop = num_pop
		self.cxpb = cxpb
		self.mutpb = mutpb

	@staticmethod
	def evaluate_indiv_using_dict(individual, features, data):
		"""
		features: a list of features to be used. 
		data:
			a dictionary of feature array with lenght N, N = number of data points
		"""
		# redefine individual 
		num_data = None
		for feature in features:
			individual = individual.replace(feature, "data[{}][idx]".format(feature))
			if num_data is None:
				num_data = len(data[feature])

		sps = np.zeors(num_data, dtype = np.float)
		# evalaute
		for idx in range(num_data):
			sps[idx] = eval(individual)
		return sps 


	@staticmethod
	def evaluate_indiv_using_array(individual, features, data):
		"""
		features: a list of features to be used. 
		data:
			a feature array with lenght [N, len(features)], N = number of data points
		"""
		num_data = len(data)
		# redefine individual 
		ones = np.ones(num_data)
		for feature_idx, feature_name in enumerate(features):
			individual = str(individual).replace(feature_name, "data[:,{}]".format(feature_idx))	
		individual = individual.replace('1.0', 'ones')
		# evalaute
		sps = eval(individual)
		return sps 


	@staticmethod
	def static_eval_func(individual, features, data_per_fault, is_flaky_per_fault, tie_breaker = 'max'):
		"""
		Evalauet current solutioin 
		data_df_lst -> contain a list of dataframe that contains metric info for a single fault
		"""
		from scipy.stats import rankdata 
		best_rank_of_flaky_classes = []; ranks_of_all = {}; ranks_of_faults = {}
		for commit, data in data_per_fault.items():
			indices_to_flaky = np.where(is_flaky_per_fault[commit] == 1)[0]
			sps = GP_model.evaluate_indiv_using_array(individual, features, data)

			ranks = rankdata(-sps, method = tie_breaker)
			ranks_of_flaky = ranks[indices_to_flaky]
			best_rank_of_flaky = np.min(ranks_of_flaky)
			best_rank_of_flaky_classes.append(best_rank_of_flaky)
			ranks_of_all[commit] = ranks
			ranks_of_faults[commit] = best_rank_of_flaky
		
		# avg wef 
		avg_rank_of_flaky_class = np.mean(best_rank_of_flaky_classes)
		return avg_rank_of_flaky_class, ranks_of_faults, ranks_of_all


	# to be used within the instance
	def eval_func(self, individual):
		"""
		Evalauet current solutioin 
		data_df_lst -> contain a list of dataframe that contains metric info for a single fault
		"""
		from scipy.stats import rankdata 
		
		best_rank_of_flaky_classes = []
		for commit, data in self.data_per_fault.items():
			indices_to_flaky = np.where(self.is_flaky_per_fault[commit] == 1)[0]
			sps = GP_model.evaluate_indiv_using_array(individual, self.features, data)

			ranks = rankdata(-sps, method = self.tie_breaker) # larger, better 
			ranks_of_flaky = ranks[indices_to_flaky]
			best_rank_of_flaky = np.min(ranks_of_flaky)
			best_rank_of_flaky_classes.append(best_rank_of_flaky)
	
		# avg wef 
		avg_rank_of_flaky_class = np.mean(best_rank_of_flaky_classes)
		return (avg_rank_of_flaky_class,)


	def gen_primitives(self):
		"""
		"""
		pset = gp.PrimitiveSet('main', len(self.features)) # arity = len(features)
		# rename
		for idx, feature_name in enumerate(self.features):
			pset.renameArguments(**{"ARG" + str(idx):feature_name})
			print ("ARG{} -> {}".format(idx, feature_name))

		pset.addPrimitive(np.add, 2, name = "np.add")
		pset.addPrimitive(np.subtract, 2, name = "np.subtract")
		pset.addPrimitive(np.multiply, 2, name = "np.multiply")
		pset.addPrimitive(np.negative, 1, name = "np.negative")
		pset.addPrimitive(protect_div, 2, name = "protect_div")
		pset.addPrimitive(protect_sqrt, 1, name = "protect_sqrt")
		pset.addTerminal(1.0) 

		return pset


	def init(self, maxTreeDepth, minTreeDepth, initMaxTreeDepth, num_pop = 40, gen_full = False):
		"""
		"""
		#Setting parameter(feature) for evolving: pset == feature set
		pset = self.gen_primitives()
		if ("Fitness" in globals()):
			del creator.Fitness
		if ("Individual" in globals()):
			del creator.Individual

		creator.create("Fitness", base.Fitness, weights = (-1.0,))
		creator.create("Individual", gp.PrimitiveTree, fitness = creator.Fitness, pset = pset)	

		toolbox = base.Toolbox()
		if not gen_full:
			toolbox.register("expr", gp.genHalfAndHalf, pset = pset, min_ = minTreeDepth, max_ = initMaxTreeDepth)
		else:
			toolbox.register("expr", gp.genFull, pset = pset, min_ = minTreeDepth, max_ = initMaxTreeDepth)

		toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
		toolbox.register("population", tools.initRepeat, list, toolbox.individual, n = num_pop)	
		toolbox.register("compile", gp.compile, pset = pset)		
		toolbox.register("evaluate", self.eval_func)	
		# This is for parent selection, not the survivor selection
		tournsize = int(num_pop * 0.2) if int(num_pop * 0.2) % 2 == 0 else int(num_pop * 0.2) + 1	
		toolbox.register("select", tools.selTournament, tournsize = tournsize, fit_attr = "fitness")
		toolbox.register("mate", gp.cxOnePoint)
		toolbox.register("mutate", gp.mutUniform, expr = toolbox.expr, pset = pset)	

		toolbox.decorate("mate", gp.staticLimit(key = operator.attrgetter("height"), max_value = maxTreeDepth))
		toolbox.decorate("mutate", gp.staticLimit(key = operator.attrgetter("height"), max_value = maxTreeDepth))	

		self.toolbox = toolbox


	def check_duplicate(self, offspring, selected):
		"""
		Return True if it is duplicated, else return False
		"""
		is_duplicated = str(offspring) == str(selected)	
		return is_duplicated


	def search(self, toolbox, ngen, num_pop, cxpb, mutpb, num_best = 1):	
		"""
		main method where genetic programming is actually taken place
		"""
		pop = toolbox.population(n = num_pop)
		fitness_per_ind = toolbox.map(toolbox.evaluate, pop)
		for fit, ind in zip(fitness_per_ind, pop):
			ind.fitness.values = fit
			print ("-\t", str(ind), fit)
		
		# contain the best results found so far
		best = tools.HallOfFame(num_best, similar = self.check_duplicate)
		best.update(pop)

		# statistics -> average, max, min
		stats = tools.Statistics(lambda ind: ind.fitness.values[0])
		stats.register("average", np.mean, axis = 0)
		stats.register("max", np.max, axis = 0)
		stats.register("min", np.min, axis = 0)
		stats_result = stats.compile(pop)

		# for logging
		logbook = tools.Logbook()
		logbook.record(gen = 0, max = stats_result["max"], mean = stats_result["average"], min = stats_result["min"])

		cnt_unchanged = 0; prev_best = None
		for idx_to_gen in tqdm(range(1, ngen + 1)):
			next_pop = []	
			while len(next_pop) < num_pop:
				# used tournment to select parents 
				parents = toolbox.select(pop, 2) 
				offsprings = algorithms.varAnd(parents, toolbox, cxpb, mutpb)	
				for offspring in offsprings:	
					if len(next_pop) == 0 or not self.check_duplicate(offspring, next_pop):
						next_pop.append(offspring)

			fitness_per_ind = toolbox.map(toolbox.evaluate, next_pop)	
			#update next_pop, with invalid fitness, with the new(valid) fitness
			for fit, ind in zip(fitness_per_ind, next_pop): 
				ind.fitness.values = fit
				
			# select next population
			# Survival Selection -> select the ones go into the next generation
			pop[:] = tools.selBest(pop + next_pop, num_pop)

			#update current best for this new pop -> HallOfFame
			best.update(pop)

			#Logging current status the pop
			stats_result = stats.compile(pop)
			logbook.record(gen = idx_to_gen, max = stats_result["max"], mean = stats_result["average"], min = stats_result["min"])
			print (logbook)

			print ("\n\tGeneration {}: {}(Max), {}(AVG), {}(MIN)".format(
				idx_to_gen, stats_result["max"], stats_result["average"], stats_result["min"]))	
			print ("\t\tbest individual: {} ({})".format(str(best[0]),best[0].fitness.values[0]))

			if prev_best == best[0]:
				cnt_unchanged += 1
				if cnt_unchanged == MAX_UNCHANGED: # continuous
					print ("The best model has not been changed for {} continuous commits".format(MAX_UNCHANGED))
					break 
			else:
				cnt_unchanged = 0
			prev_best = best[0]

		return best, logbook


	def run(self, data_per_fault, cands_per_fault, labels_per_fault,
		maxTreeDepth = None, minTreeDepth = None, initMaxTreeDepth = None,
		gen_full = False, cxpb = None, mutpb = None, num_pop = None, ngen = None, num_best = 1, tie_breaker = 'max'):
		"""
		"""
		if maxTreeDepth is None: maxTreeDepth = self.maxTreeDepth
		if minTreeDepth is None: minTreeDepth = self.minTreeDepth
		if initMaxTreeDepth is None: initMaxTreeDepth = self.initMaxTreeDepth
		if cxpb is None: cxpb = self.cxpb
		if mutpb is None: mutpb = self.mutpb
		if num_pop is None: num_pop = self.num_pop
		if ngen is None: ngen = self.ngen

		self.data_per_fault = data_per_fault
		self.cands_per_fault = cands_per_fault
		self.is_flaky_per_fault = labels_per_fault
		self.tie_breaker = tie_breaker

		# here, all those before the actual search will take place: 
		# 	type creation & instance initialisaiton, toolbox operator registration
		self.init(maxTreeDepth, minTreeDepth, initMaxTreeDepth, num_pop = num_pop, gen_full = gen_full)

		# search start!  
		print ("Genetic Programming search start!")
		t1 = time.time()
		best, logbook = self.search(self.toolbox, ngen, num_pop, cxpb, mutpb, num_best = num_best)
		t2 = time.time()
		print ("Time taken for search: {}".format(t2 - t1))

		print ("\nThe best individual ")
		print ("\t\t expression : " + str(best[0]))
		print ("\t\t fitness   : " + str(best[0].fitness.values[0]))
		best_mdl = best[0]
		return best_mdl, logbook


	@staticmethod
	def predict(individual, features, data, tie_breaker = 'max'):
		"""
		compute the suspiciousness scores and ranks based on these scores 
		using a given individual (i.e., a synthesised formula)
		"""
		from scipy.stats import rankdata 

		sps = GP_model.evaluate_indiv_using_array(individual, features, data)
		ranks = rankdata(-sps, method = tie_breaker)
		return sps, ranks


	@staticmethod
	def evaluate_model(mdl, features, data_per_fault, is_flaky_per_fault, 
		cands_per_fault = None, tie_breaker = 'max'):
		"""
		compute the suspiciousness scores using a givne mdl.
		here, we assume to have data for a single fault
		data_per_fault, is_flaky_per_fault, cands_per_fault -> should be in the same order
		"""
		avg_rank_of_flaky_class, ranks_of_faults, ranks_of_all = GP_model.static_eval_func(
			mdl, features, data_per_fault, is_flaky_per_fault, tie_breaker = tie_breaker)
		print ("For {}, fitness (avg wef): {}".format(str(mdl), avg_rank_of_flaky_class))

		if cands_per_fault is not None:
			fault_at_lst = list(cands_per_fault.keys()) # a list of fix-commit for a flaky test
			for fault_at in fault_at_lst:
				is_flaky_vs = is_flaky_per_fault[fault_at]
				indices_to_faults = np.where(is_flaky_vs == 1)[0]
				faults = cands_per_fault[fault_at][indices_to_faults]

				best_fault_rank = ranks_of_faults[fault_at]
				is_flaky_vs = is_flaky_per_fault[fault_at]
				rank_of_all_faults = ranks_of_all[fault_at][indices_to_faults]
				
				print ("For {}, best rank: {} and for each fault".format(fault_at, best_fault_rank))
				for fault, rank in zip(faults, rank_of_all_faults):
					print ("\t{}: {}".format(fault, rank))
		
		return avg_rank_of_flaky_class, ranks_of_faults, ranks_of_all



