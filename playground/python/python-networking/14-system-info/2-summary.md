# python/python-networking/14 — 시스템 정보: platform과 리소스 모니터링 — 정리 (힌트)

> 출처 — study-site 항목 `python/system-info`(항목 데이터 `data/python/networking.json`) · 정답 코드 study-practice `python/python-networking/reference/system-info.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

## 한눈에 — 쉽게 말하면

**시스템 정보 조회는 「건강검진 문진표」를 채우는 일이다.**
문진표 앞장에는 이름 · 생년월일 같은 바뀌지 않는 신상이 있고, 뒷장에는 혈압 · 체중처럼 잴 때마다 달라지는 수치가 있다.
Python 프로그램이 자기가 올라탄 컴퓨터를 조사하는 것도 똑같은 구조다.
앞장은 「어떤 OS · 어떤 CPU 구조 · 어떤 Python 인가」이고, 뒷장은 「디스크 · 메모리를 얼마나 쓰고 있나」다.

| 비유 | 실체 |
|---|---|
| 신상(이름 · 생년월일) | `platform` · `sys` 가 돌려주는 OS · 아키텍처 · Python 버전 |
| 접수 번호 · 보호자 번호 | `os.getpid()` · `os.getppid()` |
| 체중 · 혈압 측정 | `shutil.disk_usage()` · `resource.getrusage()` · `/proc/meminfo` |
| 정밀 검사 장비(병원 밖에서 빌려 옴) | `psutil` (외부 라이브러리) |
| 검진 결과지 한 장 | `system_summary()` 가 만든 dict → JSON |

```text
          ┌─────────── 바뀌지 않는 신상 ───────────┐
 Python ─▶│ platform  : OS 이름, 커널, 아키텍처      │
 프로그램  │ sys       : 인터프리터 경로, 버전, 바이트 순서 │
          └───────────────────────────────────────┘
          ┌─────────── 잴 때마다 다른 수치 ─────────┐
          │ os        : PID, CPU 수, 로드 평균       │
          │ shutil    : 디스크 전체/사용/여유         │
          │ resource  : 내 프로세스의 메모리·CPU 시간   │
          │ /proc     : (Linux) 시스템 메모리         │
          │ psutil    : (외부) 전부 + 네트워크·프로세스 │
          └───────────────────────────────────────┘
                         │
                         ▼
                 dict → json.dumps → 결과지
```

## 이 주제가 답하려는 질문

1. 지금 이 코드는 어떤 OS · 어떤 CPU 구조 · 어떤 Python 위에서 돌고 있나?
2. 지금 이 프로세스는 누구(PID)이고, 자원을 얼마나 썼나?
3. 외부 라이브러리 없이 디스크와 메모리의 남은 양을 알 수 있나?
4. 그 이상(CPU 사용률 · 네트워크 · 다른 프로세스)이 필요하면 무엇을 쓰나?

## 동작 방식

### (1) `platform` — 「어떤 환경인가」를 문자열로

**언제 쓰나** — 로그 · 버그 리포트에 실행 환경을 남길 때, OS 에 따라 분기할 때.

```text
platform.system()                 ─▶ 'Linux' / 'Windows' / 'Darwin'
platform.release()                ─▶ 커널 릴리스 (예: '6.17.0')
platform.version()                ─▶ 빌드 상세 문자열
platform.machine()                ─▶ 'x86_64' / 'arm64'
platform.processor()              ─▶ 프로세서 이름
platform.architecture()           ─▶ ('64bit', 'ELF')   ← 튜플
platform.platform()               ─▶ 위를 합친 한 줄 요약
platform.python_version()         ─▶ '3.x.x'
platform.python_implementation()  ─▶ 'CPython' / 'PyPy' …
```

- 모든 함수가 인자 없이 불리고 값을 돌려준다.
- `system()` 은 macOS 에서 `'Darwin'` 을 돌려준다(macOS 의 커널 이름이다).
- `architecture()` 만 튜플이고, 앞 칸은 비트 수, 뒤 칸은 실행 파일 형식(링커 포맷)이다.
- `python_implementation()` 은 「어느 인터프리터가 이 코드를 돌리나」를 알려 준다.

> **아키텍처** — CPU 가 이해하는 명령 집합의 종류.\
> 예: 인텔 · AMD 데스크톱은 `x86_64`, 애플 실리콘 맥은 `arm64`.

### (2) `os` — 「이 프로세스는 누구인가」

**언제 쓰나** — 로그에 PID 를 찍을 때, 작업 개수를 CPU 수에 맞출 때, 서버가 바쁜지 볼 때.

```text
os.getpid()      ─▶ 현재 프로세스 ID
os.getppid()     ─▶ 부모 프로세스 ID (이 프로그램을 띄운 쪽, 보통 셸)
os.getuid()      ─▶ 사용자 ID           ← Unix 전용
os.getcwd()      ─▶ 현재 작업 디렉터리
os.cpu_count()   ─▶ 논리 CPU 코어 수
os.getloadavg()  ─▶ (1분, 5분, 15분) 평균 부하 ← Unix 전용, 튜플
```

- `getuid` · `getloadavg` 는 Unix 계열에만 있는 함수라, Windows 의 `os` 모듈에는 그 이름 자체가 없다.
- 그래서 원본은 `hasattr(os, 'getuid')` 로 「이름이 있는지」 먼저 묻고, 없으면 `"UID: N/A"` 를 찍는다.
- 조건 표현식 `A if 조건 else B` 를 f-string 통째에 걸어서, 조건이 거짓이면 `os.getuid()` 를 아예 부르지 않는다.

> **PID** — 운영체제가 실행 중인 프로세스마다 붙이는 번호.\
> 예: 같은 스크립트를 두 번 띄우면 두 PID 가 다르다.

> **로드 평균** — 일정 시간 동안 CPU 를 쓰고 있거나 기다리던 작업 수의 평균.\
> 예: `(0.5, 0.3, 0.2)` 는 최근 1분 · 5분 · 15분의 평균이다.

### (3) `sys` — 「어떤 Python 인가」

**언제 쓰나** — 가상 환경을 제대로 쓰고 있는지(`sys.executable`), 플랫폼 분기(`sys.platform`)를 할 때.

```text
sys.executable              ─▶ 지금 돌고 있는 인터프리터 파일 경로
sys.version                 ─▶ 빌드 정보가 붙은 긴 버전 문자열
sys.byteorder               ─▶ 'little' / 'big'  (CPU 엔디안)
sys.maxsize                 ─▶ 플랫폼의 최대 크기 값
sys.getrecursionlimit()     ─▶ 재귀 호출 한계 (원본 주석: 기본 1000)
sys.getdefaultencoding()    ─▶ 기본 문자열 인코딩 (원본 주석: 보통 utf-8)
sys.platform                ─▶ 'linux' / 'darwin' / 'win32'
```

- `sys.platform` 은 `platform.system()` 과 같은 사실을 다른 꼴로 준다 — 소문자 짧은 이름이고, 함수가 아니라 값이다.
- `sys.version` 은 `platform.python_version()` 보다 길다(빌드 날짜 · 컴파일러가 붙는다).
- 원본은 `sys.maxsize` 를 「최대 정수」라고 찍지만, Python 의 `int` 는 크기 제한이 없다(「어디서 틀리나」 3 참고).

> **엔디안(바이트 순서)** — 여러 바이트로 된 수를 메모리에 놓는 순서.\
> 예: `little` 은 낮은 자리 바이트를 앞 주소에 둔다.

### (4) `shutil.disk_usage()` — 디스크 세 숫자

**언제 쓰나** — 큰 파일을 쓰기 전에 여유 공간을 확인할 때.

```text
shutil.disk_usage('/')
      │
      ▼
(total, used, free)   ← 이름 붙은 튜플, 단위는 바이트
      │  각각 / (1024**3)
      ▼
GB 로 표시, used/total*100 → 사용률 %
```

- 인자는 경로 하나이고, 그 경로가 속한 파일 시스템의 크기를 돌려준다.
- 세 값을 `total, used, free = …` 로 한 번에 풀어 받는다.
- `1024**3` 으로 나누어 바이트를 GB(엄밀히는 GiB)로 바꾼다.
- `:.1f` 로 소수 한 자리만 찍는다.

### (5) `resource.getrusage()` — 내 프로세스가 쓴 양

**언제 쓰나** — 스크립트가 끝날 무렵 「얼마나 먹었나」를 남길 때.

```text
resource.getrusage(resource.RUSAGE_SELF)
      │
      ▼
usage.ru_maxrss   최대 RSS   (Linux = kB, macOS = 바이트)
usage.ru_utime    사용자 모드 CPU 시간(초)
usage.ru_stime    커널 모드 CPU 시간(초)
```

- `RUSAGE_SELF` 는 「다른 프로세스 말고 나 자신」을 뜻한다.
- 원본은 `ru_maxrss / 1024` 를 「MB」로 찍는데, 이는 단위가 kB 인 Linux 에서만 맞다.
- `resource` 는 Unix 전용 모듈이다(원본 주석: 윈도우 미지원).

> **RSS** — 프로세스가 지금 실제 물리 메모리(RAM)에 올려 두고 있는 양.\
> 예: `ru_maxrss` 는 실행 중 RSS 가 가장 컸던 순간의 값이다.

> **사용자 모드 / 커널 모드 시간** — 내 코드가 CPU 를 쓴 시간 / 내 요청(파일 읽기 등)을 처리하느라 OS 가 CPU 를 쓴 시간.\
> 예: 파일을 많이 읽는 스크립트는 `ru_stime` 이 커진다.

### (6) `/proc/meminfo` 직접 파싱 — 외부 의존성 없는 시스템 메모리

**언제 쓰나** — Linux 에서 `psutil` 을 깔 수 없을 때.

```text
/proc/meminfo 의 한 줄
"MemTotal:       16384000 kB"
      │ line.split(':')
      ▼
["MemTotal", "       16384000 kB\n"]     ← 길이 2 인 줄만 쓴다
      │ [0].strip()          [1].strip().split()[0]
      ▼                           ▼
   key = "MemTotal"          value = "16384000"
      │
      ▼
meminfo["MemTotal"] = 16384000   (단위 kB)
      │ / 1024
      ▼
total_mb = 16000.0
```

- `/proc/meminfo` 는 디스크의 파일이 아니라 Linux 커널이 읽을 때마다 만들어 주는 가상 파일이다.
- 한 줄은 「키: 값 kB」 꼴이라 `:` 로 자르고, 값 쪽은 공백으로 잘라 첫 토큰(숫자)만 쓴다.
- `split(':')` 결과가 두 조각이 아닌 줄은 건너뛴다.
- `MemTotal` 은 전체 메모리, `MemAvailable` 은 새 프로그램이 당장 쓸 수 있는 메모리다.
- 사용률은 `(1 - 사용가능/전체) × 100` 으로 계산한다.
- 키가 없으면 `meminfo.get(키, 0)` 이 0 을 돌려준다.
- 파일이 있는지는 `os.path.exists('/proc/meminfo')` 로 먼저 확인해 Linux 가 아닌 곳에서는 이 블록을 건너뛴다.
- 같은 방식으로 `/proc/cpuinfo` 를 파싱하면 CPU 정보도 외부 라이브러리 없이 얻을 수 있다(원본 팁).

### (7) `psutil` 패턴 — 문자열로만 보여 준다

**언제 쓰나** — CPU 사용률 · 스왑 · 파티션별 디스크 · 네트워크 송수신 · 다른 프로세스 목록이 필요할 때.

```text
print("""
import psutil
print(f"CPU 사용률: {psutil.cpu_percent(interval=1)}%")
…
""")
      │
      ▼
삼중 따옴표 일반 문자열 → 안의 글자를 그대로 화면에 찍을 뿐
psutil 은 import 되지 않고, {…} 도 계산되지 않는다
```

- 원본의 6절은 `psutil` 코드를 **실행하지 않는다** — 바깥 문자열에 `f` 접두사가 없으므로 `{psutil.cpu_percent(...)}` 는 중괄호째 글자로 남는다.
- 그래서 `psutil` 이 설치되지 않은 컴퓨터에서도 6절은 오류 없이 지나간다.
- 문자열에 담긴 사용 예는 이렇게 나뉜다.

| 대상 | 호출 | 얻는 것 |
|---|---|---|
| CPU | `psutil.cpu_percent(interval=1)` · `cpu_percent(percpu=True)` · `cpu_freq()` | 전체 · 코어별 사용률, 주파수 |
| 메모리 | `virtual_memory()` · `swap_memory()` | `.total` · `.percent` |
| 디스크 | `disk_partitions()` → `disk_usage(part.mountpoint)` | 파티션별 사용률 |
| 네트워크 | `net_io_counters()` | `.bytes_sent` · `.bytes_recv` |
| 프로세스 | `process_iter(['pid', 'name', 'cpu_percent'])` | 각 `proc.info` |

> **psutil** — 여러 OS 에서 같은 함수로 시스템 · 프로세스 정보를 읽게 해 주는 외부 라이브러리.\
> 예: `pip install psutil` 로 설치한다.

### (8) `system_summary()` — dict 로 모아 JSON 으로

**언제 쓰나** — 모니터링 · 리포팅 서버에 보낼 한 장짜리 요약을 만들 때.

```text
system_summary()
  ├─ disk_usage('/')  → total, used, free
  ├─ info = { platform, python, machine, cpu_count, pid,
  │           disk_total_gb (round …, 1), disk_used_pct (round …, 1) }
  ├─ hasattr(os, 'getloadavg') 이면 info['load_avg'] = 튜플
  └─ return info
        │
        ▼
json.dumps(info, indent=2, default=str)  → 들여쓰기 2칸 JSON 문자열
```

- 값은 `round(…, 1)` 로 소수 한 자리에서 반올림해 넣는다.
- `load_avg` 는 Unix 에서만 들어가므로, 같은 함수라도 OS 에 따라 키 개수가 다르다.
- `default=str` 은 JSON 이 모르는 객체를 만나면 `str()` 로 바꿔 넣으라는 안전망이다.
- 튜플은 JSON 이 아는 꼴이라 `default` 를 거치지 않고 배열(`[...]`)이 된다 — 튜플은 JSON 의 배열로 바뀐다.

> **직렬화** — 메모리의 객체를 문자열 · 바이트처럼 저장 · 전송할 수 있는 꼴로 바꾸는 일.\
> 예: `json.dumps({'a': 1})` → `'{"a": 1}'`.

## 문법 — 형태와 규칙

```python
import os, platform, shutil

def mini_report() -> dict:
    total, used, free = shutil.disk_usage('/')
    report = {
        'os': platform.system(),
        'cpus': os.cpu_count(),
        'free_gb': round(free / 1024**3, 1),
    }
    if hasattr(os, 'getloadavg'):        # Unix 에만 있는 함수
        report['load'] = os.getloadavg()
    return report

print(mini_report())
```

- `platform.*()` 는 함수 호출, `sys.platform` · `sys.byteorder` 는 값이다 — 괄호를 붙일 자리를 헷갈리지 않는다.
- OS 마다 있고 없는 함수는 `hasattr(모듈, '이름')` 으로 먼저 묻는다.
- OS 마다 있고 없는 파일은 `os.path.exists(경로)` 로 먼저 묻는다.
- 바이트 → GB 는 `/ (1024**3)`, kB → MB 는 `/ 1024` 다.
- 표시용 반올림은 f-string 의 `:.1f`, 값 자체의 반올림은 `round(x, 1)` 이다.
- JSON 으로 내보낼 dict 에는 `json.dumps(…, default=str)` 로 안전망을 둔다.

## 어디서 틀리나

### 1. `import resource` 는 Windows 에서 그 자리에서 멈춘다

원본은 `import resource` 뒤에 `hasattr(resource, 'getrusage')` 로 확인한다.
그러나 `resource` 는 Unix 전용 모듈이라 Windows 에서는 `import` 줄에서 `ImportError` 가 난다.
`hasattr` 검사는 거기까지 가지 못하므로 보호막이 되지 못한다.
원본의 주장(「윈도우 미지원」을 `hasattr` 로 피한다는 듯한 구조) → 의심스러운 까닭: 모듈이 없으면 `import` 가 먼저 실패한다.
막으려면 `try: import resource / except ImportError:` 로 감싸야 한다.

### 2. `ru_maxrss / 1024` 를 「MB」 라고 부르는 것은 Linux 에서만 맞다

원본 주석이 직접 밝히듯 `ru_maxrss` 의 단위는 Linux 에서 kB, macOS 에서 바이트다.
같은 식을 macOS 에서 돌리면 값은 KB 인데 「MB」 표를 달고 찍힌다 — 숫자가 1024 배 부풀어 보인다.

### 3. `sys.maxsize` 는 「최대 정수」가 아니다

원본은 `최대 정수: {sys.maxsize}` 라고 찍고, 주석에 「메모리 한계 추정용」 이라고 적었다.
그러나 Python 의 `int` 는 크기 제한이 없어서 `sys.maxsize + 1` 도 평범하게 만들어진다.
원본의 주장 → 의심스러운 까닭: `sys.maxsize` 는 리스트 길이 · 인덱스 같은 「크기」 값이 가질 수 있는 최댓값이고, 정수 자체나 메모리 양의 한계가 아니다.
쓸모 있는 쓰임은 「64비트 빌드인가」를 가늠하는 정도다(`sys.maxsize > 2**32`).

### 4. `/proc/meminfo` 에 키가 없으면 조용히 틀리거나 터진다

`meminfo.get('MemAvailable', 0)` 은 키가 없을 때 0 을 준다.
`MemAvailable` 이 없는 오래된 커널이면 사용 가능이 0 MB, 사용률이 100% 로 찍힌다 — 오류 없이 틀린 값이 나온다.
`MemTotal` 이 없으면 `avail_mb / total_mb` 에서 0 으로 나누어 `ZeroDivisionError` 가 난다.

### 5. `hasattr` 로 묻지 않으면 Windows 에서 `AttributeError`

`os.getuid()` · `os.getloadavg()` 를 그냥 부르면 Windows 에서 `AttributeError` 가 난다.
원본처럼 조건 표현식으로 감싸면 호출 자체가 일어나지 않는다.

### 6. 6절의 `psutil` 은 실행되지 않는다

6절은 문자열을 찍을 뿐이다.
「이 스크립트를 돌렸으니 CPU 사용률이 보이겠지」 라고 기대하면 안 된다 — 중괄호째 코드 글자가 보인다.
실제로 쓰려면 `psutil` 을 설치하고 문자열 밖으로 꺼내 실행해야 한다.

### 7. 외부 의존성 없이 하려면 `/proc` 를 읽는다

원본 팁 — 기본 정보는 `platform` · `os` 로 충분하고, 상세 모니터링은 `psutil` 이 편하다.
설치를 피해야 하는 Linux 환경에서는 `/proc/meminfo` · `/proc/cpuinfo` 를 직접 파싱하는 길이 있다.
대가는 이식성이다 — `/proc` 는 Linux 에만 있다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 재귀 제한 기본값 1000 | CPython 구현의 기본값 — 언어 보장 아님 (원본 주석) |
| `platform.python_implementation()` 이 `'CPython'` | 지금 돌리는 인터프리터에 따라 다르다 — PyPy 면 `'PyPy'` |
| `ru_maxrss` 단위 Linux=kB, macOS=바이트 | 각 OS 의 `getrusage` 구현 (원본 주석) |
| `resource` · `os.getuid` · `os.getloadavg` 는 Unix 전용 | 플랫폼(OS)이 그 기능을 주느냐에 달렸다 |
| `/proc/meminfo` 의 줄 꼴과 `MemAvailable` 키 | Linux 커널 — 커널 버전에 따라 키가 없을 수 있다 (확인 필요) |
| `sys.maxsize` 의 실제 값 | 빌드의 비트 수(32/64) |
| `sys.byteorder` 의 값 | CPU 하드웨어 |
| 기본 인코딩이 「보통 utf-8」 | 원본 주석 — Python 3 에서 언제나 그런지는 (확인 필요) |
| `os.cpu_count()` 는 논리 코어 수 | Python 표준 라이브러리 문서의 정의 (원본 주석) |
| 튜플이 JSON 배열이 된다 | Python 표준 라이브러리 `json` 모듈의 동작 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| OS 에 따라 경로 · 명령을 나눈다 | `sys.platform` · `platform.system()` | `platform.platform()` 문자열을 잘라 비교 |
| 버그 리포트에 환경을 남긴다 | `platform.platform()` · `sys.version` | 손으로 적은 환경 메모 |
| 병렬 작업 개수를 정한다 | `os.cpu_count()` | 고정 숫자 |
| 큰 파일 쓰기 전 공간 확인 | `shutil.disk_usage(경로)` | 셸 명령 출력 파싱 |
| 내 스크립트의 최대 메모리 | `resource.getrusage(RUSAGE_SELF)` (Unix) | `/proc/meminfo` (시스템 전체 값이다) |
| Linux, 설치 불가 환경의 시스템 메모리 | `/proc/meminfo` 파싱 | `psutil` |
| 여러 OS 에서 CPU 사용률 · 네트워크 · 프로세스 목록 | `psutil` | `/proc` 파싱(Linux 에서만 된다) |

## 핵심 문장

1. **`platform` · `sys` 는 「어떤 환경인가」, `os` · `shutil` · `resource` 는 「얼마나 쓰나」를 답한다.**
2. **OS 마다 다른 기능은 먼저 묻는다** — 함수는 `hasattr`, 파일은 `os.path.exists`, 모듈은 `try/except ImportError`.
3. **단위를 따라간다** — `disk_usage` 는 바이트, `/proc/meminfo` 는 kB, `ru_maxrss` 는 OS 마다 다르다.
4. **표준 라이브러리로 부족하면 `psutil`, 설치가 안 되면 Linux 의 `/proc` 를 읽는다.**
5. **요약은 dict 로 모아 `json.dumps(…, default=str)` 로 내보낸다.**

## 관련 자료

- `environment` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [process-management](../11-process-management/2-summary.md)
- `docker-python` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/networking.json` 의 `system-info`

## 용어 풀이

- **아키텍처** — CPU 가 이해하는 명령 집합의 종류(`x86_64` · `arm64`).
- **커널 릴리스** — OS 핵심(커널)의 버전 번호.
- **PID / PPID** — 프로세스 번호 / 그 프로세스를 띄운 부모의 번호.
- **UID** — Unix 에서 사용자를 가리키는 번호.
- **CWD** — 현재 작업 디렉터리, 상대 경로의 기준점.
- **논리 CPU 코어** — OS 가 따로 일을 맡길 수 있는 CPU 단위의 수.
- **로드 평균** — 최근 1 · 5 · 15분 동안 CPU 를 쓰거나 기다린 작업 수의 평균.
- **엔디안(바이트 순서)** — 여러 바이트 수를 메모리에 놓는 순서(`little` · `big`).
- **RSS** — 프로세스가 실제 RAM 에 올려 둔 메모리 양.
- **사용자 모드 / 커널 모드 시간** — 내 코드가 쓴 CPU 시간 / OS 가 내 요청을 처리하며 쓴 CPU 시간.
- **`/proc`** — Linux 커널이 시스템 · 프로세스 정보를 파일 꼴로 보여 주는 가상 파일 시스템.
- **`MemTotal` · `MemAvailable`** — 전체 메모리 / 새 프로그램이 당장 쓸 수 있는 메모리.
- **스왑** — RAM 이 모자랄 때 디스크를 메모리처럼 빌려 쓰는 공간.
- **psutil** — 여러 OS 에서 시스템 · 프로세스 정보를 같은 함수로 읽는 외부 라이브러리.
- **직렬화** — 객체를 저장 · 전송할 수 있는 문자열 · 바이트로 바꾸는 일.
- **`hasattr`** — 객체에 그 이름의 속성이 있는지 `True`/`False` 로 답하는 내장 함수.

## 더 들어가면

- `os.cpu_count()` 는 값을 알 수 없을 때 `None` 을 돌려줄 수 있다 — 계산에 쓰기 전에 `or 1` 같은 기본값을 두는 편이 안전하다 (확인 필요).
- 컨테이너(Docker 등)나 CPU 친화도가 걸린 프로세스에서는 `os.cpu_count()` 가 실제로 쓸 수 있는 코어보다 큰 값을 줄 수 있다 — Linux 의 `os.sched_getaffinity(0)` 가 더 정확할 수 있다 (확인 필요).
- 최근 Python 에는 프로세스가 쓸 수 있는 코어 수를 주는 `os.process_cpu_count()` 가 추가되었다는 말이 있다 (확인 필요 — 버전 포함).
- `platform.processor()` 는 Linux 에서 빈 문자열이나 `machine()` 과 같은 값을 줄 때가 있다 (확인 필요).
- `psutil.cpu_percent()` 를 `interval` 없이 처음 부르면 비교할 이전 값이 없어 의미 없는 값(0.0 등)을 줄 수 있다 — 원본이 `interval=1` 을 준 까닭으로 보인다 (확인 필요).
- `shutil.disk_usage('/')` 를 Windows 에서 부르면 현재 드라이브의 루트를 가리키는 것으로 동작할 수 있다 (확인 필요).
- `ru_maxrss` 는 「최대」 값이라 메모리를 풀어도 줄지 않는다 — 지금 RSS 가 필요하면 Linux 의 `/proc/self/status` 의 `VmRSS` 를 읽는 방법이 있다 (확인 필요).
