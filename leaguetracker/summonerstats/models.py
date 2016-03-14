from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from datetime import datetime

class Match(models.Model):
    match_id = models.IntegerField(primary_key=True)
    season = models.CharField(max_length=20)
    time_stamp = models.FloatField()
    match_duration = models.FloatField()

    class Meta:
        managed = False
        db_table = 'Matches'

    def __str__(self):
        return str(self.match_id)

class Summoner(models.Model):
    summoner_id = models.IntegerField(primary_key=True)
    summoner_name = models.CharField(max_length=20)
    winrate = models.FloatField()
    total_damage_dealt_champions_min = models.FloatField()
    cs = models.FloatField()
    kills = models.FloatField()
    deaths = models.FloatField()
    assists = models.FloatField()
    kda = models.FloatField()
    gold = models.FloatField()
    cs_per_min = models.FloatField()
    gold_per_min = models.FloatField()
    wards_placed = models.FloatField()
    wards_killed = models.FloatField()
    matches_played = models.FloatField()
    # Model.refresh_from_db

    def get_winrate(self):
        return '{:.2f}'.format(100 * self.winrate) + '%'

    def __str__(self):
        return str(self.summoner_id) + ' (' + self.summoner_name + ')'

    class Meta:
        managed = False
        db_table = 'Summoners'

class Junction(models.Model):
    primary_key = models.AutoField(primary_key=True)
    summoner = models.ForeignKey(Summoner, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    champion = models.CharField(max_length=20)
    lane = models.CharField(max_length=20)
    role = models.CharField(max_length=20)
    winner = models.IntegerField()
    total_damage_dealt_champions_min = models.FloatField()
    kills = models.IntegerField()
    deaths = models.IntegerField()
    assists = models.IntegerField()
    cs = models.IntegerField()
    gold = models.IntegerField()
    wards_placed = models.IntegerField()
    wards_killed = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'Junction'

    def __str__(self):
        return str(self.summoner.summoner_id) + ' (' + self.summoner.summoner_name + '): ' + str(self.match.match_id)
