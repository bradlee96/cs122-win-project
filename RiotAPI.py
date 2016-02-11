import urllib.request
import json
import time
import sqlite3

key = '9df451c2-91bc-4584-99f5-87334af39c2a'
key2 = '8015aa1d-df1d-4cda-b319-dffcbcf2f708'
key3 = 'fa134dbe-f2ab-4ec8-87f6-3a653298a272'
key_list = [key, key2, key3]


SQL_columns = ['summoner_id', 'summoner_name', 'match_id', 
'season', 'time_stamp', 'match_duration', 'champion', 'lane', 
'role', 'winner', 'cs', 'kills', 'deaths','assists','gold',
'wards_placed', 'wards_killed']


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

def get_matches(summoner_name, summoner_id, key):
	'''
	Returns a list of matches for a given summoner. The stats for the summoner are returned, and nothing else
	'''
	match_list = []
	matches_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v2.2/matchlist/by-summoner/{}?rankedQueues=RANKED_SOLO_5x5&api_key={}'.format(summoner_id,key))
	matches_info_not_byte = matches_info.readall().decode('utf-8')
	matches = json.loads(matches_info_not_byte)

	key_counter = 1
	start_time = time.clock()
	for match in matches['matches']:
		print(time.clock())
		to_append = get_match_info_for_summoner(match, key_list[key_counter % len(key_list)], summoner_name)
		# print(key_list[key_counter % len(key_list)], time.clock() - start_time)
		to_append['lane'] = match['lane']
		to_append['role'] = match['role']
		match_list.append(to_append)
		key_counter += 1

	return match_list


def get_match_info_for_summoner(match, key, summoner_name):
	'''
	Parses out the summoner-specific information. Returns a dictionary
	Have to do this super awkward thing where for some reason the Json is not organized by name or id but rather
	a pretty much randomly assigned participantId, so we have to go in, find it, then find which index holds that player id...
	'''
	match_id = match['matchId']

	match_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v2.2/match/{}?api_key={}'.format(match_id, key))
	match_info_not_byte = match_info.readall().decode('utf-8')
	match_json = json.loads(match_info_not_byte)
	player_participant = {}
	for player in range(10):
		if match_json['participantIdentities'][player]['player']['summonerName'].lower() == summoner_name:
			match_info_for_summoner = match_json['participants'][player]
			break

	match_info_for_summoner['match_id'] = match['matchId']
	match_info_for_summoner['match_duration'] = match_json['matchDuration']
	match_info_for_summoner['season'] = match['season']
	match_info_for_summoner['timestamp'] = match['timestamp']
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


def runit(summoner_name, save_json = True, write_SQL = True):
	print('Start:', time.clock())
	champion_id_table = get_champion_id_table(key)

	summoner_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/{}?api_key={}'.format(summoner_name.replace(' ',''), key))
	summoner_info_not_byte = summoner_info.readall().decode('utf-8')
	summoner_id = json.loads(summoner_info_not_byte)[summoner_name.replace(' ','')]['id']

	print('Pulling Matches')
	pie = get_matches(summoner_name, summoner_id, key)

	if save_json == True:
		print('Saving Json')
		export_matches('{}_json.txt'.format(summoner_name+'hi'),pie)

	if write_SQL == True:
		print('Creating SQL database')
		add_to_SQL(summoner_id, summoner_name, pie, '{}_sql.db'.format(summoner_name+'hi'))

	print('Finish:', time.clock())

