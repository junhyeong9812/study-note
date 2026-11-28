# python/python-web/09 — Selenium WebDriver (브라우저 자동화) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 첫 줄은 0, 마지막 줄에는 닿지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
첫 `print` 는 `0` 을 찍는다.
`find_element` 줄에서 (최대 10초 다시 찾아 본 뒤) `NoSuchElementException` 이 나서 마지막 `print` 에는 닿지 않는다.

**왜 그런가**
복수 `find_elements` 는 없으면 예외 없이 빈 리스트를 주므로 길이가 0 이다.
단수 `find_element` 는 없으면 예외를 던지고, 암시적 대기가 걸려 있어 그 전에 최대 10초 동안 다시 찾는다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」.

### 2. 두 바퀴, 8개 — 차례는 보장되지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
반복은 두 바퀴 돌고 `len(result)` 는 `8` 이다.
차례는 A, B, C … 라고 믿을 수 없다.

**왜 그런가**
- 1바퀴: `len(items)` 0 < 5 → A B C D 수집(4개) → 스크롤 → E F G H 가 붙어 높이가 바뀜 → `last_height` 갱신.
- 2바퀴: 4 < 5 → 이제 보이는 A~H 를 모두 수집(8개) → 스크롤 → 더 붙지 않아 높이가 같음 → `break`.
- 개수 검사는 반복 머리에서만 하므로 한 바퀴 안에서 5를 넘겨 8개가 된다.
- 반환은 `list(set)` 이고, Python 은 `set` 의 차례를 보장하지 않는다.

근거: 2-summary 「동작 방식 (9)」 · 「구현 세부사항 대 언어 보장」.

### 3. None 이 들어간다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`total` 은 `None` 이다.

**왜 그런가**
JS 에서 값을 Python 으로 돌려보내는 통로는 `return` 이다.
식만 적고 `return` 이 없으면 돌아올 값이 없어 Python 쪽은 `None` 을 받는다.
원본은 「`return` 을 쓰면 반환」까지만 말하고, `None` 이 된다는 쪽은 그 반대로 읽은 것이다 (원본에 근거 없음 — 추론).
근거: 2-summary 「동작 방식 (6)」.

### 4. 조건이 맞는 순간까지만, 겨냥한 요소에만 기다리기 때문이다

`time.sleep` 은 이미 준비됐어도 정해진 시간을 다 쓰고, 준비가 늦으면 모자란다.
`implicitly_wait` 는 드라이버 전체의 「찾기」에만 일괄로 걸려 「보이나 · 클릭할 수 있나 · 글자가 들어왔나」 같은 상태를 가리지 못한다.
`WebDriverWait` + `EC` 는 특정 요소의 특정 상태를 지정해, 맞는 순간 바로 돌아오고 상한을 넘기면 `TimeoutException` 으로 알려 준다.
원본 팁도 명시적 대기를 선호하라고 하며, 원본 예제처럼 둘을 섞으면 대기 시간을 읽기 어려워진다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1」 · 「어디서 틀리나 4」.

### 5. presence 만 참이 된다

`presence_of_element_located` 는 DOM 에 있기만 하면 숨김이어도 참이다.
`visibility_of_element_located` 는 화면에 보여야 하므로 거짓이다.
`element_to_be_clickable` 은 보이고 활성화돼야 하므로 역시 거짓이다.
그래서 `presence` 로 기다린 뒤 바로 클릭하면 실패할 수 있다.
근거: 2-summary 「동작 방식 (3)」 의 조건 표 · 「어디서 틀리나 3」.

### 6. 화면 크기가 달라져 배치가 바뀔 수 있기 때문이다

헤드리스에는 실제 창이 없어 크기를 정하지 않으면 기본 크기로 그려진다.
반응형 사이트는 그 크기에 맞춰 모바일 배치를 보여 줄 수 있고, 데스크톱에서 찾던 요소가 숨거나 위치가 바뀐다.
원본은 그래서 `--window-size=1920,1080` 을 명시한다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 2」.

### 7. 전환하지 않으면 찾지 못하고, 새 탭으로도 저절로 옮겨 가지 않는다

드라이버는 한 번에 한 문맥만 보므로, iframe 안의 요소는 `switch_to.frame` 으로 들어가기 전에는 찾을 수 없다(찾기가 실패한다).
다 쓴 뒤에는 `switch_to.default_content()` 로 원래 문서로 돌아온다.
`window.open` 으로 탭을 열어도 드라이버는 옛 탭을 그대로 보고 있으므로, 그 직후의 `find_element` 는 옛 탭을 뒤진다.
새 탭에서 일하려면 `driver.switch_to.window(driver.window_handles[-1])` 로 옮긴다.
근거: 2-summary 「동작 방식 (8)」.

### 8. until 은 조건 함수에 driver 하나만 넘겨 주기 때문이다

`wait.until(조건)` 은 조건을 `조건(driver)` 꼴로 되풀이 부른다 — 인자는 `driver` 하나뿐이다.
그런데 판정에는 「어느 요소(locator)」와 「어떤 클래스(class_name)」도 필요하다.
바깥 함수가 그 둘을 받아 기억한 안쪽 함수 `_predicate(driver)` 를 돌려주면, `until` 의 약속(인자 하나)에 맞으면서 필요한 값도 쓸 수 있다.
이것이 Python 의 클로저다.
근거: 2-summary 「동작 방식 (3)」 의 커스텀 조건 설명.

### 9. 열리지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
마우스는 움직이지 않고, hover 로 열리는 메뉴는 열리지 않는다.

**왜 그런가**
`ActionChains` 의 메서드는 동작을 목록에 쌓기만 한다.
쌓인 동작은 `perform()` 을 불러야 브라우저에서 실제로 일어난다.
근거: 2-summary 「동작 방식 (5)」.

### 10. 하나로 합쳐져 하나만 남는다

`items` 는 요소가 아니라 `el.text` 를 담는 `set` 이다.
텍스트가 같은 두 항목은 `set` 에서 같은 값이므로 한 번만 남는다.
「중복 제거」가 「같은 요소를 두 번 세지 않기」뿐 아니라 「다른 항목인데 글자가 같은 경우」까지 지워 버리는 것이다.
근거: 2-summary 「동작 방식 (9)」.

## 실습 정답

### 실습 1. Selenium 기능을 한 스크립트에 차례로 모으기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 옵션 다섯 가지 | `options.add_argument('--headless')` · `'--no-sandbox'` · `'--window-size=...'` · `'--disable-gpu'` · `'user-agent=...'` |
| 2. 드라이버 만들기 | `webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)` |
| 3. 암시적 대기 | `driver.implicitly_wait(10)` |
| 4. 이동 · URL · 제목 | `driver.get(...)`, `driver.current_url`, `driver.title` |
| 5. 여덟 가지 단일 찾기 | `driver.find_element(By.ID, ...)` … `By.PARTIAL_LINK_TEXT` |
| 6. 복수 찾기 | `driver.find_elements(By.CSS_SELECTOR, '.list-item')` + `for item in items` |
| 7. 대기 객체 | `wait = WebDriverWait(driver, 10)` |
| 8. 네 조건 | `EC.element_to_be_clickable` · `EC.visibility_of_element_located` · `EC.presence_of_element_located` · `EC.text_to_be_present_in_element` |
| 9. 커스텀 조건 | `element_has_class` 와 안쪽 `_predicate`, `wait.until(element_has_class((By.ID, 'loading'), 'done'))` |
| 10. 입력과 특수 키 | `username_input.clear()` · `send_keys('myuser')` · `send_keys(Keys.TAB)`, `password_input.send_keys(Keys.ENTER)` |
| 11. 클릭 | `button.click()` |
| 12. 셀렉트 세 방식 | `Select(...)` 의 `select_by_value` · `select_by_visible_text` · `select_by_index` |
| 13. 조건부 체크 | `if not checkbox.is_selected(): checkbox.click()` |
| 14. 복합 동작 | `ActionChains(driver)` 의 `move_to_element` · `drag_and_drop` · `double_click` · `context_click` + `.perform()` |
| 15. 스크롤 둘 | `execute_script('window.scrollTo(...)')`, `execute_script('arguments[0].scrollIntoView(true)', element)` |
| 16. 숨은 클릭 · 값 받기 | `execute_script('arguments[0].click()', hidden_button)`, `total = execute_script('return ...length')` |
| 17. 스크린샷 | `driver.save_screenshot('full_page.png')`, `element.screenshot('element_only.png')` |
| 18. iframe | `driver.switch_to.frame('iframe-name')`, `driver.switch_to.default_content()` |
| 19. 새 탭 | `window.open` 실행, `switch_to.window(driver.window_handles[-1])` · `[0]` |
| 20. 알림창 | `alert = driver.switch_to.alert`, `print(alert.text)`, `alert.accept()` |
| 21. 무한 스크롤 | `scroll_and_collect` 의 `items = set()`, `last_height`/`new_height` 비교, `time.sleep(2)`, `return list(items)` |
| 22. 종료와 정리 | `driver.quit()` 과 마지막 `print` 여덟 줄(제목 · 구분선 · 정리 여섯 줄) |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web/reference/selenium.py`

```python
# [웹 프레임워크] Selenium WebDriver (브라우저 자동화)
# 설명: Selenium으로 브라우저 제어, 요소 대기, 조작, 스크린샷
# 팁: WebDriverWait(명시적 대기)를 implicitly_wait(암시적 대기)보다 선호한다. 헤드리스 모드에서는 window-size를 명시적으로 설정해야 한다. execute_script()로 복잡한 DOM 조작이 가능하다. webdriver-manager가 드라이버 버전을 자동 관리한다.

# Selenium WebDriver - 브라우저 자동화
# pip install selenium webdriver-manager

# webdriver: 브라우저 드라이버 진입점
from selenium import webdriver
# By: 요소 선택자 종류 (ID, CSS, XPATH 등)
from selenium.webdriver.common.by import By
# Keys: 특수 키 상수 (ENTER, TAB 등)
from selenium.webdriver.common.keys import Keys
# ActionChains: 마우스/키보드 복합 동작
from selenium.webdriver.common.action_chains import ActionChains
# WebDriverWait: 명시적 대기 / Select: select 박스 헬퍼
from selenium.webdriver.support.ui import WebDriverWait, Select
# expected_conditions: 대기 조건 모음
from selenium.webdriver.support import expected_conditions as EC
# Selenium 예외들
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    StaleElementReferenceException
)
import time


# === 1. 드라이버 설정 ===
# Service: 드라이버 프로세스 관리
from selenium.webdriver.chrome.service import Service
# webdriver_manager: 크롬드라이버 버전 자동 관리
from webdriver_manager.chrome import ChromeDriverManager

# Chrome 옵션 객체
options = webdriver.ChromeOptions()
# 헤드리스: GUI 없이 실행 (서버 환경에 필수)
options.add_argument('--headless')           # 헤드리스 모드
# Docker/CI 환경에서 필요
options.add_argument('--no-sandbox')
# 헤드리스에서 화면 크기 명시 (반응형 사이트 대응)
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-gpu')
# User-Agent 설정 (봇 차단 회피)
options.add_argument(
    'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36'
)

# 드라이버 인스턴스 생성
driver = webdriver.Chrome(
    # ChromeDriverManager().install(): 적합한 드라이버 자동 다운로드
    service=Service(ChromeDriverManager().install()),
    options=options
)
# implicitly_wait: 모든 find_element에 적용되는 암시적 대기
driver.implicitly_wait(10)   # 암시적 대기 (전역)


# === 2. 페이지 이동 ===
# get(url): 페이지 이동 + 로드 완료 대기
driver.get('https://example.com')
# current_url: 현재 URL (리다이렉트 후 최종 URL)
print(f"현재 URL: {driver.current_url}")
print(f"페이지 제목: {driver.title}")


# === 3. 요소 찾기 ===
# 단일 요소
# find_element: 첫 매칭 요소 (없으면 NoSuchElementException)
element = driver.find_element(By.ID, 'username')
element = driver.find_element(By.NAME, 'password')
element = driver.find_element(By.CLASS_NAME, 'login-btn')
element = driver.find_element(By.TAG_NAME, 'h1')
# CSS_SELECTOR: 가장 유연하고 빠름
element = driver.find_element(By.CSS_SELECTOR, 'div.container > h1')
# XPATH: 텍스트 기반 검색 등 강력
element = driver.find_element(By.XPATH, '//div[@class="container"]/h1')
# LINK_TEXT: a 태그 정확히 일치하는 텍스트
element = driver.find_element(By.LINK_TEXT, '로그인')
# PARTIAL_LINK_TEXT: 부분 일치
element = driver.find_element(By.PARTIAL_LINK_TEXT, '로그')

# 복수 요소
# find_elements: 매칭 모두 (없으면 빈 리스트)
items = driver.find_elements(By.CSS_SELECTOR, '.list-item')
for item in items:
    print(item.text)


# === 4. 명시적 대기 (WebDriverWait) ===
# 특정 조건이 만족될 때까지만 대기 (효율적)
wait = WebDriverWait(driver, 10)   # 최대 10초 대기

# 요소가 클릭 가능할 때까지 대기
# element_to_be_clickable: 보이고 활성화된 상태
button = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, '.submit-btn'))
)

# 요소가 보일 때까지 대기
# visibility_of_element_located: DOM 존재 + 화면 표시
element = wait.until(
    EC.visibility_of_element_located((By.ID, 'result'))
)

# 요소가 존재할 때까지 대기 (DOM에 존재)
# presence_of_element_located: DOM에만 존재 (숨김 가능)
element = wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, '.loaded'))
)

# 텍스트가 포함될 때까지 대기
wait.until(
    EC.text_to_be_present_in_element((By.ID, 'status'), '완료')
)

# 커스텀 대기 조건
# 클로저: locator/class_name을 캡쳐하여 predicate 함수 반환
def element_has_class(locator, class_name):
    def _predicate(driver):
        element = driver.find_element(*locator)
        return class_name in element.get_attribute('class')
    return _predicate

wait.until(element_has_class((By.ID, 'loading'), 'done'))


# === 5. 요소 조작 ===
# 텍스트 입력
username_input = driver.find_element(By.ID, 'username')
# clear: 기존 입력값 제거
username_input.clear()                    # 기존 텍스트 지우기
# send_keys: 키 입력 시뮬레이션
username_input.send_keys('myuser')        # 텍스트 입력
# 특수 키도 send_keys로 전송
username_input.send_keys(Keys.TAB)        # 탭 키

password_input = driver.find_element(By.ID, 'password')
password_input.send_keys('mypass')
password_input.send_keys(Keys.ENTER)      # 엔터 키

# 클릭
button = driver.find_element(By.CSS_SELECTOR, '.btn-submit')
# click: 요소 클릭 (이벤트 발생)
button.click()

# 셀렉트 박스
# Select: <select> 요소 전용 헬퍼
select_element = Select(driver.find_element(By.ID, 'country'))
select_element.select_by_value('kr')       # value 속성
select_element.select_by_visible_text('한국')  # 표시 텍스트
select_element.select_by_index(2)           # 인덱스

# 체크박스 / 라디오
checkbox = driver.find_element(By.ID, 'agree')
# is_selected: 현재 선택 상태 확인
if not checkbox.is_selected():
    checkbox.click()


# === 6. ActionChains (복합 동작) ===
# ActionChains: 여러 동작을 체이닝하고 한 번에 실행
action = ActionChains(driver)

# 마우스 hover
menu = driver.find_element(By.CSS_SELECTOR, '.dropdown-menu')
# move_to_element: 마우스 호버 / perform: 실제 실행
action.move_to_element(menu).perform()

# 드래그 앤 드롭
source = driver.find_element(By.ID, 'draggable')
target = driver.find_element(By.ID, 'droppable')
action.drag_and_drop(source, target).perform()

# 더블클릭, 우클릭
action.double_click(element).perform()
action.context_click(element).perform()


# === 7. JavaScript 실행 ===
# 스크롤
# execute_script: 임의 JS 실행 - DOM 조작 강력함
driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
# arguments[0]: Python에서 전달한 첫 인자
driver.execute_script('arguments[0].scrollIntoView(true)', element)

# 숨겨진 요소 클릭 (Selenium click이 안 될 때 우회)
driver.execute_script('arguments[0].click()', hidden_button)

# 값 추출
# return을 사용하면 결과를 Python으로 반환
total = driver.execute_script('return document.querySelectorAll(".item").length')


# === 8. 스크린샷 ===
# save_screenshot: 전체 페이지 캡처 (디버깅 필수)
driver.save_screenshot('full_page.png')            # 전체 페이지
# WebElement.screenshot: 특정 요소만 캡처
element.screenshot('element_only.png')              # 특정 요소만


# === 9. iframe / 탭 전환 ===
# iframe
# frame 내부 요소를 다루려면 컨텍스트 전환 필수
driver.switch_to.frame('iframe-name')        # iframe 진입
driver.switch_to.default_content()           # 원래 페이지로

# 새 탭
driver.execute_script('window.open("https://example.com")')
# window_handles: 현재 열린 모든 탭 핸들
driver.switch_to.window(driver.window_handles[-1])  # 새 탭으로
driver.switch_to.window(driver.window_handles[0])   # 원래 탭으로

# Alert (alert/confirm/prompt 다이얼로그)
alert = driver.switch_to.alert
print(alert.text)
# accept: 확인 버튼
alert.accept()     # 확인
# alert.dismiss()  # 취소


# === 10. 무한 스크롤 크롤링 패턴 ===
# 무한 스크롤 페이지에서 모든 항목 수집
def scroll_and_collect(driver, css_selector, max_items=100):
    # set으로 중복 제거
    items = set()
    # 현재 페이지 높이 측정
    last_height = driver.execute_script('return document.body.scrollHeight')

    while len(items) < max_items:
        # 현재 보이는 요소 수집
        elements = driver.find_elements(By.CSS_SELECTOR, css_selector)
        for el in elements:
            items.add(el.text)

        # 페이지 끝까지 스크롤
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(2)  # 로딩 대기

        # 새 컨텐츠 로드 확인 (높이 변화 없으면 종료)
        new_height = driver.execute_script('return document.body.scrollHeight')
        if new_height == last_height:
            break
        last_height = new_height

    return list(items)


# 종료
# quit: 모든 윈도우 닫고 드라이버 프로세스 종료 (close는 현재 창만)
driver.quit()

print("Selenium 핵심 정리")
print("="*50)
print("By.CSS_SELECTOR / By.XPATH: 요소 찾기")
print("WebDriverWait + EC: 명시적 대기 (동적 페이지 필수)")
print("ActionChains: hover, 드래그, 더블클릭 등 복합 동작")
print("execute_script(): JavaScript 직접 실행")
print("save_screenshot(): 디버깅용 스크린샷")
print("headless 모드: 서버 환경에서 UI 없이 실행")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `selenium` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**
- 드라이버를 세우는 1단계와 `quit` 하는 마지막 단계가 스크립트의 앞뒤를 감싼다 — 나머지는 모두 그 사이에서 `driver` 를 통해 브라우저에 지시하는 일이다.
- 대기는 `wait.until(조건)` 하나의 꼴로 통일되고, 조건만 바꿔 끼운다 — 커스텀 조건도 「`driver` 를 받는 함수」면 된다.
- `ActionChains` 는 매번 `.perform()` 까지 써야 하고, `execute_script` 에서 값을 받으려면 `return` 을 쓴다.
- 문맥 전환은 「들어가기 · 돌아오기」를 짝으로 둔다(`frame` ↔ `default_content`, `window_handles[-1]` ↔ `[0]`).
- 정답 코드는 쓰는 법을 차례로 보인 것이다 — `hidden_button` 은 정의되지 않았고, example.com 에는 3단계 이후의 요소가 없으므로 실제로 돌리려면 대상 페이지와 변수를 맞춰야 한다.
- 정답 코드는 암시적 대기와 명시적 대기를 함께 건다 — 팁대로라면 명시적 대기 하나로 가는 편이 대기 시간을 읽기 쉽다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `selenium` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
