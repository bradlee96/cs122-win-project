import urllib.request
import json

key = '9df451c2-91bc-4584-99f5-87334af39c2a'
summoner_name = 'hanazono'
summoner_name = summoner_name.replace(' ','')

summoner_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/{}?api_key={}'.format(summoner_name,key))
summoner_info_not_byte = summoner_info.readall().decode('utf-8')
summoner_id = json.loads(summoner_info_not_byte)[summoner_name]['id']

def get_matches(summoner_id, key):
	matches_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v2.2/matchlist/by-summoner/{}?rankedQueues=RANKED_SOLO_5x5&api_key={}'.format(summoner_id,key))
	matches_info_not_byte = matches_info.readall().decode('utf-8')
	matches = json.loads(matches_info_not_byte)
	return (matches['matches'][0])

def get_match_info_for_summoner(match_id, key, summoner_name):
	match_info = urllib.request.urlopen('https://na.api.pvp.net/api/lol/na/v2.2/match/{}?api_key={}'.format(match_id, key))
	match_info_not_byte = match_info.readall().decode('utf-8')
	match = json.loads(match_info_not_byte)
	#print(match['participants'][0])
	player_participant = {}
	for player in range(10):
		#print(match['participantIdentities'][player]['player']['summonerName'], match['participantIdentities'][player]['participantId'])
		player_participant[match['participantIdentities'][player]['player']['summonerName'].lower()] = match['participantIdentities'][player]['participantId']

	match_info_for_summoner = [match['participants'][i] for i in range(10) if match['participants'][i]['participantId'] == player_participant[summoner_name]][0]
	
	return match_info_for_summoner


pie = get_match_info_for_summoner(get_matches(summoner_id, key)['matchId'], key, summoner_name)
for key in pie.keys():
	print(key,pie[key])
	if key =='stats':
		for k in pie[key].keys():
			print(k, pie[key][k])
