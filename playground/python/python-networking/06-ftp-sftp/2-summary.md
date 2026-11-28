# python/python-networking/06 — FTP와 SFTP 파일 전송 — 정리 (힌트)

> 출처 — study-site 항목 `python/ftp-sftp`(항목 데이터 `data/python/networking.json`) · 정답 코드 study-practice `python/python-networking/reference/ftp-sftp.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

## 한눈에 — 쉽게 말하면

**FTP 는 「열린 창구에서 소리쳐 주고받는 택배」다.**
창구에서는 「이 상자 맡길게요」「그 상자 주세요」 같은 말이 오간다(명령 채널).
상자는 그 옆의 컨베이어로 따로 오간다(데이터 채널).
문제는 창구의 대화도, 상자의 내용물도 지나가는 누구나 들여다볼 수 있다는 점이다(평문).
SFTP 는 잠긴 터널(SSH) 하나를 뚫고, 그 안에서 대화와 상자를 모두 주고받는 다른 택배사다.
FTPS 는 옛 창구 방식을 그대로 두고, 대화와 컨베이어에 덮개(TLS)를 씌운 방식이다.
파이썬 코드도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 창구의 대화 | FTP 명령 채널 (포트 21) — `STOR` · `RETR` 같은 명령 |
| 컨베이어 | FTP 데이터 채널 — 파일 내용과 목록이 지나가는 별도 연결 |
| 「이 상자 맡길게요」 | `ftp.storbinary('STOR 이름', 파일객체)` |
| 「그 상자 주세요」 | `ftp.retrbinary('RETR 이름', 콜백)` |
| 잠긴 터널 하나 | SSH (포트 22) 위의 SFTP — `paramiko` |
| 창구에 씌운 덮개 | FTPS — `ftplib.FTP_TLS` |

```text
 FTP (평문)                       SFTP (SSH)                 FTPS (FTP + TLS)
 ┌──────┐  명령 :21  ┌──────┐     ┌──────┐  :22 ┌──────┐     ┌──────┐ 명령 :21 ┌──────┐
 │클라이│──────────▶│서버  │     │클라이│═════▶│서버  │     │클라이│═════════▶│서버  │
 │언트  │  데이터    │      │     │언트  │ 하나 │      │     │언트  │ 데이터   │      │
 │      │◀─────────▶│      │     │      │ 암호 │      │     │      │◀════════▶│      │
 └──────┘ (둘 다 평문)└──────┘     └──────┘      └──────┘     └──────┘ (둘 다 TLS)└──────┘
                                                              ↑ 데이터 쪽은 prot_p() 로 켠다
```

## 이 주제가 답하려는 질문

1. 파이썬 표준 라이브러리만으로 FTP 서버에 파일을 올리고 내려받으려면 무엇을 부르나?
2. 디스크에 없는 데이터(메모리의 `bytes`)는 어떻게 올리나?
3. 연결과 정리(로그인 · 종료)를 빠뜨리지 않게 하려면 어떻게 감싸나?
4. FTP · SFTP · FTPS 는 무엇이 다르고, 왜 평문 FTP 를 피하나?

## 동작 방식

### (1) 예제 스크립트가 실제로 하는 일

**언제 쓰나** — 예제 파일을 그냥 실행했을 때 무엇이 일어나고 무엇이 일어나지 않는지 가를 때 본다.

```text
python ftp-sftp.py
  │
  ├─ import ftplib, os, BytesIO          ← 표준 라이브러리만 들여온다
  ├─ ftp_demo_operations()               ← FTP 사용 패턴을 「문자열로」 print
  ├─ class FTPClient: ...                ← 정의만 한다 (객체를 만들지 않는다)
  ├─ print(SFTP 패턴 문자열)             ← "import paramiko" 도 문자열 안에 있을 뿐
  ├─ for ... in comparisons: print(...)  ← FTP vs SFTP 비교 표
  ├─ print(FTPS 패턴 문자열)
  └─ print(핵심 정리 4줄)
```

그림 해설:
- 스크립트가 들여오는 모듈은 `ftplib` · `os` · `io.BytesIO` 셋이고, 모두 표준 라이브러리다.
- `ftp_demo_operations()` 는 FTP 연산의 꼴을 삼중 따옴표 문자열로 담아 `print` 할 뿐이다.
- `FTPClient` 는 클래스 정의만 있고, 스크립트 안에서 `FTPClient(...)` 를 부르는 줄은 없다.
- `import paramiko` 는 문자열 안의 글자일 뿐이라 실제로 실행되는 `import` 문이 아니다.
- 그래서 이 스크립트는 서버에 접속하지 않고, 화면에 사용법과 비교 표를 찍고 끝난다.
- `import os` 는 들여오기만 하고 본문에서 쓰지 않는다.

### (2) FTP 연결 — 명령 채널과 데이터 채널

**언제 쓰나** — FTP 서버에 붙어 로그인하고, 디렉터리를 옮기고 목록을 볼 때 쓴다.

```text
ftp = FTP('ftp.example.com')     →  포트 21 로 명령 채널을 연다
ftp.login('user', 'password')    →  USER / PASS 를 명령 채널로 보낸다 (평문)
ftp.getwelcome()                 →  서버가 처음 보낸 환영 문구
ftp.cwd('/uploads')              →  서버 쪽 「현재 디렉터리」를 바꾼다
ftp.nlst()                       →  데이터 채널을 열어 이름만 받아 list 로 돌려준다
ftp.dir()                        →  상세 목록 (ls -l 꼴)
```

그림 해설:
- `FTP(호스트)` 를 만들면 서버의 명령 채널(포트 21)에 연결된다.
- `login(사용자, 비밀번호)` 은 계정 정보를 보낸다.
- 인자 없이 `login()` 을 부르면 익명 로그인이다.
- 명령 채널과 데이터 채널은 분리되어 있고, 둘 다 평문이다 — 원본 주석이 「보안 취약」이라 적은 까닭이다.
- `cwd` 는 서버 쪽 현재 디렉터리를 바꾼다.
- 그 뒤의 상대 경로(파일 이름만 쓴 것)는 바뀐 디렉터리를 기준으로 해석된다.
- `nlst` 는 이름만(간단한 `ls`), `dir` 는 상세 목록(`ls -l` 꼴)이다.

> **명령 채널** — FTP 에서 명령과 응답(`STOR` · `RETR` · 로그인 등)이 오가는 연결, 기본 포트 21.\
> 예: `ftp.login('user', 'pw')` 의 계정 정보가 이 채널로 간다.

> **데이터 채널** — 파일 내용과 목록이 실제로 지나가는, 명령 채널과 별개인 연결.\
> 예: `retrbinary` 로 받는 파일의 바이트가 이 채널로 온다.

### (3) 업로드와 다운로드 — `storbinary` · `retrbinary`

**언제 쓰나** — 파일 하나를 서버에 올리거나 서버에서 받아 올 때 쓴다.
원본 팁의 말대로, 이 둘이 바이너리 파일 전송의 핵심이다.

```text
업로드                                          다운로드
with open('local.txt', 'rb') as f:              with open('down.txt', 'wb') as f:
    ftp.storbinary('STOR remote.txt', f)            ftp.retrbinary('RETR remote.txt', f.write)
          │                 │                                │                  │
     "STOR 이름"        읽을 파일객체                  "RETR 이름"     조각마다 부를 함수
          ▼                                                   ▼
  f 를 조금씩 읽어 데이터 채널로 보냄            데이터 채널로 온 조각(bytes)을
  → 서버에 remote.txt 로 저장                    f.write(조각) 으로 차례로 넘김
```

그림 해설:
- 첫 인자는 FTP 명령 문자열이다 — `STOR <이름>` 은 「서버에 저장하라」, `RETR <이름>` 은 「서버에서 보내라」.
- `storbinary` 의 둘째 인자는 **읽을 수 있는 파일 객체**다 — 함수가 그 객체에서 바이트를 꺼내 보낸다.
- `retrbinary` 의 둘째 인자는 **콜백(함수)** 이다 — 받은 데이터 조각(청크)마다 그 함수를 부른다.
- 그래서 다운로드에는 파일 객체 `f` 가 아니라 그 객체의 메서드 `f.write` 를 넘긴다.
- 파일은 `'rb'` · `'wb'`(바이너리 모드)로 연다.
- 바이너리 모드는 바이트를 바꾸지 않고 그대로 옮기므로 어떤 파일 형식이든 안전하다(원본 주석).
- 줄 단위 텍스트 전송용으로는 `storlines('STOR 이름', f)` 가 따로 있다.

> **콜백** — 다른 함수에 넘겨 두면 그 함수가 알맞은 때에 대신 불러 주는 함수.\
> 예: `retrbinary(..., f.write)` 에서 `f.write` 가 조각마다 불린다.

> **청크** — 큰 데이터를 나눠 보낼 때의 한 조각.\
> 예: 큰 파일을 받을 때 `f.write` 가 청크마다 여러 번 불린다.

### (4) 메모리에서 바로 올리기 — `BytesIO`

**언제 쓰나** — 프로그램 안에서 만든 `bytes`(생성한 보고서, 압축 결과 등)를 디스크에 임시 파일로 쓰지 않고 바로 올릴 때 쓴다.

```text
data = b'hello'                    메모리의 bytes
BytesIO(data)                      → 파일처럼 read() 할 수 있는 객체로 감쌈
storbinary('STOR x.bin', 그 객체)   → storbinary 는 「파일객체」만 원하므로 그대로 받아들임
```

그림 해설:
- `storbinary` 는 둘째 인자에서 바이트를 읽어 갈 뿐, 그것이 진짜 디스크 파일인지는 따지지 않는다.
- `BytesIO` 는 메모리의 바이트를 파일 객체처럼 읽게 해 주는 표준 라이브러리 객체다.
- 그래서 `bytes` 를 `BytesIO` 로 감싸면 디스크를 거치지 않고 업로드할 수 있다.
- 예제의 `upload_bytes(data, remote_path)` 메서드가 정확히 이 일을 한다.

> **BytesIO** — `io` 모듈의, 메모리 안의 바이트를 파일 객체처럼 다루게 해 주는 클래스.\
> 예: `BytesIO(b'abc').read()` 는 `b'abc'` 를 돌려준다.

### (5) `with` 로 감싸기 — `FTPClient`

**언제 쓰나** — 연결 · 로그인 · 종료를 매번 손으로 쓰지 않고, 블록을 벗어나면 저절로 끊기게 할 때 쓴다.

```text
with FTPClient('host', 'user', 'pass') as ftp:
  │
  ├─ __init__   : host / user / passwd 저장, self.ftp = None
  ├─ __enter__  : self.ftp = ftplib.FTP(host) → login(user, passwd) → return self
  │                                                          (as ftp 에 self 가 묶인다)
  ├─ 본문        : ftp.upload(...) / ftp.download(...) / ftp.list_files(...) / ftp.upload_bytes(...)
  │
  └─ __exit__   : if self.ftp: self.ftp.quit()    ← 블록을 벗어날 때 (예외가 나도) QUIT
```

그림 해설:
- `__init__` 은 연결하지 않는다 — 정보만 저장하고 `self.ftp` 를 `None` 으로 둔다.
- `__enter__` 가 실제로 연결하고 로그인한 뒤 `self` 를 돌려준다.
- 그래서 `as ftp` 에 묶이는 것은 `ftplib.FTP` 객체가 아니라 `FTPClient` 객체다.
- 본문이 정상으로 끝나든 예외로 끝나든, `__exit__` 가 불려 `quit()`(QUIT 명령)으로 정상 종료한다.
- `__exit__` 가 아무것도 돌려주지 않으므로(`None`) 본문의 예외는 삼켜지지 않고 바깥으로 나간다.
- 메서드 넷은 각각 업로드(`upload`), 다운로드(`download`), 이름 목록(`list_files`), 메모리 업로드(`upload_bytes`)다.
- `upload` · `download` 는 끝에 `업로드: A -> B` · `다운로드: A -> B` 꼴의 줄을 찍는다.
- `list_files(path)` 는 먼저 `cwd(path)` 로 서버 디렉터리를 옮긴 뒤 `nlst()` 를 돌려준다 — 이동한 상태가 그 뒤에도 남는다.

> **컨텍스트 매니저** — `with` 문에 쓸 수 있도록 `__enter__` 와 `__exit__` 를 갖춘 객체.\
> 예: `with open(...) as f:` 의 파일 객체, 이 예제의 `FTPClient`.

### (6) SFTP — `paramiko` 로 SSH 위에서

**언제 쓰나** — 전송 전체를 암호화해야 하거나, 비밀번호 대신 SSH 키로 로그인해야 할 때 쓴다.

```text
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('hostname', username='user', password='pass')     ← 또는 key_filename='~/.ssh/id_rsa'
        │  포트 22, SSH 연결 하나 (전 구간 암호화)
        ▼
sftp = ssh.open_sftp()          ← 그 SSH 연결 위에서 SFTP 서브시스템을 연다
sftp.put(로컬, 원격)             업로드
sftp.get(원격, 로컬)             다운로드
sftp.listdir(경로)               목록
sftp.stat(경로) → st_size, st_mtime   크기 · 수정 시각
sftp.mkdir(경로)                 디렉터리 생성
sftp.close(); ssh.close()        정리 (SFTP 먼저, SSH 나중)
```

그림 해설:
- SFTP 는 FTP 에 무엇을 덧댄 것이 아니라, SSH 의 서브시스템이다(원본 주석).
- 그래서 포트 22 하나만 쓰고, 명령과 데이터가 모두 그 암호화된 연결 안을 지난다.
- `paramiko` 는 표준 라이브러리가 아니라 `pip install` 로 설치하는 외부 패키지다.
- 연결은 두 단계다 — `SSHClient` 로 SSH 에 접속하고, `open_sftp()` 로 SFTP 를 연다.
- 인증은 비밀번호와 키 파일(`key_filename`) 둘 다 된다.
- `put` · `get` 은 경로 문자열을 받는다 — `ftplib` 처럼 파일 객체나 콜백을 넘기지 않는다.
- 다 쓰면 `sftp.close()` 다음 `ssh.close()` 로 닫는다.

> **SSH** — 원격 컴퓨터에 암호화된 연결로 접속하는 프로토콜, 기본 포트 22.\
> 예: `ssh user@host` 로 원격 셸에 들어간다.

> **서브시스템** — SSH 연결 위에서 돌아가는 별도 기능(SFTP 가 그중 하나).\
> 예: `ssh.open_sftp()` 가 SFTP 서브시스템을 연다.

### (7) FTPS — `FTP_TLS` 와 `prot_p()`

**언제 쓰나** — 상대 서버가 FTP 만 지원하지만 암호화는 꼭 해야 할 때 쓴다.

```text
with FTP_TLS('ftp.example.com') as ftps:
    ftps.login('user', 'password')   ← 명령 채널을 TLS 로 보호한 뒤 로그인
    ftps.prot_p()                    ← 데이터 채널도 암호화하라고 켠다
    ftps.nlst()                      ← 이후는 일반 FTP 와 같은 메서드
```

그림 해설:
- `FTP_TLS` 는 `ftplib` 안에 있으므로 FTPS 는 표준 라이브러리만으로 된다.
- FTPS 는 기존 FTP 에 TLS 암호화를 더한 것이고, SFTP 와는 다른 프로토콜이다(원본 주석).
- 원본 주석의 「데이터 채널**도** 암호화」라는 말대로, `prot_p()` 는 데이터 채널 쪽을 보호하는 호출이다.
- 그래서 `prot_p()` 를 빠뜨리면 파일 내용이 오가는 데이터 채널을 따로 보호하지 않은 채로 남을 수 있다.
- `prot_p()` 뒤에는 `nlst` · `storbinary` · `retrbinary` 등 일반 FTP 와 똑같이 쓴다.

> **TLS** — 연결을 암호화하는 보안 계층(HTTPS 의 S 가 이것).\
> 예: FTPS = FTP + TLS.

### (8) 비교 표를 찍는 형식 지정

**언제 쓰나** — 예제의 4절처럼 f-string 으로 칸을 맞춘 표를 찍을 때 본다.

```text
print(f"{'특성':<14} {'FTP':>14} {'SFTP':>14}")
          └ 14칸, 왼쪽 정렬   └ 14칸, 오른쪽 정렬
한 줄 = 14 + 1(공백) + 14 + 1(공백) + 14 = 44 글자
print("-" * 44)                    ← 그 폭에 맞춘 구분선
```

그림 해설:
- `{값:<14}` 는 값을 14글자 폭에 왼쪽 정렬하고, 남는 자리를 오른쪽 공백으로 채운다.
- `{값:>14}` 는 오른쪽 정렬이라 남는 자리가 왼쪽 공백이 된다.
- 폭은 **문자 수**로 센다 — 한글 한 글자도, 영문 한 글자도 1이다.
- 칸 셋과 사이 공백 둘을 더하면 44글자라 구분선을 `"-" * 44` 로 찍는다.
- 다만 터미널은 한글을 보통 영문 두 칸 너비로 그리므로, 글자 수가 같아도 한글이 든 줄은 화면에서 더 넓게 보이기 쉽다(원본에 근거 없음 — 추론).
- 표의 일곱 줄은 프로토콜 · 포트 · 암호화 · 인증 · 파이썬 모듈 · 보안 · 방화벽을 비교한다.

## 문법 — 형태와 규칙

```python
from ftplib import FTP, FTP_TLS
from io import BytesIO

with FTP('ftp.example.com') as ftp:          # 연결 (포트 21)
    ftp.login('user', 'password')            # 익명이면 ftp.login()
    ftp.cwd('/uploads')                      # 서버 쪽 디렉터리 이동
    print(ftp.nlst())                        # 이름 목록 (list)
    with open('a.png', 'rb') as f:
        ftp.storbinary('STOR a.png', f)      # 업로드: 파일객체
    with open('b.png', 'wb') as f:
        ftp.retrbinary('RETR b.png', f.write)  # 다운로드: 콜백
    ftp.storbinary('STOR memo.txt', BytesIO(b'hi'))  # 메모리 업로드
```

`ftplib.FTP` 의 메서드 (원본에 나온 것 전부):

| 메서드 | 하는 일 | 붙는 FTP 명령 / 메모 |
|---|---|---|
| `login(user, passwd)` | 로그인 | 인자 없으면 익명 |
| `getwelcome()` | 서버 환영 문구 | — |
| `cwd(path)` | 디렉터리 이동 | 이후 상대 경로의 기준이 바뀐다 |
| `nlst()` | 이름 목록을 `list` 로 | `NLST` |
| `dir()` | 상세 목록 (`ls -l` 꼴) | — |
| `storbinary(cmd, fp)` | 바이너리 업로드 | `cmd` = `'STOR 이름'`, `fp` = 읽을 파일객체 |
| `retrbinary(cmd, callback)` | 바이너리 다운로드 | `cmd` = `'RETR 이름'`, 조각마다 `callback(bytes)` |
| `storlines(cmd, fp)` | 줄 단위(텍스트) 업로드 | 원본은 파일을 `'rb'` 로 연다 |
| `mkd(name)` / `rmd(name)` | 디렉터리 생성 / 삭제 | — |
| `delete(name)` | 파일 삭제 | — |
| `rename(old, new)` | 이름 변경 | — |
| `size(name)` | 파일 크기 | — |
| `quit()` | 정상 종료 | `QUIT` |

규칙:
- `storbinary` 는 **파일 객체**를, `retrbinary` 는 **함수(콜백)** 를 둘째 인자로 받는다.
- 바이너리 전송에는 로컬 파일을 `'rb'` · `'wb'` 로 연다.
- 원본은 `storlines` 에 넘길 텍스트 파일도 `'rb'` 로 연다 — `storlines` 가 바이트로 된 줄을 읽기 때문으로 보인다(확인 필요).
- `FTP_TLS` 는 `FTP` 와 메서드가 같고, 로그인 뒤 `prot_p()` 를 한 번 부른다.
- `paramiko` 의 SFTP 객체는 `put(로컬, 원격)` · `get(원격, 로컬)` · `listdir` · `stat` · `mkdir` · `close` 를 쓴다 — 인자 순서가 「출발지, 도착지」다.
- 원본 팁: FTP 는 `ftplib`(표준)으로, SFTP 는 `paramiko`(외부)로 쓴다.

## 어디서 틀리나

### 1. 평문 FTP 로 비밀번호와 파일을 보낸다
FTP 는 명령 채널과 데이터 채널이 모두 평문이다.
그래서 로그인 정보와 파일 내용이 그대로 노출될 수 있다.
원본 팁은 보안상 평문 FTP 보다 SFTP(SSH 기반)나 FTPS(TLS)를 쓰라고 말한다.
예제의 마지막 줄도 「실무에서는 보안상 SFTP 또는 FTPS를 사용」이다.

### 2. 이미지나 압축 파일을 `storlines` 로 보낸다
`storlines` 는 줄 단위 텍스트 전송용이다.
줄이 없는 이진 파일은 `storbinary` 로 보내야 한다.
원본 주석대로 바이너리 모드는 어떤 파일 형식이든 안전하다.

### 3. `retrbinary` 에 파일 객체를 넘긴다
`retrbinary` 는 둘째 인자를 **조각마다 부르는 함수**로 쓴다.
`f` 를 넘기면 함수가 아니므로 부를 수 없다.
`f.write` 를 넘겨야 한다 — 반대로 `storbinary` 에는 `f` 자체를 넘긴다.

### 4. 로컬 파일을 텍스트 모드로 연다
`open(..., 'r')` / `'w'` 는 문자열을 다루는 텍스트 모드다.
`storbinary` 가 읽어 갈 것도, `retrbinary` 가 넘겨줄 것도 바이트다.
그래서 예제는 늘 `'rb'` · `'wb'` 로 연다.

### 5. `list_files` 뒤에 디렉터리가 바뀐 줄 모른다
`list_files(path)` 는 목록만 보는 것 같지만, 안에서 `cwd(path)` 를 부른다.
그 뒤의 `upload('a.txt', 'a.txt')` 처럼 상대 경로를 쓰면 바뀐 디렉터리에 올라간다.
목록을 본 뒤에도 원래 자리를 기대한다면 절대 경로를 쓰거나 다시 `cwd` 해야 한다.

### 6. 로그인이 실패하면 `__exit__` 가 불리지 않는다
`with` 문은 `__enter__` 가 끝까지 성공해야 `__exit__` 를 약속한다.
`FTPClient.__enter__` 에서 `ftplib.FTP(host)` 로 연결된 뒤 `login` 이 예외를 던지면 `__exit__` 는 불리지 않는다.
그러면 열린 연결에 `quit()` 이 가지 않은 채 예외가 바깥으로 나간다.
막으려면 `__enter__` 안에서 `login` 을 `try` 로 감싸 실패 시 연결을 닫아야 한다(원본에 근거 없음 — 추론).

### 7. FTPS 와 SFTP 를 같은 것으로 안다
이름은 비슷하지만 FTPS 는 「FTP + TLS」이고, SFTP 는 「SSH 의 서브시스템」이다.
FTPS 는 `ftplib.FTP_TLS`(표준)로, SFTP 는 `paramiko`(외부)로 쓴다.
FTPS 서버에 `paramiko` 로, SFTP 서버에 `ftplib` 로 붙을 수는 없다.

### 8. FTPS 에서 `prot_p()` 를 빠뜨린다
원본은 `prot_p()` 를 「데이터 채널도 암호화」로 설명한다.
이 호출을 빼면 파일 내용이 지나가는 데이터 채널이 보호되지 않은 채로 남을 수 있다.

### 9. 방화벽 뒤에서 FTP 가 안 된다
FTP 는 명령 채널 말고도 데이터 채널을 따로 연다.
그래서 원본 비교 표의 방화벽 칸은 FTP 에 「패시브 모드 필요」, SFTP 에 「단일 포트」라고 적는다.
SFTP 는 포트 22 하나만 열면 된다.

### 10. 한글이 든 표가 어긋나 보인다
f-string 의 폭(`:<14`)은 문자 수 기준이다.
터미널에서 한글은 보통 두 칸을 차지하므로, 한글 칸이 있는 줄은 `"-" * 44` 보다 길어 보일 수 있다(원본에 근거 없음 — 추론).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `ftplib` · `io.BytesIO` 는 표준 라이브러리다 | 파이썬 표준 라이브러리 문서 |
| `paramiko` 는 외부 패키지다 | 서드파티 — 설치 여부는 환경 몫 |
| FTP 21번, SSH/SFTP 22번 포트 | 프로토콜의 기본 포트 관례 — 서버 설정으로 바뀔 수 있다 |
| `__enter__` 가 예외를 던지면 `__exit__` 는 불리지 않는다 | 언어 보장 (`with` 문의 의미) |
| `__exit__` 가 거짓 값을 돌려주면 예외가 전파된다 | 언어 보장 |
| f-string 폭 지정은 문자 수로 센다 | 언어 보장 (형식 지정 미니 언어) |
| 한글이 터미널에서 두 칸을 차지한다 | 터미널 · 글꼴의 동작 — 언어와 무관 |
| `prot_p()` 가 데이터 채널을 암호화한다 | `ftplib` 라이브러리와 서버의 FTPS 지원 |
| `cwd` 뒤 상대 경로가 새 디렉터리 기준이 된다 | FTP 서버의 동작 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 상대가 SSH 를 열어 둔 서버 | `paramiko` SFTP | 평문 FTP |
| FTP 만 되는 서버인데 암호화 필요 | `ftplib.FTP_TLS` + `prot_p()` | `ftplib.FTP` |
| 외부 패키지를 못 까는 환경에서 FTP 전송 | `ftplib` | `paramiko` |
| 이미지 · 압축 · 실행 파일 전송 | `storbinary` / `retrbinary` | `storlines` |
| 메모리에서 만든 바이트 업로드 | `storbinary` + `BytesIO` | 임시 파일을 디스크에 썼다 지우기 |
| 연결을 여러 번 열고 닫는 코드 | `with FTPClient(...)` 같은 컨텍스트 매니저 | 손으로 쓴 `login` / `quit` 짝 |
| 방화벽에서 포트를 하나만 열 수 있음 | SFTP (포트 22) | 데이터 채널을 따로 여는 FTP |

## 핵심 문장

1. **FTP 는 `ftplib`(표준), SFTP 는 `paramiko`(외부), FTPS 는 `ftplib.FTP_TLS` 로 쓴다.**
2. **`storbinary` 는 파일 객체를 읽어 올리고, `retrbinary` 는 받은 조각마다 콜백(`f.write`)을 부른다.**
3. **`BytesIO` 로 감싸면 디스크를 거치지 않고 메모리의 바이트를 올릴 수 있다.**
4. **`__enter__` 에서 연결 · 로그인, `__exit__` 에서 `quit()` 하면 `with` 블록이 연결 수명을 책임진다.**
5. **FTP 는 명령 · 데이터 채널이 모두 평문이므로, 실무에서는 SFTP(SSH, 포트 22 하나) 나 FTPS(TLS)를 쓴다.**

## 관련 자료

- [ssh-remote](../07-ssh-remote/2-summary.md)
- `socket-tcp` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `environment` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/networking.json` 의 `ftp-sftp`

## 용어 풀이

- **FTP** — 파일 전송 프로토콜, 명령 채널(21)과 데이터 채널이 나뉘고 평문이다.
- **SFTP** — SSH 위에서 돌아가는 파일 전송 서브시스템, 포트 22 하나로 전 구간 암호화한다.
- **FTPS** — FTP 에 TLS 암호화를 더한 것, SFTP 와 다른 프로토콜이다.
- **명령 채널** — FTP 명령과 응답이 오가는 연결.
- **데이터 채널** — FTP 에서 파일 내용과 목록이 지나가는 별도 연결.
- **패시브 모드** — 원본 비교 표에서 FTP 가 방화벽을 지나려면 필요하다고 적은 모드.
- **평문** — 암호화하지 않아 중간에서 그대로 읽을 수 있는 데이터.
- **TLS** — 연결을 암호화하는 보안 계층.
- **SSH** — 암호화된 원격 접속 프로토콜.
- **서브시스템** — SSH 연결 위에서 도는 별도 기능.
- **`ftplib`** — 파이썬 표준 라이브러리의 FTP 클라이언트 모듈.
- **`paramiko`** — SSH · SFTP 를 다루는 외부 파이썬 패키지.
- **`STOR` / `RETR`** — 서버에 저장 / 서버에서 받기를 뜻하는 FTP 명령.
- **`NLST`** — 이름만 나열하는 FTP 명령.
- **콜백** — 다른 함수가 알맞은 때 대신 불러 주도록 넘기는 함수.
- **청크** — 데이터를 나눠 보낼 때의 한 조각.
- **`BytesIO`** — 메모리의 바이트를 파일 객체처럼 다루는 클래스.
- **바이너리 모드** — 파일을 바이트 그대로 읽고 쓰는 모드(`'rb'` · `'wb'`).
- **컨텍스트 매니저** — `__enter__` · `__exit__` 를 갖춰 `with` 에 쓰는 객체.
- **익명 로그인** — 계정 없이 `login()` 으로 들어가는 FTP 로그인.

## 더 들어가면

- `paramiko.AutoAddPolicy()` 는 처음 보는 서버의 호스트 키를 묻지 않고 받아들인다 — 편하지만 중간자 공격을 걸러 내지 못하므로, 운영 환경에서는 알려진 호스트 키를 미리 불러 두는 쪽이 권장된다고 알려져 있다(확인 필요).
- `ftplib.FTP` 는 기본값이 패시브 모드이고 `set_pasv(False)` 로 액티브 모드로 바꿀 수 있다(확인 필요).
- 액티브 모드는 서버가 클라이언트 쪽으로 데이터 연결을 거는 방식이라 클라이언트 방화벽에 막히기 쉽고, 패시브 모드는 클라이언트가 서버의 다른 포트로 연결하는 방식이다(확인 필요).
- `storbinary` 에는 한 번에 읽는 크기를 정하는 `blocksize` 인자와 조각마다 불리는 `callback` 인자가 더 있다(확인 필요).
- `quit()` 은 서버에 QUIT 을 보내고 응답을 기다리므로 연결이 이미 끊겼으면 예외가 날 수 있고, 그때는 `close()` 로 일방적으로 닫는 방법이 있다(확인 필요).
- FTPS 에는 연결 직후 TLS 로 시작하는 「암묵적」 방식과 평문으로 붙은 뒤 TLS 로 올리는 「명시적」 방식이 있으며, `FTP_TLS` 는 명시적 방식이라고 알려져 있다(확인 필요).
- `sftp.put` · `sftp.get` 에도 진행 상황을 알려 주는 콜백 인자가 있다(확인 필요).
- 테스트용으로는 파이썬으로 띄우는 작은 FTP 서버 패키지(예: `pyftpdlib`)를 쓸 수 있다(확인 필요).
