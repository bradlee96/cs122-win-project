'''
So like itll be a champion recommender based on your champions that you like to play.

As the draft progresses, you will be able to add the current state of the draft so the recommender system will be able to update and give you a new

the main question is, how the fuck do we measure this? I mean, we would obv. have to use a greedy algorithm because as the draft evolves we can only get local solution? I mean, that wouldnt be good necesarily. That would be for a team comp recommender, but since we have a limited pool its not so good.

So how do we measure what is good for any given champion? lets say we have a zil, they have an eve, then we get a lux, how do we factor that in?
maybe we use a 'discrete' sort of thing, find the champion you play with the greatest average winrate with this champions seen?

Maybe we can just use a 'regression-like' sort of thing, where we use a greedy feed forward algorithm to pick who your champion would do the best with
'''


'''
Need to add some sort of experience factor, maybe a linear/logistic function
up to, say, like 50 games. 
'''
import time
import json
# g1 = {'winner': 1, 'me': 'malphite',
# 'allies': ['janna', 'quinn', 'ahri', 'warwick'], 
# 'enemies': ['ashe', 'braum', 'victor', 'rammus', 'shen']}
# g2 = {'winner': 1, 'me': 'lux',
# 'allies': ['janna', 'quinn', 'ahri', 'warwick'], 
# 'enemies': ['ashe', 'braum', 'victor', 'rammus', 'shen']}
# g3 = {'winner': 1, 'me': 'lux',
# 'allies': ['janna', 'quinn', 'ahri', 'warwick'], 
# 'enemies': ['ashe', 'braum', 'victor', 'rammus', 'shen']}
# g4 = {'winner': 0, 'me': 'malphite',
# 'allies': ['janna', 'quinn', 'ahri', 'warwick'], 
# 'enemies': ['ashe', 'braum', 'victor', 'rammus', 'shen']}
# g5 = {'winner': 0, 'me': 'malphite',
# 'allies': ['janna', 'quinn', 'ahri', 'warwick'], 
# 'enemies': ['ashe', 'braum', 'victor', 'rammus', 'shen']}

# matches = [g1,g2,g3,g4,g5]

def calculate_win_rate_per_champion_wrt_others(matchlist):
	'''
	Basically just want to add a bunch of shit so I can get some probs later
	[champ][allies/enemies][ally/enemy][[0,0]]
	'''
	bigdict = {}
	start_time = time.clock()
	for match in matchlist:
		bigdict.setdefault(match['me'],{'allies':{},'enemies':{}})
		for ally in match['allies']:
			bigdict[match['me']]['allies'].setdefault(ally,[0,0])
			if match['winner'] == 1:
				bigdict[match['me']]['allies'][ally][0] += 1
			else:
				bigdict[match['me']]['allies'][ally][1] += 1
		for enemy in match['enemies']:
			bigdict[match['me']]['enemies'].setdefault(enemy,[0,0])
			if match['winner'] == 1:
				bigdict[match['me']]['enemies'][enemy][0] += 1
			else:
				bigdict[match['me']]['enemies'][enemy][1] += 1

	return bigdict

def suggest(data, allies, enemies):
	'''
	might wanna restructure the above so that we have our played champs in allies/enemies JKJK
	loop through allies, put prob in dict [ally][our champ][prob], maybe [champ][ally][prob]
	Do the same thing for enemies
	then we add them all up

	More ideas: add some factor for confidence(# of games played)

	'''
	dic = {}
	#This thing aggregates the allies/enemies
	for champ in data:
		dic[champ] = {}
		for ally in data[champ]['allies']:
			dic[champ][ally] = normalize(sum(data[champ]['allies'][ally])) * data[champ]['allies'][ally][0] / sum(data[champ]['allies'][ally])
		for enemy in data[champ]['enemies']:
			dic[champ][enemy] = normalize(sum(data[champ]['enemies'][enemy])) * data[champ]['enemies'][enemy][0] / sum(data[champ]['enemies'][enemy])


	final_result = ['', 0]
	for champ in dic:
		fitness = 0
		normalizer = 0.0001
		for guy in allies + enemies:
			try:
				fitness += dic[champ][guy]
				normalizer += 1
			except KeyError:
				pass
			# print(champ, dic[champ][guy], guy)
		fitness = fitness / normalizer
		if fitness > final_result[1]:
			final_result = [champ, fitness]

	return final_result
	
def normalize(games_with_champ):
	return .85/(1 + math.e **(-5(.05x - .25))) + .15

def runit(filename):
	with open(filename) as json_data:
		d = json.load(json_data)
		json_data.close()
	
		learned = calculate_win_rate_per_champion_wrt_others(d)	
		print(learned)
		print(suggest(learned,['janna'],['kassadin']))
		print(suggest(learned,['kassadin'],['janna']))
		print(suggest(learned,['shyvana'],[]))

runit('ghibli studios_team.json')
