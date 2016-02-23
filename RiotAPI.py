import urllib.request
import json
import time
import sqlite3

key = '9df451c2-91bc-4584-99f5-87334af39c2a'
key2 = '8015aa1d-df1d-4cda-b319-dffcbcf2f708'
key3 = 'fa134dbe-f2ab-4ec8-87f6-3a653298a272'
key_list = [key, key2, key3]

def get_champion_id_table(key):
	'''
	Returns a dictionary with champions_id as keys and the champion name as values
	'''
	champ_api = urllib.request.urlopen('https://na.api.pvp.net/api/lol/static-data/na/v1.2/champion?api_key={}'.format(key))
	champ_api_not_byte = champ_api.readall().decode('utf-8')
	champ_info = json.loads(champ_api_not_byte)['data']
	cleaned_table = {}
	for champion in champ_info.keys():
		cleaned_table[champ_info[champion]['id']] = champion.lower()
	
	return cleaned_table

champion_id_table = get_champion_id_table(key)

def get_matches(summoner_name, summoner_id, key, team_data = True):
	'''
	Returns a list of matches for a given summoner. The stats for the summoner are returned, and nothing else
	'''
	match_list = []
	team_list = []
	matches_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v2.2/matchlist/by-summoner/{}?rankedQueues=TEAM_BUILDER_DRAFT_RANKED_5x5,RANKED_SOLO_5x5&api_key={}'.format(summoner_id,key))
	# matches_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v2.2/matchlist/by-summoner/{}?rankedQueues=RANKED_SOLO_5x5&api_key={}'.format(summoner_id,key))
	matches_info_not_byte = matches_info.readall().decode('utf-8')
	matches = json.loads(matches_info_not_byte)

	key_counter = 1
	for match in matches['matches']:
		print(key_counter)
		to_append = get_match_info_for_summoner(match, key_list[key_counter % len(key_list)], summoner_name)
		to_append[0]['lane'] = match['lane']
		to_append[0]['role'] = match['role']
		to_append[1]['lane'] = match['lane']
		to_append[1]['role'] = match['role']
		match_list.append(to_append[0])
		team_list.append(to_append[1])
		key_counter += 1

	return match_list, team_list


def get_match_info_for_summoner(match, key, summoner_name):
	'''
	Parses out the summoner-specific information. Returns a dictionary
	Have to do this super awkward thing where for some reason the Json is not organized by name or id but rather
	a pretty much randomly assigned participantId, so we have to go in, find it, then find which index holds that player id...

	Champion ID is in here
	I'm like 99% sure that the participantId 1-5 are on a team
	'''
	match_id = match['matchId']
	counter = 0
	while True:
		try:
			match_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v2.2/match/{}?api_key={}'.format(match_id, key))
		except urllib.error.HTTPError:
			counter+=1
			if counter == 10:
				break
			continue
		break
	match_info_not_byte = match_info.readall().decode('utf-8')
	match_json = json.loads(match_info_not_byte)

	data = {'match_id': 0,'me': 0, 'allies': [], 'enemies': []}
	for player in range(10):
		if match_json['participantIdentities'][player]['player']['summonerName'].lower() == summoner_name:
			data['me'] = champion_id_table[match_json['participants'][player]['championId']]
			player_participant_id = match_json['participantIdentities'][player]['participantId']
			match_info_for_summoner = match_json['participants'][player]
		elif player <= 4:
			data['allies'].append(champion_id_table[match_json['participants'][player]['championId']])
		else:
			data['enemies'].append(champion_id_table[match_json['participants'][player]['championId']])

	if player_participant_id > 5:
		data['allies'], data['enemies'] = data['enemies'], data['allies']

	match_info_for_summoner['match_id'] = match['matchId']
	match_info_for_summoner['match_duration'] = match_json['matchDuration']
	match_info_for_summoner['season'] = match['season']
	match_info_for_summoner['timestamp'] = match['timestamp']
	data['match_id'] = match['matchId']
	data['winner'] = match_info_for_summoner['stats']['winner']

	return match_info_for_summoner, data

def export_matches(file_name, matchlist):
	with open(file_name, 'w') as outfile:
	    json.dump(matchlist, outfile)

def add_to_SQL(s_id, s_name, match_list, team_list, file_name):
	'''
	Creates a table for the data necessary to make graphs, and another table for the team info for the team builder
	'''
	SQL_summoner_columns = ['summoner_id', 'summoner_name', 'match_id', 
'season', 'time_stamp', 'match_duration', 'champion', 'lane', 
'role', 'winner', 'cs', 'kills', 'deaths','assists','gold',
'wards_placed', 'wards_killed']

	SQL_team_columns = ['summoner_id', 'summoner_name', 'match_id', 
'winner', 'me', 'lane', 'role', 'ally1', 'ally2', 'ally3', 'ally4',
'enemy1', 'enemy2', 'enemy3',' enemy4', 'enemy5']
	#Remember that we can use some sort of encryption algortihm to condense for taem
	#in case we dont actually care about ally1, the positioning is arbitrary anyways
	#if we wanna sort by lane we can just parse the JSON, itll be easy
	values = []
	team_values = []

	for match in match_list:
		values.append((s_id, 
			s_name, 
			match['match_id'], 
			match['season'], 
			match['timestamp']/1000, 
			match['match_duration'],
			champion_id_table[match['championId']],
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

	for team in team_list:
		team_values.append((s_id, 
			s_name,
			team['match_id'],
			team['winner'],
			team['me'],
			team['lane'],
			team['role'],
			team['allies'][0],
			team['allies'][1],
			team['allies'][2],
			team['allies'][3],
			team['enemies'][0],
			team['enemies'][1],
			team['enemies'][2],
			team['enemies'][3],
			team['enemies'][4]))

	conn = sqlite3.connect(file_name)
	try:
		conn.executemany('INSERT INTO defaultinfo VALUES ({})'.format(','.join('?' * len(values[0]))), (values))
		conn.executemany('INSERT INTO team VALUES ({})'.format(','.join('?' * len(team_values[0]))), (team_values))
	except Exception:
		conn.execute('''CREATE TABLE defaultinfo ({})'''.format(','.join(SQL_summoner_columns)))
		conn.executemany('INSERT INTO defaultinfo VALUES ({})'.format(','.join('?' * len(values[0]))), (values))	
		conn.execute('''CREATE TABLE team ({})'''.format(','.join(SQL_team_columns)))
		conn.executemany('INSERT INTO team VALUES ({})'.format(','.join('?' * len(team_values[0]))), (team_values))	

	conn.commit()
	conn.close()

def runit(summoner_name,save_json = True, write_SQL = True):
	print('Start:', time.clock())
	champion_id_table = get_champion_id_table(key)

	summoner_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/{}?api_key={}'.format(summoner_name.replace(' ',''), key))
	summoner_info_not_byte = summoner_info.readall().decode('utf-8')
	summoner_id = json.loads(summoner_info_not_byte)[summoner_name.replace(' ','')]['id']

	print('Pulling Matches')
	data_tuple = get_matches(summoner_name, summoner_id, key)

	if save_json == True:
		print('Saving Jsons')
		export_matches('{}_summoner.json'.format(summoner_name),data_tuple[0])
		export_matches('{}_team.json'.format(summoner_name),data_tuple[1])

	if write_SQL == True:
		print('Creating SQL databases')
		add_to_SQL(summoner_id, summoner_name, data_tuple[0], data_tuple[1],'{}_sql.db'.format(summoner_name))

	print('Finish:', time.clock())

'''
updater, use epoch for api
'''