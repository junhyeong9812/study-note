# python/python-networking/05 — 이메일 전송: smtplib과 MIME — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 컨테이너 자신 → 텍스트 → HTML 차례로 네 줄

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
Content-Type: multipart/alternative
  파트: multipart/alternative
  파트: text/plain
  파트: text/html
```

**왜 그런가**
`get_content_type()` 은 컨테이너의 형식 `multipart/alternative` 를 돌려준다.
`walk()` 는 재귀 순회라 컨테이너 자신부터 내놓고, 그 다음 붙인 차례대로 자식 파트를 내놓는다.
텍스트를 먼저, HTML 을 나중에 붙였으므로 `text/plain` → `text/html` 순이다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (4)」.

### 2. `multipart/mixed` 와 `text/plain` 두 파트뿐이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  파트: multipart/mixed
  파트: text/plain
```

**왜 그런가**
`file_path` 의 기본값은 `None` 이라 `if file_path and os.path.exists(file_path)` 가 거짓이다.
첨부 블록 전체를 건너뛰므로 「첨부: …」 줄도 찍히지 않고, 컨테이너에는 본문 파트 하나만 들어 있다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 6」.

### 3. 헤더에는 Bcc 가 없고 전송 대상에는 있다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
To: a@ex.com, b@ex.com
Cc: cc@ex.com
실제 전송 대상: ['a@ex.com', 'b@ex.com', 'cc@ex.com', 'secret@ex.com']
```

**왜 그런가**
`To` 와 `Cc` 는 `', '.join(...)` 으로 쉼표와 공백을 넣어 이은 문자열이다.
BCC 는 헤더에 넣지 않았으므로 두 헤더 어디에도 `secret@ex.com` 이 없다.
전송 대상은 `recipients + (cc or []) + (bcc or [])` 로 합친 리스트라 넷이 모두 이 차례로 들어간다.
근거: 2-summary 「동작 방식 (5)」.

### 4. 헤더는 모든 수신자에게 보이기 때문이다

헤더는 메시지의 일부라 받는 사람 모두가 그대로 본다.
`Bcc` 헤더에 주소를 적으면 숨은 참조 명단이 다른 수신자에게 드러나 「숨은」 참조가 아니게 된다.
그래서 BCC 는 헤더에서 빼고 전송 대상 목록에만 넣는다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 3」.

### 5. `alternative` 는 마지막 파트가 우선이라서다

원본 주석에 따르면 `alternative` 에서는 마지막에 `attach` 한 파트가 우선 표시된다.
텍스트 → HTML 차례로 붙여야 HTML 을 읽을 수 있는 프로그램은 HTML 을, 못 읽는 프로그램은 텍스트 폴백을 보여 준다.
차례를 뒤집으면 HTML 을 읽을 수 있는 곳에서도 평문이 우선될 수 있다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 2」.

### 6. 메일 경로가 원시 바이트를 안전하게 나르지 못할 수 있어서다

원본 주석의 까닭은 「이메일은 7비트 ASCII 만 안전하게 전송된다」이다.
파일 바이트는 임의의 값을 가지므로, base64 로 영문자 · 숫자 · 기호만으로 바꿔 실어야 깨지지 않는다.
다만 「7비트 ASCII 만」이라는 단정은 확인이 필요하다 — 결론(base64 로 바꾸면 안전)은 그대로다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 7」 · 「어디서 틀리나 10」.

### 7. 오류 없이 본문만 있는 메일이 된다

`os.path.exists(file_path)` 가 거짓이면 첨부 블록을 통째로 건너뛴다.
예외도 경고도 없으므로, 호출한 쪽은 첨부가 빠졌다는 사실을 모른 채 메일을 보낼 수 있다.
결과 메시지는 `multipart/mixed` 안에 `text/plain` 하나다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 6」.

### 8. 보내지 않고, 표기도 실제와 다르다

이 함수는 메시지와 전송 대상 목록을 만들어 `(msg, all_recipients)` 튜플로 돌려줄 뿐 `smtplib` 을 부르지 않는다 — 서버로 아무것도 나가지 않는다.
반환 표기는 `-> MIMEMultipart` 지만 실제 반환값은 튜플이라 표기가 틀렸다.
원본 팁은 「`send_message` 의 수신자 목록에만 포함」이라고 하지만, 그 목록을 `send_message` 에 넘기는 줄은 예제에 없다.
근거: 2-summary 「어디서 틀리나 5」.

### 9. 편지 머리(헤더)에서는 빼고 배달 목록(RCPT TO)에만 넣는 일이다

편지 머리의 「받는 사람 · 참조」는 헤더 `To` · `Cc` 이고, 모든 수신자가 본다.
창구에 내는 배달 목록은 SMTP 의 `RCPT TO` 이고, 서버만 본다.
BCC 는 두 쪽을 따로 다룬다 — 헤더에서는 빼고, 배달 목록에는 넣는다.
둘 중 하나만 하면 명단이 드러나거나(헤더에 넣음) 배달이 안 된다(목록에서 뺌).
근거: 2-summary 「한눈에」 비유 대응표 · 「동작 방식 (5)」 · 「어디서 틀리나 4」.

### 10. `mixed` 상자 안에 `alternative` 상자와 첨부 파트를 나란히 넣는다

`attach` 는 MIME 파트라면 컨테이너도 받으므로 상자 안에 상자를 넣을 수 있다.
바깥 `multipart/mixed` 에 「`multipart/alternative`(텍스트 → HTML)」와 「`application/octet-stream` 첨부」를 붙이면 된다.
`alternative` 는 「같은 본문의 두 표현 중 하나」, `mixed` 는 「본문과 첨부를 모두」라는 각자의 역할을 그대로 지킨다.
근거: 2-summary 「동작 방식 (4)」 (원본에 근거 없음 — 추론).

## 실습 정답

### 실습 1. 이메일 메시지 다섯 가지 꼴을 만들고 구조를 찍기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 평문 본문과 세 헤더 | `send_simple_email` 의 `MIMEText(body, 'plain', 'utf-8')` · `msg['Subject']` · `msg['From']` · `msg['To']` |
| 2. STARTTLS 로 보내고 완료 문구 | `with smtplib.SMTP(smtp_server, port) as server:` · `server.starttls()` · `server.login` · `server.send_message` · `print(f"이메일 전송 완료: …")` |
| 3. 평문 구조 출력 | 모듈 수준의 `msg = MIMEText(...)` · `print(msg.as_string()[:300])` · `print("...")` |
| 4. 텍스트 → HTML 대체 묶음 | `create_html_email` 의 `MIMEMultipart('alternative')` · `msg.attach(text_part)` · `msg.attach(html_part)` |
| 5. 형식과 파트 출력 | `html_msg.get_content_type()` · `for part in html_msg.walk()` |
| 6. mixed 컨테이너와 본문 | `create_email_with_attachment` 의 `MIMEMultipart('mixed')` · `msg.attach(MIMEText(body, ...))` |
| 7. 조건부 첨부 | `if file_path and os.path.exists(file_path)` · `open(file_path, 'rb')` · `MIMEBase('application', 'octet-stream')` · `set_payload` · `encoders.encode_base64` · `add_header('Content-Disposition', …)` · `print(f"첨부: {filename}")` |
| 8. 경로 없이 호출 · 파트 출력 | `attach_msg = create_email_with_attachment(...)` · `for part in attach_msg.walk()` |
| 9. To/Cc 헤더 · BCC 제외 · 본문 | `send_to_multiple` 의 `', '.join(recipients)` · `if cc:` · BCC 줄 없음 · `msg.attach(MIMEText(...))` |
| 10. 합친 전송 대상 반환 | `all_recipients = recipients + (cc or []) + (bcc or [])` · `return msg, all_recipients` |
| 11. 헤더와 대상 출력 | `print(f"To: …")` · `print(f"Cc: …")` · `print(f"실제 전송 대상: …")` |
| 12. 세 연결 패턴 출력 | `=== 5. SMTP 연결 패턴 ===` 아래의 여러 줄 문자열 `print("""…""")` |
| 13. 핵심 정리 다섯 줄 | `=== 핵심 정리 ===` 아래 `print` 다섯 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-networking/reference/smtp-email.py`

```python
# [네트워크 & 시스템] 이메일 전송: smtplib과 MIME
# 설명: smtplib으로 이메일 전송, MIME 구조, 첨부 파일 개념
# 팁: 이메일은 MIMEMultipart로 구조를 만들고, MIMEText로 본문을 첨부한다. 'alternative'는 텍스트/HTML 대체, 'mixed'는 본문+첨부 파일 구조다. Gmail은 앱 비밀번호가 필요하며, BCC는 헤더에 넣지 않고 전송 대상 목록에만 포함해야 한다.

"""이메일 전송: smtplib, MIME 구조, 첨부 파일"""
# smtplib: SMTP 클라이언트 (포트 25/587/465)
import smtplib
# MIMEText: 텍스트/HTML 본문 파트
from email.mime.text import MIMEText
# MIMEMultipart: 여러 파트를 묶는 컨테이너
from email.mime.multipart import MIMEMultipart
# MIMEBase: 임의 첨부 파일용 베이스 클래스
from email.mime.base import MIMEBase
# encoders: base64 등 전송 인코딩
from email import encoders
# os: 파일 경로 처리
import os

# === 1. 간단한 텍스트 이메일 ===
# 한 통의 평문 이메일 전송 (SMTP+STARTTLS 흐름)
def send_simple_email(
    smtp_server: str,
    port: int,
    sender: str,
    password: str,
    recipient: str,
    subject: str,
    body: str
):
    """간단한 텍스트 이메일 전송"""
    # MIMEText: 본문 + Content-Type/Charset 자동
    msg = MIMEText(body, 'plain', 'utf-8')
    # 메시지 헤더 설정
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    # SMTP: 평문 연결 → STARTTLS로 업그레이드 (포트 587 표준)
    with smtplib.SMTP(smtp_server, port) as server:
        # TLS 암호화 시작 (이후 모든 통신 암호화)
        server.starttls()  # TLS 암호화 시작
        # 인증
        server.login(sender, password)
        # 송신 (헤더의 To/Cc 자동 사용)
        server.send_message(msg)
        print(f"이메일 전송 완료: {recipient}")

# 사용 예시 (실제 전송하지 않고 구조만 출력)
print("=== 1. 텍스트 이메일 구조 ===")
# 메시지 객체만 만들어서 직렬화 형태 확인
msg = MIMEText("안녕하세요, Python에서 보낸 이메일입니다.", 'plain', 'utf-8')
msg['Subject'] = '테스트 이메일'
msg['From'] = 'sender@example.com'
msg['To'] = 'recipient@example.com'
# as_string(): 메시지를 RFC 822 형식 문자열로
print(msg.as_string()[:300])
print("...")

# === 2. HTML 이메일 ===
# 텍스트/HTML 두 버전을 함께 보내 호환성 보장
def create_html_email(
    sender: str,
    recipient: str,
    subject: str
) -> MIMEMultipart:
    """HTML + 텍스트 대체 이메일 생성"""
    # 'alternative': 같은 내용의 다른 표현 (수신자가 선호 형식 선택)
    msg = MIMEMultipart('alternative')  # 텍스트/HTML 대체
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    # 텍스트 버전 (HTML 못 읽는 클라이언트용)
    # 폴백 본문
    text_part = MIMEText(
        "Python 학습 보고서\n- 완료: 기초 문법\n- 진행 중: 웹 프레임워크",
        'plain', 'utf-8'
    )

    # HTML 버전
    # 메일 클라이언트가 우선 표시 (alternative는 마지막 attach가 우선)
    html_part = MIMEText("""
    <html>
    <body>
        <h1 style="color: #333;">Python 학습 보고서</h1>
        <ul>
            <li><strong>완료:</strong> 기초 문법</li>
            <li><em>진행 중:</em> 웹 프레임워크</li>
        </ul>
        <p style="color: green;">계속 열심히!</p>
    </body>
    </html>
    """, 'html', 'utf-8')

    # 텍스트 → HTML 순서로 첨부 (HTML이 우선 표시)
    msg.attach(text_part)
    msg.attach(html_part)  # HTML이 우선 표시됨
    return msg

print("\n=== 2. HTML 이메일 구조 ===")
html_msg = create_html_email('a@ex.com', 'b@ex.com', 'HTML 테스트')
print(f"Content-Type: {html_msg.get_content_type()}")
# walk(): 모든 파트 재귀 순회
for part in html_msg.walk():
    ct = part.get_content_type()
    print(f"  파트: {ct}")

# === 3. 첨부 파일 이메일 ===
# 본문 + 첨부 파일 (mixed)
def create_email_with_attachment(
    sender: str,
    recipient: str,
    subject: str,
    body: str,
    file_path: str = None
) -> MIMEMultipart:
    """첨부 파일이 있는 이메일 생성"""
    # 'mixed': 본문 + 임의 첨부 (서로 독립된 파트)
    msg = MIMEMultipart('mixed')  # 본문 + 첨부
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    # 본문
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # 첨부 파일
    if file_path and os.path.exists(file_path):
        # 바이너리로 읽기
        with open(file_path, 'rb') as f:
            # octet-stream: 일반 바이너리
            part = MIMEBase('application', 'octet-stream')
            # payload에 원시 바이트 설정
            part.set_payload(f.read())
            # base64로 인코딩 (이메일은 7비트 ASCII만 안전 전송)
            encoders.encode_base64(part)
            # 파일명만 추출
            filename = os.path.basename(file_path)
            # Content-Disposition 헤더로 첨부 파일 이름 지정
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"'
            )
            msg.attach(part)
            print(f"첨부: {filename}")

    return msg

print("\n=== 3. 첨부 파일 이메일 구조 ===")
attach_msg = create_email_with_attachment(
    'a@ex.com', 'b@ex.com', '보고서', '첨부 파일을 확인하세요.'
)
for part in attach_msg.walk():
    print(f"  파트: {part.get_content_type()}")

# === 4. 여러 수신자에게 전송 ===
# To/Cc/Bcc 차이를 정확히 처리
def send_to_multiple(
    sender: str,
    recipients: list,
    cc: list = None,
    bcc: list = None,
    subject: str = '',
    body: str = ''
) -> MIMEMultipart:
    """여러 수신자 (To, CC, BCC) 이메일"""
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    # To/Cc는 헤더에 노출
    msg['To'] = ', '.join(recipients)
    if cc:
        msg['Cc'] = ', '.join(cc)
    # BCC는 헤더에 넣지 않음 (수신자에게 보이면 안 됨)
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # 실제 전송 시 모든 수신자를 목록으로
    # SMTP RCPT TO에는 BCC도 포함 (헤더에는 빼고)
    all_recipients = recipients + (cc or []) + (bcc or [])
    return msg, all_recipients

print("\n=== 4. 다중 수신자 ===")
msg, all_rcpt = send_to_multiple(
    'sender@ex.com',
    recipients=['a@ex.com', 'b@ex.com'],
    cc=['cc@ex.com'],
    bcc=['secret@ex.com'],
    subject='팀 공지',
    body='회의 일정입니다.'
)
print(f"To: {msg['To']}")
print(f"Cc: {msg['Cc']}")
# BCC가 헤더에 없지만 RCPT 대상에는 포함됨에 주목
print(f"실제 전송 대상: {all_rcpt}")

# === 5. SMTP 서버 연결 패턴 ===
print("\n=== 5. SMTP 연결 패턴 ===")
# 서비스별 연결 방식 차이 (TLS 모드/포트)
print("""
# Gmail 예시
with smtplib.SMTP('smtp.gmail.com', 587) as server:
    server.ehlo()      # SMTP 인사
    server.starttls()  # TLS 시작
    server.login('user@gmail.com', 'app_password')  # 앱 비밀번호
    server.send_message(msg)

# SSL 직접 연결 (포트 465)
with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
    server.login('user@gmail.com', 'app_password')
    server.send_message(msg)

# 네이버 예시
with smtplib.SMTP('smtp.naver.com', 587) as server:
    server.starttls()
    server.login('user@naver.com', 'password')
    server.send_message(msg)
""")

print("=== 핵심 정리 ===")
print("MIMEText: 텍스트/HTML 본문")
print("MIMEMultipart('alternative'): 텍스트+HTML 대체")
print("MIMEMultipart('mixed'): 본문+첨부")
print("SMTP: 587(STARTTLS) 또는 465(SSL)")
print("BCC는 헤더에 넣지 않고, send_message의 수신자 목록에만 포함")
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**
- 메시지는 「컨테이너(`MIMEMultipart`) + 파트(`MIMEText` · `MIMEBase`)」로 조립하고, 헤더는 사전처럼 넣는다.
- `alternative` 는 텍스트를 먼저, HTML 을 나중에 붙인다 — 마지막 파트가 우선이다.
- 첨부는 `'rb'` 로 읽고 `set_payload` → `encode_base64` → `Content-Disposition` 차례를 지킨다.
- 첨부 블록은 경로가 실제로 있을 때만 돌아서, 경로 없이 부르면 본문 파트만 남는다.
- BCC 는 헤더에 넣지 않고 `all_recipients` 에만 넣는다 — 원본 함수는 목록을 돌려줄 뿐 실제로 보내지 않는다.
- 연결은 587 + `starttls()` 또는 465 + `SMTP_SSL` 이며, 실습은 이 패턴을 문자열로 보여 주기만 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
