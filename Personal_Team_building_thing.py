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

def get_dict(filename, summoner_id):
	conn = sqlite3.connect('Fiendish_Codex.db')
	cursor = conn.cursor()
	match_list = cursor.execute("SELECT champion, allies, enemies, winner from Junction JOIN Summoners WHERE Summoners.summoner_id = {}".format(summoner_id)).fetchall()

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

def get_num_games_per_champ(matchlist):
	champ_dict = {}
	for match in matchlist:
		champ_dict[match['me']] = champ_dict.get(match['me'], 0) + 1
	
	return champ_dict
	
'''
def get_most_played(data):
	.85/(1+e**-5(.05x-.25)) + .15

	-1/(x/(.75e)+1.1) + 1
	champ_count_dict = {}
	for match in data:
		if not match['me'] in champ_count_dict.keys():
			champ_count_dict[match['me']] = 1
		else:
			champ_count_dict[match['me']] += 1
	most_played = max(champ_count_dict)
	most_played_count = champ_count_dict[most_played]
	if most_played_count > 50:
		most_played_count = 50
	weighter = lambda x: 1 - e**(x / (most_played_count / 2))
	return weighter
'''

def suggest(data, champ_dict, allies, enemies):
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
			#This normalize should probably be around the whole expression. Remember to properly name the functions
			dic[champ][ally] = normalize(sum(data[champ]['allies'][ally])) * data[champ]['allies'][ally][0] / sum(data[champ]['allies'][ally])
		for enemy in data[champ]['enemies']:
			dic[champ][enemy] = normalize(sum(data[champ]['enemies'][enemy])) * data[champ]['enemies'][enemy][0] / sum(data[champ]['enemies'][enemy])


	final_result = ['', 0]
	for champ in dic:
		normalizing_for_champ_experience = (-1) / (((4 * champ_dict[champ]) / (3 * math.e)) + 1.1) + 1
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
		print(champ, fitness)
		if fitness > final_result[1]:
			final_result = [champ, fitness]

	return final_result[0]


def normalize(games_with_champ):
	return .85 / (1 + math.e ** ( -5 * (.05 * games_with_champ - .25))) + .15


def runit(summoner_name, allies, enemies, role):
	'''
	NEed to add default case
	Need to add SQL stuff
	'''
	summoner_name = summoner_name.lower()
	try:
		summoner_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/{}?api_key={}'.format((summoner_name.replace(' ','')), key))
		summoner_info_not_byte = summoner_info.readall().decode('utf-8')
		summoner_id = json.loads(summoner_info_not_byte)[summoner_name.replace(' ','')]['id']
	except urllib.error.HTTPError: #Probably no summoner name exists
		print('Summoner name not found.')
		return
	
	match_list = get_dict(DATABASE_FILENAME, summoner_id, role)
	learned = calculate_win_rate_per_champion_wrt_others(match_list)
	champ_freq = get_num_games_per_champ(match_list)

	# print(learned)
	# print(suggest(learned,champ_freq,[],[]))
	# print(time.clock())
	# print(suggest(learned,champ_freq,['kassadin'],['janna']))
	# print(time.clock())
	# print(suggest(learned,champ_freq,['shyvana'],[]))

runit('ghibli studios')

'''
Freq of hero usage, correlation of pairs allies and enemies
optimize on experience, high score with heroes with and against
dont forget to give John parents' numbers
for the website, would be super nice to have on the draft input like, pictures of the champions that were picked.
Found champion squares on wikia

'''
