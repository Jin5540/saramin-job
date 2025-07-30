from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time

# ===== 드라이버 경로 수정 필요 =====
chrome_driver_path = 'C:/Users/jjin7/OneDrive/바탕 화면/이예진/X/job/chromedriver-win64/chromedriver.exe'

# 서비스 + 옵션 설정
service = Service(executable_path=chrome_driver_path)
options = Options()
options.add_argument('--headless')  # 창 안 띄우기
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=service, options=options)

rows = []

# ===== 1~5페이지 반복 =====
for page in range(1, 100):
    print(f"📄 페이지 {page} 수집 중...")

    url = f"https://www.saramin.co.kr/zf_user/jobs/list/job-category?page={page}&cat_mcls=2&panel_type=&search_optional_item=n&search_done=y&panel_count=y&preview=y"
    driver.get(url)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "list_item"))
        )
    except:
        print(f"⚠️ 페이지 {page} 로딩 실패")
        continue

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    job_cards = soup.select('div.list_item')

    for item in job_cards:
        title_elem = item.select_one('.job_tit a.str_tit')
        company_elem = item.select_one('.company_nm .str_tit')
        deadline_elem = item.select_one('.support_info .date')

        # ✅ 직무 키워드 추출 (공백 제거 + "외" 필터링)
        sector_block = item.select_one('.job_sector')
        sector_keywords = []
        if sector_block:
            spans = sector_block.find_all("span")
            sector_keywords = [
                span.get_text(strip=True) for span in spans
                if span.get_text(strip=True) and span.get_text(strip=True) != "외"
            ]

        if title_elem and company_elem and deadline_elem:
            title = title_elem.get_text(strip=True)
            link = "https://www.saramin.co.kr" + title_elem.get('href')
            company = company_elem.get_text(strip=True)
            deadline = deadline_elem.get_text(strip=True)

            rows.append({
                'title': title,
                'company': company,
                'link': link,
                'deadline': deadline,
                'sectors': ", ".join(sector_keywords)  # ✅ 최종 정제된 키워드 문자열로 저장
            })

driver.quit()

# ===== CSV 저장
df = pd.DataFrame(rows)
df.to_csv("saramin_developer_jobs_all.csv", index=False, encoding='utf-8-sig')
print(f"\n✅ 총 {len(rows)}개 공고 수집 완료. 'saramin_developer_jobs_all.csv' 저장됨.")
