#! /usr/bin/python3.

import csv
import json
import pprint
import random
import datetime

class DutiesForWeek:
    """ Set up duties for next week, including preferences and abilities.

        :param ability: CSV file with emploee preferences, defaults to 'abi.csv'
        :type ability: CSV file, required

        :param meta: json file with historical duties, defaults to 'MetaData.json'
        :type meta: json file, required

        :param how_many: number of people on duty per dat, defaults to 2
        :type how_many: int, required
    """
    def __init__(self, ability="abi.csv", meta="MetaData.json", how_many=2):
        with open(ability, "r", encoding="utf-8") as opn_fil:
            self.week_ability = list(csv.reader(opn_fil))

        with open(meta, "r", encoding="utf-8") as npo_lif:
            Meta = json.load(npo_lif)
            self.one_week_ago = list(Meta["OneWeekAgo"])
            self.two_week_ago = list(Meta["TwoWeeksAgo"])
            self.week_days = dict(Meta["WeekDays"])

        self.duty_size = how_many

    # Get volunteers for one day
    def _get_volunteers_for_day(self, day, to_exclude):
        idx = self.week_days[day]
        daily_vol = [var[0] for var in self.week_ability[1:] if var[idx] == "A" and var[0] not in to_exclude]
        return random.sample(daily_vol, self.duty_size) if len(daily_vol) > self.duty_size else daily_vol

    # Get volunteers for entire working week
    def _set_volunteers_for_week(self):
        OutPut = {}
        to_exclude = set()
        wo = self.week_days.keys()
        for day in random.sample(wo, len(wo)):
            vol = self._get_volunteers_for_day(day, to_exclude)
            to_exclude.update(vol)
            OutPut[day] = vol if len(vol) > 0 else []
        return OutPut

    # Make list of employees which will be present 
    def _available_emplo(self, day, to_exclude, on_break):
        idx = self.week_days[day]
        to_exclude.union(on_break)
        available_for_day = [avi[0] for avi in self.week_ability[1:] if avi[idx] != "U" and avi[0] not in to_exclude]
        random.shuffle(available_for_day)
        return iter(available_for_day)
    
    # Fill gaps in schedule, assigning available people next to volunteers
    def _fill_gaps_in_duties(self):
        InDict = self._set_volunteers_for_week()
        already_in = set(sin for li in InDict.values() for sin in li)
        ppl_on_break = set(self.one_week_ago + self.two_week_ago)
        lack_of_ppl = False

        for key, val in InDict.items():
            candi = self._available_emplo(key, already_in, ppl_on_break)
            while len(val) < self.duty_size:
                try:
                    new_one = next(candi)
                except StopIteration:
                    if not lack_of_ppl:
                        ppl_on_break.difference_update(self.two_week_ago)
                        lack_of_ppl = True
                    else:
                        ppl_on_break.difference_update(self.one_week_ago)
                    break
                InDict[key].append(new_one)
                already_in.add(new_one)
        return InDict

    def make_rnd_duties(self, current_week=None, touch_file=True):
        """ Create new file with metadata and set up duty.

            :return: Dictionary with people on duty for each business day.
            :rtype: dict
        """
        if current_week is None:
            current_week = self._fill_gaps_in_duties()

        new_meta = {"TwoWeeksAgo": self.one_week_ago,
                    "OneWeekAgo": [it for li in current_week.values() for it in li],
                    "WeekDays": self.week_days}

        next_week_num = (datetime.date.today() + datetime.timedelta(7)).strftime("%V")
        
        if touch_file:
            with open(f"duties_deta_w{next_week_num}.json", "w", encoding="utf-8") as op_fl:
                json.dump(new_meta, op_fl)

        return current_week