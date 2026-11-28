# python/python-security/09 — 입력 검증 (SQL Injection, XSS 방지) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 따옴표가 닫히고 `OR '1'='1'` 이 조건이 되어 모든 행이 참이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
SELECT * FROM users WHERE username = '' OR '1'='1' --'
```

조건은 **모든 행**에서 참이 된다.

**왜 그런가**
입력의 첫 `'` 가 쿼리의 여는 따옴표와 짝을 이뤄 `username = ''` 이 된다.
그 뒤 `OR '1'='1'` 은 어느 행에서나 참인 조건이 붙은 것이다.
`--` 이후는 주석이라 끝에 남은 `'` 가 문법 오류를 내지 않는다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 값이 SQL 문법이 아니라 비교할 글자 덩어리로만 쓰이기 때문이다

바인딩은 SQL 틀과 값을 따로 넘긴다.
그래서 `' OR '1'='1' --` 는 조건식이 되지 못하고, `username` 이 정확히 그 긴 문자열인 행을 찾는 비교값이 된다.
테이블에는 alice · bob 뿐이라 일치하는 행이 없어 `[]` 가 된다.
근거: 2-summary 「동작 방식 (1)」.

### 3. 꺾쇠 · 큰따옴표 · `&` 가 엔티티로 바뀐다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;
Tom &amp; Jerry
```

**왜 그런가**
`html.escape` 는 `<` · `>` · `&` · `"` · `'` 를 각각 `&lt;` · `&gt;` · `&amp;` · `&quot;` · `&#x27;` 로 바꾼다.
`quote` 를 주지 않아도 큰따옴표가 바뀌는 것은 기본값이 따옴표까지 바꾸는 쪽이기 때문이다(원본 주석의 예상 결과가 이를 보인다).
근거: 2-summary 「동작 방식 (2)」.

### 4. 막히지 않는다 — 바꿀 문자가 없다

`javascript:alert(1)` 에는 `<` · `>` · `&` · `"` · `'` 가 하나도 없어서 이스케이프 뒤에도 그대로다.
따라서 이 문자열이 `href` 값 자체가 되면 링크를 누를 때 스크립트가 실행될 수 있다.
이스케이프는 「글자로 끼워 넣는」 문맥만 지키고, URL 의 시작(스킴)은 화이트리스트로 따로 검사해야 한다.
원본 주석의 「모두 무해한 텍스트로 변환됨」은 이 경우를 덮지 못한다.
근거: 2-summary 「어디서 틀리나 4」 · 「언제 쓰고 언제 안 쓰나」 (원본에 근거 없음 — 추론).

### 5. 모르는 입력이 기본으로 거부되기 때문이다

블랙리스트는 생각해 낸 공격만 막으므로, 빠뜨린 문자 · 조합 · 표기가 통과한다.
화이트리스트는 정상 입력의 모양만 받아들이므로 예상하지 못한 입력은 모두 떨어진다.
원본 주석은 이를 「예외적 우회 케이스가 적다」고 말한다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 6. 사용자명은 첫째 · 넷째만, 정수는 42 · 50 만 통과한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
alice_123 True
ab False
admin'; DROP TABLE-- False
valid_user True
42 True
0 False
101 False
abc False
50 True
```

**왜 그런가**
`ab` 는 2자라 `{3,20}` 에 못 미치고, `admin'; DROP TABLE--` 는 `'` · `;` · 공백 · `-` 가 허용 문자 밖이다.
`0` 은 하한 1 보다 작고 `101` 은 상한 100 보다 크다.
`abc` 는 `int()` 가 `ValueError` 를 내 `except` 에서 `False` 가 된다.
근거: 2-summary 「동작 방식 (3)」.

### 7. `/app/uploads_evil/…` 처럼 이름 앞부분이 같은 이웃 디렉터리가 통과한다

`"/app/uploads_evil/x".startswith("/app/uploads")` 는 참이다.
구분자를 붙인 `"/app/uploads/"` 로 비교하면 `uploads_evil` 은 그 뒤가 `_` 라 걸러진다.
기준 디렉터리 자체(`/app/uploads`)는 `full != base` 조건으로 따로 허용한다.
근거: 2-summary 「동작 방식 (5)」.

### 8. 표기가 아니라 실제로 가리키는 곳을 비교해야 하기 때문이다

`..` 를 찾는 문자열 검사는 표기를 바꾼 입력이나 심볼릭 링크를 놓칠 수 있는 블랙리스트다.
`realpath` 는 `..` 와 링크를 실제로 계산해 최종 절대 경로를 만들기 때문에, 그 결과가 기준 안에 있는지만 보면 된다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 7」.

### 9. 「코드와 데이터를 따로 넘긴다」 — 못 나누면 이스케이프한다

바인딩은 SQL 틀과 값을, 리스트 인자는 프로그램 이름과 각 인자를 따로 넘긴다.
그래서 입력 속 `'` 나 `;` 를 문법으로 해석할 기회가 없다.
틀과 입력을 한 문자열로 섞을 수밖에 없는 경우에는 HTML 은 `html.escape`, 셸은 `shlex.quote` 로 입력을 「글자 그대로」 표기로 바꾼다.
근거: 2-summary 「핵심 문장 1 · 2」 · 「동작 방식 (1) · (4)」.

## 실습 정답

### 실습 1. 다섯 가지 취약점과 방어를 한 파일로 시연하기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. f-string 쿼리 | `unsafe_query` 의 `query = f"SELECT ... '{username}'"` |
| 2. 정상 · 공격 쿼리 출력 | `print(f"  정상: {unsafe_query(normal_input)}")` · `print(f"  공격: ...")` |
| 3. 메모리 DB · 두 행 | `sqlite3.connect(':memory:')` · `CREATE TABLE` · `INSERT` 두 줄 |
| 4. `?` 조회 두 번 · 닫기 | `cursor.execute('... = ?', (malicious_input,))` · `(normal_input,)` · `fetchall()` · `conn.close()` |
| 5. 스크립트 이스케이프 | `safe_output = html.escape(user_input)` |
| 6. 따옴표까지 이스케이프 | `sanitize_html` 의 `html.escape(text, quote=True)` |
| 7. 페이로드 표 출력 | `for inp in dangerous_inputs:` · `f"  {inp[:30]:30s} → {sanitize_html(inp)[:40]}"` |
| 8. 이메일 패턴 | `validate_email` 의 `r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'` |
| 9. 사용자명 패턴 | `validate_username` 의 `r'^[a-zA-Z0-9_]{3,20}$'` |
| 10. 정수 + 범위 | `validate_integer` 의 `int(value)` · `min_val` · `max_val` 검사 · `except (ValueError, TypeError)` |
| 11. 검증 표와 `[O]`/`[X]` | `test_cases` · `lambda v: validate_integer(v, 1, 100)` · `mark = "O" if result else "X"` · `{inp!r}` |
| 12. 위험 설명 | `user_file = "test.txt; rm -rf /"` 와 그 아래 `print` 들 |
| 13. 안전한 방법 · `shlex.quote` | `"  1. subprocess.run(['cat', user_file], shell=False)"` · `shlex.quote(user_file)` |
| 14. 경로 검사 함수 | `safe_file_path` 의 `os.path.realpath` 두 번 · `full.startswith(base + os.sep) and full != base` · `raise ValueError` |
| 15. 경로 표 출력 | `for p in test_paths:` · `try` / `except ValueError as e` · `[허용]` · `[차단]` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-security/reference/input-validation.py`

```python
# [보안 & 암호화] 입력 검증 (SQL Injection, XSS 방지)
# 설명: SQL Injection, XSS 등 주요 취약점을 방지하는 입력 검증과 안전한 코딩 패턴
# 팁: SQL 쿼리에는 반드시 파라미터 바인딩(?나 %s)을 사용하고, 문자열 포맷팅으로 쿼리를 구성하지 않는다. HTML 출력에는 html.escape()로 사용자 입력을 이스케이프한다. 입력 검증은 화이트리스트(허용 패턴) 방식이 블랙리스트(차단 패턴)보다 안전하다. subprocess는 shell=False + 리스트 형태가 안전하다.

# re: 정규식 기반 입력 화이트리스트 검증
import re
# html: HTML 특수문자 이스케이프로 XSS 방어
import html
# sqlite3: 파라미터 바인딩 시연용 DB
import sqlite3
# shlex: 셸 인자 안전 이스케이프
import shlex
# subprocess: 외부 명령 실행 (인젝션 위험 데모)
import subprocess

# === SQL Injection 방지 ===
print("=== SQL Injection 방지 ===")

# 위험: 문자열 포맷팅으로 쿼리 작성
# 사용자 입력을 그대로 SQL에 삽입 → 인젝션 취약
def unsafe_query(username):
    """절대 이렇게 하지 마세요!"""
    # f-string으로 SQL 조립 → 따옴표/주석 등 SQL 메타문자가 그대로 실행
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return query

print("--- 위험한 쿼리 (문자열 포맷팅) ---")
# 정상 사용자명
normal_input = "alice"
# 공격 페이로드: 따옴표 닫고 OR 1=1 추가하여 항상 참 → 모든 행 반환
malicious_input = "' OR '1'='1' --"
print(f"  정상: {unsafe_query(normal_input)}")
print(f"  공격: {unsafe_query(malicious_input)}")
print("  → 모든 사용자 정보가 노출됨!")
print()

# 안전: 파라미터 바인딩
print("--- 안전한 쿼리 (파라미터 바인딩) ---")
# 메모리 SQLite로 시연
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()
# 테스트 테이블/데이터 준비
cursor.execute('CREATE TABLE users (id INTEGER, username TEXT, email TEXT)')
cursor.execute('INSERT INTO users VALUES (1, "alice", "alice@test.com")')
cursor.execute('INSERT INTO users VALUES (2, "bob", "bob@test.com")')

# ? 플레이스홀더 사용 (SQLite)
# DB 드라이버가 값을 안전하게 이스케이프 → SQL 메타문자 무력화
cursor.execute('SELECT * FROM users WHERE username = ?', (malicious_input,))
results = cursor.fetchall()
# 공격 입력은 단순 문자열로 처리되어 매칭 실패
print(f"  파라미터 바인딩 결과: {results}")  # 빈 리스트 (공격 실패)

# 정상 입력은 정상 동작
cursor.execute('SELECT * FROM users WHERE username = ?', (normal_input,))
results = cursor.fetchall()
print(f"  정상 조회 결과: {results}")
conn.close()
print()

# === XSS 방지 ===
print("=== XSS 방지 ===")

# 위험: 사용자 입력을 그대로 HTML에 삽입
# 브라우저가 <script>를 실행 → 쿠키 탈취/계정 탈취 가능
user_input = '<script>alert("XSS")</script>'
print(f"  원본 입력: {user_input}")

# 안전: HTML 이스케이프
# < > & " ' 를 엔티티로 변환 → 코드가 아닌 텍스트로 표시
safe_output = html.escape(user_input)
print(f"  이스케이프: {safe_output}")
print("  → <script>가 &lt;script&gt;로 변환되어 실행되지 않음")
print()

# HTML 이스케이프 함수
def sanitize_html(text):
    """사용자 입력을 HTML 안전하게 변환"""
    # quote=True: 속성값에 들어갈 따옴표도 이스케이프 → 속성 탈출 공격 방어
    return html.escape(text, quote=True)

# 다양한 XSS 페이로드 테스트
dangerous_inputs = [
    # 이미지 태그의 onerror 핸들러로 JS 실행 시도
    '<img src=x onerror=alert(1)>',
    # 속성값 탈출 공격 (HTML 속성 안에서 따옴표 닫고 이벤트 핸들러 추가)
    '" onmouseover="alert(1)"',
    # javascript: URL 스킴 공격
    "<a href='javascript:alert(1)'>",
]
for inp in dangerous_inputs:
    # 모든 페이로드가 무해한 텍스트로 변환됨
    print(f"  {inp[:30]:30s} → {sanitize_html(inp)[:40]}")
print()

# === 입력 검증 패턴 ===
print("=== 입력 검증 패턴 ===")

# 이메일 검증 (RFC 단순화 패턴)
def validate_email(email):
    """이메일 검증"""
    # 화이트리스트 정규식: 허용 문자만 통과
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

# 사용자명: 영숫자/언더스코어만, 길이 3~20
def validate_username(username):
    """사용자명 검증 (화이트리스트 방식)"""
    # 화이트리스트가 블랙리스트보다 안전 (예외적 우회 케이스 적음)
    pattern = r'^[a-zA-Z0-9_]{3,20}$'  # 영문, 숫자, _ 만 허용
    return bool(re.match(pattern, username))

# 정수 + 범위 검증 (페이지 번호, 수량 등)
def validate_integer(value, min_val=None, max_val=None):
    """정수 검증"""
    try:
        # 정수 변환 시도
        n = int(value)
        # 하한 검사
        if min_val is not None and n < min_val:
            return False
        # 상한 검사
        if max_val is not None and n > max_val:
            return False
        return True
    except (ValueError, TypeError):
        # 변환 실패 시 거부
        return False

# 검증 케이스 모음 (정상/비정상 혼합)
test_cases = [
    ("이메일", validate_email, ["user@test.com", "invalid", "a@b", "user@test.co.kr"]),
    # SQL 주석 시도가 화이트리스트로 차단됨
    ("사용자명", validate_username, ["alice_123", "ab", "admin'; DROP TABLE--", "valid_user"]),
    ("정수", lambda v: validate_integer(v, 1, 100), ["42", "0", "101", "abc", "50"]),
]

for name, validator, inputs in test_cases:
    print(f"  --- {name} 검증 ---")
    for inp in inputs:
        # 통과 여부 표시
        result = validator(inp)
        mark = "O" if result else "X"
        print(f"    [{mark}] {inp!r}")
print()

# === 명령어 인젝션 방지 ===
print("=== 명령어 인젝션 방지 ===")

# 위험: shell=True + 사용자 입력
# 세미콜론으로 다른 명령 추가 → 임의 명령 실행 가능
user_file = "test.txt; rm -rf /"  # 악의적 입력
print(f"  위험한 입력: {user_file}")
print(f"  위험: subprocess.run(f'cat {{user_file}}', shell=True)")
print(f"  → 'cat test.txt; rm -rf /' 실행됨!")
print()

# 안전: 리스트 형태 + shell=False
print("  안전한 방법:")
# 리스트 인자: 셸을 거치지 않고 직접 exec → 메타문자 해석 안 됨
print("  1. subprocess.run(['cat', user_file], shell=False)")
print("     → 'cat' 명령에 'test.txt; rm -rf /'를 단일 인자로 전달")
# shlex.quote: 셸이 필요한 경우 안전 이스케이프
print("  2. shlex.quote()로 이스케이프")
print(f"     shlex.quote(input) = {shlex.quote(user_file)}")
print()

# === 경로 탐색 공격 방지 ===
print("=== 경로 탐색 (Path Traversal) 방지 ===")
# os: 경로 정규화에 사용
import os

# 사용자가 ../로 상위 디렉토리 접근하는 것을 차단
def safe_file_path(base_dir, user_path):
    """사용자 입력 경로가 기준 디렉토리 내인지 확인"""
    # 절대 경로로 정규화 (심볼릭 링크/.. 모두 해석)
    base = os.path.realpath(base_dir)
    full = os.path.realpath(os.path.join(base, user_path))
    # 기준 디렉토리 내인지 확인
    # base + sep prefix 검사 → 같은 prefix 디렉토리 우회 방지
    if not full.startswith(base + os.sep) and full != base:
        raise ValueError(f"경로 탐색 공격 감지: {user_path}")
    return full

# 테스트: 정상/공격 케이스 혼합
base = "/app/uploads"
test_paths = ["photo.jpg", "../../../etc/passwd", "subdir/file.txt", "..\\windows\\system32"]
for p in test_paths:
    try:
        # 정상 경로만 통과
        result = safe_file_path(base, p)
        print(f"  [허용] {p} → {result}")
    except ValueError as e:
        # ../로 탈출 시도는 차단
        print(f"  [차단] {e}")

# 출력:
# === SQL Injection 방지 ===
# 공격: SELECT * FROM users WHERE username = '' OR '1'='1' --'
# 파라미터 바인딩 결과: [] (공격 실패)
# === XSS 방지 ===
# 이스케이프: &lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;
# === 경로 탐색 방지 ===
# [차단] 경로 탐색 공격 감지: ../../../etc/passwd
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**
- SQL 은 f-string 쿼리를 「보여 주기만」 하고, 실제 조회는 언제나 `?` 와 값 튜플로 한다 — 값이 하나여도 `(x,)` 꼴이다.
- `sanitize_html` 의 `quote=True` 는 속성 탈출을 막는 자리다. 다만 `javascript:` 같은 URL 은 이스케이프로 막히지 않는다.
- 검증 함수는 모두 `bool` 을 돌려주게 하고, 정규식은 `^ … $` 로 전체를 묶는다.
- `validate_integer` 의 범위는 `lambda` 로 1~100 을 미리 채워 다른 검증 함수와 같은 「입력 하나 → bool」 꼴로 맞춘다.
- 명령어 인젝션 단계는 위험한 명령을 실제로 실행하지 않는다 — 설명과 `shlex.quote` 결과만 출력한다.
- 경로 검사는 정규화를 먼저, 비교를 나중에 하고, 비교 기준에는 반드시 `os.sep` 을 붙인다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
