# python/python-networking/14 — 시스템 정보: platform과 리소스 모니터링 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 6절처럼 `psutil` 코드를 삼중 따옴표 문자열에 담아 찍으면 (예측)

```python
# 질문용 발췌 — psutil 은 설치되어 있지 않다고 하자
print("""
print(f"CPU 사용률: {psutil.cpu_percent(interval=1)}%")
""")
```

- 화면에는 무엇이 나타나고, `psutil` 이 없어서 오류가 나는가?

### 2. `/proc/meminfo` 한 줄을 원본 방식으로 자르면 (예측)

```python
# 질문용 발췌
line = "MemTotal:       16384000 kB\n"
parts = line.split(':')
key = parts[0].strip()
value = parts[1].strip().split()[0]
print(key, int(value), int(value) / 1024)
```

- 마지막 `print` 는 무엇을 찍는가?

### 3. 원본 스크립트를 Windows 에서 처음부터 돌리면 (예측)

- 원본 스크립트는 Windows 에서 어느 절까지 진행되고, 어디서 무슨 일로 멈추는가?

### 4. `load_avg` 튜플을 JSON 으로 바꾸면 (예측)

```python
# 질문용 발췌
import json
info = {'cpu_count': 8, 'load_avg': (0.5, 0.25, 0.125)}
print(json.dumps(info, indent=2, default=str))
```

- `load_avg` 값은 JSON 안에서 어떤 꼴로 나타나고, `default=str` 은 여기서 쓰이는가?

### 5. `os.getuid()` 를 `hasattr` 로 감싼 까닭 (왜)

- 원본이 `os.getuid()` 를 곧장 부르지 않고 `hasattr(os, 'getuid')` 로 먼저 묻는 까닭은 무엇인가?

### 6. `ru_maxrss / 1024` 를 「MB」 로 찍는 식 (경계)

- 이 식이 맞는 단위를 내는 OS 와 틀린 단위를 내는 OS 는 각각 어디이고, 틀리는 쪽에서 숫자는 어떻게 보이는가?

### 7. `sys.maxsize` 를 「최대 정수」 라고 부르는 원본 (경계)

- `sys.maxsize + 1` 이라는 정수를 만들 수 있는가, 그리고 `sys.maxsize` 는 실제로 무엇의 한계인가?

### 8. `MemAvailable` 이나 `MemTotal` 이 없는 `/proc/meminfo` (경계)

- 두 키가 각각 빠졌을 때 원본의 사용률 계산은 어떻게 되는가?

### 9. `platform.system()` 과 `sys.platform` (연결)

- 둘은 같은 사실을 어떻게 다른 꼴로 주며, OS 분기 코드에는 어느 쪽이 더 다루기 쉬운가?

### 10. 표준 라이브러리 · `/proc` 파싱 · `psutil` 사이의 선택 (연결)

- 세 방법은 이식성과 설치 부담에서 어떻게 다르며, `psutil` 만이 원본에서 보여 주는 정보는 무엇인가?

## 실습

### 실습 1. 시스템 정보 조사 스크립트 만들기

**만들 것** — 실행한 컴퓨터의 플랫폼 · 프로세스 · Python 런타임 · 디스크 · 메모리 정보를 절별로 찍고, 마지막에 핵심 정보를 dict 로 모아 JSON 으로 찍는 스크립트.

**요구 조건**

1단계 — 플랫폼 정보

1. `platform` 의 아홉 함수(`system` · `release` · `version` · `machine` · `processor` · `architecture` · `platform` · `python_version` · `python_implementation`)의 값을 한 줄씩 찍는다.

2단계 — OS / 프로세스 정보

2. PID · PPID · CWD · CPU 수를 찍는다.
3. UID 와 로드 평균은 `os` 에 그 함수가 있을 때만 부르고, 없으면 `UID: N/A` · `로드: N/A` 를 찍는다.

3단계 — Python 런타임 정보

4. `sys` 의 실행 경로 · 버전 · 바이트 순서 · `maxsize` · 재귀 제한 · 기본 인코딩 · 플랫폼을 찍는다.

4단계 — 디스크

5. 루트(`/`)의 디스크 전체 · 사용 · 여유를 GB 로 소수 한 자리까지 찍고, 사용 줄에는 사용률(%)을 괄호로 붙인다.

5단계 — 메모리

6. `resource.getrusage` 가 있으면 현재 프로세스의 최대 RSS(1024 로 나눈 값) · 사용자 시간 · 시스템 시간을 찍는다.
7. `/proc/meminfo` 가 있으면 `키: 값` 줄을 읽어 키 → 정수(kB) dict 를 만들고, 전체 · 사용 가능 메모리(MB)와 사용률(%)을 찍는다.

6단계 — psutil 패턴

8. CPU · 메모리 · 스왑 · 디스크 파티션 · 네트워크 · 프로세스 목록을 다루는 `psutil` 사용 예를 삼중 따옴표 문자열로 담아 **그대로 찍기만** 한다(`psutil` 을 import 하지 않는다).

7단계 — 요약

9. `system_summary()` 함수는 플랫폼 문자열 · Python 버전 · 머신 · CPU 수 · PID · 디스크 전체(GB, 소수 한 자리) · 디스크 사용률(%, 소수 한 자리)을 담은 dict 를 돌려주고, 로드 평균은 함수가 있을 때만 `load_avg` 키로 넣는다.
10. 그 dict 를 들여쓰기 2칸 JSON 으로 찍되, 직렬화할 수 없는 값은 `str()` 로 바꾸게 한다.
11. 끝에 다섯 줄짜리 핵심 정리를 찍는다.

**시작 코드**

```python
"""시스템 정보: platform, os, 리소스 모니터링"""
import platform
import os
import sys
import shutil

# === 1. 플랫폼 정보 ===
print("=== 1. 플랫폼 정보 ===")
print(f"시스템:       {platform.system()}")
# TODO: release, version, machine, processor, architecture,
#       platform, python_version, python_implementation 을 한 줄씩

# === 2. OS 정보 ===
print("\n=== 2. OS / 프로세스 정보 ===")
# TODO: PID, PPID
# TODO: UID — os 에 getuid 가 있을 때만 호출, 없으면 "UID: N/A"
# TODO: CWD, CPU 수
# TODO: 로드 평균 — os 에 getloadavg 가 있을 때만, 없으면 "로드: N/A"

# === 3. sys 정보 ===
print("\n=== 3. Python 런타임 정보 ===")
# TODO: executable, version, byteorder, maxsize,
#       getrecursionlimit(), getdefaultencoding(), platform

# === 4. 디스크 정보 ===
print("\n=== 4. 디스크 사용량 ===")
# TODO: '/' 의 (전체, 사용, 여유) 를 받아 GB 로 바꿔 찍기
#       사용 줄에는 사용률(%) 을 괄호로

# === 5. 메모리 정보 (표준 라이브러리만) ===
print("\n=== 5. 메모리 (표준 라이브러리) ===")
import resource
# TODO: getrusage 가 있으면 RUSAGE_SELF 의 ru_maxrss/1024, ru_utime, ru_stime

# TODO: /proc/meminfo 가 있으면
#   - 줄마다 ':' 로 잘라 두 조각인 줄만
#   - 키 = 앞 조각, 값 = 뒤 조각의 첫 토큰을 int 로
#   - MemTotal, MemAvailable 을 MB 로 바꿔 전체·사용 가능·사용률 찍기
print(f"\n시스템 메모리 (Linux):")  # ← 이 줄은 위 조건 블록 안으로 옮긴다

# === 6. psutil 패턴 (개념) ===
print("\n=== 6. psutil 패턴 (개념 코드) ===")
# TODO: psutil 사용 예(CPU/메모리/스왑/디스크/네트워크/프로세스)를
#       삼중 따옴표 문자열로 찍기만 한다 (import 하지 않는다)

# === 7. 시스템 정보 수집 유틸리티 ===
print("=== 7. 시스템 정보 요약 ===")

def system_summary() -> dict:
    """시스템 정보 딕셔너리 반환"""
    # TODO: 디스크 값을 받아 info dict 를 만든다
    # TODO: getloadavg 가 있을 때만 info['load_avg']
    ...

import json
# TODO: system_summary() 를 들여쓰기 2칸 JSON 으로, 직렬화 불가 값은 str 로

print("\n=== 핵심 정리 ===")
print("platform: OS, 아키텍처, Python 버전")
print("os: PID, CPU 수, 로드 평균")
print("shutil.disk_usage(): 디스크 용량")
print("/proc/meminfo: Linux 메모리 정보")
print("psutil (외부): 상세 CPU/메모리/디스크/네트워크/프로세스")
```

**확인 방법** — Linux 에서 `python3 system-info.py` 를 돌려 1~7절 제목이 차례로 찍히는지, 5절에 「시스템 메모리 (Linux):」 블록이 나오는지, 6절에 `psutil` 코드가 중괄호째 글자로 보이는지, 7절이 들여쓰기 2칸 JSON 인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
