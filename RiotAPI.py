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
		# print(champion)
		cleaned_table[champ_info[champion]['id']] = champion.lower()
		if champion.lower() == 'monkeyking':
			cleaned_table[champ_info[champion]['id']] = 'wukong'
	
	return cleaned_table

def get_matches(summoner_name, summoner_id, key, team_data = True):
	'''
	Returns a list of matches for a given summoner. The stats for the summoner are returned, and nothing else
	This also updates, so no time is wasted
	'''
	conn = sqlite3.connect(DATABASE_FILENAME)
	cursor = conn.cursor()
	try:
		latest_match = cursor.execute("SELECT time_stamp from Matches JOIN Junction ON Junction.match_id = Matches.match_id WHERE Junction.summoner_id = {} ORDER BY time_stamp DESC LIMIT 1".format(summoner_id)).fetchall()
		if latest_match != []:
			latest_match = int(latest_match[0][0] * 1000 + 1)
		else:
			latest_match = 0
	except Exception:
		latest_match = 0

	print(latest_match)
	conn.close()

	try:
		matches_info = urllib.request.urlopen("https://na.api.pvp.net/api/lol/na/v2.2/matchlist/by-summoner/{}?rankedQueues=TEAM_BUILDER_DRAFT_RANKED_5x5,RANKED_SOLO_5x5&beginTime={}&api_key={}".format(summoner_id, latest_match, key))
		matches_info_not_byte = matches_info.readall().decode('utf-8')
		matches = json.loads(matches_info_not_byte)
	except urllib.error.HTTPError:
		return 'No new matches to update.'

	try:
		if matches["totalGames"] == 0 and latest_match == 0: #Hasn't played any games, at all
			return 'Summoner has no ranked games'
		elif matches["totalGames"] == 0 and latest_match != 0:
			return 'No new matches to update.'
	except KeyError:
		pass

	match_list = []
	key_counter = 1
	champion_id_table = get_champion_id_table(key)

	for match in matches['matches']:
		if match['region'] != 'NA':
			continue
		else:
			to_append = get_match_info_for_summoner(match, key_list[key_counter % len(key_list)], summoner_id, champion_id_table)
			to_append['lane'] = match['lane']
			to_append['role'] = match['role']
			match_list.append(to_append)
			key_counter += 1

	return match_list


def get_match_info_for_summoner(match, key, summoner_id, champion_id_table):
	'''
	Parses out the summoner-specific information. Returns a dictionary
	Have to do this super awkward thing where for some reason the Json is not organized by name or id but rather
	a pretty much randomly assigned participantId, so we have to go in, find it, then find which index holds that player id...

	Champion ID is in here
	I'm like 99% sure that the participantId 1-5 are on a team
	'''
	match_id = match['matchId']

	#Catches some weird HTTP 500 Error that comes up every like, 1000 games for some reason. Counter is probably not needed
	counter = 0
	while True:
		try:
			#Unfortunately, this is the thing that takes the most time. Don't think I can optimize it
			match_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v2.2/match/{}?api_key={}'.format(match_id, key))
		except urllib.error.HTTPError:
			counter += 1
			if counter == 10:
				break
			continue
		break

	match_info_not_byte = match_info.readall().decode('utf-8')
	match_json = json.loads(match_info_not_byte)

	data = {'allies': [], 'enemies': []}
	for player in range(10):
		if match_json['participantIdentities'][player]['player']['summonerId'] == summoner_id:
			player_participant_id = match_json['participantIdentities'][player]['participantId']
			match_info_for_summoner = match_json['participants'][player]
		elif player <= 4:
			data['allies'].append(champion_id_table[match_json['participants'][player]['championId']])
		else:
			data['enemies'].append(champion_id_table[match_json['participants'][player]['championId']])
	try:
		if player_participant_id > 5:
			data['allies'], data['enemies'] = data['enemies'], data['allies']
	except UnboundLocalError: # Take this out later 
		print(match['matchId'])
		print(match_json['participantIdentities'][player]['participantId'])

	match_info_for_summoner['championId'] = champion_id_table[match_info_for_summoner['championId']]
	match_info_for_summoner['match_id'] = match['matchId']
	match_info_for_summoner['match_duration'] = match_json['matchDuration']
	match_info_for_summoner['season'] = match['season']
	match_info_for_summoner['timestamp'] = match['timestamp']
	match_info_for_summoner['allies'] = data['allies']
	match_info_for_summoner['enemies'] = data['enemies']

	return match_info_for_summoner

def export_matches(file_name, matchlist):
	with open(file_name, 'w') as outfile:
	    json.dump(matchlist, outfile)

def add_to_SQL(s_id, s_name, match_list):

	'''
	Creates a table for the data necessary to make graphs, and another table for the team info for the team builder
	'''
	SQL_summoner_table = ['summoner_id', 'summoner_name', 'winrate', 'cs', 'kills', 'deaths', 'assists', 'kda', 'gold', 'cs_per_min', 'gold_per_min', 'wards_placed', 'wards_killed', 'matches_played']
	SQL_match_table = ['match_id', 'season', 'time_stamp', 'match_duration']
	SQL_junction_table = ['primary_key', 'summoner_id', 'match_id', 'champion', 'lane', 'role', 'winner', 'cs', 'kills', 'deaths','assists','gold', 'wards_placed', 'wards_killed', 'allies', 'enemies']

	summoner_values = []
	match_values = []
	junction_values = []

	try:
		primary_key = cursor.execute("SELECT primary_key from Junction ORDER BY primary_key DESC LIMIT 1").fetchall()[0][0]
	except Exception:
		primary_key = 0

	for match in match_list:
		match_values.append((
			match['match_id'], 
			match['season'], 
			match['timestamp']/1000, 
			match['match_duration']))

		junction_values.append((
			primary_key,
			s_id,
			match['match_id'],
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
			match['stats']['wardsKilled'],
			'|'.join(match['allies']),
			'|'.join(match['enemies'])))

		primary_key += 1

	conn = sqlite3.connect(DATABASE_FILENAME)
	cursor = conn.cursor()

	try:
		conn.executemany('INSERT INTO Matches VALUES ({})'.format(','.join('?' * len(match_values[0]))), (match_values))
		conn.executemany('INSERT INTO Junction VALUES ({})'.format(','.join('?' * len(junction_values[0]))), (junction_values))
	except Exception: #Basically if the db does not even exist yet
		conn.execute('''CREATE TABLE Matches ({})'''.format(','.join(SQL_match_table)))
		conn.executemany('INSERT INTO Matches VALUES ({})'.format(','.join('?' * len(match_values[0]))), (match_values))
		conn.execute('''CREATE TABLE Junction ({})'''.format(','.join(SQL_junction_table)))
		conn.executemany('INSERT INTO Junction VALUES ({})'.format(','.join('?' * len(junction_values[0]))), (junction_values))

	conn.commit()

	summoner_values += [s_id, s_name]
	summoner_values += update_global_values(s_id, cursor)
	summoner_values = [tuple(summoner_values)]
	
	try: #If this succeeds we don't do anything
		summoner_unique = cursor.execute("SELECT summoner_name from Summoners WHERE summoner_id = {}".format(s_id)).fetchall()[0][0]
	except sqlite3.OperationalError: #If db doesn't yet exist
		conn.execute('''CREATE TABLE Summoners ({})'''.format(','.join(SQL_summoner_table)))
		conn.executemany('INSERT INTO Summoners VALUES ({})'.format(','.join('?' * len(summoner_values[0]))), (summoner_values))
	except IndexError: #If no summoner is found
		conn.executemany('INSERT INTO Summoners VALUES ({})'.format(','.join('?' * len(summoner_values[0]))), (summoner_values))
	else: #if try doesn't fail and we want to update, this part also incidentally updates the name in case of name change
		set_list = []
		for i in SQL_summoner_table:
			set_list.append('{} = ?'.format(i))
		conn.execute('Update Summoners SET {} WHERE summoner_id = {}'.format(','.join(set_list), s_id), (summoner_values[0]))

	conn.commit()
	conn.close()

def update_global_values(summoner_id, cursor):
	'''
	This function updates the global values for a summoner

	winrate, cs, kills, deaths, assists, kda, gold, cs_per_min, gold_per_min, wards_placed, wards_killed would be good

	['primary_key', 'summoner_id', 'match_id', 'champion', 'lane', 'role', 'winner', 'cs', 'kills', 'deaths','assists','gold', 'wards_placed', 'wards_killed', 'allies', 'enemies']
	'''
	select_statement = 'match_duration, winner, cs, kills, deaths, assists, gold, wards_placed, wards_killed'
	separate_info = cursor.execute("SELECT {} from Matches JOIN Junction ON Matches.match_id = Junction.match_id WHERE summoner_id = {}".format(select_statement, summoner_id)).fetchall()

	total_duration = 0
	winrate = 0
	cs = 0
	kills = 0
	deaths = 0
	assists = 0
	kda = 0
	gold = 0
	cs_per_min = 0
	gold_per_min = 0
	wards_placed = 0
	wards_killed = 0

	for match in separate_info:
		total_duration += match[0] 
		winrate += match[1]
		cs += match[2] / len(separate_info)
		kills += match[3] / len(separate_info)
		deaths += match[4] / len(separate_info)
		assists += match[5] / len(separate_info)
		gold += match[6] / len(separate_info)
		wards_placed += match[7] / len(separate_info)
		wards_killed += match[8] / len(separate_info)

	winrate = winrate/len(separate_info)
	cs_per_min = cs * len(separate_info) / (total_duration / 60)
	gold_per_min = gold * len(separate_info) / (total_duration / 60)
	kda = (kills + assists) / max(1, deaths)

	return [winrate, cs, kills, deaths, assists, kda, gold, cs_per_min, gold_per_min, wards_placed, wards_killed, len(separate_info)]

def runit(summoner_name, save_json = False, write_SQL = True):
	print('Start:', time.clock())
	
	summoner_name = summoner_name.lower()
	try:
		summoner_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/{}?api_key={}'.format((summoner_name.replace(' ','')), key))
		summoner_info_not_byte = summoner_info.readall().decode('utf-8')
		summoner_id = json.loads(summoner_info_not_byte)[summoner_name.replace(' ','')]['id']
	except urllib.error.HTTPError: #Probably no summoner name exists
		print('Summoner name not found.')
		return

	print('Pulling Matches')
	matches = get_matches(summoner_name, summoner_id, key)

	if type(matches) != list:
		print(matches)
		print('Finish:', time.clock())
		return

	if save_json == True:
		print('Saving Jsons')
		export_matches('{}.json'.format(summoner_name, matches))

	if write_SQL == True:
		print('Creating SQL database')
		add_to_SQL(summoner_id, summoner_name, matches)

	print('Finish:', time.clock())

