# python/python-networking/06 — FTP와 SFTP 파일 전송 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 접속도 `import` 오류도 일어나지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
화면에 패턴 문자열 · 비교 표 · 정리 줄이 찍히고 끝난다.
어떤 서버에도 접속하지 않고, `paramiko` 가 없어도 `import` 오류가 나지 않는다.

**왜 그런가**
- 실제로 실행되는 `import` 는 `ftplib` · `os` · `io.BytesIO` 셋뿐이고 모두 표준 라이브러리다.
- `FTPClient` 는 정의만 되고 스크립트 어디에서도 객체를 만들지 않으므로 `ftplib.FTP(...)` 가 불리지 않는다.
- `import paramiko` 와 `FTP('ftp.example.com')` 는 `print` 하는 삼중 따옴표 문자열 안의 글자일 뿐이다.
- 근거: 2-summary 「동작 방식 (1)」.

### 2. 44글자, `'전체 암호화'` 앞 공백 8개

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
'암호화' + 공백 11개      → 14
공백 1개                  → 1
공백 2개 + '없음 (FTPS=있음)'(12글자) → 14
공백 1개                  → 1
공백 8개 + '전체 암호화'(6글자)        → 14
합계                                    44
```

**왜 그런가**
- `:<14` 는 14글자 폭에 왼쪽 정렬, `:>14` 는 오른쪽 정렬이라 모자란 자리를 공백으로 채운다.
- 폭은 문자 수로 세므로 한글 한 글자도 1이다 — `'전체 암호화'` 는 띄어쓰기까지 6글자라 앞에 공백 8개가 붙는다.
- 14 + 1 + 14 + 1 + 14 = 44 라서 구분선 `"-" * 44` 와 글자 수가 같다.
- 다만 터미널에서는 한글이 두 칸으로 그려지기 쉬워 화면상으로는 구분선보다 넓어 보일 수 있다(원본에 근거 없음 — 추론).
- 근거: 2-summary 「동작 방식 (8)」 · 「어디서 틀리나 10」.

### 3. `retrbinary` 의 둘째 인자는 조각마다 부를 함수이기 때문이다

`storbinary` 는 둘째 인자를 **읽을 파일 객체**로 쓰고, 거기서 바이트를 꺼내 보낸다.
`retrbinary` 는 둘째 인자를 **콜백**으로 쓰고, 받은 데이터 조각마다 그 함수를 부른다.
그래서 「받은 조각을 파일에 써라」는 뜻으로 함수인 `f.write` 를 넘긴다.
`f` 를 넘기면 함수가 아니므로 부를 수 없다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 4. `storbinary` 는 파일 객체에서 읽어 가는 함수라서다

`storbinary` 는 둘째 인자에서 바이트를 읽어 가는데, 그것이 디스크 파일인지는 따지지 않는다.
`bytes` 자체는 파일처럼 읽어 갈 수 있는 객체가 아니다.
`BytesIO` 는 메모리의 바이트를 파일 객체처럼 읽게 해 주므로, 감싸서 넘기면 디스크에 임시 파일을 만들지 않고 바로 올릴 수 있다.
근거: 2-summary 「동작 방식 (4)」.

### 5. `/logs/a.txt` 에 놓인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`a.txt` 는 `/` 가 아니라 `/logs/a.txt` 로 저장된다.

**왜 그런가**
- `list_files('/logs')` 는 이름 목록만 보는 것 같지만, 안에서 먼저 `self.ftp.cwd('/logs')` 를 부른다.
- 서버의 현재 디렉터리가 `/logs` 로 바뀐 채로 남는다.
- 이어서 `upload('a.txt', 'a.txt')` 가 보내는 `STOR a.txt` 는 상대 경로라 바뀐 디렉터리 기준으로 해석된다.
- 근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (5)」 · 「어디서 틀리나 5」.

### 6. 불리지 않는다 — 연결이 정리되지 않은 채 예외가 나간다

`with` 문은 `__enter__` 가 끝까지 성공해야 `__exit__` 를 부른다.
`__enter__` 안에서 `ftplib.FTP(host)` 로 연결된 뒤 `login` 이 예외를 던지면 `__enter__` 가 실패한 것이므로 `__exit__` 는 불리지 않는다.
그래서 열린 연결에 `quit()` 이 가지 않는다.
이것은 `FTPClient` 의 버릇이 아니라 `with` 문의 의미(언어 보장)에서 나온다.
막으려면 `__enter__` 안에서 `login` 을 `try` 로 감싸 실패 시 연결을 닫아야 한다(원본에 근거 없음 — 추론).
근거: 2-summary 「어디서 틀리나 6」 · 「구현 세부사항 대 언어 보장」.

### 7. `storlines` 는 줄 단위 텍스트 전송용이라 이진 파일에 맞지 않는다

`storlines` 는 파일을 줄 단위로 다루는 텍스트 전송용이다.
PNG 같은 이진 파일에는 「줄」이라는 구조가 없으므로 줄 단위로 다루면 안 된다.
`storbinary` 는 바이트를 그대로 옮기므로, 원본 주석의 말대로 어떤 파일 형식이든 안전하다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 8. FTP 는 명령 채널과 별도로 데이터 채널을 열기 때문이다

FTP 는 명령 채널(포트 21) 말고도 파일 내용과 목록이 지나가는 데이터 채널을 따로 연다.
그래서 방화벽을 지나려면 데이터 연결까지 통과시키는 방법(원본 표의 「패시브 모드」)이 필요하다.
SFTP 는 SSH 연결 하나(포트 22) 안에서 명령과 데이터를 다 주고받으므로 포트 하나만 열면 된다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (6)」 · 「어디서 틀리나 9」.

### 9. FTPS = FTP + TLS, SFTP = SSH 의 서브시스템 — `prot_p()` 는 데이터 채널 보호

FTPS 는 기존 FTP 에 TLS 암호화를 더한 것이라 `ftplib.FTP_TLS` 로 쓰고, 메서드는 일반 FTP 와 같다.
SFTP 는 FTP 와 다른 프로토콜로, SSH 연결 위의 서브시스템이며 `paramiko` 로 쓴다.
FTP 는 명령 채널과 데이터 채널이 나뉘어 있다.
원본은 `prot_p()` 를 「데이터 채널도 암호화」로 설명한다 — 로그인만으로는 데이터 채널이 따로 보호되지 않으므로 파일 내용까지 보호하려고 부른다.
근거: 2-summary 「동작 방식 (7)」 · 「어디서 틀리나 7 · 8」.

### 10. 둘 다 컨텍스트 매니저 — `__enter__` 와 `__exit__`

`open(...)` 이 돌려주는 파일 객체와 `FTPClient` 는 모두 `__enter__` · `__exit__` 를 갖춘 컨텍스트 매니저다.
`with` 블록을 벗어날 때, 본문이 정상으로 끝나든 예외로 끝나든 `__exit__` 가 불린다.
파일은 거기서 닫히고, `FTPClient` 는 거기서 `quit()` 으로 FTP 연결을 정상 종료한다.
`FTPClient.upload` 안에서도 `with open(...)` 을 쓰므로, 두 겹의 `with` 가 파일과 연결을 각각 정리한다.
근거: 2-summary 「동작 방식 (5)」.

## 실습 정답

### 실습 1. FTP · SFTP · FTPS 사용법을 찍고 FTP 래퍼 클래스 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 제목과 FTP 패턴 문자열 찍기 | `ftp_demo_operations()` 의 `print("=== FTP 연산 패턴 ===")` 와 삼중 따옴표 `print` |
| 2. 패턴 문자열의 연산들 | 문자열 안의 `ftp.login` · `getwelcome` · `cwd` · `nlst` · `dir` · `storbinary` · `retrbinary(..., f.write)` · `storlines` · `mkd` · `rmd` · `delete` · `rename` · `size` |
| 3. 곧바로 호출 | `ftp_demo_operations()` |
| 4. 값 저장 · `self.ftp = None` | `FTPClient.__init__` |
| 5. 연결 + 로그인 + `self` 반환 | `__enter__` 의 `ftplib.FTP(self.host)` · `self.ftp.login(...)` · `return self` |
| 6. 있으면 `quit()` | `__exit__` 의 `if self.ftp: self.ftp.quit()` |
| 7. 바이너리 업로드 + 안내 줄 | `upload` 의 `open(local_path, 'rb')` · `storbinary(f'STOR {remote_path}', f)` |
| 8. 바이너리 다운로드 + 안내 줄 | `download` 의 `open(local_path, 'wb')` · `retrbinary(f'RETR {remote_path}', f.write)` |
| 9. 이동 후 이름 목록 | `list_files` 의 `self.ftp.cwd(path)` · `return self.ftp.nlst()` |
| 10. 메모리 업로드 | `upload_bytes` 의 `storbinary(..., BytesIO(data))` |
| 11. 2절 제목과 사용 예 | `print("\n=== 2. FTP 유틸리티 클래스 ===")` 와 뒤의 두 `print` |
| 12. SFTP 패턴 문자열 | 3절 `print` 문자열의 `SSHClient` · `AutoAddPolicy` · `connect` · `open_sftp` · `put` · `get` · `listdir` · `stat` · `mkdir` · `close` |
| 13. 머리 줄과 구분선 | `f"{'특성':<14} {'FTP':>14} {'SFTP':>14}"` · `"-" * 44` |
| 14. 일곱 줄 | `for feature, ftp_val, sftp_val in comparisons:` 의 `print` |
| 15. FTPS 패턴 문자열 | 5절 `print` 문자열의 `FTP_TLS` · `login` · `prot_p()` · `nlst()` |
| 16. 핵심 정리 | `print("=== 핵심 정리 ===")` 와 네 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-networking/reference/ftp-sftp.py`

```python
# [네트워크 & 시스템] FTP와 SFTP 파일 전송
# 설명: ftplib으로 FTP 파일 전송, paramiko 개념으로 SFTP 접근
# 팁: FTP는 ftplib(표준)으로, SFTP는 paramiko(외부)로 사용한다. storbinary/retrbinary가 바이너리 파일 전송의 핵심이다. 보안상 평문 FTP보다 SFTP(SSH 기반)나 FTPS(TLS)를 사용해야 한다. BytesIO를 쓰면 메모리에서 직접 업로드할 수 있다.

"""FTP/SFTP 파일 전송: ftplib, paramiko 개념"""
# ftplib: 표준 라이브러리 FTP 클라이언트 (포트 21, 평문)
import ftplib
# os: 파일 경로 처리
import os
# BytesIO: 메모리 내 바이트 스트림 (파일 객체처럼 사용)
from io import BytesIO

# === 1. FTP 클라이언트 기본 ===
# FTP 주요 연산을 문서화
def ftp_demo_operations():
    """FTP 주요 연산 (구조와 패턴)"""
    print("=== FTP 연산 패턴 ===")
    # FTP는 명령 채널(21) + 데이터 채널 분리 / 평문 통신 → 보안 취약
    print("""
    from ftplib import FTP

    # 연결 + 로그인
    with FTP('ftp.example.com') as ftp:
        ftp.login('user', 'password')  # 익명: ftp.login()
        print(ftp.getwelcome())

        # 디렉토리 이동/목록
        ftp.cwd('/uploads')           # 디렉토리 이동
        files = ftp.nlst()             # 파일 목록
        ftp.dir()                      # 상세 목록 (ls -l)

        # 파일 업로드 (바이너리)
        with open('local_file.txt', 'rb') as f:
            ftp.storbinary('STOR remote_file.txt', f)

        # 파일 다운로드 (바이너리)
        with open('downloaded.txt', 'wb') as f:
            ftp.retrbinary('RETR remote_file.txt', f.write)

        # 텍스트 파일 업로드
        with open('text_file.txt', 'rb') as f:
            ftp.storlines('STOR text_remote.txt', f)

        # 파일/디렉토리 관리
        ftp.mkd('new_directory')       # 디렉토리 생성
        ftp.rmd('old_directory')       # 디렉토리 삭제
        ftp.delete('file_to_delete')   # 파일 삭제
        ftp.rename('old.txt', 'new.txt')  # 이름 변경
        ftp.size('file.txt')           # 파일 크기
    """)

ftp_demo_operations()

# === 2. FTP 유틸리티 클래스 ===
# with 문으로 자동 연결/정리
class FTPClient:
    """FTP 작업을 래핑한 유틸리티 클래스"""

    # 연결 정보 저장
    def __init__(self, host: str, user: str = '', passwd: str = ''):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.ftp = None

    # with 진입: 연결 + 로그인
    def __enter__(self):
        self.ftp = ftplib.FTP(self.host)
        self.ftp.login(self.user, self.passwd)
        return self

    # with 종료: 정상 종료(QUIT)
    def __exit__(self, *args):
        if self.ftp:
            self.ftp.quit()

    # 로컬 파일 → 원격 (바이너리 모드: 어떤 파일 형식이든 안전)
    def upload(self, local_path: str, remote_path: str):
        """파일 업로드"""
        with open(local_path, 'rb') as f:
            # STOR <name>: 서버에 파일 저장
            self.ftp.storbinary(f'STOR {remote_path}', f)
        print(f"업로드: {local_path} -> {remote_path}")

    # 원격 → 로컬
    def download(self, remote_path: str, local_path: str):
        """파일 다운로드"""
        with open(local_path, 'wb') as f:
            # RETR <name>: 서버에서 파일 받기, 콜백으로 청크 처리
            self.ftp.retrbinary(f'RETR {remote_path}', f.write)
        print(f"다운로드: {remote_path} -> {local_path}")

    # 디렉토리 파일 이름만 나열
    def list_files(self, path: str = '.') -> list:
        """파일 목록"""
        self.ftp.cwd(path)
        # NLST: 이름만 (간단한 ls)
        return self.ftp.nlst()

    # 디스크 거치지 않고 메모리에서 바로 업로드
    def upload_bytes(self, data: bytes, remote_path: str):
        """메모리에서 직접 업로드"""
        # BytesIO를 파일처럼 사용
        self.ftp.storbinary(f'STOR {remote_path}', BytesIO(data))

print("\n=== 2. FTP 유틸리티 클래스 ===")
print("사용: with FTPClient('host', 'user', 'pass') as ftp:")
print("       ftp.upload('local.txt', 'remote.txt')")

# === 3. SFTP (paramiko) 패턴 ===
print("\n=== 3. SFTP (paramiko) 패턴 ===")
# SFTP: FTP가 아니라 SSH의 서브시스템 (포트 22 단일, 전 구간 암호화)
print("""
import paramiko

# SSH 클라이언트로 SFTP 연결
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('hostname', username='user', password='pass')
# 또는 키 기반: ssh.connect('hostname', username='user', key_filename='~/.ssh/id_rsa')

sftp = ssh.open_sftp()

# 업로드
sftp.put('local_file.txt', '/remote/path/file.txt')

# 다운로드
sftp.get('/remote/path/file.txt', 'local_file.txt')

# 파일 목록
files = sftp.listdir('/remote/path')

# 파일 정보
attr = sftp.stat('/remote/path/file.txt')
print(f"크기: {attr.st_size}, 수정시간: {attr.st_mtime}")

# 디렉토리 생성
sftp.mkdir('/remote/new_dir')

# 정리
sftp.close()
ssh.close()
""")

# === 4. FTP vs SFTP 비교 ===
print("=== 4. FTP vs SFTP 비교 ===")
# 헤더
print(f"{'특성':<14} {'FTP':>14} {'SFTP':>14}")
print("-" * 44)
# 보안/포트/모듈 비교 표
comparisons = [
    ("프로토콜", "FTP", "SSH 위의 SFTP"),
    ("포트", "21", "22"),
    ("암호화", "없음 (FTPS=있음)", "전체 암호화"),
    ("인증", "ID/PW", "ID/PW + 키"),
    ("파이썬 모듈", "ftplib (표준)", "paramiko (외부)"),
    ("보안", "낮음", "높음"),
    ("방화벽", "패시브 모드 필요", "단일 포트"),
]
for feature, ftp_val, sftp_val in comparisons:
    print(f"{feature:<14} {ftp_val:>14} {sftp_val:>14}")

# === 5. FTP TLS (FTPS) ===
print("\n=== 5. FTPS (FTP over TLS) ===")
# FTPS: 기존 FTP + TLS 암호화 (SFTP와는 다른 프로토콜)
print("""
from ftplib import FTP_TLS

with FTP_TLS('ftp.example.com') as ftps:
    ftps.login('user', 'password')
    ftps.prot_p()  # 데이터 채널도 암호화
    ftps.nlst()    # 이후 일반 FTP와 동일하게 사용
""")

print("=== 핵심 정리 ===")
print("FTP: ftplib (표준 라이브러리), storbinary/retrbinary")
print("SFTP: paramiko (pip install), SSH 기반 보안 전송")
print("FTPS: ftplib.FTP_TLS, TLS 암호화된 FTP")
print("실무에서는 보안상 SFTP 또는 FTPS를 사용")
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**
- 스크립트에서 실제로 실행되는 네트워크 코드는 없다 — 접속하는 코드는 모두 문자열이거나 쓰이지 않는 클래스 안에 있다.
- `storbinary` 에는 파일 객체를, `retrbinary` 에는 콜백 `f.write` 를 넘긴다는 짝을 기억한다.
- `__enter__` 가 연결과 로그인을, `__exit__` 가 `quit()` 을 맡아 `with` 블록이 연결 수명을 정한다.
- `list_files` 는 서버 디렉터리를 바꾼 상태로 남긴다는 점을 놓치지 않는다.
- 비교 표는 14 + 1 + 14 + 1 + 14 = 44 글자 폭이라 구분선이 `"-" * 44` 다.
- FTPS 패턴에서는 `login` 뒤 `prot_p()` 로 데이터 채널까지 보호한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
