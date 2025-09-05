#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import re
import time
import gspread
from google.oauth2.service_account import Credentials
from bs4 import BeautifulSoup


# In[ ]:


def OpenGooglesheets(spreadsheet_url, sheet_name):
    # 공통 설정 및 인증
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
    ]
    json_file_name = 'life-coordinator-11396288d3b5.json'
    
    credentials = Credentials.from_service_account_file(json_file_name, scopes=scope)
    gc = gspread.authorize(credentials)
    
    doc = gc.open_by_url(spreadsheet_url)
    worksheet = doc.worksheet(sheet_name)
    
    records = worksheet.get_all_values()  # get_all_records() 대신 get_all_values() 사용 가능
    df = pd.DataFrame(records[1:], columns=records[0])  # 첫 번째 행을 컬럼으로 설정
    
    return worksheet, df

def append_dataframe_to_gsheet(worksheet, df):
    
    chunk_size = 500
    
    df = df.fillna('')
    
    # 데이터프레임을 리스트로 변환
    data = df.values.tolist()
    
    # 데이터를 chunk 단위로 나눠서 입력
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        worksheet.append_rows(chunk)
        time.sleep(1)

