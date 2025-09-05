# 파일 이름: main.py (이 내용으로 덮어쓰기)

# ==============================================================================
# 1. 라이브러리 임포트 (이전과 동일)
# ==============================================================================
import time
import datetime
import random
import re
import pandas as pd
import pyperclip
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from libs import OpenGooglesheets as Google

# ==============================================================================
# 2. 상수(CONSTANTS) 정의 (이전과 동일)
# ==============================================================================
JOBKOREA_LOGIN_URL = 'https://www.jobkorea.co.kr/Login'
JOBKOREA_SEARCH_URL = 'https://www.jobkorea.co.kr/recruit/joblist?menucode=local&localorder=1'
JOBKOREA_ID = 'misojaimo'
JOBKOREA_PW = 'qawsedrftg!@#'

JD_LIST_SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1Fif7KZEL9MEj3IslfGgVV30SsAQd4tNwMIOynQ7q2Ow/edit#gid=0'
JD_LIST_SHEET_NAME = '전체JD'
CONTACT_SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1Fif7KZEL9MEj3IslfGgVV30SsAQd4tNwMIOynQ7q2Ow/edit#gid=1614047783'
CONTACT_SHEET_NAME = '연락처'
EXCLUSION_SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1Fif7KZEL9MEj3IslfGgVV30SsAQd4tNwMIOynQ7q2Ow/edit#gid=1781334674'
EXCLUSION_SHEET_NAME = '제외리스트'
EXCLUSION_JD_TITLE_PATTERN = r"(?i)abap|sap|강사|수리|코치|멘토"

# ==============================================================================
# 3. 핵심 기능 함수 정의 (이전과 동일)
# ==============================================================================
# initialize_driver, login_to_jobkorea, ... scrape_company_details 등 모든 함수는
# 이전 답변과 동일하게 여기에 그대로 복사/붙여넣기 합니다.
def initialize_driver():
    """셀레니움 웹드라이버를 초기화하고 반환합니다."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option("excludeSwitches", ["ignore-certificate-errors", "ignore-ssl-errors"])
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    print("✅ 웹드라이버 초기화 완료")
    return driver

def login_to_jobkorea(driver, user_id, user_pw):
    """주어진 드라이버를 사용하여 잡코리아에 로그인합니다."""
    print("⏳ 잡코리아 로그인을 시작합니다...")
    driver.get(JOBKOREA_LOGIN_URL)
    time.sleep(random.uniform(0.5, 1.0))
    id_input = driver.find_element(By.NAME, 'M_ID')
    id_input.click()
    pyperclip.copy(user_id)
    id_input.send_keys(Keys.CONTROL, 'v')
    time.sleep(random.uniform(0.5, 1.0))
    pw_input = driver.find_element(By.NAME, 'M_PWD')
    pw_input.click()
    pyperclip.copy(user_pw)
    pw_input.send_keys(Keys.CONTROL, 'v')
    time.sleep(random.uniform(0.5, 1.0))
    driver.find_element(By.CLASS_NAME, 'login-button').click()
    time.sleep(random.uniform(2, 4))
    print("✅ 로그인 성공!")

def safe_extract_text(element, selector, default=""):
    try:
        target = element.select_one(selector)
        return target.text.strip() if target else default
    except Exception:
        return default

def safe_extract_attr(element, selector, attr, default=""):
    try:
        target = element.select_one(selector)
        return target[attr].strip() if target and attr in target.attrs else default
    except Exception:
        return default

def parse_jd_list_page(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    jd_list_container = soup.find('div', id="dev-gi-list")
    if not jd_list_container: return []
    jd_rows = jd_list_container.find_all('tr', class_="devloopArea")
    page_data = []
    for jd_row in jd_rows:
        jd_title_element = jd_row.select_one('td.tplTit a.link.normalLog')
        data = {
            '기업명': safe_extract_text(jd_row, 'td.tplCo a.link.normalLog'),
            '기업링크': 'https://www.jobkorea.co.kr' + safe_extract_attr(jd_row, 'td.tplCo a.link.normalLog', 'href'),
            'JD명': jd_title_element.text.strip() if jd_title_element else "",
            '등록일': safe_extract_text(jd_row, 'td.odd span.time'),
            '마감기한': safe_extract_text(jd_row, 'td.odd span.date'),
            'JD링크': 'https://www.jobkorea.co.kr' + jd_title_element['href'].strip() if jd_title_element else "",
            '작업대상': "Wait",
            '수집일시': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        page_data.append(data)
    return page_data

def scrape_company_details(driver, company_url):
    driver.get(company_url)
    time.sleep(random.uniform(1, 2))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    company_info = {
        '기업명(검색결과)': safe_extract_text(soup, 'div.company-header-branding-body div.name'),
        '기업구분': "", '대표자': "", '홈페이지': "", '설립일': "", '산업': "", '주요사업': "",
        '사원수': "", '매출액': "", '자본금': "", '주소': ""
    }
    info_container = soup.find('div', class_="company-infomation-container basic-infomation-container")
    if not info_container: return company_info
    info_rows = info_container.find_all('tr')
    for row in info_rows:
        labels = row.find_all('th', class_="field-label")
        values = row.find_all('div', class_="value")
        for i in range(min(len(labels), len(values))):
            label = labels[i].text.replace('\n', '').replace(' ', '').strip()
            value = values[i].text.strip()
            if label in company_info:
                company_info[label] = value
    return company_info

def get_contact_details(driver, jd_link):
    driver.get(jd_link)
    try:
        more_info_button_xpath = "//span[contains(text(), '담당자 정보 더 보기')]/ancestor::button"
        wait = WebDriverWait(driver, 5)
        more_info_button = wait.until(EC.element_to_be_clickable((By.XPATH, more_info_button_xpath)))
        more_info_button.click()
        print("   - '담당자 정보 더 보기' 버튼 클릭 성공!")
        time.sleep(random.uniform(0.5, 1.0))
    except TimeoutException:
        print("   - '담당자 정보 더 보기' 버튼을 찾을 수 없습니다. (Timeout)")
    except Exception as e:
        print(f"   - 버튼 클릭 중 오류 발생: {e}")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    application_section = soup.find('div', id="application-section")
    if not application_section: return None
    def _parse_manager_info(section):
        manager_name = "정보 없음"; department_name = "정보 없음"
        manager_div = section.find('div', attrs={'data-sentry-component': 'HrManagerContact'})
        if manager_div and (name_span := manager_div.find('span')):
            full_text = name_span.get_text(strip=True)
            if '(' in full_text and ')' in full_text:
                parts = full_text.split('(')
                manager_name = parts[0].strip(); department_name = parts[1].replace(')', '').strip()
            else: manager_name = full_text
        return manager_name, department_name
    def _get_contact_value(section, label_text):
        if not (label_element := section.find('span', string=re.compile(r'\s*' + label_text + r'\s*'))): return "정보 없음"
        if not (value_container := label_element.parent.find_next_sibling('div')): return "정보 없음"
        return (value_element.get_text(strip=True) if (value_element := value_container.find('span')) else "정보 없음")
    manager_name, department_name = _parse_manager_info(application_section)
    return {
        '이름': manager_name, '소속': department_name, '전화번호': _get_contact_value(application_section, "전화번호"),
        '휴대전화': _get_contact_value(application_section, "휴대폰"), '이메일': _get_contact_value(application_section, "이메일")
    }

def get_jd_details(driver, jd_link):
    return {}

def run_phase1(driver):
    # Phase 1 로직 ... (이전과 동일)
    print("🚀 [Phase 1] 채용 공고 목록 수집을 시작합니다.")
    print("⏳ 구글 시트에서 기존 JD 목록과 제외 리스트를 불러옵니다...")
    JD_LIST_sheet, JD_LIST_df = Google.OpenGooglesheets(JD_LIST_SPREADSHEET_URL, JD_LIST_SHEET_NAME)
    _, EXCLUSION_df = Google.OpenGooglesheets(EXCLUSION_SPREADSHEET_URL, EXCLUSION_SHEET_NAME)
    print(f"✅ 기존 JD {len(JD_LIST_df)}건, 제외 기업 {len(EXCLUSION_df)}건 로드 완료.")

    print("⏳ JD 목록 스크래핑을 시작합니다...")
    driver.get(JOBKOREA_SEARCH_URL)
    time.sleep(random.uniform(2, 4))
    driver.find_element(By.ID, 'devSearchedTerms').click()
    time.sleep(random.uniform(0.5, 1.0))
    driver.find_element(By.CSS_SELECTOR, "#devSearchedTermsLayer > div > div.tplList > table > tbody > tr > td.tit.dev-condition-select > span").click()
    time.sleep(random.uniform(2, 4))
    all_jds = []
    current_page = 1
    MAX_PAGE = 999 
    while current_page <= MAX_PAGE:
        print(f"   - {current_page} 페이지 수집 중...")
        try:
            jd_elements = driver.find_elements(By.CSS_SELECTOR, "#dev-gi-list .devloopArea")
            if jd_elements: ActionChains(driver).scroll_to_element(jd_elements[-1]).perform()
        except Exception as e:
            print(f"   - 스크롤 중 사소한 오류 발생 (무시하고 진행): {e}")
        time.sleep(random.uniform(1, 2))
        page_source = driver.page_source
        if "채용정보 검색결과가 존재하지 않습니다." in page_source:
            print("✅ 더 이상 채용 정보가 없어 수집을 종료합니다."); break
        page_jds = parse_jd_list_page(page_source)
        if not page_jds:
            print("✅ 현재 페이지에서 공고를 찾지 못해 수집을 종료합니다."); break
        all_jds.extend(page_jds)
        current_page += 1
        driver.get(f"{JOBKOREA_SEARCH_URL}#anchorGICnt_{current_page}")
        time.sleep(random.uniform(2, 4))
    raw_df = pd.DataFrame(all_jds)
    print(f"✅ 총 {len(raw_df)}개의 JD 정보를 수집했습니다. 데이터 정제를 시작합니다.")
    clean_df = raw_df.drop_duplicates(subset='JD링크', keep='first').copy()
    clean_df['기업명'] = clean_df['기업명'].str.replace(r'\s?\(?㈜\)?|\s?주식회사\s?', '', regex=True)
    clean_df = clean_df[~clean_df['기업명'].isin(EXCLUSION_df['기업명'])]
    clean_df = clean_df[~clean_df['JD명'].str.contains(EXCLUSION_JD_TITLE_PATTERN, na=False)]
    clean_df = clean_df[~clean_df['JD링크'].isin(JD_LIST_df['JD링크'])]
    clean_df.dropna(subset=['기업명', 'JD링크'], inplace=True)
    clean_df = clean_df[~clean_df['JD링크'].str.contains('joblist')]
    clean_df = clean_df.sort_values(by=['기업명', '등록일'], ascending=[True, False]).reset_index(drop=True)
    print(f"✅ 데이터 정제 완료. 최종적으로 {len(clean_df)}개의 새로운 JD를 구글 시트에 추가합니다.")
    if not clean_df.empty:
        columns_to_save = ['기업명', '기업링크', 'JD명', '등록일', '마감기한', 'JD링크', '작업대상', '수집일시']
        Google.append_dataframe_to_gsheet(JD_LIST_sheet, clean_df[columns_to_save])
        print("✅ 구글 시트 저장 완료!")
    else:
        print("ℹ️ 추가할 새로운 JD가 없습니다.")
    print("🎉 [Phase 1] 모든 작업이 성공적으로 완료되었습니다.")

def run_phase2(driver):
    # Phase 2 로직 ... (이전과 동일)
    print("\n🚀 [Phase 2] JD 상세 정보 및 연락처 수집을 시작합니다.")
    print("⏳ '전체JD' 시트에서 작업 대상을 불러옵니다...")
    JD_LIST_sheet, JD_LIST_df = Google.OpenGooglesheets(JD_LIST_SPREADSHEET_URL, JD_LIST_SHEET_NAME)
    target_df = JD_LIST_df[JD_LIST_df['작업대상'] == "Wait"].copy()
    if target_df.empty:
        print("✅ 상세 정보를 수집할 새로운 JD가 없습니다. 작업을 종료합니다."); return
    print(f"✅ 총 {len(target_df)}건의 JD에 대한 상세 정보 수집을 시작합니다.")
    ContactSheet = Google.OpenGooglesheets(CONTACT_SPREADSHEET_URL, CONTACT_SHEET_NAME)[0]
    for company_link, group in target_df.groupby('기업링크'):
        company_final_data = []
        company_name = group['기업명'].iloc[0]
        try:
            print(f"\n🏢 기업 '{company_name}' 정보 수집 시작...")
            company_details = scrape_company_details(driver, company_link)
            print(f"   - 기업 기본 정보 수집 완료.")
            for index, row in group.iterrows():
                jd_link = row['JD링크']; jd_title = row['JD명']
                print(f"   - JD: '{jd_title}' 연락처 수집 중...")
                contact_details = get_contact_details(driver, jd_link)
                TARGET_COLUMN_INDEX = 7 # G열
                if contact_details:
                    final_data = {
                        '수집일자': datetime.datetime.now().strftime("%Y-%m-%d"), '기업명': company_name,
                        '기업링크': company_link, 'Title': jd_title, 'JDLink': jd_link,
                        **company_details, **contact_details
                    }
                    company_final_data.append(final_data)
                    JD_LIST_sheet.update_cell(index + 2, TARGET_COLUMN_INDEX, "Done")
                    print("     ✅ 정보 수집 및 상태 업데이트 완료 (Done)")
                else:
                    JD_LIST_sheet.update_cell(index + 2, TARGET_COLUMN_INDEX, "Error")
                    print("     ❌ 정보 수집 실패. 상태 업데이트 (Error)")
            if company_final_data:
                final_df = pd.DataFrame(company_final_data)
                final_columns_order = [
                    '수집일자', '기업명', '기업명(검색결과)', '기업링크', '기업구분', '대표자', '홈페이지', '설립일', '산업',
                    '주요사업', '사원수', '매출액', '자본금', '주소', 'Title', 'JDLink', '이름', '소속', '휴대전화',
                    '전화번호', '이메일'
                ]
                final_df = final_df.reindex(columns=final_columns_order, fill_value='-')
                print(f"   -> '{company_name}' 기업의 JD {len(final_df)}건을 구글 시트에 저장합니다...")
                Google.append_dataframe_to_gsheet(ContactSheet, final_df)
                print(f"   -> ✅ 저장 완료.")
        except Exception as e:
            print(f"🚨 기업 '{company_name}' 처리 중 심각한 오류 발생: {e}")
            TARGET_COLUMN_INDEX = 7
            for index, row in group.iterrows():
                if JD_LIST_df.loc[index, '작업대상'] == 'Wait':
                    JD_LIST_sheet.update_cell(index + 2, TARGET_COLUMN_INDEX, "Error")
            continue
    print("\n🎉 [Phase 2] 모든 작업이 성공적으로 완료되었습니다.")

# ==============================================================================
# 4. [수정된] 메인 실행 블록
# ==============================================================================
def main_task():
    """크롤링의 모든 과정을 수행하는 메인 함수"""
    driver = None
    try:
        driver = initialize_driver()
        login_to_jobkorea(driver, JOBKOREA_ID, JOBKOREA_PW)
        run_phase1(driver)
        run_phase2(driver)
    except Exception as e:
        print(f"💥 스크립트 실행 중 치명적인 오류가 발생했습니다: {e}")
    finally:
        if driver:
            driver.quit()
        print("🔚 크롤링 작업 세션을 종료합니다.")

if __name__ == "__main__":
    while True:
        now = datetime.datetime.now()
        
        # 매일 아침 7시 00분에만 실행되도록 조건 설정
        if now.hour == 7 and now.minute == 0:
            print(f"==== {now.strftime('%Y-%m-%d %H:%M:%S')} ====")
            print("목표 시각(07:00)이므로 크롤링을 시작합니다.")
            main_task()
            print("크롤링 작업을 완료했습니다. 다음 실행까지 대기합니다.")
        else:
            # 현재 시간을 1분마다 보여주어 서버가 살아있는지 확인하기 용이하게 함
            print(f"현재 시각 {now.strftime('%H:%M:%S')}. 07:00까지 대기 중...")
            
        # 60초 대기 후 다시 시간 체크
        time.sleep(60)
