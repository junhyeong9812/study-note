# python/python-security/09 — 입력 검증 (SQL Injection, XSS 방지) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 공격 문자열을 f-string 쿼리에 넣으면 (예측)

```python
# 질문용 발췌
def unsafe_query(username):
    return f"SELECT * FROM users WHERE username = '{username}'"

print(unsafe_query("' OR '1'='1' --"))
```

- 출력되는 SQL 문자열은 무엇인가?
- 이 SQL 이 실행되면 `WHERE` 조건은 어떤 행에서 참이 되는가?

### 2. 파라미터 바인딩에서 같은 공격 문자열이 실패하는 까닭 (왜)

- `cursor.execute('SELECT * FROM users WHERE username = ?', (malicious_input,))` 가 빈 리스트를 돌려주는 것은 왜인가?

### 3. 스크립트 태그를 `html.escape` 에 넣으면 (예측)

```python
# 질문용 발췌
import html
print(html.escape('<script>alert("XSS")</script>'))
print(html.escape('Tom & Jerry'))
```

- 두 줄은 각각 어떤 문자열이 되는가?

### 4. `javascript:` 링크와 이스케이프의 한계 (경계)

- 사용자 입력 `javascript:alert(1)` 을 `href` 속성값으로 쓸 때 `html.escape` 만으로 막히는가?

### 5. 화이트리스트가 블랙리스트보다 안전한 까닭 (왜)

- 사용자명을 검증할 때 「허용 문자만 적는 패턴」이 「금지 문자 목록」보다 안전한 것은 왜인가?

### 6. 사용자명과 정수 검증에 여러 입력을 넣으면 (예측)

```python
# 질문용 발췌
for u in ["alice_123", "ab", "admin'; DROP TABLE--", "valid_user"]:
    print(u, validate_username(u))      # ^[a-zA-Z0-9_]{3,20}$
for v in ["42", "0", "101", "abc", "50"]:
    print(v, validate_integer(v, 1, 100))
```

- 각 입력은 `True` · `False` 중 무엇이 되는가?

### 7. `base + os.sep` 로 비교하는 까닭 (경계)

- `full.startswith(base)` 로만 비교하면 기준 디렉터리 `/app/uploads` 에 대해 어떤 경로가 잘못 통과하는가?

### 8. 문자열 검사 대신 `realpath` 를 먼저 하는 까닭 (왜)

- 경로 검사에서 `'..' in user_path` 를 찾는 대신 `os.path.realpath` 로 정규화한 결과를 비교하는 것은 왜인가?

### 9. 바인딩 · 리스트 인자 · 이스케이프를 잇는 생각 (연결)

- SQL 파라미터 바인딩과 `subprocess` 의 리스트 인자 + `shell=False` 는 어떤 같은 원리로 인젝션을 막는가?
- 그 원리를 쓸 수 없을 때 대신 쓰는 방법(HTML · 셸 각각)은 무엇인가?

## 실습

### 실습 1. 다섯 가지 취약점과 방어를 한 파일로 시연하기

**만들 것** — SQL Injection · XSS · 입력 검증 · 명령어 인젝션 · 경로 탐색을 차례로 보이며, 위험한 방식과 안전한 방식을 출력으로 비교하는 스크립트.

**준비물** — 표준 라이브러리(`re` · `html` · `sqlite3` · `shlex` · `subprocess` · `os`)만 쓴다. 외부 명령은 실제로 실행하지 않고 `print` 로 설명만 한다.

**요구 조건**

1단계 — SQL Injection
1. `unsafe_query(username)` 는 사용자명을 f-string 으로 끼운 `SELECT` 문 문자열을 돌려준다.
2. 정상 입력 `"alice"` 와 공격 입력 `"' OR '1'='1' --"` 로 만든 쿼리를 각각 출력한다.
3. 메모리 SQLite DB 에 `users(id, username, email)` 테이블을 만들고 alice · bob 두 행을 넣는다.
4. `?` 자리표시자로 공격 입력과 정상 입력을 각각 조회해 `fetchall()` 결과를 출력하고 연결을 닫는다.

2단계 — XSS
5. `<script>alert("XSS")</script>` 의 원본과 `html.escape` 결과를 출력한다.
6. `sanitize_html(text)` 는 따옴표까지 이스케이프한 문자열을 돌려준다.
7. 세 XSS 페이로드를 돌며 원본 앞 30자(30칸 폭)와 `sanitize_html` 결과 앞 40자를 한 줄씩 출력한다.

3단계 — 입력 검증
8. `validate_email` 은 `이름@도메인.영문2자이상` 꼴이면 `True` 를 돌려준다.
9. `validate_username` 은 영문 · 숫자 · `_` 만으로 된 3~20자이면 `True` 를 돌려준다.
10. `validate_integer(value, min_val, max_val)` 는 정수 변환이 되고 주어진 하한 · 상한 안이면 `True`, 변환 실패(`ValueError` · `TypeError`)면 `False` 를 돌려준다.
11. 검증 이름 · 검증 함수 · 입력 목록을 묶은 표를 돌며 입력마다 `[O]` 또는 `[X]` 와 `repr` 꼴의 입력을 출력한다. 정수 검증은 범위 1~100 으로 쓴다.

4단계 — 명령어 인젝션
12. 악의적 입력 `"test.txt; rm -rf /"` 와 `shell=True` 에서 일어나는 일을 출력한다.
13. 안전한 방법 두 가지(리스트 + `shell=False`, `shlex.quote`)를 설명하고 `shlex.quote` 결과를 출력한다.

5단계 — 경로 탐색
14. `safe_file_path(base_dir, user_path)` 는 두 경로를 `realpath` 로 정규화하고, 결과가 기준 디렉터리 + 구분자로 시작하지 않으며 기준 디렉터리 자체도 아니면 `ValueError("경로 탐색 공격 감지: …")` 를 던지고, 아니면 정규화된 경로를 돌려준다.
15. 기준 `/app/uploads` 에 대해 네 경로를 돌며 통과하면 `[허용] 입력 → 결과`, 예외면 `[차단] 메시지` 를 출력한다.

**시작 코드**

```python
import re
import html
import sqlite3
import shlex
import subprocess
import os

# === SQL Injection 방지 ===
print("=== SQL Injection 방지 ===")

def unsafe_query(username):
    """절대 이렇게 하지 마세요!"""
    # TODO: 사용자명을 f-string 으로 끼운 SELECT 문을 돌려준다
    pass

print("--- 위험한 쿼리 (문자열 포맷팅) ---")
normal_input = "alice"
malicious_input = "' OR '1'='1' --"
# TODO: 정상 · 공격 쿼리를 출력한다
print("  → 모든 사용자 정보가 노출됨!")
print()

print("--- 안전한 쿼리 (파라미터 바인딩) ---")
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()
cursor.execute('CREATE TABLE users (id INTEGER, username TEXT, email TEXT)')
cursor.execute('INSERT INTO users VALUES (1, "alice", "alice@test.com")')
cursor.execute('INSERT INTO users VALUES (2, "bob", "bob@test.com")')
# TODO: ? 자리표시자로 malicious_input 조회 → 결과 출력
# TODO: ? 자리표시자로 normal_input 조회 → 결과 출력
conn.close()
print()

# === XSS 방지 ===
print("=== XSS 방지 ===")
user_input = '<script>alert("XSS")</script>'
print(f"  원본 입력: {user_input}")
# TODO: 이스케이프한 결과를 safe_output 에 담아 출력
print("  → <script>가 &lt;script&gt;로 변환되어 실행되지 않음")
print()

def sanitize_html(text):
    """사용자 입력을 HTML 안전하게 변환"""
    # TODO: 따옴표까지 이스케이프
    pass

dangerous_inputs = [
    '<img src=x onerror=alert(1)>',
    '" onmouseover="alert(1)"',
    "<a href='javascript:alert(1)'>",
]
# TODO: 원본 앞 30자(30칸) → sanitize_html 결과 앞 40자 를 한 줄씩 출력
print()

# === 입력 검증 패턴 ===
print("=== 입력 검증 패턴 ===")

def validate_email(email):
    """이메일 검증"""
    # TODO: 허용 패턴 정규식으로 전체 일치 여부를 bool 로
    pass

def validate_username(username):
    """사용자명 검증 (화이트리스트 방식)"""
    # TODO: 영문 · 숫자 · _ 3~20자
    pass

def validate_integer(value, min_val=None, max_val=None):
    """정수 검증"""
    # TODO: int 변환 · 하한 · 상한 · 변환 실패 처리
    pass

test_cases = [
    ("이메일", validate_email, ["user@test.com", "invalid", "a@b", "user@test.co.kr"]),
    ("사용자명", validate_username, ["alice_123", "ab", "admin'; DROP TABLE--", "valid_user"]),
    # TODO: ("정수", 범위 1~100 검증 함수, ["42", "0", "101", "abc", "50"])
]

for name, validator, inputs in test_cases:
    print(f"  --- {name} 검증 ---")
    # TODO: 입력마다 [O]/[X] 와 repr 꼴 입력 출력
print()

# === 명령어 인젝션 방지 ===
print("=== 명령어 인젝션 방지 ===")
user_file = "test.txt; rm -rf /"
print(f"  위험한 입력: {user_file}")
print(f"  위험: subprocess.run(f'cat {{user_file}}', shell=True)")
print(f"  → 'cat test.txt; rm -rf /' 실행됨!")
print()
print("  안전한 방법:")
print("  1. subprocess.run(['cat', user_file], shell=False)")
print("     → 'cat' 명령에 'test.txt; rm -rf /'를 단일 인자로 전달")
print("  2. shlex.quote()로 이스케이프")
# TODO: shlex.quote(user_file) 결과 출력
print()

# === 경로 탐색 공격 방지 ===
print("=== 경로 탐색 (Path Traversal) 방지 ===")

def safe_file_path(base_dir, user_path):
    """사용자 입력 경로가 기준 디렉토리 내인지 확인"""
    # TODO: realpath 정규화 → base + os.sep 비교 → 벗어나면 ValueError
    pass

base = "/app/uploads"
test_paths = ["photo.jpg", "../../../etc/passwd", "subdir/file.txt", "..\\windows\\system32"]
for p in test_paths:
    # TODO: 허용이면 [허용] p → 결과, ValueError 면 [차단] 메시지
    pass
```

**확인 방법** — `python input-validation.py` 로 돌려, 바인딩 조회에서 공격 입력의 결과가 빈 리스트인지, 이스케이프 결과에 `<` 대신 `&lt;` 가 보이는지, 검증 표의 `[O]`/`[X]` 가 기대와 맞는지, `../../../etc/passwd` 가 `[차단]` 되는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
