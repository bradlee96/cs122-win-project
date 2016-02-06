import urllib.request
import json
import time
import sqlite3

key = '9df451c2-91bc-4584-99f5-87334af39c2a'
key2 = '8015aa1d-df1d-4cda-b319-dffcbcf2f708'

summoner_name = 'hanazono'
summoner_name = summoner_name.replace(' ','')

summoner_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/{}?api_key={}'.format(summoner_name,key))
summoner_info_not_byte = summoner_info.readall().decode('utf-8')
summoner_id = json.loads(summoner_info_not_byte)[summoner_name]['id']

def get_champion_id_table(key):
	champ_api = urllib.request.urlopen('https://na.api.pvp.net/api/lol/static-data/na/v1.2/champion?api_key={}'.format(key))
	champ_api_not_byte = champ_api.readall().decode('utf-8')
	champ_info = json.loads(champ_api_not_byte)['data']
	cleaned_table = {}
	for champion in champ_info.keys():
		cleaned_table[champ_info[champion]['id']] = champion
	
	return cleaned_table

champion_id_table = get_champion_id_table(key)

def get_matches(summoner_id, key):
	match_list = []
	matches_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v2.2/matchlist/by-summoner/{}?rankedQueues=RANKED_SOLO_5x5&api_key={}'.format(summoner_id,key))
	matches_info_not_byte = matches_info.readall().decode('utf-8')
	matches = json.loads(matches_info_not_byte)
	# print(matches['matches'][0].keys())
	for match in matches['matches'][0:20]:
		# time.sleep(1.2)
		match_list.append(get_match_info_for_summoner(match, key, summoner_name))

	return match_list

def get_match_info_for_summoner(match, key, summoner_name):
	match_id = match['matchId']
	match_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v2.2/match/{}?api_key={}'.format(match_id, key))
	match_info_not_byte = match_info.readall().decode('utf-8')
	match_json = json.loads(match_info_not_byte)
	#print(match['participants'][0])
	player_participant = {}
	for player in range(10):
		#print(match['participantIdentities'][player]['player']['summonerName'], match['participantIdentities'][player]['participantId'])
		player_participant[match_json['participantIdentities'][player]['player']['summonerName'].lower()] = match_json['participantIdentities'][player]['participantId']

	match_info_for_summoner = [match_json['participants'][i] for i in range(10) if match_json['participants'][i]['participantId'] == player_participant[summoner_name]][0]
	match_info_for_summoner['match_id'] = match['matchId']
	match_info_for_summoner['season'] = match['season']
	match_info_for_summoner['timestamp'] = match['timestamp']
	#print(match_info_for_summoner)
	time.sleep(1.2)
	return match_info_for_summoner

def add_to_SQL(s_id, s_name, match_list):
	# cur.execute("insert into contacts (name, phone, email) values (?, ?, ?)",
 #            (name, phone, email))
	conn = sqlite3.connect('info.db')
	for match in match_list:
		try:
			conn.execute('INSERT INTO defaultinfo VALUES (?, ?, ?, ?, ?, ?, ?)',\
				(s_id, s_name, match['match_id'], match['season'], match['timestamp'], champion_id_table[match['championId']], match['stats']['winner']))	
		except Exception:
			conn.execute('''CREATE TABLE defaultinfo (summoner_id, summoner_name, match_id, season, time_stamp, champion, winner)''')
			conn.execute('INSERT INTO defaultinfo VALUES (?, ?, ?, ?, ?, ?, ?)',\
				(s_id, s_name, match['match_id'], match['season'], match['timestamp'], champion_id_table[match['championId']], match['stats']['winner']))		

	conn.commit()
	conn.close()

pie = get_matches(summoner_id, key)
add_to_SQL(summoner_id, summoner_name, pie)
