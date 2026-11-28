# python/python-networking/05 — 이메일 전송: smtplib과 MIME — 정리 (힌트)

> 출처 — study-site 항목 `python/smtp-email`(항목 데이터 `data/python/networking.json`) · 정답 코드 study-practice `python/python-networking/reference/smtp-email.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

## 한눈에 — 쉽게 말하면

**이메일 한 통은 「편지지를 봉투에 담아 우체국에 접수하는 일」이다.**
편지지에는 내용이 적히고, 편지 맨 위에는 「받는 사람 · 참조 · 제목」이 적힌다.
여러 장을 보내려면 서류봉투에 편지지와 동봉물을 함께 넣는다.
우체국 창구에는 편지와 별도로 「실제로 배달할 주소 목록」을 낸다.
숨은 참조(BCC)는 편지 머리에는 적지 않고 배달 목록에만 적는다.
Python 의 `email` 패키지와 `smtplib` 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 편지지 한 장 | `MIMEText` (텍스트 또는 HTML 본문 파트) |
| 서류봉투 | `MIMEMultipart` (여러 파트를 묶는 컨테이너) |
| 동봉한 파일 | `MIMEBase('application', 'octet-stream')` 첨부 파트 |
| 편지 머리의 받는 사람 · 참조 · 제목 | 헤더 `To` · `Cc` · `Subject` |
| 창구에 내는 배달 주소 목록 | SMTP 전송 대상 목록(`RCPT TO`) |
| 우체국 | SMTP 서버 |
| 봉인된 운송 차량 | TLS 암호화 연결 |

```text
  [메시지 객체 만들기]                     [보내기]
  MIMEMultipart ─┬─ MIMEText (본문)        smtplib.SMTP(서버, 587)
                 └─ MIMEBase (첨부)   ──▶    starttls() → login() → send_message()
  헤더: From / To / Cc / Subject             배달 목록 = To + Cc + Bcc
```

## 이 주제가 답하려는 질문

1. 이메일 메시지 객체는 무엇으로 어떻게 조립하나?
2. 「텍스트와 HTML 둘 다」와 「본문과 첨부 파일」은 구조가 어떻게 다른가?
3. SMTP 서버에 어떻게 안전하게 접속해서 메시지를 넘기나?
4. 숨은 참조 수신자를 다른 수신자에게 들키지 않게 하려면 어떻게 하나?

## 동작 방식

### (1) 한 파트짜리 텍스트 메일 — `MIMEText` 와 헤더

**언제 쓰나** — 첨부도 HTML 도 없는 평문 한 통을 보낼 때다.

```text
MIMEText(body, 'plain', 'utf-8')
        │
        ▼
 ┌─────────────────────────────┐
 │ Content-Type: text/plain    │  ← 자동으로 붙는다
 │ charset 정보                 │
 ├─────────────────────────────┤
 │ msg['Subject'] = ...         │  ← 사전처럼 헤더를 넣는다
 │ msg['From']    = ...         │
 │ msg['To']      = ...         │
 ├─────────────────────────────┤
 │ 본문                          │
 └─────────────────────────────┘
        │ msg.as_string()
        ▼
 「헤더 줄들 + 빈 줄 + 본문」 꼴의 문자열
```

- `MIMEText` 는 본문 문자열 · 하위 형식(`'plain'` 또는 `'html'`) · 문자 집합(`'utf-8'`)을 받는다.
- 이때 `Content-Type` 과 문자 집합 헤더가 자동으로 붙는다.
- 제목 · 보낸 사람 · 받는 사람은 `msg['Subject'] = …` 처럼 사전에 넣듯 헤더로 넣는다.
- `as_string()` 은 메시지를 RFC 822 형식의 문자열로 바꾼다 — 서버로 실제로 흘러가는 글의 꼴이다.
- 원본 예제는 실제로 보내지 않고 이 문자열의 앞 300자만 찍어 구조를 보여 준다.

> **MIME** — 이메일 한 통에 여러 형식의 내용(텍스트 · HTML · 파일)을 담기 위한 규격이다.\
> 예: `text/plain` · `text/html` · `multipart/mixed` 가 MIME 형식 이름이다.

> **헤더** — 메시지 맨 위에 붙는 「이름: 값」 줄들이다.\
> 예: `Subject: 테스트 이메일`.

### (2) 텍스트와 HTML 을 함께 — `MIMEMultipart('alternative')`

**언제 쓰나** — 꾸민 HTML 메일을 보내되, HTML 을 못 읽는 메일 프로그램에서도 내용이 보이게 하고 싶을 때다.

```text
msg = MIMEMultipart('alternative')
msg.attach(text_part)   # 1번째: text/plain  (폴백)
msg.attach(html_part)   # 2번째: text/html   (우선)

 multipart/alternative
 ├── text/plain   "Python 학습 보고서 - 완료: ..."
 └── text/html    "<h1>Python 학습 보고서</h1> ..."
        │
        ▼
 수신자 프로그램이 둘 중 하나를 골라 보여 준다
 (HTML 을 읽을 수 있으면 HTML, 아니면 텍스트)
```

- `'alternative'` 는 「같은 내용의 다른 표현」이라는 뜻이다.
- 두 파트는 내용이 같고 형식만 다르다 — 수신자 쪽이 선호하는 형식을 고른다.
- 원본 주석은 「`alternative` 는 마지막에 `attach` 한 파트가 우선」이라고 한다.
- 그래서 텍스트를 먼저, HTML 을 나중에 붙인다 — 그러면 HTML 이 우선 표시된다.
- 텍스트 파트는 HTML 을 못 읽는 클라이언트를 위한 폴백 본문이다.

> **폴백(fallback)** — 우선 선택지를 못 쓸 때 대신 쓰는 예비 선택지다.\
> 예: HTML 을 못 그리는 메일 프로그램은 `text/plain` 파트를 보여 준다.

### (3) 본문과 첨부 파일 — `MIMEMultipart('mixed')`

**언제 쓰나** — 본문 글에 파일을 붙여 보낼 때다.

```text
msg = MIMEMultipart('mixed')
msg.attach(MIMEText(body, 'plain', 'utf-8'))          # 본문

open(file_path, 'rb')  ─▶ 바이트
MIMEBase('application', 'octet-stream')               # 일반 바이너리 파트
  .set_payload(바이트)                                  # 원시 바이트를 싣는다
encoders.encode_base64(part)                          # base64 로 바꾼다
part.add_header('Content-Disposition',
                'attachment; filename="report.pdf"')  # 첨부 + 파일 이름
msg.attach(part)

 multipart/mixed
 ├── text/plain                  본문
 └── application/octet-stream    첨부 (base64)
```

- `'mixed'` 는 서로 독립된 파트(본문 하나 · 첨부 여럿)를 나란히 담는 구조다.
- 파일은 `'rb'`(바이너리 읽기)로 연다.
- `MIMEBase('application', 'octet-stream')` 는 「종류를 따지지 않는 일반 바이너리」 파트다.
- `set_payload` 로 원시 바이트를 싣고, `encoders.encode_base64` 로 base64 로 바꾼다.
- 원본 주석의 까닭은 「이메일은 7비트 ASCII 만 안전하게 전송된다」이다.
- `Content-Disposition: attachment; filename="…"` 헤더가 「이것은 첨부 파일이고 이름은 …이다」를 알린다.
- 파일 이름은 `os.path.basename` 으로 경로를 떼고 이름만 쓴다.
- 원본 함수는 `file_path` 가 비어 있거나 `os.path.exists` 가 거짓이면 첨부 블록을 통째로 건너뛴다 — 오류 없이 본문만 있는 메일이 된다.

> **base64** — 임의의 바이트를 영문자 · 숫자 · 몇몇 기호만으로 바꾸는 인코딩이다.\
> 예: 그림 파일의 바이트를 글자만으로 된 긴 문자열로 바꿔 메일에 싣는다.

> **`Content-Disposition`** — 파트를 본문에 바로 보일지(인라인) 첨부로 다룰지 알리는 헤더다.\
> 예: `attachment; filename="report.pdf"`.

### (4) 파트 돌아보기와 겹쳐 담기 — `walk()`

**언제 쓰나** — 만든 메시지가 어떤 파트로 이루어졌는지 확인할 때다.

```text
for part in msg.walk():
    print(part.get_content_type())

 multipart/alternative      ← 1. 자기 자신(컨테이너)부터
 ├── text/plain             ← 2. 첫 자식
 └── text/html              ← 3. 둘째 자식
```

- `walk()` 는 모든 파트를 재귀로 순회한다 — 원본 주석 그대로다.
- 컨테이너 자신이 먼저 나오고, 그 안의 파트가 붙인 차례대로 나온다.
- `get_content_type()` 은 `'multipart/alternative'` · `'text/plain'` 처럼 「주형식/하위형식」 문자열을 돌려준다.
- `MIMEMultipart()` 를 하위 형식 없이 만들면 `multipart/mixed` 가 된다(원본 4번 예제가 이렇게 만든다).
- `attach` 는 MIME 파트라면 무엇이든 받으므로, 컨테이너 안에 컨테이너를 넣을 수도 있다.
- 예를 들어 「HTML 본문 + 텍스트 폴백 + 첨부 파일」은 `mixed` 상자 안에 `alternative` 상자와 첨부 파트를 나란히 넣는 꼴이 된다 (원본에 근거 없음 — 추론).

```text
 multipart/mixed
 ├── multipart/alternative
 │   ├── text/plain
 │   └── text/html
 └── application/octet-stream
```

### (5) 헤더의 수신자와 실제 전송 대상 — To · Cc · Bcc

**언제 쓰나** — 여러 사람에게 보내면서 일부는 몰래(숨은 참조로) 넣을 때다.

```text
recipients = ['a@ex.com', 'b@ex.com']
cc         = ['cc@ex.com']
bcc        = ['secret@ex.com']

 헤더 (모든 수신자가 본다)              전송 대상 목록 (서버만 본다)
 To: a@ex.com, b@ex.com               ['a@ex.com', 'b@ex.com',
 Cc: cc@ex.com                         'cc@ex.com', 'secret@ex.com']
 (Bcc 줄 없음)
```

- `To` 와 `Cc` 는 여러 주소를 `', '.join(...)` 으로 쉼표로 이어 한 헤더 값으로 넣는다.
- `Cc` 는 목록이 있을 때만 넣는다.
- 헤더는 메시지의 일부라 모든 수신자에게 그대로 보인다.
- 그래서 BCC 는 헤더에 넣지 않는다 — 넣으면 숨은 참조가 숨지 않는다.
- 대신 실제 전송 대상 목록에는 `recipients + (cc or []) + (bcc or [])` 로 셋을 모두 넣는다.
- 원본 주석대로 SMTP 의 `RCPT TO`(서버에 「이 주소로 배달하라」고 알리는 명령)에는 BCC 도 들어간다.
- `(cc or [])` 는 `cc` 가 `None` 일 때 빈 목록으로 바꿔 `+` 가 깨지지 않게 하는 꼴이다.

> **BCC(숨은 참조)** — 다른 수신자 모르게 사본을 받는 사람이다.\
> 예: 팀 공지를 보내며 상사에게 몰래 사본을 보낸다.

### (6) SMTP 서버에 접속해 보내기 — STARTTLS 와 SSL

**언제 쓰나** — 만든 메시지를 실제 메일 서버로 넘길 때다.

```text
 포트 587 (STARTTLS)                     포트 465 (SSL 직접)
 smtplib.SMTP(서버, 587)                  smtplib.SMTP_SSL(서버, 465)
   │ 평문 연결로 시작                        │ 처음부터 암호화 연결
   ├─ ehlo()      SMTP 인사 (선택)          │
   ├─ starttls()  암호화로 업그레이드         │
   ├─ login(id, pw)                       ├─ login(id, pw)
   └─ send_message(msg)                   └─ send_message(msg)
   with 블록이 끝나면 연결을 닫는다
```

- `smtplib` 은 SMTP 클라이언트다 — 원본 주석은 쓰는 포트로 25 · 587 · 465 를 든다.
- 587 은 평문으로 연결한 뒤 `starttls()` 로 TLS 암호화로 업그레이드하는 방식이다.
- `starttls()` 이후의 통신(로그인 비밀번호 포함)은 모두 암호화된다.
- 465 는 `SMTP_SSL` 로 처음부터 암호화된 연결을 연다 — `starttls()` 를 부르지 않는다.
- `ehlo()` 는 SMTP 인사다 — 원본의 Gmail 예시만 명시적으로 부른다.
- `login` 으로 인증한 뒤 `send_message(msg)` 로 보낸다.
- 원본 주석은 `send_message` 가 「헤더의 To/Cc 를 자동으로 쓴다」고 한다.
- 팁에 따르면 Gmail 은 계정 비밀번호가 아니라 앱 비밀번호가 필요하다.
- `with smtplib.SMTP(...) as server:` 꼴로 쓰면 블록이 끝날 때 연결이 정리된다.

> **SMTP** — 메일을 서버로 보내고 서버끼리 주고받는 프로토콜이다.\
> 예: `smtp.gmail.com` 의 587 번 포트로 접속해 메일을 넘긴다.

> **STARTTLS** — 평문으로 연 연결을 도중에 TLS 암호화 연결로 바꾸는 명령이다.\
> 예: `server.starttls()` 를 부른 뒤에 `login` 한다.

## 문법 — 형태와 규칙

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

msg = MIMEMultipart('alternative')
msg['Subject'] = '주간 보고'
msg['From'] = 'me@example.com'
msg['To'] = 'you@example.com'
msg.attach(MIMEText('보고 내용', 'plain', 'utf-8'))
msg.attach(MIMEText('<p>보고 내용</p>', 'html', 'utf-8'))

with smtplib.SMTP('smtp.example.com', 587) as server:
    server.starttls()
    server.login('me@example.com', '비밀번호')
    server.send_message(msg)
```

| 도구 | 하는 일 |
|---|---|
| `MIMEText(본문, 'plain'\|'html', 'utf-8')` | 텍스트 또는 HTML 본문 파트 |
| `MIMEMultipart('alternative')` | 같은 내용의 텍스트/HTML 대체 묶음 |
| `MIMEMultipart('mixed')` · `MIMEMultipart()` | 본문 + 첨부 묶음 |
| `MIMEBase('application', 'octet-stream')` | 임의 바이너리 첨부 파트 |
| `part.set_payload(바이트)` | 파트에 원시 바이트를 싣는다 |
| `encoders.encode_base64(part)` | 파트를 base64 로 인코딩한다 |
| `part.add_header('Content-Disposition', 'attachment; filename="…"')` | 첨부와 파일 이름 지정 |
| `msg.attach(part)` | 컨테이너에 파트를 붙인다 |
| `msg.walk()` | 모든 파트를 재귀로 순회 |
| `msg.get_content_type()` | `'text/plain'` 같은 형식 이름 |
| `msg.as_string()` | RFC 822 형식 문자열로 |
| `smtplib.SMTP(서버, 587)` + `starttls()` | 평문 연결 → TLS 업그레이드 |
| `smtplib.SMTP_SSL(서버, 465)` | 처음부터 SSL 연결 |
| `server.login(id, pw)` · `server.send_message(msg)` | 인증 · 전송 |

- 헤더는 `msg['이름'] = 값` 으로 넣고 `msg['이름']` 으로 읽는다.
- 여러 주소는 `', '.join(목록)` 으로 이어 한 헤더 값으로 만든다.
- `alternative` 에서는 텍스트를 먼저, HTML 을 나중에 `attach` 한다.
- 첨부 파일은 `'rb'` 로 열어 바이트로 읽는다.
- BCC 주소는 헤더가 아니라 전송 대상 목록에만 둔다.

## 어디서 틀리나

### 1. `alternative` 와 `mixed` 를 바꿔 쓴다

`alternative` 는 「같은 내용의 다른 표현 중 하나를 골라 보여 줘라」이고, `mixed` 는 「독립된 파트를 모두 담아라」다.
첨부 파일을 `alternative` 에 넣으면 본문의 대체 표현으로 취급된다.
텍스트/HTML 을 `mixed` 에 넣으면 같은 내용이 두 번 보일 수 있다 (원본에 근거 없음 — 추론).

### 2. `alternative` 에서 붙이는 차례를 거꾸로 한다

원본 주석대로 마지막에 붙인 파트가 우선이다.
HTML 을 먼저, 텍스트를 나중에 붙이면 HTML 을 읽을 수 있는 프로그램에서도 평문이 보일 수 있다.

### 3. BCC 를 헤더에 넣는다

헤더는 모든 수신자에게 보인다.
`msg['Bcc'] = …` 를 넣으면 숨은 참조 명단이 드러난다.
BCC 는 헤더에 넣지 않고 전송 대상 목록에만 포함해야 한다 — 원본 팁의 핵심이다.

### 4. BCC 를 전송 대상에서도 빼먹는다

헤더에서 뺀 BCC 를 전송 목록에도 넣지 않으면 그 사람에게는 아예 배달되지 않는다.
헤더에서 빼는 것과 배달 목록에 넣는 것은 짝이다.

### 5. 원본 `send_to_multiple` 은 이름과 달리 보내지 않는다

함수 이름은 「여러 명에게 보낸다」지만 실제로는 `(msg, all_recipients)` 튜플을 만들어 돌려줄 뿐 `smtplib` 을 부르지 않는다.
원본 팁은 「`send_message` 의 수신자 목록에만 포함」이라고 하지만, 예제에는 그 목록을 `send_message` 에 넘기는 줄이 없다.
반환 타입 표기도 `-> MIMEMultipart` 인데 실제로는 튜플을 돌려준다 — 표기가 틀렸다.

### 6. 첨부 파일 경로가 틀려도 조용히 넘어간다

`create_email_with_attachment` 는 `os.path.exists(file_path)` 가 거짓이면 첨부 블록을 건너뛴다.
오류가 나지 않으므로, 첨부가 빠진 메일이 그대로 나갈 수 있다.
원본 실행부는 `file_path` 를 아예 넘기지 않는다 — 그래서 본문 파트만 생긴다.

### 7. 바이너리 첨부를 인코딩하지 않는다

`set_payload` 로 실은 원시 바이트를 `encode_base64` 없이 두면, 원본 주석의 말대로 7비트 ASCII 로만 안전한 경로에서 깨질 수 있다.

### 8. Gmail 계정 비밀번호로 로그인한다

원본 팁에 따르면 Gmail 은 앱 비밀번호가 필요하다.
코드가 맞아도 `login` 단계에서 막힐 수 있다.

### 9. 포트와 연결 방식을 엇갈리게 짝짓는다

587 은 `SMTP` + `starttls()`, 465 는 `SMTP_SSL` 이다.
465 에 평문 `SMTP` 로 붙거나 `SMTP_SSL` 연결에서 다시 `starttls()` 를 부르는 것은 원본의 짝과 다르다.

### 10. 원본 주석의 「7비트 ASCII 만 안전」

원본의 주장 → 「이메일은 7비트 ASCII 만 안전하게 전송된다」.
왜 의심스러운가 → 8비트 전송을 허용하는 SMTP 확장이 있다고 알려져 있어, 「만」이라는 단정은 지나칠 수 있다 (확인 필요).
다만 base64 로 바꿔 두면 어느 경로로 가도 안전하다는 결론은 그대로다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `MIMEText` · `MIMEMultipart` · `walk()` · `as_string()` 의 동작 | Python 표준 라이브러리 `email` 패키지 (언어 문법이 아니라 라이브러리 규약) |
| `MIMEMultipart()` 의 기본 하위 형식이 `mixed` | `email` 패키지 문서 (확인 필요) |
| `alternative` 는 마지막 파트가 우선 | MIME 규격의 권고 — 실제로 무엇을 보일지는 각 메일 프로그램 구현이 정한다 (확인 필요) |
| `send_message` 가 헤더의 To/Cc 를 수신자로 쓴다 | `smtplib` 의 동작 (원본 주석) |
| 587 은 STARTTLS, 465 는 SSL | 메일 서비스들의 관례 · 설정 — Python 이 보장하지 않는다 |
| Gmail 은 앱 비밀번호가 필요 | Gmail 서비스 정책 — 바뀔 수 있다 (확인 필요) |
| BCC 를 헤더에 넣지 않는다 | 코드를 짜는 쪽의 책임 — 라이브러리가 막아 주는 규칙이 아니다 (원본 예제 기준) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 평문 한 통 | `MIMEText(body, 'plain', 'utf-8')` 하나 | 쓸데없는 `MIMEMultipart` |
| HTML 메일 + 평문 폴백 | `MIMEMultipart('alternative')`, 텍스트 → HTML 차례 | `mixed` |
| 본문 + 파일 | `MIMEMultipart('mixed')` + `MIMEBase` + `encode_base64` | 인코딩 없는 원시 바이트 |
| 숨은 참조 | 전송 대상 목록에만 추가 | `msg['Bcc']` 헤더 |
| 587 포트 | `SMTP` + `starttls()` | 암호화 없이 `login` |
| 465 포트 | `SMTP_SSL` | `SMTP` 평문 연결 |
| 구조만 확인 | `as_string()` · `walk()` | 실제 서버로 시험 발송 |

## 핵심 문장

1. **메시지는 파트로 조립한다** — `MIMEText` 가 내용 한 장, `MIMEMultipart` 가 그것들을 담는 상자다.
2. **`alternative` 는 「같은 내용 중 하나 고르기」, `mixed` 는 「전부 담기」다** — 텍스트/HTML 은 앞의 것, 본문/첨부는 뒤의 것.
3. **첨부 파일은 바이트로 읽어 base64 로 바꾸고 `Content-Disposition` 으로 이름을 단다.**
4. **헤더의 수신자와 실제 배달 목록은 다르다** — BCC 는 배달 목록에만 있다.
5. **연결은 587 + `starttls()` 또는 465 + `SMTP_SSL`** 이고, 그 다음이 `login` → `send_message` 다.

## 관련 자료

- `http-server` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `url-parsing` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `environment` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/networking.json` 의 `smtp-email`

## 용어 풀이

- **SMTP** — 메일을 보내는 프로토콜이다.
- **`smtplib`** — Python 표준 라이브러리의 SMTP 클라이언트다.
- **MIME** — 메일에 여러 형식의 내용을 담는 규격이다.
- **파트** — MIME 메시지를 이루는 조각 하나다.
- **`MIMEText`** — 텍스트 · HTML 본문 파트를 만드는 클래스다.
- **`MIMEMultipart`** — 여러 파트를 묶는 컨테이너 클래스다.
- **`MIMEBase`** — 임의 첨부 파일용 기본 파트 클래스다.
- **`alternative`** — 같은 내용의 다른 표현을 묶는 하위 형식이다.
- **`mixed`** — 독립된 파트를 나란히 묶는 하위 형식이다.
- **`octet-stream`** — 종류를 따지지 않는 일반 바이너리 형식이다.
- **payload** — 파트에 실린 실제 내용이다.
- **base64** — 바이트를 글자로만 표현하는 인코딩이다.
- **`Content-Type`** — 파트의 형식을 알리는 헤더다.
- **`Content-Disposition`** — 인라인인지 첨부인지와 파일 이름을 알리는 헤더다.
- **헤더** — 메시지 위쪽의 「이름: 값」 줄이다.
- **To · Cc · Bcc** — 받는 사람 · 참조 · 숨은 참조다.
- **RCPT TO** — 서버에 배달할 주소를 알리는 SMTP 명령이다.
- **TLS · SSL** — 통신을 암호화하는 방식이다.
- **STARTTLS** — 평문 연결을 도중에 TLS 로 바꾸는 명령이다.
- **EHLO** — 클라이언트가 서버에 건네는 SMTP 인사다.
- **앱 비밀번호** — 계정 비밀번호 대신 프로그램 로그인에 쓰는 별도 비밀번호다.
- **폴백** — 우선 선택지를 못 쓸 때의 예비 선택지다.
- **RFC 822 형식** — 헤더 줄과 본문으로 이루어진 메일 문자열 꼴이다.

## 더 들어가면

- `send_message` 에 수신자를 따로 넘기지 않으면 `To` · `Cc` 뿐 아니라 `Bcc` 헤더까지 읽어 배달하고, 전송하는 글에서는 `Bcc` 헤더를 지운다고 알려져 있다 (확인 필요).
- 명시적으로 수신자를 넘기려면 `server.send_message(msg, to_addrs=all_recipients)` 꼴로 쓴다 (확인 필요).
- `starttls()` 는 필요하면 안에서 `ehlo` 를 먼저 부른다고 알려져 있어, 원본의 명시적 `ehlo()` 는 생략해도 되는 경우가 많다 (확인 필요).
- `MIMEText` 에 `'utf-8'` 을 주면 본문이 base64 로 인코딩되어 `as_string()` 에서 한글이 그대로 보이지 않을 수 있다 (확인 필요).
- 한글 제목도 `=?utf-8?…?=` 꼴로 인코딩되어 찍힐 수 있다 (확인 필요).
- 최신 Python 에는 `email.message.EmailMessage` 와 `set_content` · `add_alternative` · `add_attachment` 를 쓰는 더 간단한 API 가 있다 (확인 필요).
- 첨부 파일의 MIME 형식을 `octet-stream` 대신 `mimetypes.guess_type` 으로 추정해 넣을 수도 있다 (확인 필요).
- 네이버 SMTP 도 메일 설정에서 SMTP 사용을 켜야 할 수 있다 (확인 필요).
