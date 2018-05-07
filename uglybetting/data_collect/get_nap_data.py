#!/usr/bin/env python
__author__ = "Rob Cartwright"

import  requests
import  datetime
import  calendar
import  pandas as pd
from    bs4 import BeautifulSoup

class NapData:

    def __init__(self):
        self.save_dir = "C:/Users/Robert Cartwright/Dropbox/MathsyBoyz/ugly_betting/"
        self.url_base = 'http://racing.betting-directory.com/naps/'

    def create_date_url(self, date):
        """
        date takes integer date yyyymmdd
        """
        assert type(date) == int
        date = str(date)
        year = date[:4]
        month = date[4:6]
        month = calendar.month_name[int(month)]
        day = int(date[6:])
        if 4 <= day <= 20 or 24 <= day <= 30:
            suffix = "th"
        else:
            suffix = ["st", "nd", "rd"][day % 10 - 1]
        day = str(day) + suffix
        str_date = day + '-' + month + '-' + year
        url = self.url_base + str_date + '.php'

        return url

    def get_table_html(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        table_html = soup.find_all('table')[0]

        return table_html

    def parse_html_table(self, table):
        n_columns = 0
        n_rows = 0
        column_names = []

        # Find number of rows and columns
        # we also find the column titles if we can
        for row in table.find_all('tr'):

            # Determine the number of rows in the table
            td_tags = row.find_all('td')
            if len(td_tags) > 0:
                n_rows += 1
                if n_columns == 0:
                    # Set the number of columns for our table
                    n_columns = len(td_tags)

            # Handle column names if we find them
            th_tags = row.find_all('th')
            if len(th_tags) > 0 and len(column_names) == 0:
                for th in th_tags:
                    column_names.append(th.get_text())

        # Safeguard on Column Titles
        if len(column_names) > 0 and len(column_names) != n_columns:
            raise Exception("Column titles do not match the number of columns")

        columns = column_names if len(column_names) > 0 else range(0, n_columns)
        df = pd.DataFrame(columns=columns,
                          index=range(0, n_rows))
        row_marker = 0
        for row in table.find_all('tr'):
            column_marker = 0
            columns = row.find_all('td')
            for column in columns:
                df.iat[row_marker, column_marker] = column.get_text()
                column_marker += 1
            if len(columns) > 0:
                row_marker += 1

        # Convert to float if possible
        for col in df:
            try:
                df[col] = df[col].astype(float)
            except ValueError:
                pass

        df.columns = df.iloc[0].values
        df = df.iloc[1:]
        try:
            df['Result'] = df['Result'].astype(str)
        except:
            KeyError
        df['Odds'] = df['Odds'].astype(str)
        df.drop(['Silk'], axis=1, inplace=True)

        return df

    def table_on_date(self, date):
        """
        date takes integer date yyyymmdd
        """
        date_url = self.create_date_url(date)
        table_html = self.get_table_html(date_url)
        table_on_date = self.parse_html_table(table_html)

        return table_on_date

    def today_table(self):
        today_url = 'http://racing.betting-directory.com/daily-naps.php'
        table_html = self.get_table_html(today_url)
        today_table = self.parse_html_table(table_html)

        return today_table

    def save_table(self, date):
        """
        date takes integer date yyyymmdd
        """
        path = self.save_dir + str(date) + '.csv'
        table_on_date = self.table_on_date(date)
        table_on_date.to_csv(path, index=False)

    def update_today_table(self):
        curr_dttime = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        path = self.save_dir + curr_dttime + '.csv'
        curr_table = self.today_table()
        curr_table.to_csv(path, index=False)
