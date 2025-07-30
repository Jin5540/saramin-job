from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from dotenv import load_dotenv
import os
import time

# ==================== 설정 ====================

load_dotenv()

# 쉼표로 구분된 문자열을 리스트로 변환
def get_list(key):
    value = os.getenv(key, "")
    return [item.strip() for item in value.split(",") if item.strip()]

CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH")
ID = os.getenv("ID")
PW = os.getenv("PW")
KEYWORDS_TO_EXCLUDE = get_list("KEYWORDS_TO_EXCLUDE")
KEYWORDS_TO_INCLUDE = get_list("KEYWORDS_TO_INCLUDE")
COMPANY_TO_EXCLUDE = get_list("COMPANY_TO_EXCLUDE")
TITLE_TO_EXCLUDE = get_list("TITLE_TO_EXCLUDE")
MAX_PAGES = int(os.getenv("MAX_PAGES", "5"))  # 기본값 5
# ==================== 브라우저 설정 ====================
options = Options()
options.add_argument("--start-maximized")
#options.add_argument("--headless=new")  # 또는 "--headless"
service = Service(CHROME_DRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 15)

# ==================== 로그인 ====================
driver.get("https://www.saramin.co.kr/zf_user/")
# 로그인 여부 확인
try:
    login_button = driver.find_element(By.CSS_SELECTOR, "a.btn_sign.signin")
    if login_button.is_displayed():
        login_button.click()

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.login-form")))

        driver.find_element(By.ID, "id").send_keys(ID)
        driver.find_element(By.ID, "password").send_keys(PW)
        driver.find_element(By.CSS_SELECTOR, "button.btn_login.BtnType.SizeML").click()

        time.sleep(3)
        print("✅ 로그인 수행 완료")
    else:
        print("🔓 로그인 버튼이 표시되지 않음 → 이미 로그인된 상태로 간주")

except NoSuchElementException:
    print("🔓 로그인 버튼이 없음 → 이미 로그인된 상태로 간주")
# ==================== 공고 크롤링 및 필터링 + 지원 ====================
for page in range(1, MAX_PAGES + 1):
    print(f"📄 페이지 {page} 확인 중...")

    url = f"https://www.saramin.co.kr/zf_user/jobs/list/job-category?page={page}&loc_mcd=101000&cat_mcls=2&exp_cd=1%2C2&exp_max=4&exp_none=y&edu_max=11&edu_none=y&panel_type=&search_optional_item=y&search_done=y&panel_count=y&preview=y"
    driver.get(url)
    try:
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "list_item")))
    except:
        print("❌ 공고 없음 또는 로딩 실패")
        continue

    job_cards = driver.find_elements(By.CSS_SELECTOR, "div.list_item")

    for job in job_cards:
        try:
            title_elem = job.find_element(By.CSS_SELECTOR, ".job_tit a.str_tit")
            company_elem = job.find_element(By.CSS_SELECTOR, ".company_nm .str_tit")
            sector_elems = job.find_elements(By.CSS_SELECTOR, ".job_sector span")
            apply_btns = job.find_elements(By.XPATH, ".//button[span[contains(@class, 'sri_btn_immediately')]]")
            if not apply_btns:
                print(f"⏭️ {company} - {title}: 지원 버튼 없음, 건너뜀")
                continue

            apply_btn = apply_btns[0]

            title = title_elem.text.strip()
            company = company_elem.text.strip()
            sectors = [s.text.strip() for s in sector_elems if s.text.strip() != "외"]

            if KEYWORDS_TO_EXCLUDE and any(kw in sectors for kw in KEYWORDS_TO_EXCLUDE):
                continue
            if COMPANY_TO_EXCLUDE and any(ex in company for ex in COMPANY_TO_EXCLUDE):
                continue
            if TITLE_TO_EXCLUDE and any(ex in title for ex in TITLE_TO_EXCLUDE):
                continue
            if KEYWORDS_TO_INCLUDE and not any(kw in title or any(kw in s for s in sectors) for kw in KEYWORDS_TO_INCLUDE):
                print(f"⏭️ {company} - {title}: 포함 키워드 없음 → 패스")
                continue

            print(f"🚀 지원 중: {company} - {title}")

            apply_btn.click()
            time.sleep(2)

            # 새 창 전환 (지원 창)
            driver.switch_to.window(driver.window_handles[-1])

            # 1~2. 개인정보 동의 및 입사지원 버튼 클릭
            try:
                WebDriverWait(driver, 5).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, "quick_apply_layer_frame"))
                )

                # 1. 개인정보 수집 동의 체크
                try:
                    area = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".inpChk.small"))
                    )
                    # label 클릭으로 체크
                    label = driver.find_element(By.CSS_SELECTOR, "label[for='chk_speed_matching']")
                    driver.execute_script("arguments[0].click();", label)
                    print("✅ 개인정보 수집 동의 체크 완료 (label 클릭)")

                except TimeoutException:
                    print("⏭️ 개인정보 수집 동의 영역 없음 (건너뜀)")
                except Exception as e:
                    print(f"⚠️ 개인정보 동의 처리 중 예외 발생: {type(e).__name__}")


                except TimeoutException:
                    print("⏭️ 동의 체크 항목 없음 (건너뜀)")
                except Exception as e:
                    print(f"⚠️ 동의 체크 중 예외 발생: {type(e).__name__}")

                # 2. 입사지원 가능 여부 판단 및 클릭
                try:
                    # 기업 전용 지원서 여부 확인
                    try:
                        download_btn = driver.find_element(By.CLASS_NAME, "download_form")
                        print("⏭️ 기업 전용 입사지원서 다운로드 버튼 있음 → 자동 지원 건너뜀")
                        raise Exception("전용서식")
                    except NoSuchElementException:
                        pass  # 다운로드 버튼이 없으면 계속 진행

                    # 이미 지원한 경우
                    try:
                        driver.find_element(By.XPATH, "//button[contains(text(), '입사지원현황 바로가기')]")
                        print("⏭️ 이미 지원한 공고 → 자동 패스")
                        raise Exception("이미지원")
                    except NoSuchElementException:
                        pass

                    # 지원 부문 선택 옵션 있는 경우 패스
                    try:
                        select_elem = driver.find_element(By.ID, "inpApply")
                        options = select_elem.find_elements(By.TAG_NAME, "option")
                        if len(options) > 1:
                            print("⏭️ 지원 부문 선택 옵션 존재 → 자동 패스")
                            raise Exception("선택옵션")
                    except NoSuchElementException:
                        print("✅ 지원 부문 선택 없음 → 계속 진행")
                    except Exception as e:
                        print(f"⚠️ 지원 부문 처리 오류: {type(e).__name__}")
                        raise

                    try:
                        area = driver.find_element(By.CLASS_NAME, "area_btn_form")
                        print("🧾 '지원 양식 선택' 박스 발견 → 사람인 이력서로 지원 시도")

                        buttons = area.find_elements(By.CSS_SELECTOR, "button.btn")
                        if buttons:
                            driver.execute_script("arguments[0].click();", buttons[0])
                            print("✅ 첫 번째 버튼 클릭 완료")

                            try:
                                WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, "area_btns"))
                                )
                                # 3. '이력서 선택 완료' 버튼 기다렸다가 클릭
                                confirm_button = driver.find_element(By.CSS_SELECTOR, "div.area_btns > button.btn_type_blue")

                                if confirm_button:
                                    driver.execute_script("arguments[0].click();", confirm_button)
                                    print("✅ '이력서 선택 완료' 버튼 클릭 완료")
                                else:
                                    print("⚠️ 이력서 선택 버튼이 존재하지 않음 → 패스")

                            except Exception as e:
                                print(f"⚠️ 이력서 선택 처리 중 예외 발생: {type(e).__name__}")
                        else:
                            print("⚠️ 버튼이 존재하지 않음 → 패스")

                    except NoSuchElementException:
                        print("⏭️ '지원 양식 선택' 박스 없음 → 해당 절차 건너뜀")
                    except Exception as e:
                        print(f"⚠️ 지원 양식 처리 중 예외 발생: {type(e).__name__}")

                    # 최종 입사지원 버튼 클릭
                    try:
                        area = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "area_btns"))
                        )
                        apply_btn = area.find_element(By.CSS_SELECTOR, "button.meta_pixel_event")
                        driver.execute_script("arguments[0].click();", apply_btn)
                        print("🎯 입사지원 버튼 클릭 완료")
                        print(f"🟢 {company} - {title} 지원 완료됨!")

                        driver.switch_to.default_content()
                        time.sleep(2)

                        # 추가: 로그인 레이어 닫기
                        try:
                            close_layer_btn = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.CLASS_NAME, "once_ly_close"))
                            )
                            driver.execute_script("arguments[0].click();", close_layer_btn)
                            print("✅ 지원 완료 레이어 닫기 완료")
                        except TimeoutException:
                            print("✅ 지원 완료 없음 또는 자동 닫힘 (건너뜀)")

                    except Exception as e:
                        print(f"⚠️ 입사지원 버튼 클릭 실패: {type(e).__name__}")
                        raise

                except Exception as e:
                    print(f"⏭️ 조건 불충족으로 지원 생략 → ({type(e).__name__})")

                    # 3. 팝업 닫기
                    try:
                        close_btn = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.CLASS_NAME, "btn_apply_form_close"))
                        )
                        driver.execute_script("arguments[0].click();", close_btn)
                        print("✅ 현재 입사지원 창 닫기 완료")
                    except (NoSuchElementException, TimeoutException):
                        print("✅ 닫을 팝업 없음 (건너뜀)")
                    except Exception as e:
                        print(f"⚠️ 닫기 처리 중 예외 발생: {type(e).__name__}")
                    finally:
                        driver.switch_to.default_content()
                        time.sleep(2)

            except (NoSuchElementException, TimeoutException):
                print("❌ 프레임을 찾을 수 없거나 시간 초과 → 패스")
                driver.switch_to.default_content()
                continue

            except Exception as e:
                print(f"⚠️ iframe 처리 중 예외 발생: {type(e).__name__} → 패스")
                driver.switch_to.default_content()
                continue

        except Exception as e:
            print(f"⚠️ 공고 찾기 중 예외 발생")
            continue
print("✅ 자동 지원 완료")
driver.quit()
