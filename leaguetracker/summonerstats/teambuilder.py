import urllib.request
import sqlite3
import math
import json
import os

key = '9df451c2-91bc-4584-99f5-87334af39c2a'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_FILENAME = os.path.join(BASE_DIR, 'Fiendish_Codex.db')


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
	'''
	This function returns a simple dictionary with all the information that we need to recommend.
	Lane/Role selection is also performed here
	'''
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


def get_pair_counts(matchlist, drafted):
	'''
	Returns a dictionary that has, for each champion the player has used, another dictionary with champions that they
	have played with and the number of wins and total games.
	e.g. {'A': {'enemies': {'B': [0, 1], 'C': [0, 1], 'D': [0, 1]}, 'allies':{...}, 'Q':{...}}
	'''
	pair_dict = {}
	for match in matchlist:
		pair_dict.setdefault(match['me'],{'allies':{},'enemies':{}})
		for ally in match['allies']:
			pair_dict[match['me']]['allies'].setdefault(ally,[0,0])
			if match['winner'] == 1:
				pair_dict[match['me']]['allies'][ally][0] += 1
			else:
				pair_dict[match['me']]['allies'][ally][1] += 1
		for enemy in match['enemies']:
			pair_dict[match['me']]['enemies'].setdefault(enemy,[0,0])
			if match['winner'] == 1:
				pair_dict[match['me']]['enemies'][enemy][0] += 1
			else:
				pair_dict[match['me']]['enemies'][enemy][1] += 1

	#This sections ensures that the recommender does not suggest a champion that has already been drafted.
	for champ in drafted:
		try:
			del pair_dict[champ]
		except KeyError:
			pass

	return pair_dict

def normalize_for_champ_experience(matchlist):
	'''
	Takes care of "Play a lot of A, but only 1 game with A and B"
	Gives higher weight to champions that the player has many games on
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
	If someone has never played with a champion in the draft, we continue as if the champion weren't there

	'''
	dic = {}
	for champ in data:
		dic[champ] = {}
		for ally in data[champ]['allies']:
			#Remember to properly name the functions
			dic[champ][ally] = normalize_pairs(sum(data[champ]['allies'][ally])) * data[champ]['allies'][ally][0] / sum(data[champ]['allies'][ally])
		for enemy in data[champ]['enemies']:
			dic[champ][enemy] = normalize_pairs(sum(data[champ]['enemies'][enemy])) * data[champ]['enemies'][enemy][0] / sum(data[champ]['enemies'][enemy])

	#First pick case, want to return highest winrate & most experienced
	if allies + enemies == []:
		return fitness_gen(dic, champ_experience_normalizer, None)

	#This section checks for if the person has played any games with the other champions in the draft
	#If they haven't, it defaults to the above case
	for champ in dic:
		has_least = False
		for guy in allies + enemies:
			try:
				if dic[champ][guy]:
					has_least = True
					break
			except KeyError:
				pass

	#If they have, we go through the allies and enemies to select a fitting champion.
	#Note that if they have played with 8/9 drafted champions, the algorithm will just ignore the unplayed
	if has_least == False:
		return fitness_gen(dic, champ_experience_normalizer, None)
	else:
		return fitness_gen(dic, champ_experience_normalizer, allies + enemies)

def fitness_gen(data, champ_experience_normalizer, iterator):
	'''
	This function calculated the fitness for each champion.
	normalizer keeps the fitness between 0 and 1, so that having many unique pairs doesn't skew the data

	'''
	final_result = ['', -1]
	if iterator == None:
		for champ in data:
			normalizing_for_champ_experience = champ_experience_normalizer[champ]
			fitness = 0
			normalizer = None
			for guy in data[champ]: #We iterate over the person's played champions
				fitness += normalizing_for_champ_experience * data[champ][guy]
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

	else:
		for champ in data:
			normalizing_for_champ_experience = champ_experience_normalizer[champ]
			fitness = 0
			normalizer = None
			for guy in iterator: #We iterate over the allies and enemies in the draft
				fitness += normalizing_for_champ_experience * data[champ][guy]
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


def normalize_pairs(pair_count):
	'''
	Takes care of "1 win with A and B"
	Gives weight to statistically significant pairs.
	'''
	return .85 / (1 + math.e ** ( -5 * (.05 * pair_count - .25))) + .15

def get_recommendation(summoner_id, allies, enemies, role):
	match_list = get_dict(DATABASE_FILENAME, summoner_id, role)

	#Person has no champions capable of playing a certain role
	if match_list == []:
		return "insufficientdata"

	for i in range(len(allies)):
		allies[i] = allies[i].lower().replace(' ','')

	for i in range(len(enemies)):
		enemies[i] = enemies[i].lower().replace(' ','')

	learned = get_pair_counts(match_list, allies + enemies)

	#Person has no champions for a certain role that are not within the draft
	if learned == {}:
		return "insufficientdata"

	champ_experience_normalizer = normalize_for_champ_experience(match_list)
	champion_list = get_champion_id_table(key)

	#Naming consistency
	for champ in allies + enemies:
		if champ[0:6] == "jarvan":
			if champ in allies:
				allies.remove(champ)
				allies.append("jarvaniv")
			else:
				enemies.remove(champ)
				enemies.append("jarvaniv")
			break

	#In case of misspelled name
	for champ in allies + enemies:
		if not champ in champion_list:
			return 'champerror'

	return suggest(learned, champ_experience_normalizer, allies, enemies)
