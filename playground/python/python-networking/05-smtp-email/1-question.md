# python/python-networking/05 — 이메일 전송: smtplib과 MIME — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `alternative` 메시지를 `walk()` 로 돌면 (예측)

```python
# 질문용 발췌
msg = MIMEMultipart('alternative')
msg.attach(MIMEText("평문", 'plain', 'utf-8'))
msg.attach(MIMEText("<p>HTML</p>", 'html', 'utf-8'))
print(f"Content-Type: {msg.get_content_type()}")
for part in msg.walk():
    print(f"  파트: {part.get_content_type()}")
```

- 몇 줄이 어떤 차례로 찍히나?

### 2. 파일 경로 없이 만든 첨부 메일 (예측)

```python
# 질문용 발췌
attach_msg = create_email_with_attachment(
    'a@ex.com', 'b@ex.com', '보고서', '첨부 파일을 확인하세요.'
)
for part in attach_msg.walk():
    print(f"  파트: {part.get_content_type()}")
```

- `file_path` 를 넘기지 않았을 때 찍히는 파트는 무엇무엇인가?

### 3. To · Cc · Bcc 를 넣은 다중 수신자 (예측)

```python
# 질문용 발췌
msg, all_rcpt = send_to_multiple(
    'sender@ex.com',
    recipients=['a@ex.com', 'b@ex.com'],
    cc=['cc@ex.com'],
    bcc=['secret@ex.com'],
)
print(f"To: {msg['To']}")
print(f"Cc: {msg['Cc']}")
print(f"실제 전송 대상: {all_rcpt}")
```

- 세 줄은 각각 무엇으로 찍히나?

### 4. BCC 를 헤더에 넣지 않는 까닭 (왜)

- 숨은 참조 주소를 `msg['Bcc']` 헤더에 넣으면 왜 안 되나?

### 5. `alternative` 에서 텍스트를 먼저, HTML 을 나중에 붙이는 까닭 (왜)

- 붙이는 차례가 왜 중요한가?

### 6. 첨부 파일을 base64 로 바꾸는 까닭 (왜)

- `set_payload` 로 실은 바이트를 왜 `encode_base64` 로 다시 인코딩하나?

### 7. 존재하지 않는 경로를 `file_path` 로 넘기면 (경계)

- `create_email_with_attachment` 는 오류를 내나, 아니면 어떤 메일이 되나?

### 8. `send_to_multiple` 이 실제로 하는 일과 그 표기 (경계)

- 이 함수를 부르면 메일이 서버로 나가나, 그리고 `-> MIMEMultipart` 표기는 실제 반환값과 맞나?

### 9. 헤더의 수신자와 SMTP 배달 목록 (연결)

- 편지 머리의 「받는 사람」과 우체국 창구에 내는 배달 목록이라는 비유로 보면, BCC 처리는 어느 쪽을 건드리는 일인가?

### 10. HTML 본문 · 텍스트 폴백 · 첨부 파일을 한 통에 (연결)

- `alternative` 상자와 `mixed` 상자를 어떻게 겹쳐야 세 가지를 모두 담을 수 있나?

## 실습

### 실습 1. 이메일 메시지 다섯 가지 꼴을 만들고 구조를 찍기

**만들 것** — 실제로 보내지 않고, 평문 · HTML 대체 · 첨부 · 다중 수신자 메시지를 만들어 구조를 찍고, SMTP 연결 패턴을 문자열로 보여 주는 스크립트를 만든다.

**준비물** — 표준 라이브러리(`smtplib` · `email` · `os`)만 쓴다. 실제 전송 함수는 정의만 하고 부르지 않으므로 메일 계정은 필요 없다.

**요구 조건**

1단계 — 평문 메일
1. `send_simple_email` 은 `MIMEText` 로 평문 본문을 만들고 `Subject` · `From` · `To` 헤더를 넣는다.
2. 같은 함수는 `with smtplib.SMTP(서버, 포트)` 안에서 `starttls()` → `login()` → `send_message()` 차례로 보내고 완료 문구를 찍는다.
3. 함수와 별도로 평문 메시지 객체를 만들어 `as_string()` 의 앞 300자와 `...` 을 찍는다.

2단계 — HTML 대체 메일
4. `create_html_email` 은 `MIMEMultipart('alternative')` 에 헤더를 넣고, 텍스트 파트를 먼저, HTML 파트를 나중에 붙여 돌려준다.
5. 만든 메시지의 `Content-Type` 을 찍고, `walk()` 로 모든 파트의 형식을 찍는다.

3단계 — 첨부 메일
6. `create_email_with_attachment` 는 `MIMEMultipart('mixed')` 에 헤더와 평문 본문을 붙인다.
7. `file_path` 가 있고 실제로 존재할 때만 파일을 바이트로 읽어 `MIMEBase('application', 'octet-stream')` 파트에 싣고, base64 로 인코딩하고, 파일 이름을 담은 `Content-Disposition` 헤더를 붙여 첨부한 뒤 「첨부: 이름」을 찍는다.
8. 파일 경로 없이 이 함수를 불러 `walk()` 로 파트 형식을 찍는다.

4단계 — 다중 수신자
9. `send_to_multiple` 은 `To` 와 (있으면) `Cc` 를 쉼표로 이어 헤더에 넣고, BCC 는 헤더에 넣지 않으며, 본문을 붙인다.
10. 같은 함수는 To · Cc · Bcc 를 모두 합친 전송 대상 목록을 메시지와 함께 돌려준다.
11. To 두 명 · Cc 한 명 · Bcc 한 명으로 불러 `To` · `Cc` 헤더와 전송 대상 목록을 찍는다.

5단계 — 연결 패턴과 정리
12. Gmail 587(`ehlo` · `starttls` · 앱 비밀번호 로그인) · SSL 465(`SMTP_SSL`) · 네이버 587 의 세 연결 패턴을 여러 줄 문자열로 찍는다.
13. 핵심 정리 다섯 줄(`MIMEText` · `alternative` · `mixed` · 포트 · BCC)을 찍는다.

**시작 코드**

```python
"""이메일 전송: smtplib, MIME 구조, 첨부 파일"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

# === 1. 간단한 텍스트 이메일 ===
def send_simple_email(smtp_server: str, port: int, sender: str, password: str,
                      recipient: str, subject: str, body: str):
    """간단한 텍스트 이메일 전송"""
    # TODO: MIMEText 로 평문 본문 만들기 (utf-8)
    # TODO: Subject / From / To 헤더
    # TODO: with smtplib.SMTP(...) 안에서 starttls → login → send_message
    print(f"이메일 전송 완료: {recipient}")

print("=== 1. 텍스트 이메일 구조 ===")
# TODO: "안녕하세요, Python에서 보낸 이메일입니다." 로 평문 메시지를 만들고
#       Subject='테스트 이메일', From='sender@example.com', To='recipient@example.com'
# TODO: as_string() 앞 300자 출력
print("...")

# === 2. HTML 이메일 ===
def create_html_email(sender: str, recipient: str, subject: str) -> MIMEMultipart:
    """HTML + 텍스트 대체 이메일 생성"""
    msg = None  # TODO: 텍스트/HTML 대체 컨테이너
    # TODO: 헤더 세 개

    text_body = "Python 학습 보고서\n- 완료: 기초 문법\n- 진행 중: 웹 프레임워크"
    html_body = """
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
    """
    # TODO: 두 본문을 각각 파트로 만들고, 올바른 차례로 attach
    return msg

print("\n=== 2. HTML 이메일 구조 ===")
html_msg = create_html_email('a@ex.com', 'b@ex.com', 'HTML 테스트')
# TODO: Content-Type 출력, walk() 로 "  파트: ..." 출력

# === 3. 첨부 파일 이메일 ===
def create_email_with_attachment(sender: str, recipient: str, subject: str,
                                 body: str, file_path: str = None) -> MIMEMultipart:
    """첨부 파일이 있는 이메일 생성"""
    # TODO: 본문 + 첨부 컨테이너, 헤더, 평문 본문 attach
    # TODO: 파일이 있을 때만 → 바이트로 읽기 → MIMEBase → set_payload
    #       → base64 인코딩 → Content-Disposition → attach → "첨부: 이름" 출력
    return msg

print("\n=== 3. 첨부 파일 이메일 구조 ===")
attach_msg = create_email_with_attachment(
    'a@ex.com', 'b@ex.com', '보고서', '첨부 파일을 확인하세요.'
)
# TODO: walk() 로 "  파트: ..." 출력

# === 4. 여러 수신자에게 전송 ===
def send_to_multiple(sender: str, recipients: list, cc: list = None,
                     bcc: list = None, subject: str = '', body: str = ''):
    """여러 수신자 (To, CC, BCC) 이메일"""
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    # TODO: To 헤더, (있으면) Cc 헤더 — BCC 는?
    # TODO: 본문 attach
    # TODO: 모든 수신자를 합친 전송 대상 목록
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
# TODO: To / Cc / 실제 전송 대상 출력

# === 5. SMTP 서버 연결 패턴 ===
print("\n=== 5. SMTP 연결 패턴 ===")
# TODO: Gmail 587 / SSL 465 / 네이버 587 패턴을 여러 줄 문자열로 출력

print("=== 핵심 정리 ===")
# TODO: 핵심 정리 다섯 줄
```

**확인 방법** — `python smtp-email.py` 로 돌려 다섯 절이 차례로 찍히는지 본다. 2절에 컨테이너와 두 파트가, 3절에 컨테이너와 본문 파트가, 4절의 `To` · `Cc` 줄에는 숨은 참조 주소가 없고 전송 대상 목록에는 있는지 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
