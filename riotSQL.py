import math
import sqlite3
'''
champ winrate - (SELECT win/loss, time_stamp FROM defaultinfo WHERE champion = ? and summoner_id = ?, [])
gold per min - (SELECT goldEarned, time_stamp, matchDuration FROM defaultinfo WHERE champion = ? and summoner_id = ?, [])
KDA - (SELECT kills, assists, death, time_stamp FROM defaultinfo WHERE champion = ? and summoner_id = ?, [])
CS - (SELECT minionsKilled, matchDuration FROM info.db WHERE champion = ? and summoner_id = ?, [])

Notes: changed timestamp to time_stamp; winner is 1, loser is 0 so I changed that from t/f; named the table defaultinfo
time_interval is weeks?
'''
time_start = 1398902400
time_end = 1453593600

info = sqlite3.connect('info.db')
cursor = info.cursor()

def sql_query(summoner, champion, stat, time_interval):
	# interval is a number of weeks (integer)
	interval = time_interval * 604800
	num_divisions = math.ceil((time_end - time_start) / interval)
	
	values = [summoner]
	where_statement = "WHERE summoner_id = ? "
	if champion != None:
		where_statement += "AND champion = ?"
		values.append(champion)
	
	if stat == "winrate":
		select_statement = "SELECT winner, time_stamp FROM defaultinfo "
		full_statement = select_statement + where_statement
		print(full_statement)
		print(where_statement)
		result = cursor.execute(full_statement, values)
		rv = result.fetchall()
		print(rv)
		
		return_values = [[0,0]] * num_divisions
		print(len(return_values))
		for single_match in rv:
			print(single_match[1])
			division = math.floor((single_match[1] - time_start) / interval)
			print('division', division)
			if single_match[1] == 1:
				return_values[division][0] += 1
			return_values[division][1] += 1
		print(return_values)
		for i in range(len(return_values)):
			return_values[i] = return_values[i][0] / return_values[i][1]
			
	elif stat == "gold per minute":
		select_statement = "SELECT goldEarned, time_stamp, matchDuration FROM defaultinfo "
		full_statement = select_statement + where_statement
		result = cursor.execute(full_statement, values)
		rv = result.fetchall()
		
		return_values = [[]] * num_divisions
		for single_match in rv:
			division = math.floor((single_match[1] - time_start) / interval)
			return_values[division].append(single_match[0] / single_match[2])
		for i in range(len(return_values)):
			return_values[i] = sum(return_values[i]) / len(return_values[i])
			
	elif stat == "KDA":
		select_statement = "SELECT kills, assists, deaths, time_stamp FROM defaultinfo "
		full_statement = select_statement + "WHERE summoner_id = ? " + where_statement
		result = cursor.execute(full_statement, values)
		rv = result.fetchall()
		
		return_values = [[]] * num_divisions
		for single_match in rv:
			division = math.floor((single_match[3] - time_start) / interval)
			return_values[division].append((single_match[0] + single_match[1]) / single_match[2])
		for i in range(len(return_values)):
			return_values[i] = sum(return_values[i]) / len(return_values[i])
			
	elif stat == "CS":
		select_statement = "SELECT minionsKilled, matchDuration, time_stamp FROM defaultinfo "
		full_statement = select_statement + where_statement
		result = cursor.execute(full_statement, values)
		rv = result.fetchall()
		
		return_values = [[]] * num_divisions
		for single_match in rv:
			division = math.floor((single_match[2] - time_start) / interval)
			return_values[division].append(single_match[0] / single-match[1])
		for i in range(len(return_values)):
			return_values[i] = sum(return_values[i]) / len(return_values[i]) 
			
	return return_values