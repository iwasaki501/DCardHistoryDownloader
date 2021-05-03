import requests
from bs4 import BeautifulSoup, element
from http.cookiejar import LWPCookieJar
import csv
from time import sleep
from datetime import datetime
import os
from dateutil.relativedelta import relativedelta
from getpass import getpass


class HistoryScraper():
    def __init__(self) -> None:
        self.COOKIE_SAVE_PATH: str = 'cookie.txt'
        self.ID: str = input('ID: ')
        self.PWD: str = getpass()
        self.AUTH_URL: str = 'https://cfg.smt.docomo.ne.jp/auth/cgi/idauth'
        self.INITIAL_URL: str = 'https://d-card.smt.docomo.ne.jp/'

    def __update_sess_info(self) -> None:
        self.bs: BeautifulSoup = BeautifulSoup(self.res.text, 'html.parser')
        arcv_em: element.Tag = self.bs.find(attrs={'name': 'arcv'})
        if arcv_em:
            self.arcv: str = arcv_em.get('value')
        funcid_em: str = self.bs.find(attrs={'name': 'funcid'})
        if arcv_em:
            self.funcid: str = funcid_em.get('value')
        sleep(1)

    def login(self) -> None:
        self.session: requests.sessions.Session = requests.Session()

        if os.path.exists(self.COOKIE_SAVE_PATH):
            cookiejar: LWPCookieJar = LWPCookieJar(self.COOKIE_SAVE_PATH)
            cookiejar.load()
            self.session.cookies.update(cookiejar)

        self.res: requests.models.Response = self.session.get(self.INITIAL_URL)
        self.__update_sess_info()

        if self.ID not in self.res.text:
            print('Log in with the two-step verification.')
            self.__first_login()
        else:
            print('Log in using the password.')
            self.__second_login()

        cookiejar: LWPCookieJar = LWPCookieJar(self.COOKIE_SAVE_PATH)
        for cookie in self.session.cookies:
            cookiejar.set_cookie(cookie)
        cookiejar.save()

    def __first_login(self) -> None:
        payload: dict[str, str] = {'funcid': self.funcid,
                                   'arcv': self.arcv,
                                   'authid': self.ID,
                                   'idomitflag': '1'}
        self.res = self.session.post(self.AUTH_URL, data=payload)
        self.__update_sess_info()

        payload: dict[str, str] = {'funcid': self.funcid,
                                   'arcv': self.arcv,
                                   'authpass': self.PWD,
                                   'rotpwd': input('Auth code: '),
                                   'devicename': 'bs',
                                   'deviceflag': '1'}
        self.res = self.session.post(self.AUTH_URL, data=payload)
        self.__update_sess_info()

    def __second_login(self) -> None:
        payload: dict[str, str] = {'funcid': self.funcid,
                                   'arcv': self.arcv,
                                   'authpass': self.PWD,
                                   'rotpwd': '',
                                   'devicename': ''}
        self.res = self.session.post(self.AUTH_URL, data=payload)
        self.__update_sess_info()

    def save_history(self, year: int, month: int, save_directory: str = './csv') -> None:
        print(f'Saving {year}/{month}...')
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        ym: str = str(year) + str(month).zfill(2)
        url: str = f'https://www5.dcmx.jp/dcmx/meisai?processCode=03Meisai&ym={ym}'
        self.res = self.session.get(url)
        self.__update_sess_info()

        tables: element.ResultSet = self.bs.find_all('table')
        table: element.Tag = tables[4]
        tbody: element.Tag = table.find('tbody')
        trs: element.ResultSet = tbody.find_all('tr')
        rows: list[list[str]] = []
        for tr in trs:
            row: list[str] = [td.text for td in tr.find_all(['td'])]
            if len(row) == 9:
                rows.append(row[1:])
            elif len(row) == 8:
                rows.append(row)
        print(f'{len(rows)} histories found!')
        with open(f'{save_directory}/{ym}.csv', 'w', encoding='shift_jis') as f:
            writer: csv._writer = csv.writer(f, lineterminator='\n')
            writer.writerows(rows)


if __name__ == '__main__':
    history_scraper = HistoryScraper()
    history_scraper.login()

    now: datetime = datetime.now()
    history_scraper.save_history(now.year, now.month)
    one_month_after: datetime = now + relativedelta(months=1)
    history_scraper.save_history(one_month_after.year, one_month_after.month)
