'''
Need to add some sort of experience factor, maybe a linear/logistic function
up to, say, like 50 games.
M 5:30-7:30pm Horace RY 162
Tu 10-12pm Qinqin RY 255


Notes from Pan OH :

Basically what we did. Maybe split functions for champion experience and affinity and then add an alpha, (1-alpha) sort of thing
This is sort of what we did, we calculated purely on affinity and then applied a weight to it as a function of experience.

'''
import time
import urllib.request
import sqlite3
import math
import json

key = '9df451c2-91bc-4584-99f5-87334af39c2a'
DATABASE_FILENAME = 'Fiendish_Codex.db'


def get_champion_id_table(key):
	'''
	Returns a list of acceptable champion names
	'''
	champ_api = urllib.request.urlopen('https://na.api.pvp.net/api/lol/static-data/na/v1.2/champion?api_key={}'.format(key))
	champ_api_not_byte = champ_api.read().decode('utf-8')
	champ_info = json.loads(champ_api_not_byte)['data']
	champion_list = []
	for champion in champ_info.keys():
		if champion.lower() == 'monkeyking':
			champion_list.append('wukong')
		else:
			champion_list.append(champion.lower())
	return champion_list

def get_dict(filename, summoner_id, role):
	conn = sqlite3.connect(filename)
	cursor = conn.cursor()
	if role == "DUO_CARRY" or role == "DUO_SUPPORT":
		match_list = cursor.execute("SELECT champion, allies, enemies, winner from Junction WHERE summoner_id = {} AND lane = '{}' AND role = '{}'".format(summoner_id, "BOTTOM", role)).fetchall()
	else:
		match_list = cursor.execute("SELECT champion, allies, enemies, winner from Junction WHERE summoner_id = {} AND lane = '{}'".format(summoner_id, role)).fetchall()
	cleaned_match_list = []
	for match in match_list:
		temp = {}
		temp['me'] = match[0]
		temp['allies'] = match[1].split('|')
		temp['enemies'] = match[2].split('|')
		temp['winner'] = match[3]
		cleaned_match_list.append(temp)

	return cleaned_match_list


def calculate_win_rate_per_champion_wrt_others(matchlist):
	'''
	Note, doesn't actually calculate the winrate, only returns the count, but y'know close enough
	Basically just want to add a bunch of shit so I can get some probs later
	[champ][allies/enemies][ally/enemy][[0,0]]
	Think about specific comopositions, the global weighting does not take that into account.
	Eg. Play a lot of Annie, but only 1 game with Annie and shen
	1 game of Annie and Shen, lost, but 1000 games of Annie
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

def normalize_for_champ_experience(matchlist):
	'''
	Takes care of "Play a lot of A, but only 1 game with A and B"
	'''
	champ_experience_normalizer = {}
	for match in matchlist:
		champ_experience_normalizer[match['me']] = champ_experience_normalizer.get(match['me'], 0) + 1
	for champ in champ_experience_normalizer.keys():
		games_played = champ_experience_normalizer[champ]
		champ_experience_normalizer[champ] = (-1) / (((4 * games_played) / (3 * math.e)) + 1.1) + 1

	return champ_experience_normalizer

def suggest(data, champ_experience_normalizer, allies, enemies):
	'''
	might wanna restructure the above so that we have our played champs in allies/enemies JKJK
	loop through allies, put prob in dict [ally][our champ][prob], maybe [champ][ally][prob]
	Do the same thing for enemies
	then we add them all up
	Also take into account how recent the champ was played
	More ideas: add some factor for confidence(# of games played)

	rename all these normalizing things
	'''
	dic = {}
	#This thing aggregates the allies/enemies
	for champ in data:
		dic[champ] = {}
		for ally in data[champ]['allies']:
			#Remember to properly name the functions
			dic[champ][ally] = normalize_pairs(sum(data[champ]['allies'][ally])) * data[champ]['allies'][ally][0] / sum(data[champ]['allies'][ally])
		for enemy in data[champ]['enemies']:
			dic[champ][enemy] = normalize_pairs(sum(data[champ]['enemies'][enemy])) * data[champ]['enemies'][enemy][0] / sum(data[champ]['enemies'][enemy])

	final_result = ['', 0]
	if allies + enemies == []:
		'''
		First pick case, want to return highest winrate & most experienced
		Aggregate all the allies and enemies into just champion, and applies the normalizing function
		'''
		for champ in dic:
			normalizing_for_champ_experience = champ_experience_normalizer[champ]
			fitness = 0
			normalizer = None
			for guy in dic[champ]:
				fitness += normalizing_for_champ_experience * dic[champ][guy]
				if normalizer == None:
					normalizer = 1
				else:
					normalizer += 1

			if normalizer == None:
				normalizer = 1
			fitness = fitness / normalizer
			if fitness > final_result[1]:
				final_result = [champ, fitness]
		return final_result[0]

	for champ in dic:
		normalizing_for_champ_experience = champ_experience_normalizer[champ]
		fitness = 0
		normalizer = None

		for guy in allies + enemies:
			try:
				fitness += normalizing_for_champ_experience * dic[champ][guy]
				if normalizer == None:
					normalizer = 1
				else:
					normalizer += 1
			except KeyError:
				pass

		if normalizer == None:
			normalizer = 1
		fitness = fitness / normalizer
		if fitness > final_result[1]:
			final_result = [champ, fitness]

	return final_result[0]


def normalize_pairs(pair_count):
	'''
	Takes care of "1 win with A and B" bias

	A logistic growth function to weight games played with an ally champ or against an
	enemy champion. We weight values more if there are more games because the sample
	size is bigger and therefore more accurate.
	'''
	return .85 / (1 + math.e ** ( -5 * (.05 * pair_count - .25))) + .15

def get_recommendation(summoner_id, allies, enemies, role):
	'''
	Need to add default case
	Need to add SQL stuff
	'''

	match_list = get_dict(DATABASE_FILENAME, summoner_id, role)
	learned = calculate_win_rate_per_champion_wrt_others(match_list)
	champ_experience_normalizer = normalize_for_champ_experience(match_list)
	champion_list = get_champion_id_table(key)

	for i in range(len(allies)):
		allies[i] = allies[i].lower().replace(' ', '')

	for i in range(len(enemies)):
		enemies[i] = enemies[i].lower().replace(' ', '')

	for champ in allies + enemies:
		if champ[0:6] == "jarvan":
			if champ in allies:
				allies.remove(champ)
				allies.append("jarvaniv")
			else:
				enemies.remove(champ)
				enemies.append("jarvaniv")
			break

	for champ in allies + enemies:
		if not champ in champion_list:
			print('ehrer')
			return ''

	return suggest(learned, champ_experience_normalizer, allies, enemies)

# p = runit('ghibli studios', [],[], 'JUNGLE')
# print(p)
'''
Freq of hero usage, correlation of pairs allies and enemies
optimize on experience, high score with heroes with and against
dont forget to give John parents' numbers
for the website, would be super nice to have on the draft input like, pictures of the champions that were picked.
Found champion squares on wikia

'''
'''
nidalee issue
'''
