# python/python-web/09 — Selenium WebDriver (브라우저 자동화) — 정리 (힌트)

> 출처 — study-site 항목 `python/selenium`(항목 데이터 `data/python/web-frameworks.json`) · 정답 코드 study-practice `python/python-web/reference/selenium.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `selenium` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**Selenium 은 「전화로 지시받아 움직이는 현장 직원」이다.**
나는 사무실(Python 스크립트)에서 전화로 「이 버튼 눌러」「저 칸에 글자 써」라고 말한다.
가운데의 통역사(드라이버)가 그 말을 현장 직원(브라우저)이 알아듣는 말로 바꿔 전한다.
직원은 실제 페이지에서 손을 움직이고, 본 것을 다시 전화로 알려 준다.
Selenium WebDriver 도 똑같은 구조다.

> **WebDriver** — 프로그램이 브라우저를 원격으로 조종하게 해 주는 인터페이스.\
> 예: `driver.get(url)` 한 줄로 크롬이 그 주소로 간다.

> **드라이버** — 스크립트와 실제 브라우저 사이에서 명령을 옮기는 별도 프로그램(크롬이면 ChromeDriver).\
> 예: `ChromeDriverManager().install()` 이 맞는 버전의 ChromeDriver 를 받아 온다.

| 비유 | 실체 |
|---|---|
| 사무실의 나 | Python 스크립트 |
| 통역사 | ChromeDriver (드라이버 프로세스) |
| 현장 직원 | Chrome 브라우저 |
| 전화로 하는 지시 | `driver.find_element(...)`, `.click()` 같은 호출 |
| 직원의 보고 | 돌아오는 요소 · 텍스트 · 값 · 예외 |
| 불 꺼진 현장에서 일하기 | 헤드리스 모드 |

```text
Python 스크립트 ──명령──▶ ChromeDriver ──조종──▶ Chrome 브라우저
  (driver.click())       (드라이버 프로세스)       (실제 페이지)
        ◀────────── 요소 · 텍스트 · 값 · 예외 ──────────┘
```

> **헤드리스** — 화면 창을 띄우지 않고 브라우저를 돌리는 방식.\
> 예: `options.add_argument('--headless')` 로 서버에서 UI 없이 크롬을 띄운다.

## 이 주제가 답하려는 질문

1. 스크립트는 페이지 안의 특정 요소를 어떻게 집어내나?
2. 자바스크립트로 늦게 그려지는 요소(동적 페이지)를 어떻게 기다리나?
3. 클릭 · 입력만으로 안 되는 일(hover, 드래그, 스크롤, 숨은 요소)은 어떻게 하나?
4. iframe · 새 탭 · 알림창처럼 「다른 문맥」에 있는 것은 어떻게 다루나?

## 동작 방식

### (1) 드라이버 세우기 — 옵션 · 서비스 · 암시적 대기

**언제 쓰나** — 스크립트 맨 처음 한 번.
브라우저를 어떤 모습으로 띄울지 정하고 드라이버를 연결한다.

```text
ChromeOptions()
  ├ '--headless'              → 창 없이
  ├ '--no-sandbox'            → Docker/CI 환경용
  ├ '--window-size=1920,1080' → 헤드리스 화면 크기 명시
  ├ '--disable-gpu'
  └ 'user-agent=...'          → 브라우저 신분 문자열 바꾸기
ChromeDriverManager().install() → 드라이버 파일 경로 → Service(경로)
          ↓
webdriver.Chrome(service=..., options=...)  → driver
driver.implicitly_wait(10)  → 이후 find_element 마다 최대 10초 다시 찾아 봄
```

- `ChromeOptions` 에 `add_argument` 로 명령줄 옵션을 하나씩 쌓는다.
- 헤드리스는 화면이 없으므로 창 크기를 직접 정해야 반응형 사이트가 데스크톱 배치로 그려진다.
- `webdriver-manager` 는 설치된 크롬에 맞는 드라이버를 내려받고 그 경로를 돌려준다 — 드라이버 버전을 손으로 맞출 필요가 없어진다.
- `Service` 는 드라이버 프로세스를 띄우고 관리한다.
- `implicitly_wait(10)` 은 드라이버 전체에 걸리는 설정이다 — 이후 모든 `find_element` 가 요소를 못 찾으면 최대 10초 동안 다시 찾는다.

> **암시적 대기** — 드라이버 전체에 걸어 두는 「요소 찾기 재시도 시간」.\
> 예: `driver.implicitly_wait(10)` 뒤에는 모든 `find_element` 가 최대 10초 기다린다.

### (2) 페이지 이동과 요소 찾기

**언제 쓰나** — 어떤 주소로 가서 그 안의 요소를 손에 쥘 때.

```text
driver.get('https://example.com')   → 이동 + 로드 완료까지 기다림
driver.current_url / driver.title   → 리다이렉트 후 최종 URL, 제목

find_element(By.ID, 'username')
  있음 → 첫 번째로 맞는 WebElement 하나
  없음 → NoSuchElementException

find_elements(By.CSS_SELECTOR, '.list-item')
  있음 → [WebElement, WebElement, ...]
  없음 → []   (예외 없음)
```

- `get` 은 이동한 뒤 페이지 로드가 끝날 때까지 돌아오지 않는다.
- `current_url` 은 처음 준 주소가 아니라 리다이렉트를 거친 최종 주소다.
- 단수 `find_element` 는 첫 매칭 하나만 주고, 없으면 예외를 던진다.
- 복수 `find_elements` 는 맞는 것을 모두 리스트로 주고, 없으면 빈 리스트를 준다.
- 「있는지 없는지만 보고 싶다」면 복수형의 길이를 보는 편이 예외 처리보다 간단하다.

> **로케이터** — `(By.종류, '값')` 꼴의 튜플로, 「어떤 방법으로 무엇을 찾나」를 담는다.\
> 예: `(By.ID, 'result')`.

### (3) 기다리기 — 명시적 대기와 커스텀 조건

**언제 쓰나** — 버튼 · 결과 영역이 자바스크립트로 늦게 나타나는 동적 페이지.
`time.sleep` 처럼 무조건 몇 초를 쉬지 않고 「조건이 맞는 순간」까지만 기다린다.

```text
wait = WebDriverWait(driver, 10)
wait.until(조건)
   │
   ├─ 조건(driver) 호출 ─▶ 거짓/예외 → 잠깐 쉬고 다시 호출
   │                    ─▶ 참인 값  → until 이 그 값을 돌려줌 (보통 요소)
   └─ 10초가 지나도 거짓 → TimeoutException
```

- `WebDriverWait(driver, 10)` 은 「최대 10초」라는 상한만 정한 대기 객체다.
- `until(조건)` 은 조건 함수를 `driver` 를 넣어 되풀이 부르고, 참인 값이 나오면 바로 그 값을 돌려준다.
- 상한을 넘기면 `TimeoutException` 이 난다.

`expected_conditions`(`EC`) 의 조건들은 엄격함이 다르다.

| 조건 | 언제 참이 되나 |
|---|---|
| `presence_of_element_located` | DOM 에 있기만 하면 (숨김 상태여도) |
| `visibility_of_element_located` | DOM 에 있고 화면에 보일 때 |
| `element_to_be_clickable` | 보이고 활성화되어 클릭할 수 있을 때 |
| `text_to_be_present_in_element` | 요소 텍스트에 주어진 문자열이 들어 있을 때 |

커스텀 조건은 「`driver` 를 받아 참/거짓을 돌려주는 함수」면 된다.
원본은 클로저로 만든다.

```python
def element_has_class(locator, class_name):
    def _predicate(driver):                       # until 이 되풀이 부를 함수
        element = driver.find_element(*locator)
        return class_name in element.get_attribute('class')
    return _predicate                             # locator, class_name 을 기억한 채 반환
```

- 바깥 함수는 `locator` 와 `class_name` 을 받아 안쪽 함수를 돌려준다.
- 안쪽 함수는 그 두 값을 기억(캡처)하고 있어, `until` 이 `driver` 하나만 넘겨도 무엇을 볼지 안다.
- `*locator` 는 튜플 `(By.ID, 'loading')` 을 풀어 두 인자로 넘긴다.

> **명시적 대기** — 특정 조건을 지정해 그 조건이 맞을 때까지만 기다리는 방식.\
> 예: `wait.until(EC.visibility_of_element_located((By.ID, 'result')))`.

> **클로저** — 바깥 함수의 변수를 기억한 채 반환되는 안쪽 함수.\
> 예: `element_has_class(...)` 가 돌려주는 `_predicate`.

### (4) 요소 조작 — 입력 · 클릭 · 셀렉트 · 체크박스

**언제 쓰나** — 로그인 폼 채우기, 버튼 누르기, 드롭다운 고르기.

```text
input.clear()              → 기존 값 지움
input.send_keys('myuser')  → 글자를 한 자씩 치는 것처럼 입력
input.send_keys(Keys.TAB)  → 특수 키도 같은 메서드로
button.click()             → 클릭 이벤트 발생
Select(<select 요소>)      → select_by_value / select_by_visible_text / select_by_index
checkbox.is_selected()     → 이미 체크됐으면 click 을 건너뜀
```

- `send_keys` 는 키 입력을 흉내 내므로 글자와 `Keys.ENTER` · `Keys.TAB` 같은 특수 키를 똑같이 보낸다.
- `Select` 는 `<select>` 요소 전용 도우미다 — `value` 속성, 화면에 보이는 글자, 순서 번호 셋 중 하나로 고른다.
- 체크박스에 `click` 을 무조건 부르면 이미 체크된 것이 풀린다 — 그래서 `is_selected()` 로 먼저 확인한다.

### (5) ActionChains — 여러 동작을 쌓았다가 한 번에

**언제 쓰나** — hover 해야 열리는 메뉴, 드래그 앤 드롭, 더블클릭, 우클릭.

```text
action = ActionChains(driver)
action.move_to_element(menu)   → 목록에 「hover」 적어 둠 (아직 안 움직임)
      .perform()               → 적어 둔 동작을 실제로 실행
action.drag_and_drop(source, target).perform()
action.double_click(el).perform() / action.context_click(el).perform()
```

- `ActionChains` 의 메서드는 동작을 바로 하지 않고 목록에 쌓는다.
- `perform()` 을 불러야 쌓인 동작이 브라우저에서 실제로 일어난다.
- 메서드가 자기 자신을 돌려주므로 `.move_to_element(...).perform()` 처럼 이어 쓴다.

### (6) execute_script — 브라우저 안에서 JS 직접 실행

**언제 쓰나** — 스크롤, 일반 `click` 이 막힌 숨은 요소 클릭, DOM 에서 값 바로 뽑기.

```text
driver.execute_script('JS 코드', 인자0, 인자1, ...)
   JS 안에서 arguments[0] = 인자0 (WebElement 면 DOM 요소로 넘어감)
   'return ...' 이 있으면 → 그 값이 Python 으로 돌아옴
   return 이 없으면       → 돌아올 값이 없어 None
```

- Python 에서 넘긴 인자는 JS 안에서 `arguments[0]`, `arguments[1]` … 로 받는다.
- `'arguments[0].scrollIntoView(true)'` 는 넘긴 요소가 보이게 스크롤한다.
- `'arguments[0].click()'` 은 브라우저의 DOM `click` 을 직접 불러, Selenium `click` 이 안 될 때 우회한다.
- 원본은 「`return` 을 쓰면 결과를 Python 으로 반환한다」고 적는다 — 거꾸로 `return` 을 빠뜨리면 Python 쪽은 `None` 을 받는다.

### (7) 스크린샷

**언제 쓰나** — 헤드리스로 돌려 화면을 볼 수 없을 때, 무엇이 그려졌는지 확인하는 디버깅.

- `driver.save_screenshot('full_page.png')` 는 브라우저 화면을 파일로 저장한다(원본 주석은 「전체 페이지」).
- `element.screenshot('element_only.png')` 는 그 요소 영역만 저장한다.

### (8) 문맥 전환 — iframe · 탭 · 알림창

**언제 쓰나** — 찾으려는 요소가 iframe 안에 있거나, 새 탭이 열렸거나, `alert` 창이 떴을 때.

```text
[원래 문서] ──switch_to.frame('iframe-name')──▶ [iframe 내부 문서]
     ◀────────switch_to.default_content()──────────┘

window.open(...)  → 탭은 늘지만 driver 는 아직 옛 탭을 보고 있음
driver.window_handles      → [옛 탭, 새 탭]
switch_to.window(handles[-1]) → 새 탭으로
switch_to.window(handles[0])  → 원래 탭으로

switch_to.alert → alert.text / alert.accept() / alert.dismiss()
```

- 드라이버는 한 번에 한 문맥만 본다.
- iframe 안의 요소는 `switch_to.frame` 으로 들어가기 전에는 찾을 수 없고, 다 쓰면 `default_content()` 로 돌아온다.
- 새 탭을 열어도 드라이버가 저절로 옮겨 가지 않는다 — `window_handles` 에서 핸들을 골라 `switch_to.window` 로 옮긴다.
- 알림창(`alert` · `confirm` · `prompt`)은 `switch_to.alert` 로 잡고 `accept`(확인)나 `dismiss`(취소)로 닫는다.

> **윈도우 핸들** — 열린 탭(창) 하나를 가리키는 식별 문자열.\
> 예: `driver.window_handles[-1]` 은 목록의 마지막 핸들이다.

### (9) 무한 스크롤 수집 패턴

**언제 쓰나** — 끝까지 내려야 다음 항목이 붙는 피드형 페이지.

```text
last_height = 문서 높이
반복 (모은 개수 < max_items 인 동안):
   보이는 요소 텍스트를 set 에 넣음 (중복 제거)
   맨 아래로 스크롤 → 2초 쉼
   new_height = 문서 높이
   new_height == last_height → 새로 붙은 게 없음 → 멈춤
   아니면 last_height = new_height
list(set) 반환
```

- 높이가 그대로면 더 불러올 것이 없다고 보고 멈춘다.
- 개수 검사는 반복을 「시작할 때」만 한다 — 한 바퀴 안에서 한꺼번에 많이 모으면 `max_items` 를 넘긴 채로 끝날 수 있다.
- `set` 은 텍스트로 중복을 없앤다 — 다른 항목이라도 텍스트가 같으면 하나로 합쳐진다.
- 반환은 `list(set)` 이라 페이지에 나온 차례를 지키지 않는다.

### (10) 끝내기

- `driver.quit()` 은 모든 창을 닫고 드라이버 프로세스까지 끝낸다.
- `driver.close()` 는 현재 창 하나만 닫는다.
- 프로세스를 남기지 않으려면 끝에서 `quit()` 을 부른다.

## 문법 — 형태와 규칙

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--window-size=1280,800')
driver = webdriver.Chrome(options=options)
driver.get('https://example.com')
h1 = WebDriverWait(driver, 5).until(
    EC.visibility_of_element_located((By.TAG_NAME, 'h1')))
print(h1.text)
driver.quit()
```

```bash
pip install selenium webdriver-manager
```

| `By` 종류 | 무엇으로 찾나 |
|---|---|
| `By.ID` | `id` 속성 |
| `By.NAME` | `name` 속성 |
| `By.CLASS_NAME` | 클래스 이름 하나 |
| `By.TAG_NAME` | 태그 이름 |
| `By.CSS_SELECTOR` | CSS 선택자 — 원본은 「가장 유연하고 빠름」이라 적는다 |
| `By.XPATH` | XPath — 텍스트 기반 검색 등에 강하다 |
| `By.LINK_TEXT` | `<a>` 의 텍스트와 정확히 일치 |
| `By.PARTIAL_LINK_TEXT` | `<a>` 의 텍스트 일부 일치 |

- 로케이터는 `find_element(By.X, '값')` 처럼 두 인자로, `EC` 조건에는 `(By.X, '값')` 튜플 하나로 넘긴다.
- `wait.until` 의 반환값은 조건이 돌려준 값이다 — 요소 조건이면 그 요소를 바로 쓸 수 있다.
- `ActionChains` 는 끝에 `.perform()` 이 있어야 실행된다.
- `execute_script` 에서 값을 받으려면 JS 안에 `return` 을 쓴다.
- 문맥을 바꾼 뒤에는 원래 문맥으로 되돌리는 호출을 짝으로 둔다.

## 어디서 틀리나

### 1. 암시적 대기와 명시적 대기를 섞는다

원본 팁은 「`WebDriverWait`(명시적 대기)를 `implicitly_wait`(암시적 대기)보다 선호한다」이다.
그런데 원본 예제는 `implicitly_wait(10)` 을 건 드라이버에 `WebDriverWait(driver, 10)` 도 함께 쓴다.
원본의 주장(두 방식 병용) → 의심스러운 까닭: 명시적 대기의 조건 함수 안에서 `find_element` 가 다시 암시적 대기로 최대 10초를 묶일 수 있어, 전체 대기 시간을 읽기 어려워진다(정확한 합산 방식은 확인 필요).
암시적 대기는 「모든 찾기」에 일괄로 걸리고, 명시적 대기는 「이 요소의 이 상태」만 겨냥한다 — 그래서 명시적 대기가 동적 페이지에 더 맞다.

### 2. 헤드리스에서 창 크기를 안 정한다

원본 팁: 헤드리스 모드에서는 `window-size` 를 명시적으로 설정해야 한다.
창 크기를 정하지 않으면 기본 크기로 그려져 반응형 사이트가 모바일 배치를 보여 줄 수 있고, 데스크톱에서 보던 요소가 숨겨지거나 위치가 달라진다.

### 3. `presence` 로 기다리고 바로 클릭한다

`presence_of_element_located` 는 숨김 요소에도 참이 된다.
클릭하려면 `element_to_be_clickable`, 보여야 한다면 `visibility_of_element_located` 를 쓴다.

### 4. `time.sleep` 으로 고정 시간 쉬기

원본의 무한 스크롤 패턴은 `time.sleep(2)` 로 로딩을 기다린다.
2초 안에 못 불러오면 높이가 그대로라 「끝났다」고 잘못 멈춘다.
반대로 빨리 불러와도 매번 2초를 다 쓴다.

### 5. `execute_script` 로 숨은 요소를 누르는 것은 우회다

원본 팁: `execute_script()` 로 복잡한 DOM 조작이 가능하다.
다만 JS `click()` 은 사람이 누를 수 없는 요소도 눌러 버리므로, 「사용자가 실제로 누를 수 있나」는 검증하지 못한다.
원본 예제의 `hidden_button` 은 어디에서도 정의되지 않은 이름이라, 그 줄에 오면 `NameError` 가 난다.

### 6. 커스텀 조건의 `get_attribute('class')`

원본 코드: `class_name in element.get_attribute('class')`.
의심스러운 까닭: `class` 속성이 아예 없으면 `get_attribute` 가 `None` 을 줄 수 있고, `'done' in None` 은 `TypeError` 다(확인 필요).

### 7. `--no-sandbox` · User-Agent 를 습관처럼 넣는다

원본 주석은 `--no-sandbox` 를 「Docker/CI 환경에서 필요」, User-Agent 설정을 「봇 차단 회피」라고 적는다.
의심스러운 까닭: 샌드박스를 끄면 브라우저의 보호 장치 하나가 빠지고, User-Agent 를 바꿔도 차단을 피한다는 보장은 없다.

### 8. 그 밖의 주장

- 원본은 `CSS_SELECTOR` 를 「가장 빠름」이라 적는다 → 속도는 브라우저와 페이지 구조에 달려 언제나 그렇다고 말할 수 없다(확인 필요).
- `element.screenshot` 은 마지막으로 `element` 에 담긴 요소를 찍는다 — 변수를 여러 번 덮어쓰는 예제에서는 어느 요소인지 놓치기 쉽다.
- 원본 예제는 `https://example.com` 에 `username` · `country` 같은 요소가 있다고 가정한다 — 실제 그 페이지에는 그런 폼이 없어, 요소 찾기 단계부터 예외가 난다. 예제는 「쓰는 법을 차례로 보인 것」이지 그대로 돌아가는 스크립트가 아니다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `find_element` 는 없으면 예외, `find_elements` 는 빈 리스트 | Selenium 라이브러리의 API 규약 |
| `wait.until` 이 조건을 되풀이하고 시간 초과 시 `TimeoutException` | Selenium 라이브러리 |
| `--headless` · `--no-sandbox` · `--window-size` 의 효과 | Chrome 브라우저의 명령줄 옵션 — 브라우저 버전에 따라 다를 수 있다(확인 필요) |
| User-Agent 를 바꾸면 봇 차단을 피한다 | 아무도 보장하지 않는다 — 사이트마다 다르다 |
| `CSS_SELECTOR` 가 가장 빠르다 | 보장 없음 — 브라우저 구현에 달렸다 |
| `time.sleep(2)` 이면 로딩이 끝난다 | 보장 없음 — 네트워크와 사이트에 달렸다 |
| `list(set)` 의 차례 | Python 언어는 `set` 의 차례를 보장하지 않는다 |
| `ChromeDriverManager().install()` 이 맞는 드라이버를 받는다 | `webdriver-manager` 라이브러리 (네트워크 접근 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 요소가 JS 로 늦게 나타난다 | `WebDriverWait` + `EC` | 고정 `time.sleep` |
| 있는지 없는지만 확인 | `find_elements` 의 길이 | `find_element` + 예외 잡기 남발 |
| hover 해야 메뉴가 열린다 | `ActionChains.move_to_element().perform()` | `click` 으로 흉내 |
| 일반 `click` 이 가려져 실패 | `execute_script('arguments[0].click()', el)` (우회임을 알고) | 테스트 검증 목적의 기본 수단으로 |
| iframe 안의 요소 | `switch_to.frame` → 작업 → `default_content` | 전환 없이 찾기 |
| 서버 · CI 에서 돌리기 | 헤드리스 + `window-size` 명시 | 창 크기 없는 헤드리스 |
| 작업을 다 끝냄 | `driver.quit()` | `close()` 만 부르고 끝내기 |

## 핵심 문장

1. **Selenium 은 스크립트 → 드라이버 → 브라우저로 명령을 옮겨 실제 브라우저를 조종한다.**
2. **동적 페이지는 「조건이 맞을 때까지만」 기다리는 `WebDriverWait` + `EC` 로 다룬다** — 조건마다 엄격함(존재 · 보임 · 클릭 가능)이 다르다.
3. **단수 `find_element` 는 없으면 예외, 복수 `find_elements` 는 빈 리스트다.**
4. **클릭 · 입력으로 안 되는 일은 `ActionChains`(`perform` 필수)와 `execute_script`(값은 `return` 으로)로 한다.**
5. **드라이버는 한 문맥만 본다** — iframe · 탭 · 알림창은 `switch_to` 로 옮겨 가서 다룬다.

## 관련 자료

- `beautifulsoup` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [scrapy-basics](../10-scrapy-basics/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/web-frameworks.json` 의 `selenium`

## 용어 풀이

- **Selenium** — 브라우저 자동화 라이브러리.
- **WebDriver** — 프로그램이 브라우저를 원격 조종하게 하는 인터페이스.
- **드라이버(ChromeDriver)** — 스크립트의 명령을 브라우저로 옮기는 별도 프로그램.
- **`webdriver-manager`** — 브라우저에 맞는 드라이버를 자동으로 내려받아 버전을 관리하는 라이브러리.
- **`Service`** — 드라이버 프로세스를 띄우고 관리하는 객체.
- **헤드리스** — 창 없이 브라우저를 돌리는 방식.
- **User-Agent** — 브라우저가 자신을 소개하는 문자열.
- **DOM** — 브라우저가 페이지를 나무 구조로 들고 있는 것.
- **로케이터** — `(By.종류, '값')` 꼴의 「찾는 방법 + 값」 튜플.
- **`WebElement`** — 찾아낸 요소를 가리키는 Python 객체.
- **암시적 대기** — 드라이버 전체의 「찾기 재시도 시간」.
- **명시적 대기** — 특정 조건이 맞을 때까지만 기다리기.
- **`expected_conditions`(EC)** — 미리 만들어 둔 대기 조건 모음.
- **클로저** — 바깥 변수를 기억한 채 반환되는 안쪽 함수.
- **`Select`** — `<select>` 요소 전용 도우미.
- **`Keys`** — `ENTER` · `TAB` 같은 특수 키 상수.
- **`ActionChains`** — 마우스 · 키보드 동작을 쌓아 `perform` 으로 한 번에 실행하는 도구.
- **`execute_script`** — 브라우저 안에서 JS 를 실행하는 메서드.
- **iframe** — 페이지 안에 끼워 넣은 또 하나의 문서.
- **윈도우 핸들** — 탭(창) 하나를 가리키는 식별 문자열.
- **Alert** — `alert` · `confirm` · `prompt` 로 뜨는 브라우저 대화상자.
- **무한 스크롤** — 아래로 내릴 때마다 항목이 덧붙는 페이지 방식.

## 더 들어가면

- Selenium 4.6 무렵부터 `Selenium Manager` 가 들어 있어, `webdriver-manager` 없이 `webdriver.Chrome()` 만으로 드라이버를 찾아 준다고 알려져 있다(확인 필요).
- 최근 Chrome 은 `--headless=new` 라는 새 헤드리스 모드를 두고, 예전 `--headless` 와 동작이 다르다고 한다(확인 필요).
- `WebDriverWait` 는 기본으로 `NoSuchElementException` 을 무시하고 다시 시도하므로, 커스텀 조건 안의 `find_element` 가 실패해도 곧바로 터지지 않는다(확인 필요).
- 암시적 대기는 `find_elements` 에도 적용되어, 하나도 없을 때 빈 리스트를 돌려주기 전에 대기 시간만큼 기다린다고 알려져 있다(확인 필요).
- `StaleElementReferenceException` 은 찾아 둔 요소가 페이지 갱신으로 DOM 에서 사라졌을 때 난다 — 원본은 import 만 하고 쓰지 않는다(확인 필요).
- `driver.save_screenshot` 은 보통 현재 보이는 영역(뷰포트)만 찍고, 스크롤 전체를 한 장에 담지는 않는다는 설명이 많다 — 원본 주석의 「전체 페이지」와 다를 수 있다(확인 필요).
- 사이트의 이용 약관 · `robots.txt` 를 지키는 것은 크롤링의 기본 예의다.
