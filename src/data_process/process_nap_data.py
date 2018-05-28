#!/usr/bin/env python
__author__ = "Rob Cartwright"

import  pandas as pd
import  pytz
from    os import listdir
from    os.path import isfile, join

class ProcessNapData:

    def __init__(self):
        self.raw_dir = "C:/Users/Robert Cartwright/Dropbox/MathsyBoyz/ugly_betting/test/"

    def split_name_track(self, row):

        upper_idx = [i for i, c in enumerate(row) if c.isupper()]
        return [row[:upper_idx[-1]], row[upper_idx[-1]:]]

    def split_pub_perf(self, row):

        sign_idx = [i for i, c in enumerate(row) if c in ["+", "-"]]
        return [row[:sign_idx[-1]], row[sign_idx[-1]:]]

    def split_name_place(self, row):

        int_row = []
        for x in row:
            try:
                x = int(x)
            except ValueError:
                pass
            int_row.append(x)
        int_idx = [i for i, c in enumerate(int_row) if isinstance(c, int)]
        return [row[:int_idx[0]], row[int_idx[0]:]]

    def split_place(self, row):

        int_row = []
        for x in row:
            try:
                x = int(x)
                int_row.append(x)
            except ValueError:
                pass
        place = int(''.join(map(str, int_row)))

        return place

    def process_live_df(self, live_df):

        if len(live_df) == 0:
            return None
        else:
            # split nap column
            nap_df = live_df[['Nap']].copy()
            nap_df = nap_df['Nap'].str.split(pat=" - ", expand=True)
            nap_df.columns = ['name_track', 'race_time']
            nap_df['name_track'] = nap_df['name_track'].apply(self.split_name_track)
            nap_df[['name', 'track']] = pd.DataFrame(nap_df['name_track'].values.tolist(), index=nap_df.index)
            nap_df = nap_df[['name', 'track', 'race_time']]

            # split tipster column
            tipster_df = live_df[['Tipster']].copy()
            tipster_df = tipster_df['Tipster'].str.split(pat="(", expand=True)
            tipster_df.columns = ['tip_name', 'tip_pub']
            tipster_df['tip_pub'] = tipster_df['tip_pub'].str.replace(")", "")
            tipster_df['tip_pub'] = tipster_df['tip_pub'].apply(self.split_pub_perf)
            tipster_df[['tip_pub', 'perf']] = pd.DataFrame(tipster_df['tip_pub'].values.tolist(), index=tipster_df.index)

            # sort odds df
            odds_df = live_df[['Odds']].copy()
            odds_df['Odds'] = odds_df['Odds'].str.replace("EVS", "1/1")
            odds_df = odds_df['Odds'].str.split(pat='/', expand=True)
            odds_df.columns = ['ret', 'stake']
            odds_df = odds_df.astype(int)
            odds_df['prob'] = odds_df['stake'] / (odds_df['ret'] + odds_df['stake'])

            proc_live_df = pd.concat([nap_df, tipster_df, odds_df], axis=1)
            proc_live_df['status'] = 'live'

            return proc_live_df

    def process_result_df(self, result_df):

        result_df = result_df[result_df['Nap'].str.contains("@")].copy()
        if len(result_df) == 0:
            return None
        else:
            # split nap column
            nap_df = result_df[['Nap']].copy()
            nap_df = nap_df['Nap'].str.split(pat=" @ ", expand=True)
            nap_df.columns = ['name_place', 'Odds']
            nap_df['name_place'] = nap_df['name_place'].apply(self.split_name_place)
            nap_df[['name', 'place']] = pd.DataFrame(nap_df['name_place'].values.tolist(), index=nap_df.index)
            nap_df = nap_df[['Odds', 'name', 'place']]

            # get place
            place_df = nap_df[['place']].copy()
            place_df = place_df['place'].str.split(pat=" of ", expand=True)
            place_df.columns = ['place', 'runners']
            place_df['place'] = place_df['place'].apply(self.split_place).astype(int)

            # split tipster column
            tipster_df = result_df[['Tipster']].copy()
            tipster_df = tipster_df['Tipster'].str.split(pat="(", expand=True)
            tipster_df.columns = ['tip_name', 'tip_pub']
            tipster_df['tip_pub'] = tipster_df['tip_pub'].str.replace(")", "")
            tipster_df['tip_pub'] = tipster_df['tip_pub'].apply(self.split_pub_perf)
            tipster_df[['tip_pub', 'perf']] = pd.DataFrame(tipster_df['tip_pub'].values.tolist(), index=tipster_df.index)

            # split odds column
            odds_df = nap_df[['Odds']].copy()
            odds_df['Odds'] = odds_df['Odds'].str.replace("EVS", "1/1")
            odds_df = odds_df['Odds'].str.split(pat='/', expand=True)
            odds_df.columns = ['ret', 'stake']
            odds_df = odds_df.astype(int)
            odds_df['prob'] = odds_df['stake'] / (odds_df['ret'] + odds_df['stake'])

            proc_result_df = pd.concat([nap_df[['name']], tipster_df, odds_df, place_df], axis=1)
            proc_result_df['status'] = 'result'

            return proc_result_df

    def process_nonrun_df(self, nonrun_df):

        if len(nonrun_df) == 0:
            return None
        else:
            nonrun_df['status'] = 'non_runner'
            return nonrun_df

    def add_datetime_columns(self, df, filename):

        # add write time
        file_write_time = filename.replace(".csv", "")
        write_time_stamp = pd.to_datetime(file_write_time, format="%Y%m%d%H%M%S")
        gmt = pytz.timezone('Europe/London')
        write_time_stamp_gmt = write_time_stamp.tz_localize(pytz.utc).tz_convert(gmt)
        df['write_time'] = pd.to_datetime(write_time_stamp_gmt)

        if 'race_time' in df.columns:
            # raced df (doesn't contain race time any longer)
            result_df = df[df['race_time'].isnull()]
            live_df = df[~df['race_time'].isnull()]

            # convert race time
            racetime_df = live_df[['race_time']].copy()
            racetime_df = racetime_df['race_time'].str.split(pat=':', expand=True)
            racetime_df.columns = ['hour', 'minutes']
            racetime_df['hour'] = (racetime_df['hour'].astype(int) + 12).astype(str)
            ydm = file_write_time[:8]
            racetime_df['race_time_full'] = ydm + racetime_df['hour'] + racetime_df['minutes'] + '00'
            racetime_df['race_time_full'] = pd.to_datetime(racetime_df['race_time_full'], format="%Y%m%d%H%M%S")
            racetime_df['race_time_full'] = racetime_df['race_time_full'].dt.tz_localize(gmt)
            live_df = pd.concat([live_df, racetime_df[['race_time_full']]], axis=1)
            live_df['seconds_to_race'] = (
                pd.to_datetime(live_df['race_time_full']) -
                pd.to_datetime(live_df['write_time'])
            ).dt.seconds.astype(int)
            live_df['race_time_full'] = live_df['race_time_full'].dt.tz_localize(None)
        else:
            result_df = df
            live_df = None

        # join back up
        date_time_df = pd.concat([result_df, live_df], axis=0)
        date_time_df['write_time'] = date_time_df['write_time'].dt.tz_localize(None)
        date_time_df['date'] = int(file_write_time[:8])

        return date_time_df

    def process_file(self, filename):

        df = pd.read_csv(self.raw_dir + filename)

        # drop 'SP' values and don't progress if length then becomes 0
        df = df[~(df['Odds'] == 'SP')]
        if len(df) == 0:
            return None
        else:
            # split into results and live
            live_df = df[~df['Odds'].isin(['Result', 'Non-Runner', 'OFF'])].copy()
            result_df = df[df['Odds'] == 'Result'].copy()
            nonrun_df = df[df['Odds'] == 'Non-Runner'].copy()

            proc_live_df = self.process_live_df(live_df)
            proc_result_df = self.process_result_df(result_df)
            proc_nonrun_df = self.process_nonrun_df(nonrun_df)
            proc_df = pd.concat([proc_live_df, proc_result_df, proc_nonrun_df], axis=0)
            proc_df['perf'] = proc_df['perf'].astype(float)

            proc_df = self.add_datetime_columns(proc_df, filename)

            return proc_df

    def get_date_df(self, date):

        files = [f for f in listdir(self.raw_dir) if isfile(join(self.raw_dir, f))]
        date_files = [f for f in files if f[:8] == date]
        date_files_list = []
        for file_name in date_files:
            date_files_list.append(self.process_file(file_name))
        date_df = pd.concat(date_files_list, axis=0)

        return date_df

    def get_ohlc_on_date(self, date):

        date_df = self.get_date_df(date)
        date_df.sort_values('write_time', ascending=True, inplace=True)
        ohlc_list = []
        for tipster in date_df['tip_name'].unique():
            try:
                tipster_df = date_df[date_df['tip_name'] == tipster].copy()
                tipster_df['prob'].dropna(inplace=True)
                open = tipster_df.iloc[0]['prob']
                high = tipster_df['prob'].max()
                low = tipster_df['prob'].min()
                close = tipster_df.iloc[-1]['prob']
                name = tipster_df.iloc[0]['name']
                ohlc_list.append([tipster, name, open, high, low, close])
            except IndexError:
                pass
        ohlc_df = pd.DataFrame(ohlc_list, columns=['tipster', 'name', 'open', 'high', 'low', 'close'])
        ohlc_df.sort_values('name', ascending=True, inplace=True)

        return ohlc_df


test = ProcessNapData()
# test.process_file('20180519130519.csv')
# x = test.get_date_df('20180526')
x = test.get_ohlc_on_date('20180519')
print(x)






