from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from .models import Summoner, Match, Junction
from datetime import date, datetime
import time

OFFSET_EPOCH_WEEK_TO_SUNDAY = 345600
EPOCH_TIME_COUNTERS = {'Year': 31557600, '30 Day Period': 2592000, 'Week': 604800, 'Day': 86400}

def home(request):
    '''Remember to comment'''
    if request.method == "GET":
        if 'summoner' in request.GET:
            return HttpResponseRedirect('summoner/' + request.GET['summoner'])
    template_name = 'summonerstats/home.html'
    summoner_list = Summoner.objects.all()
    return render(request, 'summonerstats/home.html', {'summoner_list': summoner_list})

def stats(request, summoner_name):
    '''Remember to comment'''
    time_interval = '30 Day Period'
    context = {}
    try:
        summoner = Summoner.objects.filter(summoner_name=summoner_name.lower())[0]
    except:
        context['summoner_id'] = summoner_name
    else:
        matches = summoner.junction_set.all().order_by('match__time_stamp')

        time_start = matches[0].match.time_stamp
        time_end = matches[len(matches)-1].match.time_stamp
        print((time_start))
        print((time_end))

        time_start_category = get_epoch_time_category(time_start, time_interval)
        time_end_category = get_epoch_time_category(time_end, time_interval)

        num_time_stamps = get_num_time_stamps(time_interval, time_start, time_end)
        print(num_time_stamps)

        print(time.strftime("%a, %b %d %Y", time.gmtime(time_start_category)))
        gold_values = [0] * num_time_stamps
        cs_values = [0] * num_time_stamps
        # other value lists
        average_counter = [0.0] * num_time_stamps

        for summoner_match in matches:
            time_stamp = summoner_match.match.time_stamp
            time_stamp_category = get_epoch_time_category(time_stamp, time_interval)
            index = get_relative_epoch_time_category(time_stamp_category, time_start_category, time_interval)
            average_counter[index] += 1
            gold_values[index] = gold_values[index] * (1 - 1/average_counter[index]) + summoner_match.gold / average_counter[index]
            cs_values[index] = cs_values[index] * (1 - 1/average_counter[index]) + summoner_match.cs / average_counter[index]
        gold_values = [round(x/1000, 1) for x in gold_values]
        cs_values = [round(x, 1) for x in cs_values]
        context['summoner'] = summoner
        context['cs_values'] = cs_values
        context['gold_values'] = gold_values
        context['time_interval'] = EPOCH_TIME_COUNTERS[time_interval]*1000
        context['time_interval_name'] = time_interval
        if time_interval == 'Year':
            context['time_start'] = [time_start_category, 1, 1]
        elif time_interval == '30 Day Period':
            y = time_start_category / 12
            m = time_start_category % 12
            context['time_start'] = [y, m, 1]
        else:
            context['time_start'] = get_UTC_time(time_start_category)
    return render(request, 'summonerstats/stats.html', context)

def get_UTC_time(epoch_time):
    return list(time.gmtime(epoch_time)[:3])

def get_epoch_time_category(epoch_time, time_interval):
    '''Remember to comment'''
    if time_interval == 'Year':
        category = time.gmtime(epoch_time)[0]
    elif time_interval == '30 Day Period':
        category = time.gmtime(epoch_time)[0] * 12 + time.gmtime(epoch_time)[1]
    elif time_interval == 'Week':
        category = epoch_time // EPOCH_TIME_COUNTERS[time_interval] * EPOCH_TIME_COUNTERS[time_interval] - OFFSET_EPOCH_WEEK_TO_SUNDAY
        if epoch_time % EPOCH_TIME_COUNTERS[time_interval] >= OFFSET_EPOCH_WEEK_TO_SUNDAY:
            category += EPOCH_TIME_COUNTERS[time_interval]
    elif time_interval == 'Day':
        category = epoch_time // EPOCH_TIME_COUNTERS[time_interval] * EPOCH_TIME_COUNTERS[time_interval]
    return category

def get_relative_epoch_time_category(epoch_time_category, start_time_category, time_interval):
    '''Remember to comment'''
    if time_interval == 'Year' or time_interval == '30 Day Period':
        return epoch_time_category - start_time_category
    elif time_interval == 'Week' or time_interval == 'Day':
        return int((epoch_time_category - start_time_category) / EPOCH_TIME_COUNTERS[time_interval])

def get_num_time_stamps(time_interval, time_start, time_end):
    if time_interval == 'Year':
        num_time_stamps = time.gmtime(time_end)[0] - time.gmtime(time_start)[0] + 1
    elif time_interval == '30 Day Period':
        gmtime_start = time.gmtime(time_start)
        gmtime_end = time.gmtime(time_end)
        num_time_stamps = 12 * (gmtime_end[0] - gmtime_start[0]) + (gmtime_end[1] - gmtime_start[1]) + 1
    elif time_interval == 'Week' or time_interval == 'Day':
        time_start = get_epoch_time_category(time_start, time_interval)
        time_end = get_epoch_time_category(time_end, time_interval)
        num_time_stamps = int(round( ((time_end - time_start) / EPOCH_TIME_COUNTERS[time_interval]) + 1 ))
    print('Num Time Stamps:', num_time_stamps)
    return num_time_stamps
