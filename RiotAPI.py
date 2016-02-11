import urllib.request
import json
import time
import sqlite3

key = '9df451c2-91bc-4584-99f5-87334af39c2a'
key2 = '8015aa1d-df1d-4cda-b319-dffcbcf2f708'
key3 = 'fa134dbe-f2ab-4ec8-87f6-3a653298a272'
'''
dmg dealt as percent of team
'''
SQL_columns = ['summoner_id', 'summoner_name', 'match_id', 
'season', 'time_stamp', 'match_duration', 'champion', 'lane', 
'role', 'winner', 'cs', 'kills', 'deaths','assists','gold',
'wards_placed', 'wards_killed']

summoner_name = 'ghibli studios'

summoner_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/{}?api_key={}'.format(summoner_name.replace(' ',''),key))
summoner_info_not_byte = summoner_info.readall().decode('utf-8')
summoner_id = json.loads(summoner_info_not_byte)[summoner_name.replace(' ','')]['id']

def get_champion_id_table(key):
	'''
	Returns a dictionary with champions_id as keys and the champion name as values
	'''
	champ_api = urllib.request.urlopen('https://na.api.pvp.net/api/lol/static-data/na/v1.2/champion?api_key={}'.format(key))
	champ_api_not_byte = champ_api.readall().decode('utf-8')
	champ_info = json.loads(champ_api_not_byte)['data']
	cleaned_table = {}
	for champion in champ_info.keys():
		cleaned_table[champ_info[champion]['id']] = champion
	
	return cleaned_table

champion_id_table = get_champion_id_table(key)

def get_matches(summoner_id, key):
	'''
	Returns a list of matches for a given summoner. The stats for the summoner are returned, and nothing else
	'''
	match_list = []
	matches_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v2.2/matchlist/by-summoner/{}?rankedQueues=RANKED_SOLO_5x5&api_key={}'.format(summoner_id,key))
	matches_info_not_byte = matches_info.readall().decode('utf-8')
	matches = json.loads(matches_info_not_byte)

	# print('hi',matches['matches'][0].keys())
	for match in matches['matches'][0:5]:
		time.sleep(1.2)
		to_append = get_match_info_for_summoner(match, key, summoner_name)
		to_append['lane'] = match['lane']
		to_append['role'] = match['role']
		match_list.append(to_append)

	return match_list


def get_match_info_for_summoner(match, key, summoner_name):
	'''
	Parses out the summoner-specific information. Returns a dictionary
	'''
	match_id = match['matchId']

	match_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v2.2/match/{}?api_key={}'.format(match_id, key))
	time.sleep(1.1)
	match_info_not_byte = match_info.readall().decode('utf-8')
	match_json = json.loads(match_info_not_byte)
	#print(match['participants'][0])
	player_participant = {}
	for player in range(10):
		#print(match['participantIdentities'][player]['player']['summonerName'], match['participantIdentities'][player]['participantId'])
		player_participant[match_json['participantIdentities'][player]['player']['summonerName'].lower()] = match_json['participantIdentities'][player]['participantId']


	match_info_for_summoner = [match_json['participants'][i] for i in range(10) if match_json['participants'][i]['participantId'] == player_participant[summoner_name]][0]
	match_info_for_summoner['match_id'] = match['matchId']
	match_info_for_summoner['match_duration'] = match_json['matchDuration']
	match_info_for_summoner['season'] = match['season']
	match_info_for_summoner['timestamp'] = match['timestamp']
	# print(match_info_for_summoner.keys())
	return match_info_for_summoner

def export_matches(file_name,matchlist):
	with open(file_name, 'w') as outfile:
	    json.dump(matchlist, outfile)

def add_to_SQL(s_id, s_name, match_list, file_name):
	values = []
	for match in match_list:
		values.append((s_id, 
			s_name, 
			match['match_id'], 
			match['season'], 
			match['timestamp']/1000, 
			match['match_duration'],
			champion_id_table[match['championId']].lower(),
			match['lane'],
			match['role'], 
			match['stats']['winner'], 
			match['stats']['minionsKilled'],
			match['stats']['kills'],
			match['stats']['deaths'],
			match['stats']['assists'],
			match['stats']['goldEarned'],
			match['stats']['wardsPlaced'],
			match['stats']['wardsKilled']))

	conn = sqlite3.connect(file_name)
	try:
		conn.executemany('INSERT INTO defaultinfo VALUES ({})'.format(','.join('?' * len(values[0]))), (values))
	except Exception:
		conn.execute('''CREATE TABLE defaultinfo ({})'''.format(','.join(SQL_columns)))
		conn.executemany('INSERT INTO defaultinfo VALUES ({})'.format(','.join('?' * len(values[0]))), (values))	

	conn.commit()
	conn.close()

pie = get_matches(summoner_id, key)
export_matches('50hanazonotest.txt',pie)
add_to_SQL(summoner_id, summoner_name, pie, 'Johnathan_Games.db')
