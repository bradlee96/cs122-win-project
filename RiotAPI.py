import urllib.request
import json
import time
import sqlite3

key = '9df451c2-91bc-4584-99f5-87334af39c2a'
key2 = '8015aa1d-df1d-4cda-b319-dffcbcf2f708'
key3 = 'fa134dbe-f2ab-4ec8-87f6-3a653298a272'
key_list = [key, key2, key3]
DATABASE_FILENAME = 'Fiendish_Codex.db'

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

def get_matches(summoner_name, summoner_id, key, team_data = True):
	'''
	Returns a list of matches for a given summoner. The stats for the summoner are returned, and nothing else
	This also updates, so no time is wasted
	'''

	conn = sqlite3.connect(DATABASE_FILENAME)
	cursor = conn.cursor()
	try:
		latest_match = cursor.execute("SELECT time_stamp FROM {}_stats ORDER BY time_stamp DESC LIMIT 1".format(summoner_name)).fetchall()
		if latest_match != []:
			latest_match = latest_match[0] * 1000
		else:
			latest_match = 0
	except Exception:
		latest_match = 0

	conn.close()

	matches_info = urllib.request.urlopen("https://na.api.pvp.net/api/lol/na/v2.2/matchlist/by-summoner/{}?rankedQueues=TEAM_BUILDER_DRAFT_RANKED_5x5,RANKED_SOLO_5x5&beginTime={}&api_key={}".format(summoner_id, latest_match, key))
	matches_info_not_byte = matches_info.readall().decode('utf-8')
	matches = json.loads(matches_info_not_byte)

	#Checks if there are any new matches
	try:
		if matches['status']['status_code'] == 404: #Hasn't played any new games
			return
	except KeyError:
		pass

	try:
		if matches["totalGames"] == 0: #Hasn't played any games, at all
			return
	except KeyError:
		pass

	match_list = []
	team_list = []
	key_counter = 1
	champion_id_table = get_champion_id_table(key)

	for match in matches['matches']:
		to_append = get_match_info_for_summoner(match, key_list[key_counter % len(key_list)], summoner_name, champion_id_table)
		to_append[0]['lane'] = match['lane']
		to_append[0]['role'] = match['role']
		to_append[1]['lane'] = match['lane']
		to_append[1]['role'] = match['role']
		match_list.append(to_append[0])
		team_list.append(to_append[1])
		key_counter += 1

	return match_list, team_list


def get_match_info_for_summoner(match, key, summoner_name, champion_id_table):
	'''
	Parses out the summoner-specific information. Returns a dictionary
	Have to do this super awkward thing where for some reason the Json is not organized by name or id but rather
	a pretty much randomly assigned participantId, so we have to go in, find it, then find which index holds that player id...

	Champion ID is in here
	I'm like 99% sure that the participantId 1-5 are on a team
	'''
	# print(0, time.clock())
	match_id = match['matchId']

	#Catches some weird HTTP 500 Error that comes up every like, 1000 games for some reason. Counter is probably not needed
	counter = 0
	while True:
		try:
			match_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v2.2/match/{}?api_key={}'.format(match_id, key))
		except urllib.error.HTTPError:
			counter += 1
			if counter == 10:
				break
			continue
		break
	# print(1, time.clock())
	match_info_not_byte = match_info.readall().decode('utf-8')
	# print(2, time.clock())
	match_json = json.loads(match_info_not_byte)
	# print(3, time.clock())

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

	match_info_for_summoner['championId'] = champion_id_table[match_info_for_summoner['championId']]
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
'winner', 'me', 'lane', 'role', 'allies', 'enemies']

	values = []
	team_values = []
	conn = sqlite3.connect(file_name)
	for match in match_list:
		values.append((s_id, 
			s_name, 
			match['match_id'], 
			match['season'], 
			match['timestamp']/1000, 
			match['match_duration'],
			match['championId'],
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
			'|'.join(team['allies']),
			'|'.join(team['enemies'])))

	try:
		conn.executemany('INSERT INTO {}_stats VALUES ({})'.format(s_name, ','.join('?' * len(values[0]))), (values))
		conn.executemany('INSERT INTO {}_team VALUES ({})'.format(s_name, ','.join('?' * len(team_values[0]))), (team_values))
	except Exception:
		conn.execute('''CREATE TABLE {}_stats ({})'''.format(s_name, ','.join(SQL_summoner_columns)))
		conn.executemany('INSERT INTO {}_stats VALUES ({})'.format(s_name, ','.join('?' * len(values[0]))), (values))	
		conn.execute('''CREATE TABLE {}_team ({})'''.format(s_name, ','.join(SQL_team_columns)))
		conn.executemany('INSERT INTO {}_team VALUES ({})'.format(s_name, ','.join('?' * len(team_values[0]))), (team_values))	

	conn.commit()
	conn.close()

def runit(summoner_name, save_json = False, write_SQL = True):
	print('Start:', time.clock())
	
	summoner_name = summoner_name.lower()
	summoner_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/{}?api_key={}'.format(summoner_name.replace(' ',''), key))
	summoner_info_not_byte = summoner_info.readall().decode('utf-8')
	summoner_id = json.loads(summoner_info_not_byte)[summoner_name.replace(' ','')]['id']

	print('Pulling Matches')
	data_tuple = get_matches(summoner_name, summoner_id, key)

	if data_tuple == None:
		print('Finish:', time.clock())
		return

	if save_json == True:
		print('Saving Jsons')
		export_matches('{}_summoner.json'.format(summoner_name.replace(' ','_')),data_tuple[0])
		export_matches('{}_team.json'.format(summoner_name.replace(' ','_')),data_tuple[0])

	if write_SQL == True:
		print('Creating SQL databases')
		add_to_SQL(summoner_id, summoner_name.replace(' ','_'), data_tuple[0], data_tuple[1], DATABASE_FILENAME)

	print('Finish:', time.clock())

runit('Lee Rush Sin')