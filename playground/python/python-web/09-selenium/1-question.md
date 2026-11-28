# python/python-web/09 — Selenium WebDriver (브라우저 자동화) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 없는 id 로 두 찾기 메서드를 부르면 (예측)

```python
# 질문용 발췌 — 페이지에 id="ghost" 인 요소는 없다
driver.implicitly_wait(10)
a = driver.find_elements(By.ID, 'ghost')
print(len(a))
b = driver.find_element(By.ID, 'ghost')
print('여기까지 오나?')
```

- 첫 번째 `print` 는 무엇을 찍는가?
- 마지막 `print` 까지 실행이 닿는가?

### 2. 무한 스크롤 수집을 max_items=5 로 돌리면 (예측)

```python
# 질문용 발췌 — 가정한 페이지:
# 처음엔 항목 A B C D (4개). 맨 아래로 스크롤하면 E F G H 가 붙고 높이가 커진다.
# 그 뒤로는 아무리 스크롤해도 더 붙지 않는다. 텍스트는 모두 다르다.
result = scroll_and_collect(driver, '.item', max_items=5)
print(len(result))
```

- `while` 반복은 몇 바퀴 돌고, `len(result)` 는 몇인가?
- `result` 의 차례는 A, B, C … 순서라고 믿어도 되는가?

### 3. return 없는 execute_script (예측)

- `total = driver.execute_script('document.querySelectorAll(".item").length')` 처럼 `return` 을 빠뜨리면 `total` 에는 무엇이 들어가는가?

### 4. 명시적 대기를 암시적 대기보다 선호하는 까닭 (왜)

- 동적 페이지에서 `WebDriverWait` + `EC` 가 `implicitly_wait` 이나 `time.sleep` 보다 나은 까닭은 무엇인가?

### 5. 숨김 상태의 버튼과 세 가지 대기 조건 (경계)

- DOM 에는 있지만 화면에 숨겨진 버튼에 대해 `presence_of_element_located` · `visibility_of_element_located` · `element_to_be_clickable` 중 어느 것이 참이 되는가?

### 6. 헤드리스에서 창 크기를 적어 주는 까닭 (왜)

- 헤드리스 모드에 `--window-size` 를 명시하지 않으면 무엇이 어긋날 수 있는가?

### 7. iframe 안의 요소와 새 탭의 요소 (경계)

- iframe 안의 요소를 `switch_to.frame` 없이 찾으면 어떻게 되며, 다 쓴 뒤에는 무엇을 불러야 하는가?
- `window.open` 으로 새 탭을 연 직후의 `find_element` 는 어느 탭을 뒤지는가?

### 8. 커스텀 대기 조건과 클로저 (연결)

- `element_has_class` 가 함수를 반환하는 꼴(클로저)이어야 하는 까닭은 `wait.until` 의 어떤 약속 때문인가?

### 9. perform 을 빠뜨린 ActionChains (예측)

- `action.move_to_element(menu)` 까지만 쓰고 `perform()` 을 부르지 않으면 드롭다운 메뉴는 열리는가?

### 10. 텍스트로 중복을 없애는 수집의 빈틈 (경계)

- `scroll_and_collect` 에서 서로 다른 두 항목의 텍스트가 똑같으면 결과에 어떻게 남는가?

## 실습

### 실습 1. Selenium 기능을 한 스크립트에 차례로 모으기

**만들 것** — 헤드리스 크롬을 띄워 이동 · 찾기 · 대기 · 조작 · 복합 동작 · JS 실행 · 스크린샷 · 문맥 전환 · 무한 스크롤 수집까지 한 파일에 차례로 쓰고, 마지막에 드라이버를 끝낸 뒤 핵심 정리를 찍는 스크립트.

**준비물** — Chrome 브라우저, `pip install selenium webdriver-manager`, 드라이버를 받기 위한 네트워크. 3단계부터 쓰는 `username` · `country` · `draggable` 같은 요소는 가상의 로그인 · 데모 페이지를 가정한 것이다.

**요구 조건**

1단계 — 드라이버 설정
1. `ChromeOptions` 에 헤드리스, 샌드박스 끄기, 창 크기, GPU 끄기, User-Agent 지정 옵션을 넣는다.
2. `ChromeDriverManager().install()` 로 받은 드라이버를 `Service` 로 감싸 `webdriver.Chrome` 을 만든다.
3. 드라이버에 10초 암시적 대기를 건다.

2단계 — 페이지 이동
4. `https://example.com` 으로 가서 현재 URL 과 제목을 찍는다.

3단계 — 요소 찾기
5. `By` 의 여덟 가지 방식(ID · NAME · CLASS_NAME · TAG_NAME · CSS_SELECTOR · XPATH · LINK_TEXT · PARTIAL_LINK_TEXT)으로 단일 요소를 한 번씩 찾는다.
6. `.list-item` 을 복수로 찾아 각 텍스트를 찍는다.

4단계 — 명시적 대기
7. 최대 10초짜리 `WebDriverWait` 를 만든다.
8. 클릭 가능 · 보임 · 존재 · 텍스트 포함(`status` 에 「완료」) 네 조건으로 각각 기다린다.
9. 로케이터와 클래스 이름을 받아 「그 요소의 class 에 이름이 들어 있나」를 판정하는 함수를 돌려주는 `element_has_class` 를 만들고, `loading` 요소가 `done` 클래스를 가질 때까지 기다린다.

5단계 — 요소 조작
10. `username` 칸을 비우고 글자를 넣은 뒤 TAB 키를, `password` 칸에는 글자를 넣은 뒤 ENTER 키를 보낸다.
11. 제출 버튼을 클릭한다.
12. `country` 셀렉트 박스를 value · 보이는 텍스트 · 인덱스 세 방식으로 고른다.
13. `agree` 체크박스가 선택되지 않았을 때만 클릭한다.

6단계 — ActionChains
14. 메뉴에 hover, `draggable` → `droppable` 드래그 앤 드롭, 더블클릭, 우클릭을 각각 실행한다.

7단계 — JavaScript 실행
15. 문서 맨 아래로 스크롤하고, 넘긴 요소가 보이게 스크롤한다.
16. 숨겨진 버튼을 JS 로 클릭하고, `.item` 개수를 JS 에서 받아 변수에 담는다.

8단계 — 스크린샷
17. 화면 전체와 요소 하나를 각각 파일로 저장한다.

9단계 — 문맥 전환
18. iframe 에 들어갔다가 원래 문서로 돌아온다.
19. JS 로 새 탭을 열고, 새 탭으로 갔다가 원래 탭으로 돌아온다.
20. 알림창의 글자를 찍고 확인을 누른다.

10단계 — 무한 스크롤 수집
21. `scroll_and_collect(driver, css_selector, max_items=100)` 을 만든다 — 텍스트를 `set` 에 모으고, 맨 아래로 스크롤한 뒤 쉬고, 문서 높이가 그대로면 멈추며, 리스트로 돌려준다.

11단계 — 종료
22. 드라이버를 완전히 끝내고, 핵심 정리 여섯 줄을 구분선과 함께 찍는다.

**시작 코드**

```python
# selenium_practice.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    StaleElementReferenceException
)
import time

# === 1. 드라이버 설정 ===
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

options = webdriver.ChromeOptions()
# TODO: 헤드리스 / no-sandbox 옵션
options.add_argument('--window-size=1920,1080')   # 크기 값은 미리 채워 둠
# TODO: GPU 끄기
options.add_argument(
    'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36'
)
driver = None  # TODO: Service + ChromeDriverManager 로 드라이버 만들기
# TODO: 암시적 대기 10초

# === 2. 페이지 이동 ===
# TODO: example.com 으로 이동, URL · 제목 출력

# === 3. 요소 찾기 ===
# TODO: By 여덟 가지로 element 찾기
# TODO: '.list-item' 복수로 찾아 텍스트 출력

# === 4. 명시적 대기 ===
# TODO: wait 만들기, 네 가지 EC 조건으로 기다리기

def element_has_class(locator, class_name):
    # TODO: driver 를 받는 판정 함수를 만들어 돌려주기
    pass

# TODO: wait.until(element_has_class((By.ID, 'loading'), 'done'))

# === 5. 요소 조작 ===
# TODO: username / password 입력, 버튼 클릭, Select 세 방식, 체크박스

# === 6. ActionChains ===
# TODO: hover, 드래그 앤 드롭, 더블클릭, 우클릭 — 각각 실행까지

# === 7. JavaScript 실행 ===
# TODO: 맨 아래 스크롤, 요소로 스크롤, 숨은 버튼 클릭, .item 개수 받기

# === 8. 스크린샷 ===
# TODO: 전체 / 요소만

# === 9. iframe / 탭 전환 ===
# TODO: iframe 진입·복귀, 새 탭 열고 오가기, alert 글자 출력 후 확인

# === 10. 무한 스크롤 크롤링 패턴 ===
def scroll_and_collect(driver, css_selector, max_items=100):
    items = set()
    # TODO: 처음 높이 재기
    # TODO: while 반복 — 수집 → 스크롤 → time.sleep → 높이 비교
    return list(items)

# 종료
# TODO: 드라이버 완전 종료

print("Selenium 핵심 정리")
print("="*50)
# TODO: 핵심 정리 여섯 줄 출력
```

**확인 방법** — `python selenium_practice.py` 로 돌린다. 2단계까지는 example.com 에서 URL 과 제목이 찍히는지 본다. 3단계부터는 해당 id · 클래스를 가진 실제 대상 페이지로 바꿔야 끝까지 진행되므로, 정답 코드와 단계별 구조가 맞는지 대조한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
