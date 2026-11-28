# python/python-networking/06 — FTP와 SFTP 파일 전송 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 예제 스크립트를 그대로 실행하면 (예측)
- 예제 파일을 `python` 으로 그냥 실행하면 어떤 서버에든 네트워크 접속이 일어나는가?
- `paramiko` 가 설치되지 않은 환경에서 실행하면 `import` 오류가 나는가?

### 2. 비교 표의 한 줄 (예측)

```python
# 질문용 발췌
print(f"{'특성':<14} {'FTP':>14} {'SFTP':>14}")
print("-" * 44)
print(f"{'암호화':<14} {'없음 (FTPS=있음)':>14} {'전체 암호화':>14}")
```

- 셋째 줄은 몇 글자(문자 수)로 찍히는가?
- 셋째 줄에서 `'전체 암호화'` 앞에는 공백이 몇 개 붙는가?

### 3. 다운로드에 `f` 대신 `f.write` 를 넘기는 까닭 (왜)
- `storbinary` 에는 `f` 를 넘기는데, 왜 `retrbinary` 에는 `f.write` 를 넘기는가?

### 4. `upload_bytes` 가 `BytesIO(data)` 로 감싸는 까닭 (왜)
- `bytes` 를 `storbinary` 에 바로 넘기지 않고 왜 `BytesIO` 로 감싸는가?

### 5. 목록을 본 뒤의 업로드 (예측)

```python
# 질문용 발췌 — 로그인 직후 서버의 현재 디렉터리는 / 라고 하자
with FTPClient('host', 'u', 'p') as c:
    c.list_files('/logs')
    c.upload('a.txt', 'a.txt')
```

- `a.txt` 는 서버의 어느 경로에 놓이는가?

### 6. 로그인이 실패할 때 (경계)
- `with FTPClient(...)` 에서 연결은 됐는데 `__enter__` 안의 `login` 이 예외를 던지면, `__exit__` 의 `quit()` 은 불리는가?

### 7. 사진 파일을 `storlines` 로 (경계)
- PNG 같은 이진 파일을 올릴 때 `storlines` 가 아니라 `storbinary` 를 써야 하는 까닭은 무엇인가?

### 8. FTP 가 방화벽에서 더 까다로운 까닭 (왜)
- 비교 표가 FTP 에는 「패시브 모드 필요」, SFTP 에는 「단일 포트」라고 적는 까닭은 무엇인가?

### 9. FTPS 와 SFTP 의 관계 (연결)
- FTPS 는 FTP 에 무엇을 더한 것이고, SFTP 는 무엇 위에서 도는가?
- FTPS 에서 `login` 뒤에 `prot_p()` 를 따로 부르는 까닭은 무엇인가?

### 10. `with open(...)` 과 `with FTPClient(...)` (연결)
- 파일의 `with open(...)` 과 `with FTPClient(...)` 는 어떤 같은 장치로 정리를 보장하는가?

## 실습

### 실습 1. FTP · SFTP · FTPS 사용법을 찍고 FTP 래퍼 클래스 만들기

**만들 것** — FTP 연산 패턴 · SFTP 패턴 · FTPS 패턴을 화면에 찍고, FTP 작업을 `with` 로 감싸는 `FTPClient` 클래스와 FTP vs SFTP 비교 표를 갖춘 스크립트.

**준비물** — 표준 라이브러리(`ftplib` · `os` · `io`)만 있으면 된다. `paramiko` 와 FTP 서버는 문자열로 사용법을 보여 줄 뿐이라 실행에 필요 없다.

**요구 조건**

1단계 — FTP 연산 패턴
1. `ftp_demo_operations()` 함수는 `=== FTP 연산 패턴 ===` 제목을 찍고, FTP 사용 패턴을 담은 여러 줄 문자열을 찍는다.
2. 그 문자열에는 `with FTP(...)` 연결, `login`(익명이면 인자 없이), `getwelcome`, `cwd` · `nlst` · `dir`, `'rb'` 로 연 파일의 `storbinary('STOR ...', f)`, `'wb'` 로 연 파일의 `retrbinary('RETR ...', f.write)`, `storlines`, `mkd` · `rmd` · `delete` · `rename` · `size` 가 들어간다.
3. 함수를 정의한 뒤 곧바로 한 번 부른다.

2단계 — `FTPClient` 클래스
4. `__init__(host, user='', passwd='')` 는 세 값을 저장하고 `self.ftp` 를 `None` 으로 둔다.
5. `__enter__` 는 `ftplib.FTP(host)` 로 연결하고 `login(user, passwd)` 한 뒤 `self` 를 돌려준다.
6. `__exit__` 는 `self.ftp` 가 있으면 `quit()` 한다.
7. `upload(local_path, remote_path)` 는 로컬 파일을 바이너리로 열어 `STOR` 로 올리고 `업로드: 로컬 -> 원격` 을 찍는다.
8. `download(remote_path, local_path)` 는 로컬 파일을 바이너리 쓰기로 열어 `RETR` 로 받고 `다운로드: 원격 -> 로컬` 을 찍는다.
9. `list_files(path='.')` 는 그 디렉터리로 이동한 뒤 이름 목록을 돌려준다.
10. `upload_bytes(data, remote_path)` 는 `bytes` 를 `BytesIO` 로 감싸 `STOR` 로 올린다.
11. 클래스 뒤에 `=== 2. FTP 유틸리티 클래스 ===` 제목과 사용 예 두 줄을 찍는다.

3단계 — SFTP 패턴
12. `=== 3. SFTP (paramiko) 패턴 ===` 제목 뒤에, `SSHClient` 생성 · `AutoAddPolicy` 설정 · 비밀번호 `connect`(키 기반 대안은 주석) · `open_sftp` · `put` · `get` · `listdir` · `stat`(`st_size` · `st_mtime` 출력) · `mkdir` · `close` 두 번을 담은 문자열을 찍는다.

4단계 — 비교 표
13. `특성` · `FTP` · `SFTP` 머리 줄을 첫 칸 왼쪽 정렬, 나머지 두 칸 오른쪽 정렬(각 14칸)로 찍고, 그 아래 `-` 44개를 찍는다.
14. 미리 주어진 `comparisons` 의 일곱 줄을 같은 형식으로 찍는다.

5단계 — FTPS 와 정리
15. `=== 5. FTPS (FTP over TLS) ===` 제목 뒤에 `FTP_TLS` 로 연결 · `login` · `prot_p()` · `nlst()` 를 담은 문자열을 찍는다.
16. `=== 핵심 정리 ===` 와 정리 네 줄을 찍는다.

**시작 코드**

```python
"""FTP/SFTP 파일 전송: ftplib, paramiko 개념"""
import ftplib
import os
from io import BytesIO

# === 1. FTP 클라이언트 기본 ===
def ftp_demo_operations():
    """FTP 주요 연산 (구조와 패턴)"""
    print("=== FTP 연산 패턴 ===")
    print("""
    from ftplib import FTP

    # 연결 + 로그인
    with FTP('ftp.example.com') as ftp:
        # TODO: 로그인 (익명 방법은 주석으로), 환영 문구 출력

        # 디렉토리 이동/목록
        # TODO: /uploads 로 이동, 이름 목록, 상세 목록

        # 파일 업로드 (바이너리)
        # TODO: local_file.txt 를 열어 remote_file.txt 로 저장

        # 파일 다운로드 (바이너리)
        # TODO: remote_file.txt 를 받아 downloaded.txt 에 쓰기

        # 텍스트 파일 업로드
        # TODO: text_file.txt 를 줄 단위로 text_remote.txt 에 저장

        # 파일/디렉토리 관리
        # TODO: 디렉토리 생성 · 삭제, 파일 삭제, 이름 변경, 크기
    """)

# TODO: 함수 호출

# === 2. FTP 유틸리티 클래스 ===
class FTPClient:
    """FTP 작업을 래핑한 유틸리티 클래스"""

    def __init__(self, host: str, user: str = '', passwd: str = ''):
        pass  # TODO

    def __enter__(self):
        pass  # TODO: 연결 + 로그인 + self 반환

    def __exit__(self, *args):
        pass  # TODO: 연결이 있으면 정상 종료

    def upload(self, local_path: str, remote_path: str):
        """파일 업로드"""
        pass  # TODO
        print(f"업로드: {local_path} -> {remote_path}")

    def download(self, remote_path: str, local_path: str):
        """파일 다운로드"""
        pass  # TODO
        print(f"다운로드: {remote_path} -> {local_path}")

    def list_files(self, path: str = '.') -> list:
        """파일 목록"""
        pass  # TODO

    def upload_bytes(self, data: bytes, remote_path: str):
        """메모리에서 직접 업로드"""
        pass  # TODO

print("\n=== 2. FTP 유틸리티 클래스 ===")
print("사용: with FTPClient('host', 'user', 'pass') as ftp:")
print("       ftp.upload('local.txt', 'remote.txt')")

# === 3. SFTP (paramiko) 패턴 ===
print("\n=== 3. SFTP (paramiko) 패턴 ===")
print("""
import paramiko

# SSH 클라이언트로 SFTP 연결
# TODO: SSHClient 생성, 호스트 키 정책, 비밀번호 connect (키 기반은 주석)

# TODO: SFTP 열기

# 업로드
# TODO
# 다운로드
# TODO
# 파일 목록
# TODO
# 파일 정보
# TODO: stat 후 크기 · 수정시간 출력
# 디렉토리 생성
# TODO
# 정리
# TODO
""")

# === 4. FTP vs SFTP 비교 ===
print("=== 4. FTP vs SFTP 비교 ===")
# TODO: 머리 줄 (14칸씩: 왼쪽 / 오른쪽 / 오른쪽 정렬)
# TODO: 구분선
comparisons = [
    ("프로토콜", "FTP", "SSH 위의 SFTP"),
    ("포트", "21", "22"),
    ("암호화", "없음 (FTPS=있음)", "전체 암호화"),
    ("인증", "ID/PW", "ID/PW + 키"),
    ("파이썬 모듈", "ftplib (표준)", "paramiko (외부)"),
    ("보안", "낮음", "높음"),
    ("방화벽", "패시브 모드 필요", "단일 포트"),
]
# TODO: 일곱 줄을 머리 줄과 같은 형식으로

# === 5. FTP TLS (FTPS) ===
print("\n=== 5. FTPS (FTP over TLS) ===")
print("""
# TODO: FTP_TLS 들여오기, with 로 연결, 로그인, 데이터 채널 암호화, 목록
""")

print("=== 핵심 정리 ===")
print("FTP: ftplib (표준 라이브러리), storbinary/retrbinary")
print("SFTP: paramiko (pip install), SSH 기반 보안 전송")
print("FTPS: ftplib.FTP_TLS, TLS 암호화된 FTP")
print("실무에서는 보안상 SFTP 또는 FTPS를 사용")
```

**확인 방법** — `python ftp-sftp.py` 로 실행해 다섯 절의 제목과 패턴 문자열, 일곱 줄짜리 비교 표, 핵심 정리 네 줄이 찍히는지 본다. `FTPClient` 는 접속할 수 있는 FTP 서버가 있을 때 `with FTPClient(...) as c:` 로 `upload` · `download` · `list_files` · `upload_bytes` 를 하나씩 불러 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
