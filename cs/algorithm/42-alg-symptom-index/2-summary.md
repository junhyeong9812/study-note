# algorithm/42-alg-symptom-index — 증상 사전: 데이터 늘자 타임아웃·정렬 계약 예외·재귀 스택 오버플로·정규식 CPU 100%·이진 탐색 무한 루프 → 원인·첫 진단·leaf — 정리 (힌트)

## 해결하는 문제

이 영역의 다른 노트는 **알고리즘에서 증상으로** 간다.\
"고정 피벗 퀵 정렬에 정렬된 입력이 오면 분할이 한쪽으로 쏠린다 → O(n²)·재귀 깊이 n"처럼 쓴다.\
현장에서는 반대 방향이 필요하다.\
손에 든 것은 증상 한 줄이다. "어제까지 1초였던 배치가 오늘 타임아웃", "`Comparison method violates its general contract!`", "`StackOverflowError`", "요청 하나가 CPU를 다 먹는다", "이 요청만 영원히 안 끝난다".

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                                 이 노트 (역방향)
  알고리즘·전제 --> 깨지는 입력 --> 보이는 증상          증상 --> 어떤 모양으로 --> 흔한 원인 --> 첫 진단 --> leaf
  "비교자가 추이성을 어기면 TimSort가 예외"            "IllegalArgumentException ... TimSort.mergeHi. 먼저 비교자 코드와 n >= 32인지"
```

쉬운 예: 내비게이션이 "평소 20분"이라던 길이 오늘 2시간 걸린다.\
원인은 길이 막혔거나(입력이 커짐), 길을 잘못 들었거나(알고리즘이 가정 밖 입력을 만남), 같은 골목을 맴도는 것(종료 조건 결함)이다.\
"늦었다"는 증상 하나에 세 원인이 있고, 처방이 다르다.

똑같은 구조다.\
"요청이 타임아웃 난다"는 같은 증상에 원인이 여럿이다.
- n이 두 배일 때 시간이 네 배면 O(n²) 알고리즘을 의심한다(측정은 가설의 근거이고, 확인은 코드의 연산 수로 한다 — [asymptotic-analysis 1](../02-asymptotic-analysis/2-summary.md)). 확인되면 알고리즘을 바꾼다.
- 특정 입력(이미 정렬된 파일, 같은 값만 든 배열, 공백 2만 개짜리 글)에서만 느리면 최악 입력이다([quick-sort 1·2](../03-quick-sort/2-summary.md), [43-alg-incidents](../43-alg-incidents/2-summary.md)). 무작위화하거나 최악이 보장된 알고리즘으로 바꾼다.
- 그 요청만 영원히 안 끝나고 덤프가 같은 줄이면 종료 조건 결함이다([binary-search 2](../06-binary-search/2-summary.md)). 불변식을 고친다.

실무 예:
- 알고리즘 증상의 대부분은 **입력이 가정을 벗어날 때** 보인다. 크기(n), 모양(정렬됨·전부 같음·치우침), 값의 범위(int 경계), 계약(비교자 규칙)이 가정이다.
- 그래서 첫 질문은 "그때의 입력은 무엇이었나"다. 크기·모양·경계값을 손에 넣기 전에는 원인을 고르지 않는다.

  - *역색인*: "leaf → 증상" 목록을 "증상 → leaf" 목록으로 뒤집은 것([data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)).
  - *leaf 표기 `이름 k`*: 이 영역 노트의 「장애 시나리오와 대처」 k번째 시나리오다. 예: `binary-search 2` = [06-binary-search](../06-binary-search/2-summary.md)의 시나리오 2(요청 하나가 영원히 끝나지 않는다). 이 영역은 기존 폴더 번호와 커리큘럼 번호가 달라 번호가 겹치는 폴더가 있어(`03-quick-sort`와 `03-recursion`) 이름으로 적는다.
  - *첫 진단*: 고치기 전에 원인 후보를 가르는 가장 싼 확인 한 가지.

## 동작·원리

### 0. 증상은 알고리즘의 어느 가정이 깨진 것인가

```text
   증상                                   깨진 가정                         이 노트의 절
   ────                                   ────────                          ──────────
   데이터 늘자 타임아웃                     "n이 작다" / "입력이 평균적이다"      1절
   Comparison method violates ...          "비교자가 전순서다"                   2절
   StackOverflowError                     "재귀 깊이가 작다"(log n)             3절
   정규식 하나로 CPU 100%                  "매칭은 입력 길이에 선형이다"          4절
   이진 탐색이 안 끝남 / 음수 인덱스        "구간이 매번 준다" / "int가 안 넘친다"   5절
   예외 없이 틀린 답, 메모리 폭발 등         그 밖의 전제                         6절
```

- 커리큘럼의 다섯 증상이 1~5절이다. 6절은 leaf 시나리오의 나머지 증상이다.
- 자료구조 쪽 원인(해시 충돌, 무한 큐, resize 스파이크, `ConcurrentModificationException`)은 [data-structure/43-ds-symptom-index](../../data-structure/43-ds-symptom-index/2-summary.md)가 정본이다. 두 색인은 `StackOverflowError`와 CPU 100%에서 겹친다.

### 0-1. 색인을 쓰기 전에 확보할 것

```text
  ① 원문     예외 전체 + 스택 트레이스(StackOverflowError는 1024줄에서 잘린다 — ds 43 0-1 실험), JDK 판
  ② 입력     그때의 n, 입력의 모양(정렬됨? 같은 값? 최대 길이?), 경계값(int 최대 근처?)
  ③ 비율     크기를 두 배씩 키웠을 때 시간이 몇 배인가 (1절 실험)
  ④ 덤프     2~3장: 같은 줄이면 "안 끝남", 진행하면 "느림"
```

### 1. 데이터가 늘자 타임아웃 — 복잡도

먼저 **크기를 두 배로 했을 때 시간이 몇 배인가**를 잰다. 같은 n에서 특정 입력만 느리면 최악 입력이다.

```text
  데이터가 늘자 타임아웃
     │
     ├─ n 두 배 → 시간 약 4배, 무작위 입력에서도 ─────────────────────────▶ O(n²) 알고리즘           asymptotic-analysis 1 · algorithm-basics 1 · elementary-sort 1
     ├─ n 하나 늘 때 몇 배씩 (n=8 → 9 에 약 9배) ───────────────────────▶ 지수·팩토리얼 탐색        backtracking 3 · recursion 4 · complexity-p-np 1
     ├─ 같은 n, 특정 입력만 (정렬된 파일·같은 값만) ─────────────────────▶ 최악 입력                 quick-sort 1·2 · randomized-algorithms 2
     ├─ 같은 n, 반복 문자 많은 텍스트만 ───────────────────────────────▶ 나이브 문자열 검색 최악    string-matching 1
     ├─ 공격자가 고른 입력에서만 ──────────────────────────────────────▶ 적대적 입력                quick-sort 3 · randomized-algorithms 1 · hash-functions 1
     ├─ 평균은 정상, 가끔 한 번 수백 ms ────────────────────────────────▶ 분할 상환의 그 한 번        asymptotic-analysis 2
     ├─ 데이터가 메모리를 넘자 급격히 느려짐 ────────────────────────────▶ 디스크 스필·패스 수         external-sort-and-k-way-merge 1·3
     └─ 판정 함수 하나가 비싸서 이분 탐색 30번도 못 돔 ─────────────────────▶ 판정 비용 × log 범위      parametric-search 3
```

| 보이는 것 (메시지·수치·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 게이트웨이 504, 배치 시간이 데이터 두 배에 네 배, 덤프에 같은 이중 루프 프레임 | 이중 루프 대조, 루프 안 `List.contains` | 크기 두 배 → 시간 비율(아래 실험) | [asymptotic-analysis 1](../02-asymptotic-analysis/2-summary.md) · [algorithm-basics 1](../01-algorithm-basics/2-summary.md) · [elementary-sort 1](../01-elementary-sort/2-summary.md) |
| 거품 정렬 n=1,000에서 97~121 ms → n=100,000이면 추정 16~20분(실행 안 한 추정, OpenJDK 21) | O(n²)을 작은 n에서만 검증 | 운영 최대 n으로 성능 테스트 | [algorithm-basics 1](../01-algorithm-basics/2-summary.md) |
| 정렬된 입력에서만 비교 수 n(n-1)/2(16,000개 → 127,992,000), 또는 `StackOverflowError` | 고정 피벗 | 입력이 이미 정렬돼 있나 | [randomized-algorithms 2](../39-randomized-algorithms/2-summary.md) · [quick-sort 1](../03-quick-sort/2-summary.md) |
| 같은 값만 든 배열에서 CPU 100%, 덤프가 분할 루프 | 호어 분할이 등호에서 안 멈춤 | 입력의 서로 다른 값 수 | [quick-sort 2](../03-quick-sort/2-summary.md) |
| n이 30 → 40일 때 호출 수 2,692,537 → 331,160,281(약 123배) | 중복 부분문제(메모 없음) | 플레임 그래프에 같은 재귀가 탑처럼 쌓이나 | [recursion 4](../03-recursion/2-summary.md) |
| 놓기 수 n=8 109,600 → n=9 986,409(약 9배) | 가지치기 없는 순열 전수 탐색(n! — 배율이 n+1로 커진다) | n을 하나씩 늘려 배율 | [backtracking 3](../13-backtracking/2-summary.md) |
| 반복 문자 많은 로그에서 비교 999,900 vs KMP 29,899 | 나이브 검색의 n×m 최악 | 입력을 남이 고르나 | [string-matching 1](../25-string-matching/2-summary.md) |
| 정렬 메모리 초과 → 쿼리가 급격히 느려짐 | 외부 정렬로 전환, 팬인이 작아 패스가 많음 | 실행 계획의 스필·패스 수 | [external-sort-and-k-way-merge 1·3](../11-external-sort-and-k-way-merge/2-summary.md) |

- 처방의 방향: O(n²) → 해시·정렬 기반 O(n)·O(n log n). 최악 입력 → 무작위화(무작위 피벗) 또는 최악 보장 알고리즘(표준 `Arrays.sort`·`List.sort`). 지수 → 가지치기·DP·근사([complexity-p-np 1·2](../40-complexity-p-np/2-summary.md)).

#### 실험: 크기 두 배 → 시간 몇 배 (`Doubling.java`)

같은 일(정수 배열의 서로 다른 값 세기)을 세 방법으로 하고, n을 1만에서 8만까지 두 배씩 늘렸다. 각 n에서 5번 재고 최솟값을 썼다. 측정 전 크기 2만으로 세 방법을 세 번씩 돌려 JIT를 데웠다.

```java
static int dedupNested(int[] a) {   // O(n²): 앞의 원소 전부와 비교
    int c = 0;
    outer: for (int i = 0; i < a.length; i++) { for (int j = 0; j < i; j++) if (a[j] == a[i]) continue outer; c++; }
    return c;
}
static int dedupHash(int[] a) { Set<Integer> s = new HashSet<>(); for (int x : a) s.add(x); return s.size(); }   // 기대 O(n)
static int dedupSort(int[] a) {     // O(n log n): 정렬 후 이웃 비교
    int[] b = a.clone(); Arrays.sort(b);
    int c = b.length == 0 ? 0 : 1; for (int i = 1; i < b.length; i++) if (b[i] != b[i-1]) c++;
    return c;
}
```

(실험, eclipse-temurin:21-jdk = OpenJDK 21.0.12, docker `--network none --cpus=2`, 2026-10-05 — 두 번 실행. 시간은 실행마다 다르다)

```text
이중 루프    | n=10,000     28.68 ms | n=20,000    109.77 ms (x3.8) | n=40,000    464.33 ms (x4.2) | n=80,000  1,856.15 ms (x4.0)
HashSet  | n=10,000      1.87 ms | n=20,000      3.59 ms (x1.9) | n=40,000      7.35 ms (x2.0) | n=80,000     13.38 ms (x1.8)
정렬 후 비교  | n=10,000      2.46 ms | n=20,000      4.53 ms (x1.8) | n=40,000     11.36 ms (x2.5) | n=80,000     19.42 ms (x1.7)
이중 루프    | n=10,000     32.62 ms | n=20,000     88.97 ms (x2.7) | n=40,000    449.15 ms (x5.0) | n=80,000  1,826.84 ms (x4.1)
HashSet  | n=10,000      1.61 ms | n=20,000      3.54 ms (x2.2) | n=40,000      6.29 ms (x1.8) | n=80,000     11.93 ms (x1.9)
정렬 후 비교  | n=10,000      1.95 ms | n=20,000      4.75 ms (x2.4) | n=40,000      8.09 ms (x1.7) | n=80,000     15.98 ms (x2.0)
```

사실 점검 재실행(같은 코드·같은 명령, 한 번): 두 배마다 이중 루프 x4.2·x4.0·x4.1, `HashSet` x2.1·x1.9·x1.9, 정렬 후 비교 x2.1·x1.8·x2.1.

- 관찰
  - 이중 루프는 두 배마다 2.7~5.0배, 큰 n(4만 → 8만)에서는 두 번 다 4.0~4.1배였다. O(n²)의 "두 배에 네 배"가 보인다.
  - `HashSet`과 정렬은 두 배마다 1.7~2.5배였다. 이 크기·이 측정으로는 O(n)과 O(n log n)을 가를 수 없었다. log n의 차이(log 2만 대 log 4만)는 1.07배 정도라 측정 잡음에 묻힌다(해석).
  - 작은 n의 비율(2.7배, 5.0배)이 흔들렸다. 진단에는 큰 n 쪽 비율을 쓰고, 여러 번 잰다.
- 진단 함의: 두 배 실험은 **제곱 이상과 그 아래**를 가르는 싼 첫 진단이다. 측정한 범위 안의 비율이라 점근 복잡도를 확정하지는 않는다 — 확정은 코드의 연산 수 분석으로 한다. n log n과 n을 가르려면 크기 범위를 훨씬 넓혀야 한다. 정밀 측정은 JMH([reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md)).

### 2. 정렬 계약 예외 — `Comparison method violates its general contract!`

먼저 **비교자 코드**를 본다. 예외는 위반을 우연히 만났을 때만 난다. 예외가 안 난 실행도 틀렸을 수 있다.

```text
  정렬 결과가 이상함 / 계약 예외
     │
     ├─ IllegalArgumentException: Comparison method violates its general contract! ─▶ 비교자가 대칭·추이 위반   sorting-in-practice 1 · elementary-sort 3
     ├─ 예외 없음, 아주 큰 값과 작은 값의 순서가 뒤집힘 ──────────────────────────────▶ 뺄셈 비교자 오버플로      sorting-in-practice 2
     ├─ 페이지 간 중복·누락, 다시 돌리면 결과가 다름 ────────────────────────────────▶ 동점 해소 키 없음          sorting-in-practice 3 · elementary-sort 2
     ├─ TreeSet/TreeMap에 넣은 원소가 사라짐 ───────────────────────────────────▶ compare == 0 이면 같은 원소  sorting-in-practice 4
     └─ 이진 탐색이 있는 값을 "없다" ───────────────────────────────────────────▶ 정렬·탐색 비교자가 다름     binary-search 3 · algorithm-basics 4
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| `java.lang.IllegalArgumentException: Comparison method violates its general contract!`, 트레이스에 `java.util.TimSort.mergeHi`/`mergeLo` | 같으면 1 반환, `a - b` 오버플로, `NaN`, 정렬 중 바뀌는 키, 일관되지 않은 다중 필드 | 비교자 코드, 입력 n이 32 이상인가 | [sorting-in-practice 1](../09-sorting-in-practice/2-summary.md) |
| 같은 위반 비교자: n=31에서 200회 중 예외 0회, n=32에서 4회(OpenJDK 21) | `MIN_MERGE = 32` 미만은 병합 없이 이진 삽입 정렬 | 단위 테스트의 n이 31 이하였나 | [sorting-in-practice 1](../09-sorting-in-practice/2-summary.md) |
| `subtract` 비교자 n=2000: 20회 중 예외 3회, 예외 없이 틀린 순서 17회 | 위반을 만날 때만 예외 | 정렬 결과를 `Integer.compare`로 재검사 | [sorting-in-practice 2](../09-sorting-in-practice/2-summary.md) |
| 이름순 `TreeSet`에 3명 넣었는데 2명(`name만: 2 [...]`) | 비교자가 `equals`와 일관되지 않음 | 비교자에 유일 키가 있나 | [sorting-in-practice 4](../09-sorting-in-practice/2-summary.md) |
| 무한 스크롤에서 중복·누락(시뮬레이션 10페이지에 중복 55·누락 55) | 동점 많은 키에 유일 키 없음 | `ORDER BY` 마지막에 유일 키가 있나 | [sorting-in-practice 3](../09-sorting-in-practice/2-summary.md) |

- `-Djava.util.Arrays.useLegacyMergeSort=true`로 예외를 덮지 않는다. 실험에서 이 옵션은 예외를 0회로 만들었지만 비교자 위반은 그대로다. 기본 TimSort에서도 예외가 안 난 17회(20회 중)가 모두 틀린 순서였다 — 예외가 없다는 것은 순서가 맞다는 뜻이 아니다([sorting-in-practice 1](../09-sorting-in-practice/2-summary.md)).
- 처방: `Integer.compare`·`Comparator.comparing(...).thenComparing(...)`, 정렬 전 키 스냅숏, 테스트는 32개 이상·동점 많은 무작위 데이터로.

### 3. 재귀 스택 오버플로 — `StackOverflowError`

먼저 **깊이가 무엇에 비례하나**를 본다.

```text
  StackOverflowError
     │
     ├─ 특정 입력이면 크기와 무관하게 (음수, mid == hi) ──────────────────▶ 기저 누락·축소 실패         recursion 1
     ├─ 큰 데이터에서만, 깊이 ∝ n (긴 리스트·직선 그래프·치우친 트리) ──────▶ 깊이 = n                  recursion 2 · dfs 1 · scc 3 · euler-path 4
     ├─ 정렬된 입력의 재귀 퀵 정렬 ───────────────────────────────────────▶ 고정 피벗, 깊이 = n         quick-sort 1 · randomized-algorithms 2
     ├─ 메모이제이션 재귀, n이 수만 ──────────────────────────────────────▶ 상태 사슬 깊이 = n          dp-basics 1
     ├─ 외부 입력의 중첩 [[[[…]]]] ───────────────────────────────────────▶ 재귀 하강 파서              recursion 3
     └─ 꼬리 재귀로 짰는데도 ─────────────────────────────────────────────▶ HotSpot·V8은 꼬리 호출 제거 안 함  recursion 5
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| `java.lang.StackOverflowError`, 같은 프레임 반복, `catch (Exception e)`를 통과 | 기저가 특정 입력을 놓침, 축소량 0 | 그 입력에서 매 호출 인자가 기저 쪽으로 줄어드나 | [recursion 1](../03-recursion/2-summary.md) |
| 1,000개는 되고 1,000,000개는 안 됨. 같은 `-Xss1m`에서도 깊이 한계 19,415~41,224(실행마다 다름, JIT 영향) | 깊이 ∝ n | 깊이가 log n인가 n인가 | [recursion 2](../03-recursion/2-summary.md) |
| 기본 설정에서 직선 5,000은 되고 10,000에서 실패 | 재귀 DFS, 깊이 = DFS 트리의 최대 깊이(최악 정점 수 V — 직선 그래프면 V) | 그래프가 긴 사슬 꼴인가, 정점 수가 얼마인가 | [dfs 1](../12-dfs/2-summary.md) · [scc 3](../18-scc/2-summary.md) · [euler-path 4](../16-euler-path/2-summary.md) |
| Jackson 2.15+면 `StreamConstraintsException`(문구는 판마다 다르다 — 2.15.0은 `Depth (1001) exceeds the maximum allowed nesting depth (1000)`, 2.16.0부터는 `Document nesting depth (1001) exceeds the maximum allowed (1000, …)`) | 공격자가 중첩 깊이를 정함 | 파서 깊이 상한이 켜져 있나 | [recursion 3](../03-recursion/2-summary.md) |
| Java `StackOverflowError`, Node.js `RangeError: Maximum call stack size exceeded` — 꼬리 재귀 코드 | 꼬리 호출 제거 없음(OpenJDK 21·Node 22 실험) | 언어·런타임이 꼬리 호출을 제거하나 | [recursion 5](../03-recursion/2-summary.md) |

- 처방: 깊이를 입력에서 떼어 놓는다 — 명시적 스택(힙에 쌓임), 작은 쪽만 재귀(퀵 정렬), 타뷸레이션(DP), 파서 깊이 상한. `-Xss`만 키우는 것은 경계를 미룰 뿐이다(1,000,000 깊이에 `-Xss64m`도 부족, [recursion 2](../03-recursion/2-summary.md)).
- 자료구조 쪽 갈래(균형 없는 트리, 재귀 `find`, rope)는 [data-structure/43-ds-symptom-index](../../data-structure/43-ds-symptom-index/2-summary.md) 3절.

### 4. 정규식 하나로 CPU 100% — 백트래킹

먼저 **어느 정규식이, 어떤 입력에서**인지 찾는다. 덤프 맨 위가 정규식 엔진 안이고, 그 요청의 입력이 길다.

```text
  요청 하나가 CPU를 다 씀, 덤프가 java.util.regex.Pattern 안
     │
     ├─ 중첩 수량자 (a+)+$ 꼴, 입력 한 글자마다 시간 두 배 ─────────────▶ 지수 백트래킹(ReDoS)        backtracking 1
     ├─ \s+$ 꼴, 매칭 실패하는 긴 공백 ───────────────────────────────▶ 시작 위치마다 끝까지 → O(n²)  43-alg-incidents (Stack Overflow 2016)
     ├─ .*.*=.* 꼴, = 없는 긴 입력 ───────────────────────────────────▶ 겹치는 .* → 다항(두 배에 약 8배)  43-alg-incidents (Cloudflare 2019)
     └─ 정규식이 아니라 직접 짠 문자열 검색 ─────────────────────────────▶ 나이브 검색 최악            string-matching 1
```

| 보이는 것 (메시지·수치·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 스레드 덤프 맨 위가 `java.util.regex.Pattern$…`, 입력 길이가 한 글자 늘 때 시간 두 배 | `(a+)+$` 같은 중첩 수량자 + 끝이 안 맞는 입력 | 패턴에 중첩·겹치는 수량자가 있나 | [backtracking 1](../13-backtracking/2-summary.md) |
| `\s+$`: 공백 2만 개 + 다른 문자 하나에 약 4초, 4만 개에 약 15초(OpenJDK 21.0.12, `--cpus=2`) | 실패한 시작 위치마다 공백 끝까지 다시 확인 | 입력의 최장 공백·반복 구간 길이 | [43-alg-incidents](../43-alg-incidents/2-summary.md) 사건 2 |
| `.*.*=.*`: 매칭 실패 입력 2,000자에 약 19초(OpenJDK 21.0.12, `--cpus=1`) | 겹치는 `.*` 셋이 분할 방법을 전부 시도 | 패턴에 `.*`가 둘 이상 이어지나 | [43-alg-incidents](../43-alg-incidents/2-summary.md) 사건 3 · [engineering-practice/20](../../engineering-practice/20-practice-incidents/2-summary.md) 실험 B |

- 처방: 입력 길이 상한, 정규식 대신 문자열 함수(Stack Overflow는 substring 함수로 교체), 패턴 재작성, 선형 시간 엔진(RE2 계열 — 역참조·전후방 탐색은 지원하지 않음), CI에서 적대적 입력에 시간 예산 검사([engineering-practice/20](../../engineering-practice/20-practice-incidents/2-summary.md) 실험 C).
- 테스트가 "매칭 결과"만 보면 이 결함은 통과한다. 위 입력은 모두 결과가 `false`(매칭 실패)로 정상이다. **시간**을 재야 보인다.

### 5. 이진 탐색이 안 끝난다 — 또는 음수 인덱스

먼저 **덤프가 같은 줄인가(안 끝남), 예외인가(음수 인덱스), 조용히 틀린가**를 가른다.

```text
  이진 탐색(또는 매개변수 탐색) 이상
     │
     ├─ 그 키만 응답 없음, 덤프가 같은 search 줄 ─────────────────────▶ 구간이 안 줄어듦(hi = mid 섞임)  binary-search 2
     ├─ 원소 약 10억(2^30) 넘는 배열에서만 음수 인덱스 예외 ──────────────▶ (lo + hi) / 2 오버플로       binary-search 1 · algorithm-basics 3
     ├─ 있는 값인데 "없음", 예외 없음 ───────────────────────────────▶ 정렬 전제 깨짐               binary-search 3 · algorithm-basics 4
     ├─ 매개변수 탐색이 반례에서만 다른 답 ───────────────────────────────▶ 판정이 단조가 아님           parametric-search 1·2
     └─ 이진 탐색이 아닌데 비슷하게 멈춤 ─────────────────────────────────▶ 펜윅 0 인덱스·부분집합 순회   data-structure fenwick-tree 1 · bit-manipulation 2
```

| 보이는 것 (메시지·수치·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| CPU 한 코어 100%, 덤프 여러 장이 같은 `search` 프레임·같은 줄 | 닫힌 판(`lo <= hi`)에 `hi = mid`, 또는 `lo = mid` — 구간 2칸에서 제자리 | 판(닫힌/반열린)과 갱신식이 한 판으로 맞나 | [binary-search 2](../06-binary-search/2-summary.md) |
| `ArrayIndexOutOfBoundsException: Index -1073741824 out of bounds for length 1073741825`(가상 배열 실험, OpenJDK 21.0.12) | `(low + high)`가 `int` 최대를 넘어 음수 | n이 2^30 근처 이상인가, 중간값 계산식 | [binary-search 1](../06-binary-search/2-summary.md) · [43-alg-incidents](../43-alg-incidents/2-summary.md) 사건 1 |
| `Arrays.binarySearch`가 음수(없음), 선형으로 훑으면 있음 | 정렬 안 됨, 정렬·탐색 비교자 다름 | 디버그 빌드에서 `isSorted` | [binary-search 3](../06-binary-search/2-summary.md) · [algorithm-basics 4](../01-algorithm-basics/2-summary.md) |
| 펜윅 `add` 한 번이 끝나지 않음(테스트 30초 제한) | 1-base 구조에 0 인덱스 — `0 & -0 == 0` | 진입점에서 `+1` 했나 | [data-structure/17-fenwick-tree](../../data-structure/17-fenwick-tree/2-summary.md) 장애 1 |
| `subsetsOf`가 끝나지 않음 | `(0 - 1) & mask == mask`로 되돌아감 | 빈 집합 뒤 `break`가 있나 | [bit-manipulation 2](../29-bit-manipulation/2-summary.md) |

- 처방: 판 하나로 고정하고 "mid가 아직 답 후보인가"로 `hi = mid` / `mid - 1`을 정한다. 중간값은 `lo + (hi - lo) / 2` 또는 `(lo + hi) >>> 1`. 작은 경계(길이 0~40)를 다 도는 전수 대조 테스트와 시간 제한을 둔다.
- 루프에 반복 상한(예: `64`번 — `int` 구간의 이진 탐색은 32번 안에 끝난다)을 두면 "안 끝남"이 예외로 드러난다(해석 — 방어 장치).

### 6. 그 밖의 증상

| 증상 | 보이는 것 | 흔한 원인 | leaf |
|---|---|---|---|
| 합·거리가 조용히 음수 | 큰 입력에서만 부호 반전 | `int` 오버플로 | [prefix-sum 1](../10-prefix-sum/2-summary.md) · [mst 3](../17-mst/2-summary.md) · [number-theory 2·3](../28-number-theory/2-summary.md) · [divide-conquer 2](../24-divide-conquer/2-summary.md) |
| 10억 개 넘는 순간 음수 인덱스 | 병합 정렬 중간값 | 오버플로(이진 탐색과 같은 줄) | [merge-sort 3](../02-merge-sort/2-summary.md) |
| 음수 나머지로 인덱스·샤드 예외 | `Index -8 out of bounds for length 10` | `%`가 음수, `Math.abs(Integer.MIN_VALUE)` | [hash-functions 5](../12-hash-functions/2-summary.md) · [number-theory 4](../28-number-theory/2-summary.md) · [string-hashing 3](../27-string-hashing/2-summary.md) |
| 메모리 폭발 | OOM | 병합 임시 배열, 키 범위 큰 계수 정렬, 상태 수 폭발 | [merge-sort 1](../02-merge-sort/2-summary.md) · [non-comparison-sort 1](../05-non-comparison-sort/2-summary.md) · [dp-basics 4](../21-dp-basics/2-summary.md) · [dp-advanced 1](../22-dp-advanced/2-summary.md) · [bfs 1](../11-bfs/2-summary.md) · [complexity-p-np 3](../40-complexity-p-np/2-summary.md) |
| 경로·답이 조용히 틀림 | 예외 없음, 특정 입력만 | 전제 위반(음수 간선, 비허용 휴리스틱, 증명 없는 그리디) | [dijkstra 1](../14-dijkstra/2-summary.md) · [a-star 1](../20-a-star/2-summary.md) · [greedy 1](../23-greedy/2-summary.md) · [bfs 2](../11-bfs/2-summary.md) |
| 거리가 라운드마다 계속 줄어듦 | 수렴 안 함 | 음수 사이클 | [bellman-floyd 1](../15-bellman-floyd/2-summary.md) |
| 해시로 비교했는데 없는 답을 찾음 | 가끔 오답 | 해시 충돌 확인 생략 | [string-hashing 1](../27-string-hashing/2-summary.md) |
| 무작위 테스트가 가끔 실패, 재현 안 됨 | CI 간헐 실패 | 시드 미기록 | [randomized-algorithms 4](../39-randomized-algorithms/2-summary.md) |
| 압축이 메모리·CPU를 다 먹음 / 오히려 커짐 | OOM, CPU 병목, 비율 > 1 | 압축 폭탄, 최고 레벨 고정, 작은·이미 압축된 데이터 | [lossless-compression 1·2·3](../33-lossless-compression-lz77-huffman/2-summary.md) · [modern-codecs 1·3·5](../34-modern-codecs-lz4-zstd-brotli/2-summary.md) |
| 압축 해제 실패 | "깨진 압축 데이터", 딕셔너리 불일치 | 포맷·윈도·딕셔너리 버전 | [lossless-compression 4](../33-lossless-compression-lz77-huffman/2-summary.md) · [modern-codecs 2·4](../34-modern-codecs-lz4-zstd-brotli/2-summary.md) |
| 타임아웃을 "무한 루프 검출"로 씀 | 느린 정상 작업이 무한 루프로 분류 | 정지 문제는 일반적으로 판정 불가 | [computability-and-halting 2·4](../41-computability-and-halting/2-summary.md) |

### 7. 증상별 "하지 말 것" 한 줄

| 증상 | 하지 말 것 | 대신 |
|---|---|---|
| 데이터 늘자 타임아웃 | 타임아웃 값만 늘림 | 두 배 실험으로 차수 확인, 알고리즘 교체 |
| 정렬 계약 예외 | `useLegacyMergeSort`로 덮음 | 표준 비교자, 32개 이상 무작위 테스트 |
| 재귀 스택 오버플로 | `-Xss`만 키움 | 명시적 스택·작은 쪽만 재귀·타뷸레이션 |
| 정규식 CPU 100% | 서버 증설 | 입력 상한·패턴 재작성·선형 엔진·시간 예산 테스트 |
| 이진 탐색 무한 루프 | 재시작 | 판 하나로 고정, 경계 전수 테스트, 반복 상한 |

## 쓰이는 자료구조·알고리즘

- **역색인·결정 트리**: 이 노트의 뼈대([data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)). 결정 트리의 질문 순서는 확인 비용 순이다.
- **두 배 실험(doubling ratio)**: 크기를 두 배씩 늘려 시간 비율로 차수를 추정한다. Sedgewick 『Algorithms』 4판 1.4절의 `DoublingTest.java`·`DoublingRatio.java`(크기를 두 배씩 늘리며 실행 시간과 그 비율을 찍는 프로그램)와 같은 방법이다([asymptotic-analysis](../02-asymptotic-analysis/2-summary.md)).
- **이 노트가 가리키는 알고리즘**: 정렬([09-sorting-in-practice](../09-sorting-in-practice/2-summary.md)·[03-quick-sort](../03-quick-sort/2-summary.md)), 재귀([03-recursion](../03-recursion/2-summary.md)), 백트래킹([13-backtracking](../13-backtracking/2-summary.md)), 이진 탐색([06-binary-search](../06-binary-search/2-summary.md)), 무작위화([39-randomized-algorithms](../39-randomized-algorithms/2-summary.md)).
- **쓰이는 곳(🔧)**: 장애 대응의 "알고리즘 원인" 갈래. 운영 색인([reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md))의 "지연 급증"에서 이 노트로 내려온다.

## 적용 — 풀어나가는 법

### 1. 증상을 받으면 이 순서로

1. 원문·입력·비율·덤프를 모은다(0-1절).
2. 0절 표에서 깨진 가정을 고른다. 예외 이름이 있으면 그 절로, 없으면 "느림(진행) / 안 끝남(같은 줄)"으로.
3. 결정 트리의 질문을 위에서부터 묻는다.
4. 원인이 둘 이상 남으면 둘을 가르는 입력을 하나 만든다. 예: 같은 n의 무작위 입력과 정렬된 입력을 둘 다 돌린다 — 둘 다 느리면 차수, 정렬된 것만 느리면 최악 입력.
5. leaf의 처방으로 간다. 처방이 "한도 올리기"뿐이면 7절을 다시 본다.

### 2. 첫 진단 명령·도구

```bash
jcmd <pid> Thread.print > d1.txt; sleep 3; jcmd <pid> Thread.print > d2.txt   # 같은 줄이면 "안 끝남"
grep -A3 'java.util.regex.Pattern' d1.txt | head                             # 정규식 엔진 안에 있나
jcmd <pid> JFR.start duration=60s filename=/tmp/cpu.jfr                       # 어느 메서드가 CPU를 쓰나
java -XX:MaxJavaStackTraceDepth=10000 ...                                     # 재현 환경에서 잘리지 않은 재귀 트레이스가 필요할 때
```

- 정규식이 의심되면 그 요청의 입력을 로그에서 꺼내 **길이를 두 배씩 늘려** 시간을 잰다. 두 배에 약 4배면 O(n²), 약 8배면 O(n³) 쪽, 한 글자에 두 배면 지수 쪽으로 의심한다(패턴을 읽어 확인).
- 마지막 줄의 `MaxJavaStackTraceDepth`는 OpenJDK 21 기본 1024([data-structure/43-ds-symptom-index](../../data-structure/43-ds-symptom-index/2-summary.md) 0-1 실험). 크게 잡으면 예외 생성 비용이 커지므로 운영 기본값으로 두지 않는다(해석).

### 3. 증상을 미리 드러내는 테스트 — Java 21

```java
import java.time.Duration;
import java.util.*;
import java.util.function.IntFunction;

final class AlgoGuards {
    // 1절: 두 배 비율 테스트 — 운영 최대 n과 그 두 배에서 시간 비율이 3을 넘으면 실패
    static void assertSubQuadratic(IntFunction<Runnable> workOfSize, int nMax) {
        long t1 = best(workOfSize.apply(nMax)), t2 = best(workOfSize.apply(nMax * 2));
        double r = (double) t2 / t1;
        if (r > 3.0) throw new AssertionError("n 두 배에 시간 x" + String.format("%.1f", r) + " — 제곱 이상 의심");
    }
    static long best(Runnable r) { long b = Long.MAX_VALUE; for (int i = 0; i < 5; i++) { long t = System.nanoTime(); r.run(); b = Math.min(b, System.nanoTime() - t); } return b; }

    // 5절: 이진 탐색 — 반복 상한으로 "안 끝남"을 예외로, 중간값은 >>> 1
    static int lowerBound(int[] a, int key) {
        int lo = 0, hi = a.length;                 // 반열린 [lo, hi)
        for (int guard = 0; lo < hi; guard++) {
            if (guard > 64) throw new IllegalStateException("구간이 줄지 않음 lo=" + lo + " hi=" + hi);
            int mid = (lo + hi) >>> 1;
            if (a[mid] < key) lo = mid + 1; else hi = mid;   // mid 는 아직 답 후보 → hi = mid
        }
        return lo;
    }

    // 2절: 정렬 결과 검증 — 예외가 안 나도 틀린 순서를 잡는다
    // ref는 정렬에 쓴 비교자가 아니라 따로 쓴 올바른 기준(예: Comparator.comparingInt(...)) — 같은 깨진 비교자로 검사하면 통과해 버린다
    static <T> void assertSorted(List<T> xs, Comparator<? super T> ref) {
        for (int i = 1; i < xs.size(); i++)
            if (ref.compare(xs.get(i - 1), xs.get(i)) > 0) throw new AssertionError("역전 at " + i);
    }
}
```

- 비율 기준 3.0은 예시 값이다. 1절 실험처럼 작은 n에서는 비율이 흔들리므로 nMax는 충분히 크게, 여러 번 잰 최솟값으로 비교한다.
- 정규식 시간 예산 검사(중단 가능한 `CharSequence`로 감싸기)는 [engineering-practice/20](../../engineering-practice/20-practice-incidents/2-summary.md) 실험 C에 코드가 있다.

## 장애 시나리오와 대처

### 1. 타임아웃 값을 늘려 증상을 덮음

- **현상**: 배치가 타임아웃 나서 제한을 30분에서 2시간으로 늘렸다. 석 달 뒤 데이터가 두 배가 되자 다시 타임아웃이다.
- **보이는 형태**: 배치 시간 지표가 데이터 두 배에 약 네 배. 타임아웃 설정 이력에 상향이 반복된다.
- **원인**: O(n²) 경로(1절)를 고치지 않고 경계만 미뤘다.
- **대처**: 두 배 실험으로 차수를 확인하고 알고리즘을 바꾼다. 제한을 늘렸다면 다음에 닿을 데이터 크기를 계산해 기록한다.

### 2. 같은 "CPU 100%"에 반대 처방

- **현상**: CPU 100% 사고를 "트래픽 증가"로 보고 서버를 늘렸다. 다음 날 같은 요청 몇 개가 새 서버의 CPU도 다 먹는다.
- **보이는 형태**: 요청률은 평소와 같다. 덤프 맨 위가 `java.util.regex.Pattern` 또는 정렬·분할 루프다. 느린 요청의 입력이 유난히 길거나 특정 모양(공백 2만 개, 정렬된 파일)이다.
- **원인**: 요청 수가 아니라 요청 하나의 비용이 문제였다(4절·1절의 최악 입력). 증설은 요청 하나의 비용을 줄이지 않는다.
- **대처**: 요청률과 요청당 CPU 시간을 나눠 본다. 요청당 비용이 튀면 입력을 꺼내 두 배 실험을 한다.

### 3. 예외만 없애고 틀린 결과를 남김

- **현상**: `Comparison method violates its general contract!`가 나서 `useLegacyMergeSort`를 켰다. 예외는 사라졌다. 고객이 랭킹이 이상하다고 문의한다.
- **보이는 형태**: 정렬 결과를 `Integer.compare`로 재검사하면 역전 쌍이 나온다(뺄셈 비교자 실험: 예외가 안 난 17회가 모두 틀린 순서 — [sorting-in-practice](../09-sorting-in-practice/2-summary.md)).
- **원인**: 예외는 비교자 위반의 **증상**이었다. 위반은 그대로다.
- **대처**: 비교자를 표준 메서드로 다시 쓴다. 정렬 결과 검증(`assertSorted`)을 테스트에 둔다.

### 4. "테스트 데이터에선 됐다" — 경계를 넘는 입력을 시험하지 않음

- **현상**: 단위 테스트는 다 통과한다. 운영에서만 계약 예외(n ≥ 32), 음수 인덱스(n > 2^30), 스택 오버플로(깊이 ∝ n), 정규식 폭주(긴 공백)가 난다.
- **보이는 형태**: 실패 입력이 테스트 입력보다 길거나 크거나 특정 모양이다.
- **원인**: 알고리즘의 가정(0절)을 깨는 입력을 테스트가 만들지 않았다. `MIN_MERGE = 32`처럼 구현 경계 아래의 테스트는 위반을 원리적으로 못 잡는다([sorting-in-practice](../09-sorting-in-practice/2-summary.md)).
- **대처**: 가정마다 그것을 깨는 입력을 테스트에 넣는다 — 32개 이상 동점 많은 데이터, 정렬된 입력, 최대 길이 입력, `int` 경계값(배열 없이 탐색 함수에 직접 `lo`·`hi`를 넣어서). 시간도 잰다.

### 5. 안 끝나는 루프를 재시작으로만 처리

- **현상**: 특정 키 조회가 가끔 응답하지 않아 감시 도구가 프로세스를 재시작한다. 재시작 횟수가 늘어난다.
- **보이는 형태**: 재시작 직전 덤프에 같은 `search`·`add` 프레임·같은 줄. 예외·로그 없음.
- **원인**: 종료 조건 결함(구간이 안 줄어듦, 0 인덱스, 빈 집합 뒤 미종료). 재시작은 그 키가 다시 오면 같은 결과다.
- **대처**: 덤프의 줄로 루프를 찾아 불변식을 고친다. 루프에 반복 상한을 넣어 "안 끝남"을 예외로 바꾼다. 테스트에 시간 제한을 건다.

## 핵심 문장

- 이 노트는 **증상 → 깨진 가정 → 흔한 원인 → 첫 진단 → leaf** 순서의 역색인이다.
- 알고리즘 증상의 대부분은 입력이 가정(크기·모양·값 범위·계약)을 벗어날 때 보인다. 첫 질문은 "그때의 입력은?"이다.
- "데이터가 늘자 타임아웃"은 크기 두 배 실험으로 가른다. 실험에서 이중 루프는 두 배마다 약 4배, 해시·정렬은 약 2배였다. n과 n log n은 이 방법으로 잘 갈리지 않는다.
- 계약 예외·스택 오버플로·정규식 폭주는 모두 "작은 테스트에선 안 보이는" 증상이다. 구현 경계(32개, 스택 1MB, 입력 길이)를 넘는 입력을 일부러 넣고, 결과뿐 아니라 시간도 잰다.
- 예외를 덮는 처방(`useLegacyMergeSort`, `-Xss`, 타임아웃 상향, 재시작)은 가정 위반을 그대로 둔다.

## 관련 주제·근거

- 선행: 이 영역 leaf 전체([curriculum.md](../curriculum.md)). 링크 표기 `이름 k`는 각 leaf 「장애 시나리오와 대처」의 k번째 시나리오다.
- leaf 노트(가장 많이 가리키는 것)
  - [01-algorithm-basics](../01-algorithm-basics/2-summary.md) · [02-asymptotic-analysis](../02-asymptotic-analysis/2-summary.md) · [03-recursion](../03-recursion/2-summary.md) — 분석·재귀
  - [06-binary-search](../06-binary-search/2-summary.md) · [03-quick-sort](../03-quick-sort/2-summary.md) · [09-sorting-in-practice](../09-sorting-in-practice/2-summary.md) · [11-external-sort-and-k-way-merge](../11-external-sort-and-k-way-merge/2-summary.md) — 탐색·정렬
  - [13-backtracking](../13-backtracking/2-summary.md) · [25-string-matching](../25-string-matching/2-summary.md) · [39-randomized-algorithms](../39-randomized-algorithms/2-summary.md) · [40-complexity-p-np](../40-complexity-p-np/2-summary.md) — 최악 입력·지수 탐색
- 후속: [43-alg-incidents](../43-alg-incidents/2-summary.md) — JDK 이진 탐색 오버플로(2006), Stack Overflow 정규식(2016), Cloudflare WAF 정규식(2019)
- 다른 영역 색인: [data-structure/43-ds-symptom-index](../../data-structure/43-ds-symptom-index/2-summary.md) · [reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md) · [engineering-practice/19-practice-symptom-index](../../engineering-practice/19-practice-symptom-index/2-summary.md)
- 측정·운영: [reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md) · [reliability/36-profiling](../../reliability/36-profiling/2-summary.md) · [reliability/35-timeout-design-worksheet](../../reliability/35-timeout-design-worksheet/2-summary.md)
- 근거 문서
  - Sedgewick, Wayne, 『Algorithms』 4판 1.4 "Analysis of Algorithms" — `DoublingTest.java`·`DoublingRatio.java` <https://algs4.cs.princeton.edu/14analysis/>
  - OpenJDK 21 `TimSort.java`(`MIN_MERGE = 32`, 계약 위반 예외) — [09-sorting-in-practice](../09-sorting-in-practice/2-summary.md)에서 확인한 범위
  - RE2 문법 문서 — `\1` 역참조, `(?=re)` 전방 탐색 "NOT SUPPORTED" <https://github.com/google/re2/wiki/Syntax>
  - 표의 수치·메시지는 각 leaf의 실험 출력과 인용을 따른다(OpenJDK 21.0.12 temurin 등, 2026-09-28~10-05 판). 정규식 시간은 [43-alg-incidents](../43-alg-incidents/2-summary.md)와 [engineering-practice/20](../../engineering-practice/20-practice-incidents/2-summary.md) 실험에서 옮겼다.
- 실험 목록
  - `Doubling.java` — 세 방법의 크기 두 배 → 시간 비율. eclipse-temurin:21-jdk(OpenJDK 21.0.12), `docker run --rm --pull never --network none --cpus=2 -u $(id -u):$(id -g) -e HOME=/tmp -v <dir>:/w -w /w eclipse-temurin:21-jdk java Doubling.java` 두 번. 시간은 실행마다 다르다.
