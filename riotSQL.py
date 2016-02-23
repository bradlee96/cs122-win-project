import math
import sqlite3
import time
'''
champ winrate - (SELECT win/loss, time_stamp FROM defaultinfo WHERE champion = ? and summoner_id = ?, [])
gold per min - (SELECT gold, time_stamp, match_duration FROM defaultinfo WHERE champion = ? and summoner_id = ?, [])
KDA - (SELECT kills, assists, death, time_stamp FROM defaultinfo WHERE champion = ? and summoner_id = ?, [])
CS - (SELECT cs, match_duration FROM info.db WHERE champion = ? and summoner_id = ?, [])
Notes: changed timestamp to time_stamp; winner is 1, loser is 0 so I changed that from t/f; named the table defaultinfo
time_interval is weeks?
'''
time_start = 1398902400
time_end = 1453593600

info = sqlite3.connect('ghibli studios_sql.db')
cursor = info.cursor()


def pick_time_interval(start_date, end_date):
    #date = "mm-dd-yyyy"
    pattern = '%d.%m.%Y'
    # start = time_start + int(start_date[0:2]) *  2419200 + \
    #         int(start_date[3:5]) * 86400 + int(start_date[6:10]) * 31536000
    # end = time_end + int(end_date[0:2]) *  2419200 + \
    #       int(end_date[3:5]) * 86400 + int(end_date[6:10]) * 31536000
    start = int(time.mktime(time.strptime(start_date,'%d.%m.%Y')))
    end = int(time.mktime(time.strptime(end_date,'%d.%m.%Y')))
    return start,end

def get_sql_info(stat, values, where_statement):
	if stat == "winrate":
		select_statement = "SELECT time_stamp, winner FROM defaultinfo"
	elif stat == "gold per minute":
		select_statement = "SELECT time_stamp, match_duration, gold FROM defaultinfo "
	elif stat == "KDA":
		select_statement = "SELECT time_stamp, match_duration, kills, assists, deaths FROM defaultinfo "
	elif stat == "cs":
		select_statement = "SELECT time_stamp, match_duration, cs FROM defaultinfo "
	elif stat == "wards placed":
		select_statement = "SELECT time_stamp, match_duration, wards_placed FROM defaultinfo"

	full_statement = select_statement + ' ' + where_statement
	print(full_statement)
	print(values)
	result = cursor.execute(full_statement, values)
	rv = result.fetchall()

	return rv

def get_graph_data(stat, rv, start, interval, num_divisions):
	return_values = []
	for i in range(num_divisions):
		return_values.append([])
	for single_match in rv:
		# print(single_match[1])
		division = math.floor((single_match[0] - start) / interval)
		# print('division', division)
		if stat == "winrate":
			# print(return_values[division])
			return_values[division].append(single_match[1])
		if stat == "cs" or stat == "wards placed" or stat == "gold per minute":
			return_values[division].append(single_match[2] / (single_match[1] / 60))
		if stat == "KDA":
			if single_match[4] != 0:
				return_values[division].append((single_match[2] + single_match[3]) / single_match[4])
			else:
				return_values[division].append((single_match[2] + single_match[3]))
		# print(return_values)
	for i,j in enumerate(return_values):
		if len(j) != 0:
			return_values[i] = sum(j) / len(j)
		else:
			return_values[i] = 0
	return return_values

def sql_query(summoner, champion, stat, time_interval, start_date, end_date):
	# interval is a number of weeks (integer)
	interval = time_interval * 604800

	start, end = pick_time_interval(start_date, end_date)
	num_divisions = math.ceil((end - start) / interval)

	values = [summoner, start, end]
	where_statement = "WHERE summoner_name = ? "
	where_statement += "AND time_stamp >= ? AND time_stamp <= ?"
	if champion != None:
		where_statement += "AND champion = ?"
		values.append(champion)

	rv = get_sql_info(stat, values, where_statement)
	return_values = get_graph_data(stat, rv, start, interval, num_divisions)

	return return_values

print(sql_query('ghibli studios', 'shyvana', 'wards placed', 2, '01.01.2015', '31.12.2015'))
# print(sql_query('hanazono', 'annie', 'cs', 2, '01.01.2015', '31.12.2015'))