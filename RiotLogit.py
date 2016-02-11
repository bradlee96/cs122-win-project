#Statsmodels Test
import sqlite3
import pandas as pd
import statsmodels.api as sm
import numpy as np

DATABASE_FILE_NAME = 'info.db'

def get_data(dbfilename):
	conn = sqlite3.connect('{}'.format(dbfilename))
	c = conn.cursor()
	raw = c.execute('SELECT winner, kills, deaths, assists, cs, wards_placed, wards_killed FROM defaultinfo').fetchall()
	data = pd.DataFrame(raw)
	data.columns = ['winner', 'kills', 'deaths', 'assists', 'cs', 'wards_placed', 'wards_killed']
	data['intercept'] = 1.0
	conn.close()
	return data

def get_model(data):
	'''
	maybe we should add overall damage dealt and stuff, who knows
	'''
	print(data)
	train_cols = data.columns[1:]
	logit = sm.Logit(data['winner'], data[train_cols])
	result = logit.fit()
	print (result.summary())
	print(np.exp(result.params))
	return result

get_model(get_data(DATABASE_FILE_NAME))