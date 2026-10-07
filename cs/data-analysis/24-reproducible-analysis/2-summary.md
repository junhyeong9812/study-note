# data-analysis/24-reproducible-analysis — 재현 가능한 분석: 노트북 숨은 상태·시드·버전·파이프라인 — 정리 (힌트)

## 해결하는 문제

지난달 보고서의 숫자를 다시 만들어 달라는 요청을 받았다. 같은 노트북을 위에서부터 다시 돌렸더니 숫자가 다르다. 어느 쪽이 맞는지 아무도 모른다.

```text
  같은 분석인데 결과가 달라지는 출처
   ├─ 숨은 상태     노트북 셀을 고쳐 가며 순서 없이 실행 → 저장된 출력은 지금 코드와 다른 상태에서 나옴
   ├─ 무작위        시드 없는 표본 추출·부트스트랩 → 실행마다 다른 구간
   ├─ 순회 순서     set 순서·동률 처리 → 프로세스마다 다른 "1등"
   ├─ 환경          라이브러리 버전·함수 기본값 → 같은 "p90"이 다른 값
   └─ 데이터        원본을 정제본으로 덮어씀·손으로 고친 셀 → 처음부터 다시 만들 수 없음
```

- *재현 가능(reproducible)*: 이 노트에서는 "같은 입력 데이터와 같은 코드·환경으로 다시 실행하면 같은 결과가 나온다"는 뜻으로 쓴다. 다른 데이터로 같은 결론을 얻는 것(replication)과는 구분한다. 용어 정의는 분야마다 다르다 `[?]`.

쉬운 예: 요리 레시피에 "소금 적당히", "아까 만든 소스(만드는 법 없음)"가 적혀 있으면 다음에 같은 맛이 안 난다.

똑같은 구조다.\
분석 결과는 데이터 + 코드 + 환경 + 실행 순서의 함수다. 그중 하나라도 기록되지 않으면 다시 만들 수 없다.

실무 예:
- 실험 결과 보고서의 신뢰구간을 다른 사람이 다시 계산했더니 끝자리가 다르다. 시드가 없었다.
- "세그먼트별 최다 채널"이 대시보드를 새로 고칠 때마다 바뀐다. 동률을 순회 순서로 깼다.
- 노트북의 마지막 셀 출력이 보고서에 붙었는데, 그 출력은 지금은 지워진 셀이 만든 상태에서 나왔다.

## 동작·원리

### 1. 노트북의 숨은 상태 — 실행 순서가 결과를 정한다

```text
  셀       코드                                   위→아래 실행    실제 작성자 실행 순서
  c1_load  rows = [100, 120, None, 90, 300]           ①              ①
  c2_clean rows = [r for r in rows if r is not None]   ②              ②
  c3_cap   rows = [min(r, 200) for r in rows]          ③              ④ (나중에 추가)
  c4_report result = sum(rows)/len(rows)               ④ → 127.5      ③ → 152.5 (저장된 출력)
```

- 노트북은 셀들이 **하나의 전역 상태**를 공유한다. 셀을 어떤 순서로 몇 번 실행했느냐가 상태를 정한다. 화면의 위→아래 순서는 실행 순서를 보장하지 않는다.
- 같은 셀을 고쳐 가며 여러 번 실행하면 상태가 누적된다. `rows = [min(r, 150) …]`을 한 번 돌렸다가 200으로 되돌려도, 이미 150으로 깎인 값은 돌아오지 않는다(아래 실험 C).
- 대규모 관찰: Pimentel 외(2019)는 GitHub 노트북 약 116만 개를 모아 분석했다.
  - 실행 순서가 모호하지 않은 노트북 중 36.36%에 순서가 뒤바뀐 셀이 있었다.
  - 실행을 시도한 863,878개 중 오류 없이 끝난 것은 24.11%, 같은 결과를 낸 것은 4.03%였다.
  - 게재: 2019 IEEE/ACM 16th International Conference on Mining Software Repositories(MSR), pp. 507–517, DOI 10.1109/MSR.2019.00077(Crossref 서지).

### 2. 무작위 — 시드는 결과의 일부다

```text
  random.Random(None) ─▶ 운영체제 난수(없으면 시스템 시간)로 초기화 ─▶ 실행마다 다른 재표집 ─▶ 다른 구간
  random.Random(7)    ─▶ 같은 상태에서 시작     ─▶ 같은 재표집       ─▶ 같은 구간
```

- Python 3.12 문서 "Notes on Reproducibility": 같은 시드를 다시 쓰면 같은 수열이 재현된다(여러 스레드가 돌지 않는 한). `random` 모듈의 알고리즘·시딩은 버전마다 바뀔 수 있지만, 호환 시더에 같은 시드를 주면 `random()` 메서드가 같은 수열을 낸다는 것은 바뀌지 않는다고 보장한다.
  - 흔한 오해: "시드만 고정하면 모든 버전에서 같은 결과". 보장은 `random()` 수열에 대한 것이다. 문서는 "모듈의 알고리즘과 시딩 함수 대부분"이 버전마다 바뀔 수 있다고 적는다. `choices`·`sample` 같은 함수도 보장 밖이다(문서가 함수 이름을 하나하나 꼽지는 않는다).
- 시드는 보고서에 적는다. 결과가 시드에 민감하면(구간 끝자리가 크게 흔들리면) 반복 수가 부족하다는 신호이기도 하다. PRNG 원리는 [math/12-randomness-and-prng](../../math/12-randomness-and-prng/2-summary.md).

### 3. 해시 시드 — set 순서가 프로세스마다 다르다

```text
  {"web","ios","android","partner","kiosk"}
   프로세스 1 순회: ios, partner, android, kiosk, web     동률(40·40·40) 중 "먼저 본 것" → ios
   프로세스 2 순회: kiosk, android, partner, ios, web     → android
   sorted() 후 고르기                                     → android (해시 시드와 무관)
```

- Python 3.12 문서: `PYTHONHASHSEED`를 설정하지 않거나 `random`이면 `str`·`bytes` 해시에 무작위 시드가 쓰인다(해시 무작위화가 기본). 그래서 문자열 `set`의 순회 순서가 프로세스마다 다를 수 있다. `dict`는 삽입 순서로 순회하므로(Python 3.12 문서) 해시 시드와 무관하다. 다만 `set`을 순회해 채운 `dict`는 그 순서를 물려받는다.
  - 해시 무작위화는 충돌 공격을 막는 방어다([algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md)). `PYTHONHASHSEED=0`으로 고정하면 재현은 되지만 방어를 끈다.
- 분석 코드의 대처는 해시 시드 고정이 아니라 **순서에 기대지 않는 것**이다. 동률은 명시적 규칙(정렬 후 첫째, 키 순)으로 깬다. SQL의 `ORDER BY` 없는 결과 순서도 같은 문제다.

### 4. 환경 — 버전과 기본값

```text
  같은 12개 값의 "p90"
   Python 3.12 statistics.quantiles(n=10) 기본 method='exclusive'   → 65.0
   statistics.quantiles(method='inclusive')                         → 28.6
   PostgreSQL 17 percentile_cont(0.9)                               → 28.600000000000005
   PostgreSQL 17 percentile_disc(0.9)                               → 30
```

- 함수 이름이 같아도 정의·기본값이 다르다. Python 3.12 문서는 `quantiles`의 기본 방법이 `exclusive`이고, 표본에서 더 극단값이 나올 수 있는 데이터에 쓰며, `inclusive`는 모집단 데이터나 최소·최대를 포함하는 표본에 쓴다고 적는다.
- 그래서 "p90 = 65"는 함수·방법·버전과 함께 적어야 재현된다. 의존성과 버전을 명시한다(Wilson 외 2017 "Make dependencies and requirements explicit").
- 이 실험의 스크립트들은 호스트 Python 3.12.3과 컨테이너 Python 3.12.14에서 같은 출력을 냈다(시드 7 부트스트랩, `PYTHONHASHSEED=0` 순회 순서, 분위수). 같은 마이너 버전 안에서 확인한 것이다. 다른 마이너 버전에서도 같다고 이 실험이 보이지는 않는다.

### 5. 데이터와 단계 — 원본 보존, 모든 단계를 스크립트로

```text
  data/raw/      ← 받은 그대로. 덮어쓰지 않는다 (읽기 전용)
  src/clean.py   ← 원본 → 정제본. 손으로 고치지 않고 코드로
  results/       ← 정제·분석 중 생긴 산출물 (원본 + 코드로 다시 만들 수 있다)
  runall         ← 처음부터 끝까지 한 번에
```

- Wilson 외 2017 "Good enough practices in scientific computing"의 요점(Box 1에서 고름)
  - 원본 데이터를 저장한다(1a). 정제본으로 원본을 덮어쓰고 싶은 유혹이 있지만, 처음부터 다시 돌리려면 원본 보존이 필수다.
  - 데이터 처리의 모든 단계를 기록한다(1e). 가장 좋은 방법은 모든 단계를 스크립트로 쓰는 것이다.
  - 의존성과 요구사항을 명시한다(2g).
  - 코드 일부를 주석 처리했다 풀었다 하며 동작을 바꾸지 않는다(2h). 대신 조건문으로 제어한다.
  - 원본 데이터·메타데이터는 `data`, 정리·분석 중 생긴 파일은 `results` 디렉터리에 둔다(4c).
  - 버전 관리 시스템을 쓴다(5h). 원본 데이터는 바뀌지 않으므로 버전 추적이 필요 없고, 원본과 코드로 다시 만들 수 있는 중간 결과도 꼭 넣을 필요는 없다고 적는다. 단, 데이터·결과가 작으면 협업자의 접근과 버전 비교를 위해 넣기를 권한다.
- 논문은 Make 같은 빌드 도구를 "일부러 뺀 것"으로 분류한다. 입문자는 전부 다시 돌리는 셸 스크립트로도 같은 효과를 얻을 수 있다고 적는다.

### 6. 파이프라인 DAG — 바뀐 것과 그 하류만 다시

```text
  raw ──▶ clean ──▶ features ──┐
                               ├──▶ report
  dims ────────────────────────┘

  단계의 키 = hash(단계 이름, 단계 입력·코드 버전, 상류 단계들의 키)
  키가 바뀐 단계만 다시 실행 → 상류가 바뀌면 키가 연쇄로 바뀌어 하류도 다시
```

- 분석을 단계(노드)와 의존(간선)의 DAG로 쓰면, 위상 정렬이 **그래프에 적힌** 의존의 실행 순서를 보장한다. 의존을 빠짐없이 적고 단계들이 공유 가변 상태(전역 변수·같은 파일 덮어쓰기)에 기대지 않을 때 숨은 순서 의존이 사라진다. 의존이 없는 단계끼리의 순서는 정해지지 않는다. 노트북의 "셀 순서"가 코드로 명시된 의존이 된다.
- 단계마다 입력 해시를 키로 두면 바뀐 것과 그 하류만 다시 돌린다. 빌드 시스템과 같은 원리다([engineering-practice/07](../../engineering-practice/07-build-systems-and-reproducibility/2-summary.md)).
- 각 단계는 같은 입력이면 같은 출력을 내고(결정적), 다시 돌려도 결과가 겹치지 않아야(멱등) 캐시·재실행이 안전하다([data-engineering/08](../../data-engineering/08-idempotent-pipelines-and-backfill/2-summary.md)).

### 실험: 다섯 가지 재현성 함정을 직접 본다

(실험, `boot.py`·`hashorder.py`·`notebook.py`·`pipeline.py`·`defaults.py`, 호스트 Python 3.12.3 표준 라이브러리. A·B·E는 `python:3.12-slim`(Python 3.12.14) 일회용 컨테이너(`--network none`)에서도 돌려 같은 출력을 확인. 합성 데이터.)

```python
# A: 부트스트랩 95% 구간 (재표집 2000회)
rng = random.Random(None if arg == "none" else int(arg))
means = sorted(st.fmean(rng.choices(data, k=len(data))) for _ in range(2000))
# B: 동률을 순회 순서로 깸 vs 정렬 후
top = max(set(segments), key=lambda s: counts[s])
top_stable = max(sorted(set(segments)), key=lambda s: counts[s])
# D: graphlib 위상 정렬 + 입력 해시 캐시
key = h(step, inputs.get(step, ""), *[out[d] for d in sorted(DAG[step])])
```

```text
== A
seed=none  95% 부트스트랩 구간 [12.17, 32.42]
seed=none  95% 부트스트랩 구간 [12.17, 32.17]
seed=none  95% 부트스트랩 구간 [12.17, 31.92]
seed=   7  95% 부트스트랩 구간 [12.08, 31.92]
seed=   7  95% 부트스트랩 구간 [12.08, 31.92]
== B
set 순서: ['ios', 'partner', 'android', 'kiosk', 'web'] -> 최다 세그먼트: ios
set 순서: ['kiosk', 'android', 'partner', 'ios', 'web'] -> 최다 세그먼트: android
set 순서: ['partner', 'android', 'kiosk', 'web', 'ios'] -> 최다 세그먼트: android
PYTHONHASHSEED=0  set 순서: ['partner', 'android', 'web', 'kiosk', 'ios'] -> 최다 세그먼트: android
PYTHONHASHSEED=0  set 순서: ['partner', 'android', 'web', 'kiosk', 'ios'] -> 최다 세그먼트: android
PYTHONHASHSEED=1  set 순서: ['web', 'ios', 'partner', 'kiosk', 'android'] -> 최다 세그먼트: web
PYTHONHASHSEED=2  set 순서: ['kiosk', 'web', 'partner', 'android', 'ios'] -> 최다 세그먼트: web
(정렬 후 고르기는 모든 줄에서 android)
== C
위에서 아래로 c1 c2 c3 c4          : 127.5
c3 추가 전에 c4를 돌려 둔 결과(저장됨): 152.5
c3를 150으로 고쳐 돌렸다가 200으로 되돌림: 115.0
== D
실행 순서: ['raw', 'dims', 'clean', 'features', 'report']
1회차 실행: ['raw', 'dims', 'clean', 'features', 'report']
2회차(변경 없음) 실행: []
dims만 변경: ['dims', 'report']
raw 변경: ['raw', 'clean', 'features', 'report']
== E
p90 exclusive(기본): 65.0  inclusive: 28.6
median: 13.5  median_low: 13  median_high: 14
```

관찰과 해석:
- A: 시드 없는 세 번의 실행에서 위쪽 끝이 32.42·32.17·31.92로 달랐다. 실행할 때마다 다른 값이 나오므로 이 세 숫자 자체도 다시 돌리면 바뀐다. 시드 7은 두 번 모두 [12.08, 31.92]였다. 표본 12개 중 80 하나가 위쪽 끝을 크게 흔든다.
- B: 해시 시드를 정하지 않은 세 프로세스에서 "최다 세그먼트"가 ios·android·android로 갈렸다. `PYTHONHASHSEED=0`은 두 번 같았고, 1·2는 web을 골랐다. 정렬 후 고르기는 해시 시드와 무관하게 android였다.
- C: 같은 네 셀에서 실행 순서에 따라 127.5·152.5·115.0이 나왔다. 115.0은 지금 코드(상한 200)로는 나올 수 없는 값이다. 상한 150을 한 번 적용한 상태가 남았다.
- D: 변경이 없으면 아무것도 다시 돌지 않았다. `dims`만 바뀌면 `dims`와 `report`만, `raw`가 바뀌면 `dims`를 뺀 네 단계가 다시 돌았다.
- E: 같은 데이터의 p90이 함수 기본값에 따라 65.0(exclusive)과 28.6(inclusive)으로 두 배 넘게 달랐다. 같은 데이터에 PostgreSQL 17 `percentile_cont(0.9)`는 28.600000000000005, `percentile_disc(0.9)`는 30이었다(17번 실험 컨테이너에서 확인).

## 쓰이는 자료구조·알고리즘

- **파이프라인 DAG + 위상 정렬** — 단계 의존을 그래프로 두고 위상 정렬 순서로 실행. Python 3.9+ 표준 라이브러리 `graphlib.TopologicalSorter`(실험 D), 원리는 [data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md)·[algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md). 순환이 있으면 정렬이 실패한다(순환 의존 검출).
- **내용 해시 키(content addressing)** — 단계 입력·코드·상류 키를 해시해 캐시 키로 쓴다. 상류가 바뀌면 하류 키가 연쇄로 바뀌는 구조는 머클 트리와 같은 생각이다([data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md)).
- **결정적 의사난수** — 시드로 초기화한 PRNG([math/12](../../math/12-randomness-and-prng/2-summary.md)).
- **계보(lineage)** — 어떤 결과가 어떤 입력·실행에서 나왔는지의 그래프([data-engineering/11-data-lineage](../../data-engineering/11-data-lineage/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 순서

1. **증상**: 다시 돌리면 숫자가 다르다, 사람마다 다르다, 다시 만들 수 없다.
2. **출처를 가른다**: 같은 프로세스에서 두 번 돌려도 다른가(무작위·시드) / 프로세스마다 다른가(해시 순서) / 환경마다 다른가(버전·기본값) / 처음부터 돌리면 다른가(숨은 상태·수작업).
3. **원리로 고친다**: 시드를 명시, 순서에 기대지 않기, 버전·방법 명시, 원본 보존 + 전 단계 스크립트화.
4. **확인한다**: 깨끗한 환경에서 처음부터 끝까지 한 번에 돌려 같은 결과가 나오는지 본다.

### 2. 노트북을 재현 가능하게 쓰는 규칙

```text
  [ ] 커널 재시작 후 "모두 실행"으로 끝까지 도는가? 보고서에 붙일 출력은 이 실행의 것만
  [ ] 무작위를 쓰는 모든 곳에 시드 (random.Random(seed) 인스턴스를 넘긴다 — 전역 random.seed 대신)
  [ ] set 순서(set에서 만든 dict 순서 포함)·동률에 기대는 곳이 없는가 (sorted, 명시적 tie-break)
  [ ] 분위수·검정 함수의 방법(method) 인자를 기본값에 맡기지 않고 적었나
  [ ] 원본 파일을 읽기 전용으로 두었나, 정제 단계가 코드인가
  [ ] 의존성 버전 고정 파일(requirements 등)과 Python 버전을 기록했나
  [ ] 안정된 단계는 노트북에서 스크립트·함수로 옮겼나 (노트북은 탐색과 설명에)
```

### 3. 실행 기록을 결과에 붙인다 (Python)

```python
import sys, platform, hashlib, json, datetime

def run_manifest(seed, inputs):
    """결과 파일 옆에 남길 실행 기록 — 무엇으로 이 숫자를 만들었나."""
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "seed": seed,
        "inputs": {p: hashlib.sha256(open(p, "rb").read()).hexdigest() for p in inputs},
        "quantile_method": "exclusive",                       # 기본값도 명시
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
# json.dump(run_manifest(7, ["data/raw/orders.csv"]), open("results/manifest.json", "w"), indent=2)
```

## 장애 시나리오와 대처

### 1. 셀 실행 순서 의존 → 재실행 시 다른 결과 (⚠ 커리큘럼)

- **현상**: 지난달 보고서의 평균(152.5)을 다시 만들려고 노트북을 위에서부터 돌렸더니 127.5가 나온다.
- **보이는 형태**: 노트북의 실행 번호가 뒤죽박죽이다. 저장된 출력과 재실행 출력이 다르다(실험 C).
- **원인**: 보고서 출력은 나중에 추가한 셀(상한 처리) 이전 상태에서 나왔다. 셀들이 전역 상태를 공유한다.
- **대처**: 보고서 수치는 커널 재시작 후 전체 실행의 결과만 쓴다. 안정된 단계는 스크립트·파이프라인으로 옮긴다. 정제 규칙의 변경(상한 추가)은 변경 기록에 남긴다.

### 2. 시드 없는 재표집 → 리포트마다 구간이 다르다

- **현상**: 리뷰어가 같은 데이터로 부트스트랩 구간을 다시 냈는데 끝자리가 다르다. 어느 쪽이 맞는지 논쟁한다.
- **보이는 형태**: 실험 A — 위쪽 끝 32.42·32.17·31.92.
- **원인**: 시드 없이 재표집했다. 둘 다 "맞는" 추정이지만 같은 값을 재현할 수 없다.
- **대처**: 시드를 정하고 보고서에 적는다. 끝자리가 크게 흔들리면 재표집 횟수를 늘린다.

### 3. 동률을 순회 순서로 깸 → 새로 고칠 때마다 1등이 바뀐다

- **현상**: "최다 유입 채널"이 대시보드를 새로 고칠 때마다 ios·android·web으로 바뀐다.
- **보이는 형태**: 동률(40·40·40)인 범주들 사이에서만 바뀐다(실험 B).
- **원인**: `set`의 순회 순서(해시 무작위화 — set에서 만든 `dict`도 물려받음) 또는 `ORDER BY` 없는 SQL 결과 순서에 기대 동률을 깼다.
- **대처**: 동률 규칙을 명시한다(정렬 후 첫째, 또는 동률을 그대로 보고). SQL에는 고유 키까지 포함한 `ORDER BY`. 해시 시드 고정은 증상만 가린다.

### 4. 원본을 정제본으로 덮어씀 → 처음부터 다시 만들 수 없다

- **현상**: 정제 규칙의 버그를 찾았는데 원본이 없어 다시 정제할 수 없다.
- **보이는 형태**: `data/orders.csv` 하나뿐이고, 언제 무엇이 바뀌었는지 기록이 없다.
- **원인**: 원본 보존(Wilson 1a)과 단계 기록(1e)을 하지 않았다.
- **대처**: 원본은 읽기 전용 위치에 받은 그대로 둔다. 정제는 코드로만. 원본이 너무 크면 원본을 얻는 절차·버전·날짜를 기록한다(Wilson 1a의 예외).

### 5. 함수 기본값·버전 차이 → 같은 지표가 다른 값

- **현상**: 노트북의 p90(65.0)과 DB 대시보드의 p90(28.6)이 두 배 넘게 다르다.
- **보이는 형태**: 데이터는 같은데 도구마다 값이 다르다(실험 E). 표본이 작을수록 차이가 크다.
- **원인**: Python `quantiles`의 기본 `exclusive`와 PostgreSQL `percentile_cont`(inclusive와 같은 값)의 정의가 다르다.
- **대처**: 방법 인자를 명시하고, 비교하는 수치는 같은 정의로 계산한다. 버전과 방법을 실행 기록에 남긴다.

## 핵심 문장

- 분석 결과는 데이터·코드·환경·실행 순서의 함수다. 하나라도 기록되지 않으면 다시 만들 수 없다.
- 노트북의 셀들은 전역 상태를 공유한다. 보고서 수치는 커널을 재시작한 뒤 처음부터 끝까지 실행한 결과만 쓴다.
- 시드는 결과의 일부다. 무작위를 쓰는 모든 곳에 시드를 두고 보고서에 적는다.
- set 순회 순서와 `ORDER BY` 없는 결과 순서에 기대지 않는다. 동률은 명시적 규칙으로 깬다.
- 원본은 덮어쓰지 않고, 모든 단계를 스크립트로 쓰고, 단계를 DAG로 엮으면 바뀐 것과 그 하류만 다시 돌릴 수 있다.

## 관련 주제·근거

- 선행
  - [18-data-cleaning-and-quality](../18-data-cleaning-and-quality/2-summary.md) — 정제 단계(원본 → 정제본)
- 후속·연결
  - [engineering-practice/07-build-systems-and-reproducibility](../../engineering-practice/07-build-systems-and-reproducibility/2-summary.md) — 입력 해시 DAG·증분 빌드·재현 가능 빌드
  - [engineering-practice/03-version-control-and-git-internals](../../engineering-practice/03-version-control-and-git-internals/2-summary.md) — 버전 관리
  - [data-engineering/08-idempotent-pipelines-and-backfill](../../data-engineering/08-idempotent-pipelines-and-backfill/2-summary.md) — 결정적·멱등 단계
  - [data-engineering/11-data-lineage](../../data-engineering/11-data-lineage/2-summary.md) — 결과의 계보
  - [math/12-randomness-and-prng](../../math/12-randomness-and-prng/2-summary.md) — 시드와 PRNG
  - [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md) — 해시 무작위화(PYTHONHASHSEED)의 이유
  - [17-sql-for-analysis](../17-sql-for-analysis/2-summary.md) — `percentile_cont`/`disc`, 쿼리를 스크립트로
  - [data-analysis 07](../07-sampling-distributions-and-clt/2-summary.md) 부트스트랩
- 근거
  - Wilson, G., Bryan, J., Cranston, K., Kitzes, J., Nederbragt, L., Teal, T.K. (2017) "Good enough practices in scientific computing", PLoS Comput Biol 13(6), 2017-06-22 <https://doi.org/10.1371/journal.pcbi.1005510> — Box 1 요약, 1a 원본 저장, 1e 모든 단계 기록, 2g 의존성 명시, 2h 주석 토글 금지, 4c data·results 디렉터리, 5h 버전 관리, "What we left out"의 빌드 도구(2026-10-08 열람)
  - Pimentel, J.F., Murta, L., Braganholo, V., Freire, J. (2019) "A Large-scale Study about Quality and Reproducibility of Jupyter Notebooks", MSR 2019, pp. 507–517, DOI 10.1109/MSR.2019.00077 — 저자 사본 PDF <http://www.ic.uff.br/~leomurta/papers/pimentel2019a.pdf>: 1,159,166개 고유 노트북·264,023개 저장소, 실행 시도 863,878개 중 24.11% 오류 없이 종료·4.03% 같은 결과, 실행 순서가 모호하지 않은 노트북(912,343개) 중 36.36% 순서 뒤바뀐 셀. 게재 학회는 Crossref 서지로 확인 <https://doi.org/10.1109/MSR.2019.00077>
  - Python 3.12 문서 — `random` "Notes on Reproducibility"·`random.seed`(None이면 운영체제 난수원, 없으면 시스템 시간) <https://docs.python.org/3.12/library/random.html>, 내장형 `dict`(삽입 순서 보존) <https://docs.python.org/3.12/library/stdtypes.html>, 명령행 `-R`·`PYTHONHASHSEED`(해시 무작위화 기본 켜짐) <https://docs.python.org/3.12/using/cmdline.html>, `statistics.quantiles`의 `exclusive`(기본)·`inclusive` <https://docs.python.org/3.12/library/statistics.html>, `graphlib.TopologicalSorter` <https://docs.python.org/3.12/library/graphlib.html>
  - PostgreSQL 17 문서 9.21 표 9.62 `percentile_cont`·`percentile_disc`
- 실험 목록
  - A `boot.py` — 시드 없음 ×3 vs 시드 7 ×2 부트스트랩 구간. B `hashorder.py` — 해시 시드 미설정 ×3, `PYTHONHASHSEED` 0·0·1·2에서 동률 tie-break. C `notebook.py` — 같은 네 셀의 실행 순서 세 가지. D `pipeline.py` — `graphlib` 위상 정렬 + 입력 해시 캐시의 선택적 재실행. E `defaults.py` — `quantiles` exclusive vs inclusive, `median` 세 가지.
  - 환경: 호스트 Python 3.12.3. A(시드 7)·B(`PYTHONHASHSEED=0`)·E를 `python:3.12-slim`(Python 3.12.14) 일회용 컨테이너(`--network none`, `-u` 사용자)에서 다시 돌려 같은 출력 확인. E와 같은 데이터의 `percentile_cont`/`disc`는 `postgres:17`(17.11) 컨테이너에서 확인.
