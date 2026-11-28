# python/python-networking/14 — 시스템 정보: platform과 리소스 모니터링 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 코드 글자가 중괄호째 찍히고, 오류는 나지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

빈 줄 하나, 이어서 아래 한 줄, 그리고 빈 줄 하나가 보인다.

```text

print(f"CPU 사용률: {psutil.cpu_percent(interval=1)}%")

```

**왜 그런가**

바깥 문자열은 `"""…"""` 일반 문자열이고 `f` 접두사가 없다.
그래서 안쪽의 `{psutil.cpu_percent(interval=1)}` 는 계산되지 않고 글자로 남는다.
안쪽의 `f"…"` 도 문자열의 일부일 뿐 실행되는 코드가 아니다.
`psutil` 이라는 이름이 평가되지 않으므로 설치되지 않아도 `NameError` · `ImportError` 가 나지 않는다.
문자열이 줄바꿈으로 시작하고 줄바꿈으로 끝나며, `print` 가 줄바꿈을 하나 더 붙이므로 앞뒤로 빈 줄이 생긴다.
근거 — 2-summary 「동작 방식 (7)」, 「어디서 틀리나 6」.

### 2. `MemTotal 16384000 16000.0`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
MemTotal 16384000 16000.0
```

**왜 그런가**

`split(':')` 는 `["MemTotal", "       16384000 kB\n"]` 두 조각을 만든다.
앞 조각을 `strip()` 하면 `MemTotal` 이다.
뒤 조각을 `strip()` 하면 `"16384000 kB"`, 공백으로 `split()` 한 첫 토큰이 `"16384000"` 이다.
`int` 로 바꾸면 16384000(kB), 1024 로 나누면 16000.0(MB)이다 — `/` 는 언제나 실수를 내므로 `.0` 이 붙는다.
근거 — 2-summary 「동작 방식 (6)」의 그림.

### 3. 4절까지 지나가고, 5절의 `import resource` 에서 멈춘다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

1~3절은 `platform` · `os` · `sys` 만 쓰므로 지나간다.
2절의 UID · 로드 평균은 `hasattr` 덕에 `UID: N/A` · `로드: N/A` 로 찍힌다.
4절의 `shutil.disk_usage('/')` 도 지나갈 것으로 보인다(Windows 에서 `'/'` 의 의미는 확인 필요).
5절 제목을 찍은 뒤 `import resource` 줄에서 `ImportError`(정확히는 `ModuleNotFoundError`)가 나고 스크립트가 끝난다.

**왜 그런가**

`resource` 는 Unix 전용 모듈이라 Windows 에는 없다.
뒤따르는 `hasattr(resource, 'getrusage')` 검사는 `import` 가 성공한 뒤에야 의미가 있어서 보호막이 되지 못한다.
근거 — 2-summary 「어디서 틀리나 1」 · 「어디서 틀리나 5」. (Windows 에서 4절의 동작은 원본에 근거 없음 — 추론)

### 4. JSON 배열이 되고, `default=str` 은 쓰이지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
{
  "cpu_count": 8,
  "load_avg": [
    0.5,
    0.25,
    0.125
  ]
}
```

**왜 그런가**

`json` 모듈은 튜플을 배열로 직렬화하는 법을 이미 안다.
`default` 는 JSON 이 모르는 객체를 만났을 때만 불리므로 이 dict 에서는 한 번도 불리지 않는다.
`indent=2` 라서 한 단계 깊어질 때마다 두 칸씩 들여쓴다.
근거 — 2-summary 「동작 방식 (8)」, 「구현 세부사항 대 언어 보장」의 마지막 줄.

### 5. Windows 의 `os` 에는 `getuid` 라는 이름이 없기 때문이다

`getuid` 는 Unix 전용 함수라 Windows 에서 `os.getuid()` 를 부르면 `AttributeError` 가 난다.
`hasattr(os, 'getuid')` 로 이름이 있는지 먼저 묻고, 조건 표현식 `A if 조건 else B` 로 감싸면 조건이 거짓일 때 호출 자체가 일어나지 않는다.
그래서 같은 스크립트가 OS 를 가리지 않고 2절을 지나가며, 없는 쪽에서는 `UID: N/A` 를 찍는다.
근거 — 2-summary 「동작 방식 (2)」, 「어디서 틀리나 5」.

### 6. Linux 에서는 맞고, macOS 에서는 1024 배 부풀어 보인다

`ru_maxrss` 의 단위는 Linux 에서 kB, macOS 에서 바이트다.
Linux 에서 kB ÷ 1024 = MB 이므로 표가 맞다.
macOS 에서는 바이트 ÷ 1024 = KB 인데 「MB」 표가 붙으니, 실제보다 1024 배 큰 MB 값처럼 읽힌다.
Windows 는 `resource` 모듈이 없어 이 줄까지 오지 못한다.
근거 — 2-summary 「동작 방식 (5)」, 「어디서 틀리나 2」.

### 7. 만들 수 있다 — `sys.maxsize` 는 「크기」 값의 한계다

Python 의 `int` 는 크기 제한이 없어서 `sys.maxsize + 1` 도 평범한 정수다.
`sys.maxsize` 는 리스트 길이 · 인덱스처럼 「크기」를 나타내는 값이 가질 수 있는 최댓값이다.
그래서 원본의 「최대 정수」 표와 「메모리 한계 추정용」 주석은 의심스럽고, 쓸모는 64비트 빌드인지 가늠하는 정도다.
근거 — 2-summary 「어디서 틀리나 3」.

### 8. `MemAvailable` 이 없으면 100%, `MemTotal` 이 없으면 0 으로 나누기 오류

`meminfo.get(키, 0)` 은 키가 없을 때 0 을 돌려준다.
`MemAvailable` 이 없으면 `avail_mb = 0` 이라 `(1 - 0/total_mb) × 100 = 100.0%` 가 오류 없이 찍힌다 — 조용히 틀린 값이다.
`MemTotal` 이 없으면 `total_mb = 0` 이라 `avail_mb / total_mb` 에서 `ZeroDivisionError` 가 난다.
근거 — 2-summary 「동작 방식 (6)」, 「어디서 틀리나 4」.

### 9. 함수 호출이 주는 대문자 이름 대 값으로 주는 소문자 짧은 이름 — 분기에는 `sys.platform`

`platform.system()` 은 함수를 불러 `'Linux'` · `'Windows'` · `'Darwin'` 을 받는다.
`sys.platform` 은 괄호 없는 값으로 `'linux'` · `'win32'` · `'darwin'` 을 준다.
둘 다 「어떤 OS 인가」라는 같은 사실이다.
2-summary 「언제 쓰고 언제 안 쓰나」 는 OS 분기에 두 쪽을 모두 권하고, `platform.platform()` 의 긴 요약 문자열을 잘라 비교하는 것만 피하라고 한다.
짧고 고정된 값이라 `if sys.platform == 'win32':` 처럼 비교하기 쉽다는 점에서 `sys.platform` 이 조금 더 가볍다. (원본에 근거 없음 — 추론)
근거 — 2-summary 「동작 방식 (3)」, 「언제 쓰고 언제 안 쓰나」.

### 10. 표준 라이브러리는 설치 없이 기본 정보, `/proc` 는 설치 없이 Linux 전용, `psutil` 은 설치하고 여러 OS 에서 상세 정보

- 표준 라이브러리(`platform` · `os` · `sys` · `shutil`)는 설치가 필요 없지만, 일부(`resource` · `getuid` · `getloadavg`)는 Unix 에만 있다.
- `/proc/meminfo` · `/proc/cpuinfo` 파싱은 외부 의존성이 없지만 Linux 에서만 된다.
- `psutil` 은 설치해야 하는 대신 여러 OS 에서 같은 함수로 읽는다.
- 원본에서 `psutil` 만이 보여 주는 정보는 CPU 사용률(전체 · 코어별) · CPU 주파수 · 스왑 · 파티션별 디스크 사용률 · 네트워크 송수신 바이트 · 다른 프로세스 목록이다.

근거 — 2-summary 「동작 방식 (7)」의 표, 「어디서 틀리나 7」, 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 시스템 정보 조사 스크립트 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `platform` 아홉 함수 | 1절의 `platform.system()` ~ `platform.python_implementation()` |
| 2. PID · PPID · CWD · CPU 수 | `os.getpid()` · `os.getppid()` · `os.getcwd()` · `os.cpu_count()` |
| 3. UID · 로드 평균은 있을 때만 | `… if hasattr(os, 'getuid') else "UID: N/A"` · `… if hasattr(os, 'getloadavg') else "로드: N/A"` |
| 4. `sys` 일곱 값 | `sys.executable` · `sys.version` · `sys.byteorder` · `sys.maxsize` · `sys.getrecursionlimit()` · `sys.getdefaultencoding()` · `sys.platform` |
| 5. 디스크 GB · 사용률 | `total, used, free = shutil.disk_usage('/')`, `/ (1024**3):.1f`, `used/total*100` |
| 6. 현재 프로세스 사용량 | `if hasattr(resource, 'getrusage'):` → `resource.getrusage(resource.RUSAGE_SELF)` 의 `ru_maxrss` · `ru_utime` · `ru_stime` |
| 7. `/proc/meminfo` 파싱 | `if os.path.exists('/proc/meminfo'):` → `line.split(':')`, `len(parts) == 2`, `split()[0]`, `meminfo[key] = int(value)`, `total_mb` · `avail_mb` |
| 8. psutil 예를 찍기만 | 6절의 `print("""…""")` (import 없음) |
| 9. 요약 dict | `def system_summary() -> dict:` 의 `info` 와 `if hasattr(os, 'getloadavg'): info['load_avg'] = …` |
| 10. JSON 으로 | `json.dumps(system_summary(), indent=2, default=str)` |
| 11. 핵심 정리 | 마지막 다섯 `print` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-networking/reference/system-info.py`

```python
# [네트워크 & 시스템] 시스템 정보: platform과 리소스 모니터링
# 설명: platform, os 모듈로 시스템 정보 조회, psutil 패턴으로 CPU/메모리/디스크 모니터링
# 팁: platform과 os 모듈로 기본 시스템 정보를 얻을 수 있다. 상세한 리소스 모니터링에는 psutil(외부 라이브러리)을 사용한다. Linux에서는 /proc/meminfo, /proc/cpuinfo를 직접 파싱하면 외부 의존성 없이 시스템 정보를 얻을 수 있다.

"""시스템 정보: platform, os, 리소스 모니터링"""
# platform: OS/아키텍처/Python 버전 정보
import platform
# os: PID, CPU 수, 환경 변수
import os
# sys: Python 런타임 정보
import sys
# shutil: 디스크 사용량
import shutil

# === 1. 플랫폼 정보 ===
print("=== 1. 플랫폼 정보 ===")
# 시스템(OS) 종류
print(f"시스템:       {platform.system()}")           # Linux, Windows, Darwin
# 커널 릴리스 (예: 6.17.0)
print(f"릴리스:       {platform.release()}")          # 커널 버전
# 빌드 상세
print(f"버전:         {platform.version()}")          # 상세 버전
# 머신 (아키텍처)
print(f"머신:         {platform.machine()}")          # x86_64, arm64
# 프로세서명
print(f"프로세서:     {platform.processor()}")        # 프로세서 정보
# (비트, 링커 포맷)
print(f"아키텍처:     {platform.architecture()}")     # ('64bit', 'ELF')
# 전체 요약 문자열
print(f"플랫폼:       {platform.platform()}")         # 전체 문자열
# Python 버전 (X.Y.Z)
print(f"Python:       {platform.python_version()}")   # 3.x.x
# CPython/PyPy 등
print(f"Python 구현:  {platform.python_implementation()}")  # CPython

# === 2. OS 정보 ===
print("\n=== 2. OS / 프로세스 정보 ===")
# 현재 프로세스 ID
print(f"PID:          {os.getpid()}")
# 부모 프로세스 ID
print(f"PPID:         {os.getppid()}")
# UID (Unix 전용)
print(f"UID:          {os.getuid()}" if hasattr(os, 'getuid') else "UID: N/A")
# 현재 작업 디렉토리
print(f"CWD:          {os.getcwd()}")
# 논리 CPU 코어 수
print(f"CPU 수:       {os.cpu_count()}")
# 1/5/15분 평균 부하 (Unix)
print(f"로드 평균:    {os.getloadavg()}" if hasattr(os, 'getloadavg') else "로드: N/A")

# === 3. sys 정보 ===
print("\n=== 3. Python 런타임 정보 ===")
# Python 인터프리터 경로
print(f"실행 경로:    {sys.executable}")
# 빌드 정보 포함 버전
print(f"버전:         {sys.version}")
# 'little' 또는 'big' (CPU 엔디안)
print(f"바이트 순서:  {sys.byteorder}")
# 플랫폼 최대 정수 (메모리 한계 추정용)
print(f"최대 정수:    {sys.maxsize}")
# 재귀 호출 한계 (기본 1000)
print(f"재귀 제한:    {sys.getrecursionlimit()}")
# 기본 문자열 인코딩 (보통 utf-8)
print(f"기본 인코딩:  {sys.getdefaultencoding()}")
# 'linux', 'darwin', 'win32'
print(f"플랫폼:       {sys.platform}")

# === 4. 디스크 정보 ===
print("\n=== 4. 디스크 사용량 ===")
# disk_usage: (전체, 사용, 여유) 바이트
total, used, free = shutil.disk_usage('/')
print(f"전체: {total / (1024**3):.1f} GB")
print(f"사용: {used / (1024**3):.1f} GB ({used/total*100:.1f}%)")
print(f"여유: {free / (1024**3):.1f} GB")

# === 5. 메모리 정보 (표준 라이브러리만) ===
print("\n=== 5. 메모리 (표준 라이브러리) ===")
# resource: Unix 리소스 사용량 (윈도우 미지원)
import resource
if hasattr(resource, 'getrusage'):
    # RUSAGE_SELF: 현재 프로세스 사용량
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss: 최대 RSS (Linux=kB, macOS=bytes)
    print(f"최대 RSS:     {usage.ru_maxrss / 1024:.1f} MB")
    # 사용자 모드 CPU 시간
    print(f"사용자 시간:  {usage.ru_utime:.3f}초")
    # 커널 모드 CPU 시간
    print(f"시스템 시간:  {usage.ru_stime:.3f}초")

# /proc/meminfo 파싱 (Linux)
# Linux 전용: /proc로 시스템 정보 직접 조회 (외부 라이브러리 불필요)
if os.path.exists('/proc/meminfo'):
    meminfo = {}
    with open('/proc/meminfo') as f:
        for line in f:
            # "Key: value kB" 형태
            parts = line.split(':')
            if len(parts) == 2:
                key = parts[0].strip()
                # 첫 토큰만 (kB 단위)
                value = parts[1].strip().split()[0]  # kB 숫자만
                meminfo[key] = int(value)

    # kB → MB 변환
    total_mb = meminfo.get('MemTotal', 0) / 1024
    avail_mb = meminfo.get('MemAvailable', 0) / 1024
    print(f"\n시스템 메모리 (Linux):")
    print(f"  전체: {total_mb:.0f} MB")
    print(f"  사용 가능: {avail_mb:.0f} MB")
    print(f"  사용률: {(1 - avail_mb/total_mb)*100:.1f}%")

# === 6. psutil 패턴 (개념) ===
print("\n=== 6. psutil 패턴 (개념 코드) ===")
# psutil: 크로스 플랫폼 시스템/프로세스 모니터링 (외부 라이브러리)
print("""
import psutil

# CPU
print(f"CPU 사용률: {psutil.cpu_percent(interval=1)}%")
print(f"CPU별: {psutil.cpu_percent(percpu=True)}")
print(f"CPU 주파수: {psutil.cpu_freq()}")

# 메모리
mem = psutil.virtual_memory()
print(f"메모리: {mem.total/1024**3:.1f}GB, 사용률: {mem.percent}%")

swap = psutil.swap_memory()
print(f"스왑: {swap.total/1024**3:.1f}GB, 사용률: {swap.percent}%")

# 디스크
for part in psutil.disk_partitions():
    usage = psutil.disk_usage(part.mountpoint)
    print(f"{part.mountpoint}: {usage.percent}% 사용")

# 네트워크
net = psutil.net_io_counters()
print(f"송신: {net.bytes_sent/1024**2:.1f}MB")
print(f"수신: {net.bytes_recv/1024**2:.1f}MB")

# 프로세스
for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
    print(f"PID {proc.info['pid']}: {proc.info['name']}")
""")

# === 7. 시스템 정보 수집 유틸리티 ===
print("=== 7. 시스템 정보 요약 ===")

# 핵심 정보를 dict로 모아 반환 (모니터링/리포팅용)
def system_summary() -> dict:
    """시스템 정보 딕셔너리 반환"""
    total, used, free = shutil.disk_usage('/')
    info = {
        'platform': platform.platform(),
        'python': platform.python_version(),
        'machine': platform.machine(),
        'cpu_count': os.cpu_count(),
        'pid': os.getpid(),
        # GB 단위 + 소수점 1자리
        'disk_total_gb': round(total / (1024**3), 1),
        # 사용률 %
        'disk_used_pct': round(used / total * 100, 1),
    }
    # Unix만 가능
    if hasattr(os, 'getloadavg'):
        info['load_avg'] = os.getloadavg()
    return info

# JSON으로 깔끔히 출력
import json
# default=str: 직렬화 불가 객체는 str()로 변환
print(json.dumps(system_summary(), indent=2, default=str))

print("\n=== 핵심 정리 ===")
print("platform: OS, 아키텍처, Python 버전")
print("os: PID, CPU 수, 로드 평균")
print("shutil.disk_usage(): 디스크 용량")
print("/proc/meminfo: Linux 메모리 정보")
print("psutil (외부): 상세 CPU/메모리/디스크/네트워크/프로세스")
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**

- 플랫폼마다 다른 것은 세 가지 방법으로 먼저 묻는다 — 함수는 `hasattr`, 파일은 `os.path.exists`, (원본엔 없지만) 모듈은 `try/except ImportError`.
- `import resource` 는 원본처럼 그냥 두면 Windows 에서 멈춘다 — 이식성이 필요하면 `try` 로 감싼다.
- 단위 변환이 핵심이다 — 디스크는 바이트 ÷ `1024**3`, `/proc/meminfo` 는 kB ÷ 1024, `ru_maxrss` 는 OS 에 따라 kB 또는 바이트다.
- `/proc/meminfo` 파싱은 `:` 로 한 번, 공백으로 한 번 잘라 첫 토큰만 쓰는 두 번 자르기다.
- 6절은 문자열을 찍을 뿐이라 `f` 접두사가 없는 한 `{…}` 가 계산되지 않는다.
- `system_summary()` 는 OS 에 따라 `load_avg` 키가 있거나 없으므로, 받는 쪽은 `.get('load_avg')` 처럼 읽는 편이 안전하다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
