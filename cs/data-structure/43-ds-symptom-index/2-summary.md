# data-structure/43-ds-symptom-index — 증상 사전: ConcurrentModificationException·해시 성능 절벽·StackOverflowError·무한 큐 OOM·resize 스파이크·캐시 적중률 절벽 → 원인·첫 진단·leaf — 정리 (힌트)

## 해결하는 문제

이 영역의 다른 노트는 **구조에서 증상으로** 간다.\
"순회 중에 같은 리스트를 고치면 반복자가 들고 있던 위치가 무효가 된다 → `ConcurrentModificationException`"처럼 쓴다.\
현장에서는 반대 방향이 필요하다.\
손에 든 것은 증상 한 줄이다. 로그의 예외 이름, CPU 그래프, 힙 그래프, 적중률 그래프.

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                              이 노트 (역방향)
  구조·연산 --> 깨지는 조건 --> 보이는 증상          증상 --> 어떤 모양으로 --> 흔한 원인 --> 첫 진단 --> leaf
  "버킷 하나에 키가 몰리면 조회가 O(n)"             "CPU 100%, 덤프에 HashMap$TreeNode.find. 먼저 키 수와 해시 분포를 본다"
```

쉬운 예: 자동차 계기판의 경고등이다.\
경고등은 "엔진 점검"만 알려 준다. 정비 설명서의 고장 진단표가 "먼저 냉각수, 다음 오일 압력"처럼 볼 순서를 정한다.\
진단표는 차를 고치지 않는다. **어디를 먼저 볼지**만 정한다.

똑같은 구조다.\
"CPU 한 코어가 100%이고 덤프에 `HashMap`이 보인다"라는 같은 증상에 원인이 셋 이상이다.
- 요청 파라미터 수만 개가 같은 해시로 몰렸다(해시 충돌 공격) — 덤프 여러 장에서 `TreeNode.find`·`getNode`가 **바뀌며** 진행한다.
- 동기화 없는 `HashMap`을 여러 스레드가 고쳐 구조가 순환한다 — 덤프 여러 장에서 같은 스레드가 **같은 줄**에 머문다.
- 자체 키 클래스의 `hashCode`가 좁고 `Comparable`도 아니다 — 특정 고객 데이터에서만, 공격 없이 느리다.

처방이 셋 다 다르다. 첫째는 입력 상한과 키 있는 해시, 둘째는 `ConcurrentHashMap`, 셋째는 키 클래스 수정이다.

실무 예:
- 자료구조의 증상은 대부분 **크기가 커질 때** 처음 보인다. 테스트의 n은 작고 운영의 n은 크다. 그래서 "어제까지 멀쩡했다"는 말이 이 영역 증상의 단골 머리말이다.
- 예외가 나는 증상(`ConcurrentModificationException`·`StackOverflowError`·`OutOfMemoryError`)보다 예외 없이 틀리는 증상(건너뛴 원소, 잃은 put, 순서가 틀린 결과)이 더 위험하다. 예외는 최선 노력으로만 던져지는 경우가 많다(1절).

  - *역색인(inverted index)*: "문서 → 단어" 목록을 뒤집어 "단어 → 문서" 목록으로 만든 것이다([32-inverted-index](../32-inverted-index/2-summary.md)). 여기서는 "leaf → 증상"을 "증상 → leaf"로 뒤집었다.
  - *leaf 표기 `이름 k`*: 이 영역 노트의 「장애 시나리오와 대처」 `k`번째 시나리오다. 예: `hashmap 1` = [05-hashmap](../05-hashmap/2-summary.md)의 시나리오 1(해시 충돌 공격). 이 영역은 기존 폴더 번호와 커리큘럼 번호가 달라 번호가 겹치는 폴더가 있다(`01-dynamic-array`와 `01-data-structures-basics`). 그래서 번호 대신 이름으로 적는다.
  - *첫 진단*: 고치기 전에 원인 후보를 가르는 가장 싼 확인 한 가지다.

## 동작·원리

### 0. 증상은 어느 층에서 보이나

```text
   증상 그래프·로그                    층                         이 노트의 절
   ────────────────                    ──                         ──────────
   예외: ConcurrentModificationException  ┐
         (또는 예외 없이 건너뜀)          ├ 구조의 일관성 (순회·공유)    1절
   CPU 100%, 같은 줄에 머문 스레드         ┘
   CPU 100%, 특정 요청만 느림           ── 연산 비용 계약 (시간)         2절
   StackOverflowError                  ── 호출 스택 (재귀 깊이)          3절
   OutOfMemoryError, 힙 우상향          ── 용량 (상한 없는 구조)          4절
   p99·최대 지연만 튐, 평균은 정상       ── 분할 상환의 "그 한 번"         5절
   적중률 절벽, 원본 DB 부하 급증        ── 지역성 가정 (캐시 교체 정책)     6절
   예외 없이 틀린 값·끝나지 않는 루프 등  ── 그 밖의 불변식 위반            7절
```

- 커리큘럼의 여섯 증상이 1~6절이다. 7절은 leaf 시나리오에 나오는 나머지 증상이다.
- 한 증상이 두 층에 걸치는 경우가 있다. 예: 동기화 없는 `HashMap`은 1절(유실·순환)과 2절(CPU 100%)에 둘 다 나온다. 첫 진단으로 가른다.

### 0-1. 색인을 쓰기 전에 확보할 것

```text
  ① 원문        예외 이름 + 전체 스택 트레이스 + "Caused by" 체인, JDK 판(java -version)
  ② 크기        그때의 n — 컬렉션 크기, 키 수, 큐 길이, 재귀 깊이, 요청 파라미터 수
  ③ 시간축      언제부터? 매번인가 가끔인가? 데이터 증가·배포·배치·트래픽과 겹치나?
  ④ 스냅숏 2~3장  스레드 덤프를 몇 초 간격으로 여러 번 (한 장으로는 "멈춤"과 "진행 중"을 못 가른다)
```

- ②가 빠지면 이 영역의 진단은 거의 안 된다. 자료구조 증상의 대부분은 "n이 어떤 경계를 넘었다"이기 때문이다.
- `StackOverflowError`의 트레이스는 잘린다. OpenJDK 21의 기본 `MaxJavaStackTraceDepth`는 1024다. 아래 실험에서 실제 깊이 2만 언저리 재귀의 트레이스가 1024프레임이었다. 트레이스 맨 아래가 재귀의 시작점이 아닐 수 있다.

#### 실험: `StackOverflowError` 트레이스는 실제 깊이보다 짧다 (`SoeTrace.java`)

```java
static int depth = 0;
static void down() { depth++; down(); }
// main: try { down(); } catch (StackOverflowError e) { depth, e.getStackTrace().length, (Object) e instanceof Exception 출력 }
```

(실험, eclipse-temurin:21-jdk = OpenJDK 21.0.12, docker `--network none --cpus=2`, 기본 `-Xss`, 2026-10-05 — 두 번 실행. 깊이는 실행마다 다르다)

```text
실제 재귀 깊이 = 21667, 트레이스 프레임 수 = 1024
맨 위 = SoeTrace.down(SoeTrace.java:4), 맨 아래 = SoeTrace.down(SoeTrace.java:4)
instanceof Exception = false
실제 재귀 깊이 = 19972, 트레이스 프레임 수 = 1024
```

같은 이미지에서 `java -XX:+PrintFlagsFinal -version`: `MaxJavaStackTraceDepth = 1024 {default}`, `ThreadStackSize = 1024 {default}`(KB).

- 관찰: 깊이 약 2만 번의 재귀가 1024줄로 잘렸다. 맨 아래 줄도 `down`이다. 처음 재귀로 들어온 호출자(`main`)는 트레이스에 없다.
- 관찰: `StackOverflowError`는 `Exception`이 아니다. `catch (Exception e)`로는 안 잡힌다([03-recursion](../../algorithm/03-recursion/2-summary.md) 장애 1).
- 진단 함의: 트레이스에서 **반복되는 프레임 묶음**(1개면 직접 재귀, 2~3개 교대면 상호 재귀)을 찾는다. 시작점이 필요하면 로그·요청 ID로 찾는다.

### 1. `ConcurrentModificationException` — 또는 예외 없이 건너뛰기

먼저 **스레드가 하나인가 여럿인가**를 가른다. "Concurrent"는 스레드가 아니라 "순회와 수정이 겹쳤다"는 뜻이다.

```text
  ConcurrentModificationException / 처리 건수 불일치
     │
     ├─ 같은 스레드, for-each 안에서 list.remove / map.remove ────────▶ 반복자 밖 수정           concurrent-data-structures 3 · dynamic-array 4 · hashmap 4
     ├─ 예외 없음, 마지막 원소만 처리 안 됨 ───────────────────────────▶ 끝에서 두 번째 삭제(검사 지점 우회) concurrent-data-structures 3
     ├─ 다른 스레드가 같은 컬렉션을 고침 ─────────────────────────────▶ 공유 비동기 컬렉션        concurrent-data-structures 1·3
     ├─ TreeMap/TreeSet 순회 중 ──────────────────────────────────▶ 같은 원인, 트리판          red-black-tree 3
     └─ 예외도 없고 고리처럼 끝나지 않음 (직접 만든 리스트) ────────────▶ 동시 수정으로 순환        linked-list 2
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| `java.util.ConcurrentModificationException`, 스택에 `ArrayList$Itr.checkForComodification`·`HashMap$HashIterator.nextNode` | 순회 중 반복자 밖에서 `remove`/`add` | 스택의 순회 줄과 같은 컬렉션을 고치는 줄이 같은 스레드인가 | [concurrent-data-structures 3](../29-concurrent-data-structures/2-summary.md) · [hashmap 4](../05-hashmap/2-summary.md) |
| 예외 없이 `[a, b, d]` — 끝에서 두 번째 `c`를 지우자 `d`는 검사도 안 됨(OpenJDK 21.0.12 실험) | 크기가 줄어 `hasNext()`가 `false`, 검사 지점(`next()`)에 닿지 않음 | 입력 건수 = 처리 건수 + 제외 건수인가 | [concurrent-data-structures 3](../29-concurrent-data-structures/2-summary.md) |
| 직접 만든 동적 배열에서 앞에서부터 `remove(i)` → 중복이 남거나 원소를 빠뜨림, 예외 없음 | 삭제가 뒤를 당겨 아직 안 본 인덱스가 바뀜 | 뒤에서부터 지웠을 때 결과가 다른가 | [dynamic-array 4](../01-dynamic-array/2-summary.md) |
| 반복자 `remove()` 두 번에 `IllegalStateException` | 반복자 상태 계약 위반 | `next()` 한 번에 `remove()` 한 번인가 | [linked-list 3](../02-linked-list/2-summary.md) |
| 정렬 맵 순회 중 예외, 또는 예외 없이 손상 | 같은 원인. 동시 수정이면 조용히 깨질 수 있음 | 공유 여부 | [red-black-tree 3](../16-red-black-tree/2-summary.md) |

- 처방: 단일 스레드면 `Iterator.remove`·`removeIf`, 또는 지울 것을 모았다가 순회 뒤 삭제. 여러 스레드면 동시 컬렉션이나 스냅숏 복사 후 순회.
- `ArrayList` Javadoc은 fail-fast 동작을 "cannot be guaranteed"라고 적는다. 예외에 기대지 말고 **건수를 대조**한다([concurrent-data-structures](../29-concurrent-data-structures/2-summary.md) 6절).

### 2. 해시 성능 절벽 — 평소엔 빠른 맵이 특정 입력에서 CPU 100%

먼저 **입력이 외부에서 오는가, 키 클래스가 우리 것인가, 맵이 공유되는가**를 가른다.

```text
  해시 맵 조회·삽입이 갑자기 느림 / CPU 100%
     │
     ├─ 요청 하나의 파라미터·JSON 키가 수만 개, 덤프가 진행 중 ──────────▶ 해시 충돌 공격(HashDoS)     hashmap 1 · hash-functions 1 · 44-ds-incidents
     ├─ 공격 없음, 특정 데이터만, 자체 키 클래스 ──────────────────────▶ 좁은 hashCode + 비Comparable  hash-functions 2 · adt-and-cost-contracts 4
     ├─ 덤프 여러 장에서 같은 스레드가 같은 줄 (RUNNABLE) ─────────────▶ 비동기화 HashMap 구조 손상   concurrent-data-structures 1 · 44-ds-incidents
     ├─ size는 작은데 점점 느려짐 (개방 주소법) ───────────────────────▶ 묘비(tombstone) 누적         open-addressing 1 · hashmap 3
     ├─ 넣은 키를 못 찾음, 예외 없음 ────────────────────────────────▶ 넣은 뒤 키가 바뀜(hashCode 변화) hashmap 2 · open-addressing 3
     └─ 쿠쿠 맵에 특정 키 몇 개 → 재해싱 반복 끝에 예외 ─────────────────▶ 쿠쿠 사이클                 open-addressing 2
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 요청률은 평소인데 요청 처리 스레드 CPU 100%, 덤프에 `HashMap.putVal`·`getNode`·`TreeNode.find`, 요청 하나가 수십 초 | 공격자가 같은 해시의 키를 미리 계산해 보냄 | 느린 요청의 파라미터·키 개수, 그 키들의 `hashCode` 중복 수 | [hashmap 1](../05-hashmap/2-summary.md) · [hash-functions 1](../../algorithm/12-hash-functions/2-summary.md) |
| 같은 hashCode 키 32,768개 삽입: `String` 키 46~68 ms, 같은 hashCode의 비`Comparable` 키 31.7~35.3초(OpenJDK 21.0.12, 집필·점검 네 번, [44-ds-incidents](../44-ds-incidents/2-summary.md) 실험 A) | JDK 8+ 트리 버킷 조회는 같은 해시의 서로 다른 키를 `compareTo`가 구별할 때만 O(log n)(비`Comparable`이거나 `compareTo`가 0이면 양쪽을 뒤짐) | 키 클래스가 `Comparable`인가, `hashCode`가 몇 개의 서로 다른 값을 내나 | [hash-functions 2](../../algorithm/12-hash-functions/2-summary.md) · [adt-and-cost-contracts 4](../02-adt-and-cost-contracts/2-summary.md) |
| 예외 없음, 서버 하나가 한 코어 100%. 덤프에 `HashMap$TreeNode.root`·`putTreeVal`·`balanceInsertion`(JDK 21 실험에서 집필 16번 중 2번·점검 8번 중 1번 멈춤) | 동시 `put`·리사이즈가 버킷 구조를 망가뜨림 | 덤프 2~3장에서 같은 프레임·같은 줄인가, 그 맵이 필드로 공유되나 | [concurrent-data-structures 1](../29-concurrent-data-structures/2-summary.md) |
| `size()`는 400 언저리로 일정, `get`이 시간이 갈수록 느려짐, 묘비가 `size`보다 많음 | 삭제가 묘비를 남겨 탐사 사슬이 줄지 않음 | 리사이즈 판단이 `size`인가 `used`(점유+묘비)인가 | [open-addressing 1](../29-open-addressing/2-summary.md) · [hashmap 3](../05-hashmap/2-summary.md) |
| `put` 했는데 `get`이 `null`, 순회하면 보임 | 키 객체를 넣은 뒤 바꿈, `equals`/`hashCode` 불일치 | 키가 불변인가, 두 메서드가 같은 필드를 쓰나 | [hashmap 2](../05-hashmap/2-summary.md) · [open-addressing 3](../29-open-addressing/2-summary.md) |

- 해시 맵의 "상수 시간"은 **해시가 고르게 퍼진다는 가정** 위의 기대 비용이다([adt-and-cost-contracts](../02-adt-and-cost-contracts/2-summary.md)). 가정을 깨는 것이 공격(1행), 나쁜 `hashCode`(2행), 구조 손상(3행)이다.
- Java `String.hashCode`는 시드가 없다. 그래서 `String` 키의 방어선은 트리화(JEP 180)와 입력 상한이다. CPython은 3.3부터 `str` 해시 랜덤화가 기본이다(사건은 [44-ds-incidents](../44-ds-incidents/2-summary.md)).

### 3. `StackOverflowError` — 작은 입력에선 멀쩡하다

먼저 **깊이가 무엇에 비례하나**를 본다. 기저 누락이면 크기와 무관하게 터지고, 데이터 모양이면 큰 데이터에서만 터진다.

```text
  StackOverflowError
     │
     ├─ 크기와 무관하게, 같은 입력이면 매번 ───────────────────────────▶ 기저 누락·축소 실패        recursion 1 (algorithm)
     ├─ 큰 데이터에서만: 정렬된 키를 균형 없는 트리에 ──────────────────▶ 트리 높이 = n            data-structures-basics 2 · binary-search-tree 1 · persistent 1
     ├─ 큰 데이터에서만: 긴 사슬·긴 키·한쪽으로만 붙인 rope ────────────▶ 깊이 = 사슬 길이          union-find 1 · trie 3 · rope 1
     ├─ 큰 그래프·깊은 트리의 재귀 DFS ─────────────────────────────▶ 깊이 = 최장 경로           graph 1 · dfs 1 (algorithm)
     └─ 외부 입력 [[[[…]]]] 수만 겹 ────────────────────────────────▶ 재귀 하강 파서 깊이 = 입력   recursion 3 (algorithm)
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| `StackOverflowError`, 같은 메서드 프레임이 반복(OpenJDK 21에서 1024줄로 잘림 — 0-1 실험) | 재귀 깊이가 스레드 스택(기본 1024KB, Linux x64)을 넘음 | 그때 n과 깊이의 관계: log n인가 n인가 | [stack 1](../03-stack/2-summary.md) · [recursion 2](../../algorithm/03-recursion/2-summary.md) |
| 정렬 입력 1만 200개는 되고 1만 300개에서 `put`이 터짐(원본 README 실측) | 균형 없는 트리가 한 줄 → 높이 = 원소 수 | 입력이 정렬돼 들어오나, 트리 높이 | [persistent 1](../26-persistent/2-summary.md) · [binary-search-tree 1](../06-binary-search-tree/2-summary.md) · [data-structures-basics 2](../01-data-structures-basics/2-summary.md) |
| 10만 개를 한 줄로 이은 뒤 `find`에서 터짐 | 크기로 붙이기 없는 재귀 `find` | 크기·랭크로 붙이나, `find`가 재귀인가 | [union-find 1](../14-union-find/2-summary.md) |
| `toString()`을 부르는 순간 터짐, `appendRange`가 수만 번(원본 실측 깊이 19,628 생존·19,726 실패) | 한쪽에만 `concat`, 재균형 없음 | `depth()`가 `2·log2(leafCount)`를 넘나 | [rope 1](../28-rope/2-summary.md) |
| `keysWithPrefix`에서 `collect`가 수천 번 | 깊이 = 가장 긴 키 길이 | 키 길이 분포, 상한 | [trie 3](../09-trie/2-summary.md) |
| 순환에서 탐색이 끝나지 않음, 재귀면 결국 `StackOverflowError` | 방문 표시 누락 | 방문 집합이 있나 | [graph 1](../08-graph/2-summary.md) |

- `-Xss`를 키우는 것은 경계를 미룰 뿐이다. 같은 `-Xss1m`에서도 깊이 한계가 실행마다 크게 달랐다(19,415~41,224, [recursion](../../algorithm/03-recursion/2-summary.md) 실험). 깊이가 입력에 비례하면 명시적 스택(`ArrayDeque`)으로 바꾼다([stack 1](../03-stack/2-summary.md)).
- 알고리즘 쪽 원인(축소 실패·중복 부분문제·꼬리 재귀 착각)은 [algorithm/42-alg-symptom-index](../../algorithm/42-alg-symptom-index/2-summary.md) 3절이 정본이다.

### 4. 무한 큐 OOM — 힙이 우상향하다 `OutOfMemoryError`

먼저 **무엇이 쌓이나**를 힙 히스토그램으로 본다. 큐·배열·트리 중 어느 것이 크고, 그 원소가 살아 있는 일인가 죽은 일인가.

```text
  OutOfMemoryError: Java heap space / 힙 우상향
     │
     ├─ 거대한 큐 하나, 앞의 요청이 몇 분 전 것 ───────────────────────▶ 소비 < 생산, 상한 없음        queue-deque 1
     ├─ 큐 size가 진행 중 작업 수보다 몇 자릿수 큼 (ScheduledFutureTask) ─▶ 취소한 타이머가 남음         timer-structures 2 · heap 2
     ├─ 거대한 Object[] 하나, add만 하고 안 지움 ───────────────────────▶ 상한 없는 버퍼              dynamic-array 2
     ├─ size()는 줄었는데 메모리 그대로 ──────────────────────────────▶ 지운 칸의 참조가 남음(누수)    dynamic-array 3
     ├─ 캐시 항목 수는 상한 안인데 메모리 초과 ─────────────────────────▶ 개수 상한 ≠ 바이트 상한       lru-cache 4
     ├─ 고유한 긴 키로 노드 폭증 ─────────────────────────────────────▶ 트라이 노드 수 = 글자 수      trie 1
     └─ 버전·undo 이력을 붙잡음 ──────────────────────────────────────▶ 영속 구조의 옛 버전 참조     persistent 2 · rope 2
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| `java.lang.OutOfMemoryError: Java heap space`, 힙 덤프에 거대한 큐 하나, 처리 지연 누적 | 넣는 속도 > 빼는 속도, 큐에 상한 없음 | 생산률·소비률을 같은 시간축에, 큐 길이 추세 | [queue-deque 1](../04-queue-deque/2-summary.md) |
| `getQueue().size()`가 진행 중 요청보다 몇 자릿수 큼, 히스토그램 상위 `ScheduledFutureTask` | STPE 기본 `removeOnCancel=false` — 취소 표시만 하고 만료까지 남김 | 취소 정책, 큐 크기 대 활성 작업 수 | [timer-structures 2](../26-timer-structures/2-summary.md) · [heap 2](../07-heap/2-summary.md) |
| 거대한 `Object[]` 하나 | 로그·이벤트를 `add`만 | 그 배열의 소유자, 지우는 경로가 있나 | [dynamic-array 2](../01-dynamic-array/2-summary.md) |
| `size()`는 줄었는데 힙 그대로, 덤프에서 지운 객체가 배열에 남음 | `elements[--size] = null` 누락 | 배열의 size 밖 칸이 `null`인가 | [dynamic-array 3](../01-dynamic-array/2-summary.md) |
| 노드 수 적은데 몇 개의 큰 값이 힙 대부분 | 용량을 항목 개수로만 셈 | 항목 무게(바이트) 분포 | [lru-cache 4](../10-lru-cache/2-summary.md) |
| 요청 스레드 다수가 `WAITING`, 스택에 `ArrayBlockingQueue.put` (OOM 대신 멈춤) | 상한 있는 큐 + 블로킹 정책이 생산자로 전파 | 큐가 찼나, 소비자가 왜 느린가 | [ring-buffer 2](../25-ring-buffer/2-summary.md) |
| 오류 없이 데이터 일부가 빔, drop 카운터 증가 | 상한 있는 링의 덮어쓰기·거부 정책 | 드롭·덮어쓰기 지표가 있나 | [ring-buffer 1](../25-ring-buffer/2-summary.md) |

- 상한을 두면 증상이 **OOM → 멈춤(블로킹) → 드롭**으로 바뀐다. 어느 쪽이 덜 나쁜지는 데이터가 무엇인가로 정한다(감사 로그는 잃으면 안 되고, 진단 로그는 버려도 된다 — [ring-buffer 2](../25-ring-buffer/2-summary.md)). 상한 없는 큐는 정책을 "OOM"으로 정한 것과 같다(해석).
- 큐 길이를 재는 방법도 비용이 있다. `ConcurrentLinkedQueue.size()`는 원소를 훑는 선형 연산이다([adt-and-cost-contracts 3](../02-adt-and-cost-contracts/2-summary.md)).
- 백프레셔·부하 차단 설계는 [reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md), 힙 분석 절차는 [reliability/37-memory-leak-and-heap-analysis](../../reliability/37-memory-leak-and-heap-analysis/2-summary.md), 컨테이너 메모리 한도와 OOM killer는 [os/13-oom-and-memory-limits](../../os/13-oom-and-memory-limits/2-summary.md)가 정본이다.

### 5. resize 스파이크 — 평균은 좋은데 가끔 한 번 튄다

먼저 **튀는 간격**을 본다. 크기가 일정 배율로 커질 때마다(두 배로 키우는 배열·`HashMap`은 두 배, OpenJDK `ArrayList`는 약 1.5배) 튀면 확장, 경계 근처에서 계속 튀면 thrashing이다.

```text
  p99·최대 지연만 튐 (평균·처리량은 정상)
     │
     ├─ 크기가 4·8·16·… 을 넘을 때마다, 간격이 두 배씩 길어짐 ───────────▶ 확장 복사 O(n)            dynamic-array 1 · stack 4
     ├─ 크기가 경계 근처를 오가는 동안 계속 ─────────────────────────────▶ 확장·축소 경계가 붙음      systems/thrashing
     ├─ 거대 컬렉션, GC 로그에 G1 Humongous Allocation ─────────────────▶ 큰 새 배열 할당 + GC        asymptotic-analysis 2 (algorithm)
     ├─ HashMap 크기 증가 구간에서 HashMap.resize ──────────────────────▶ 리해시 O(n)                 asymptotic-analysis 2 (algorithm)
     └─ 확장 직후 dequeue가 엉뚱한 값 (지연 아닌 오답) ───────────────────▶ 감긴 원형 배열을 통째 복사   queue-deque 4
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| p99가 튐, 프로파일에 `Arrays.copyOf`/`System.arraycopy`가 용량 경계마다 | 꽉 찬 순간의 전체 복사 — 분할 상환은 O(1)이지만 그 한 번은 O(n) | 튀는 시점의 크기가 용량 수열 근처인가(두 배 배열은 2의 거듭제곱, OpenJDK `ArrayList`는 10에서 약 1.5배씩 — [asymptotic-analysis 2](../../algorithm/02-asymptotic-analysis/2-summary.md) 실험) | [dynamic-array 1](../01-dynamic-array/2-summary.md) · [stack 4](../03-stack/2-summary.md) |
| size 약 2천만에서 `add` 한 번이 688~826 ms, 같은 시점 GC 로그 `Pause Young (Concurrent Start) (G1 Humongous Allocation)`(OpenJDK 21 실험) | 확장 복사 + 큰 배열 할당이 부른 GC | `-Xlog:gc`에서 같은 시각의 정지 | [asymptotic-analysis 2](../../algorithm/02-asymptotic-analysis/2-summary.md) |
| 크기가 경계(예: 16↔17)를 오갈 때마다 새 배열 생성 + 복사 | 확장 경계(`size == capacity`)와 축소 경계(`size <= capacity/2`)가 붙음 | 축소 조건이 무엇인가 — `capacity/4`로 떼어 놓았나 | [systems/thrashing](../../systems/thrashing/2-summary.md) |
| 확장(4→8) 직후 순서가 뒤바뀌거나 `null` | 감긴 상태를 물리 순서로 복사 | 감긴 상태에서 확장하는 테스트가 있나 | [queue-deque 4](../04-queue-deque/2-summary.md) |

- 처방: 최종 크기를 알면 초기 용량을 미리 잡는다(`new ArrayList<>(n)`, `HashMap`은 기대 원소 수 / 0.75 이상). 지연 상한이 중요한 경로면 확장이 없는 구조(고정 크기 링 버퍼 — [25-ring-buffer](../25-ring-buffer/2-summary.md))를 쓴다. 축소는 확장 경계에서 떨어뜨린다.
  - *분할 상환(amortized)*: 연산 여러 번의 총비용을 횟수로 나눈 비용이다. "평균"이지만 입력 분포의 평균이 아니라 **연산 순서 전체**에 대한 보장이다. 그래서 한 번의 비용 상한은 말해 주지 않는다.
- 꼬리 지연을 재는 법은 [reliability/34-tail-latency-and-stragglers](../../reliability/34-tail-latency-and-stragglers/2-summary.md).

### 6. 캐시 적중률 절벽 — 조금 늘었을 뿐인데 갑자기

먼저 **절벽이 언제 왔나**를 본다. 배치 시각에 왔다가 서서히 회복하면 스캔 오염, 데이터가 어느 날 임계를 넘은 뒤 계속이면 워킹 셋 초과다.

```text
  적중률 급락 + 원본(DB) 부하 급증
     │
     ├─ 배치·전체 스캔 시각에 떨어졌다가 서서히 회복 ────────────────────▶ 순차 스캔이 캐시를 밀어냄    lru-cache 1
     ├─ 데이터·사용자 수가 임계를 넘은 날부터 계속 낮음 ─────────────────▶ 워킹 셋 > 용량              lru-cache 2
     ├─ 캐시 서버 한 대가 죽은 뒤 옆 서버가 연달아 죽음 ──────────────────▶ 재배치가 한쪽으로 몰림        consistent-hashing 1
     ├─ 키 하나가 트래픽 30% ─────────────────────────────────────────▶ 핫 키                       consistent-hashing 2
     └─ 만료 순간 같은 키에 요청이 몰림 ──────────────────────────────────▶ 캐시 스탬피드               reliability/29
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 적중률 그래프가 배치 시각에 절벽, 미스가 몰려 DB 부하가 튐 | 한 번만 쓸 데이터 n개가 지나가며 자주 쓰던 항목을 다 밀어냄 | 절벽 시각과 배치·스캔 작업 시각이 겹치나 | [lru-cache 1](../10-lru-cache/2-summary.md) |
| 용량 3에 키 4개를 돌아가며 찍으면 적중률 0%, 용량 4면 첫 네 번의 적재 미스 뒤 100% | LRU는 워킹 셋이 용량을 조금만 넘어도 매번 "다음에 쓸 것"을 버림 | 기간별 고유 키 수(워킹 셋)와 용량 비교, 접근 로그로 용량-적중률 곡선 | [lru-cache 2](../10-lru-cache/2-summary.md) |
| 노드 하나 장애 후 이웃 노드만 부하 급증·연쇄 장애 | 가상 노드 없이 링에서 이웃이 키를 다 받음 | 노드별 키·요청 분포 | [consistent-hashing 1](../31-consistent-hashing/2-summary.md) |
| 어느 서버로 옮겨도 그 서버가 죽음 | 키 하나에 트래픽이 몰림 | 키별 요청 상위 목록 | [consistent-hashing 2](../31-consistent-hashing/2-summary.md) |

- 적중률 절벽은 **비선형**이다. 용량이 워킹 셋보다 조금 작은 상태와 조금 큰 상태의 차이가 0%와 100%만큼 날 수 있다([lru-cache 2](../10-lru-cache/2-summary.md)). 그래서 평균 적중률 추세만 보면 절벽 직전을 놓친다(해석).
- 만료 순간의 몰림(스탬피드)은 [reliability/29-cache-stampede](../../reliability/29-cache-stampede/2-summary.md)가 정본이다.

### 7. 그 밖의 증상 — 예외 없이 틀린 값, 끝나지 않는 루프, 줄지 않는 메모리

| 증상 | 보이는 것 | 흔한 원인 | leaf |
|---|---|---|---|
| 끝나지 않는 루프, CPU 100%, 예외 없음 | 덤프 여러 장에서 같은 루프 | 동시 수정으로 생긴 순환 리스트, 1-base 인덱스에 0이 들어간 펜윅 `add`, 디렉터리 하드 링크 순환 | [linked-list 2](../02-linked-list/2-summary.md) · [fenwick-tree 1](../17-fenwick-tree/2-summary.md) · [filesystem 4](../33-filesystem/2-summary.md) |
| 합·크기가 조용히 음수 | 큰 입력에서만 부호 반전 | `int` 오버플로 | [segment-tree 3](../13-segment-tree/2-summary.md) · [fenwick-tree 2](../17-fenwick-tree/2-summary.md) · [suffix-array 4](../21-suffix-array/2-summary.md) · [spatial-index 4](../25-spatial-index/2-summary.md) |
| 특정 n에서만 `ArrayIndexOutOfBoundsException` | 배열을 `2n`으로 잡음, `(head - 1) % length`가 -1 | 크기 계산·음수 나머지 | [segment-tree 1](../13-segment-tree/2-summary.md) · [queue-deque 2](../04-queue-deque/2-summary.md) |
| 동시 갱신에서 원소·비트가 사라짐 | 개수 불일치, 예외 없음 | 읽고-고치고-쓰기 경쟁, 복합 연산 비원자 | [concurrent-data-structures 2](../29-concurrent-data-structures/2-summary.md) · [bitset 3](../18-bitset/2-summary.md) · [bloom-filter 4](../11-bloom-filter/2-summary.md) · [skip-list 2](../12-skip-list/2-summary.md) |
| "동시에 읽기만 했는데" 결과가 틀림 | 읽기 잠금만 잡음 | 읽기가 구조를 바꿈(스플레이, 경로 압축, 지연 전파) | [splay-tree 1](../23-splay-tree/2-summary.md) · [union-find 2](../14-union-find/2-summary.md) · [segment-tree 4](../13-segment-tree/2-summary.md) |
| 드물게 원소 소실·같은 객체를 두 곳에서 씀 | 부하 높을 때만, 재현 거의 불가 | lock-free 구조의 ABA | [concurrent-data-structures 4](../29-concurrent-data-structures/2-summary.md) |
| "확실히 없다"는데 있음 / "있다"를 확정으로 처리 | 블룸 필터 결과 오용·동기화 누락 | 필터와 저장소의 쓰기 순서 | [bloom-filter 1·3](../11-bloom-filter/2-summary.md) |
| 지웠는데 용량·메모리가 안 줄어듦 | 참조가 남음 | 열린 핸들·옛 버전·이력 | [filesystem 2](../33-filesystem/2-summary.md) · [persistent 2](../26-persistent/2-summary.md) · [rope 2](../28-rope/2-summary.md) |
| 남은 공간은 충분한데 할당 실패 | 지표 착시 | 단편화 | [allocator 2](../35-allocator/2-summary.md) |
| 조회가 점점 느려짐 (LSM) | 읽기 증폭 증가 | compaction 정체, 병합 전략 | [lsm-tree 1](../24-lsm-tree/2-summary.md) · [lsm-merge-model 4](../19-lsm-merge-model/2-summary.md) |
| 쓰기 증폭·공간 증폭 폭증 | 디스크 쓰기량·용량 급증 | 워크로드와 맞지 않는 병합 방식 | [lsm-merge-model 1·2](../19-lsm-merge-model/2-summary.md) |
| 타임아웃이 늦게 울림, 휠이 O(1)인데 느림 | 틱보다 짧은 타임아웃, 칸 수 부족 | 타이머 휠 해상도·칸 수 | [timer-structures 3·4](../26-timer-structures/2-summary.md) |
| 같은 입력인데 실행마다 순서가 다름 | 테스트가 흔들림 | 해시 순서에 기대는 출력 | [dependency-resolver 3](../34-dependency-resolver/2-summary.md) · [filesystem 3](../33-filesystem/2-summary.md) |

### 8. 증상별 "하지 말 것" 한 줄

| 증상 | 하지 말 것 | 대신 |
|---|---|---|
| `ConcurrentModificationException` | `catch`로 삼키고 재시도 | `removeIf`·반복자 삭제, 건수 대조 |
| 해시 성능 절벽 | 서버 증설로 버팀(요청 하나가 코어 하나를 계속 씀) | 입력 상한, 키 클래스 수정, 동시 컬렉션 |
| `StackOverflowError` | `-Xss`만 키움 | 깊이를 입력과 떼어 놓음(명시적 스택, 균형) |
| 무한 큐 OOM | `-Xmx`만 키움 | 상한 + 꽉 찼을 때의 정책 + 드롭 지표 |
| resize 스파이크 | 평균 지연만 봄 | 초기 용량, p99·최대, 확장 없는 구조 |
| 캐시 적중률 절벽 | 용량을 감으로 두 배 | 접근 로그로 용량-적중률 곡선, 스캔 우회 |

## 쓰이는 자료구조·알고리즘

- **역색인**: 이 노트의 뼈대가 "증상 → leaf" 역색인이다([32-inverted-index](../32-inverted-index/2-summary.md)).
- **결정 트리**: 각 절의 그림은 "싼 질문부터" 묻는 결정 트리다. 질문 순서는 확인 비용 순(로그 한 줄 → 덤프 → 히스토그램 → 프로파일)이다.
- **이 노트가 가리키는 구조**: 동적 배열·연결 리스트·스택·큐([01](../01-dynamic-array/2-summary.md)~[04](../04-queue-deque/2-summary.md)), 해시 맵·개방 주소법([05](../05-hashmap/2-summary.md)·[29-open-addressing](../29-open-addressing/2-summary.md)), 힙·타이머([07](../07-heap/2-summary.md)·[26-timer-structures](../26-timer-structures/2-summary.md)), 링 버퍼([25-ring-buffer](../25-ring-buffer/2-summary.md)), LRU([10](../10-lru-cache/2-summary.md)), 동시성 구조([29-concurrent-data-structures](../29-concurrent-data-structures/2-summary.md)).
- **쓰이는 곳(🔧)**: 장애 대응·온콜 런북의 "자료구조 원인" 갈래. 운영 영역 색인([reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md))과 OS 색인([os/37-os-symptom-index](../../os/37-os-symptom-index/2-summary.md))에서 이 노트로 내려온다.

## 적용 — 풀어나가는 법

### 1. 증상을 받으면 이 순서로

1. 원문을 모은다: 예외 전체(`Caused by` 포함), JDK 판, 그때의 n(0-1절).
2. 0절 그림에서 층을 고른다. 예외 이름이 있으면 그 절로, 없으면 지표 모양(CPU·힙·꼬리 지연·적중률)으로.
3. 그 절 결정 트리의 질문을 위에서부터 묻는다. 각 질문은 명령 하나로 답이 나오게 골랐다(2).
4. 원인 후보가 둘 이상 남으면 **둘을 가르는 관찰**을 하나 더 한다. 예: 덤프 두 장 사이에 프레임이 바뀌나.
5. leaf로 가서 처방을 읽는다. 처방이 "증상 끄기"(`catch`, `-Xss`, `-Xmx`, 재시작)뿐이면 8절을 다시 본다.

### 2. 첫 진단 명령 모음 (JDK 21)

```bash
jcmd <pid> Thread.print                  # 스레드 덤프. 2~5초 간격으로 2~3번 — 같은 줄이면 멈춤 의심, 바뀌면 진행 중 쪽(단정은 CPU 시간·코드로)
jcmd <pid> GC.class_histogram | head -30 # 무엇이 힙을 채우나 (큐·배열·엔트리 클래스가 상위인가)
jcmd <pid> GC.heap_dump /tmp/heap.hprof  # 소유자(누가 그 큐를 붙잡나)는 덤프 분석 도구에서
java -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/tmp ...   # OOM 순간을 남긴다
java -Xlog:gc*:file=gc.log ...           # resize 스파이크와 GC 정지(Humongous Allocation)가 같은 시각인가
jcmd <pid> JFR.start duration=60s filename=/tmp/rec.jfr          # CPU·할당 핫스팟
```

- 덤프를 읽는 법: `RUNNABLE`인 스레드 중 덤프마다 같은 프레임·같은 줄에 있는 것을 찾는다. `HashMap$TreeNode`·`HashMap.getNode`에 머물면 2절, `checkForComodification`이면 1절, `ArrayBlockingQueue.put`의 `WAITING`이 많으면 4절이다.
- 프로파일 절차는 [reliability/36-profiling](../../reliability/36-profiling/2-summary.md).

### 3. 증상이 "조용히" 지나가지 않게 — Java 21

1절의 건너뛰기, 4절의 드롭처럼 예외 없이 지나가는 증상은 **세는 장치**가 있어야 보인다.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.LongAdder;

final class Guards {
    // 1절: 처리 건수 대조 — 예외 대신 건수로 건너뛰기를 잡는다
    static <T> void forEachChecked(List<T> in, java.util.function.Predicate<T> keep, java.util.function.Consumer<T> work) {
        int seen = 0, done = 0, skipped = 0;
        for (T t : List.copyOf(in)) {          // 스냅숏을 돈다: work 안의 원본 수정과 순회가 겹치지 않는다 (다른 스레드가 고치면 복사도 동기화 필요)
            seen++;
            if (keep.test(t)) { work.accept(t); done++; } else skipped++;
        }
        if (seen != in.size() || seen != done + skipped)
            throw new IllegalStateException("건수 불일치 in=" + in.size() + " seen=" + seen + " done=" + done + " skipped=" + skipped);
    }

    // 4절: 상한 있는 큐 + 꽉 찼을 때의 정책(타임아웃 후 거부) + 드롭 지표
    static final BlockingQueue<Runnable> Q = new ArrayBlockingQueue<>(10_000);
    static final LongAdder DROPPED = new LongAdder();
    static boolean submit(Runnable r) throws InterruptedException {
        if (Q.offer(r, 50, TimeUnit.MILLISECONDS)) return true;
        DROPPED.increment();                   // 지표로 내보내고 경보를 건다
        return false;                          // 호출자에게 "거부"를 알린다 (조용한 드롭 금지)
    }
}
```

- 상한 10,000·대기 50ms는 예시 값이다. 값은 처리 시간·메모리 예산에서 정한다.
- `List.copyOf`는 변경 가능한 리스트를 받으면 원소 수만큼 복사한다(이미 불변 리스트면 보통 복사하지 않는다 — `List.copyOf` Javadoc). 큰 리스트를 자주 돌면 비용이 된다. 복사는 같은 스레드 안의 수정만 떼어 놓는다. 다른 스레드가 원본을 고치는 중이면 복사 자체가 깨질 수 있으므로 쓰기와 같은 락으로 복사하거나 `CopyOnWriteArrayList`를 쓴다. 단일 스레드라면 `removeIf`가 더 싸다([concurrent-data-structures](../29-concurrent-data-structures/2-summary.md) 적용 3).

## 장애 시나리오와 대처

### 1. 증상을 삼키는 처방 — `catch`·재시작·한도 올리기

- **현상**: `ConcurrentModificationException`을 `catch`해 재시도하고, `StackOverflowError`에 `-Xss`를, OOM에 `-Xmx`를 올렸다. 경보는 줄었다. 몇 주 뒤 데이터가 더 커지자 같은 증상이 더 큰 규모로 돌아온다.
- **보이는 형태**: 설정 이력에 `-Xss`·`-Xmx` 상향이 반복된다. 재시도 로그가 꾸준하다. 처리 건수가 입력 건수와 맞지 않는다.
- **원인**: 증상(예외·한도)을 없애는 것과 원인(순회 중 수정, 깊이 ∝ n, 상한 없는 큐)을 고치는 것을 혼동했다.
- **대처**: 8절의 "대신" 열로 간다. 한도를 올렸다면 그 한도가 다시 닿을 n을 계산해 적어 둔다(예: 깊이 ∝ n이면 n이 두 배가 될 때).

### 2. 같은 증상에 반대 처방 — "CPU 100% + HashMap"을 하나로 봄

- **현상**: CPU 100% 사고를 "해시 충돌 공격"으로 보고 파라미터 수 상한을 걸었다. 다음 주 공격 없이 같은 서버가 또 멈춘다.
- **보이는 형태**: 두 번째 사고의 덤프 세 장에서 같은 스레드가 `HashMap$TreeNode.root` 같은 줄에 머문다. 요청 파라미터는 평범하다.
- **원인**: 공격(덤프마다 진행)과 비동기화 공유(같은 줄에 고정)를 가르지 않았다([concurrent-data-structures 1](../29-concurrent-data-structures/2-summary.md)).
- **대처**: 2절 결정 트리의 질문 순서로 가른다 — 요청 하나의 키 수, 덤프 여러 장의 프레임 변화, 맵의 공유 여부.

### 3. 증상이 보인 곳을 원인으로 착각

- **현상**: OOM 스택 트레이스의 할당 지점(예: 응답 직렬화)을 고쳤다. OOM은 다른 할당 지점에서 다시 난다.
- **보이는 형태**: 매번 다른 줄에서 `OutOfMemoryError`. 힙 히스토그램 상위는 매번 같은 큐·같은 엔트리 클래스다.
- **원인**: OOM은 "마지막으로 할당을 시도한 곳"에서 난다. 힙을 채운 것은 다른 구조(소비가 느린 큐, 취소된 타이머)다([queue-deque 1](../04-queue-deque/2-summary.md), [timer-structures 2](../26-timer-structures/2-summary.md)).
- **대처**: 트레이스 대신 히스토그램·덤프의 소유자 사슬을 본다. 큐라면 생산·소비 속도를 같은 그래프에 놓는다.

### 4. 평균 지표로 비선형 증상을 놓침

- **현상**: 평균 지연·평균 적중률은 매주 조금씩만 나빠졌다. 어느 날 갑자기 DB가 넘친다.
- **보이는 형태**: p99·최대 지연은 이미 몇 주 전부터 용량 경계마다 튀었다. 고유 키 수가 캐시 용량에 가까워지고 있었다.
- **원인**: resize 스파이크(5절)와 적중률 절벽(6절)은 비선형이다. 평균은 "그 한 번"과 "임계 직전"을 가린다.
- **대처**: 꼬리 지표(p99·최대)와 경계까지 남은 거리(용량 대비 워킹 셋, 컬렉션 크기 대비 다음 확장 경계)를 따로 본다.

### 5. "작은 테스트에선 됐다" — 크기 경계를 시험하지 않음

- **현상**: 단위 테스트는 다 통과한다. 운영의 큰 고객 데이터에서만 `StackOverflowError`·해시 절벽·타임아웃이 난다.
- **보이는 형태**: 실패 입력의 n이 테스트 n보다 몇 자릿수 크다. 실패 입력이 정렬돼 있거나 한쪽으로 치우쳐 있다.
- **원인**: 이 영역 증상의 대부분은 "n이 경계를 넘을 때"다. 테스트가 경계 너머를 만들지 않았다.
- **대처**: 운영 최대 n과 그 두 배로 테스트한다. 최악 모양(정렬된 입력, 같은 해시의 키, 한 줄로 이은 사슬)을 테스트 데이터에 일부러 넣는다([union-find 1](../14-union-find/2-summary.md)의 "한 줄로 이은 뒤 find" 테스트처럼).

## 핵심 문장

- 이 노트는 **증상 → 층 → 흔한 원인 → 첫 진단 → leaf** 순서의 역색인이다. 고치지 않고 어느 노트로 갈지 정한다.
- 자료구조 증상은 대부분 n이 어떤 경계(스택 깊이, 버킷 길이, 용량, 워킹 셋)를 넘을 때 처음 보인다. 그래서 첫 질문은 "그때의 n은?"이다.
- 예외는 최선 노력이다. `ConcurrentModificationException`은 놓칠 수 있고 `StackOverflowError` 트레이스는 1024줄에서 잘린다. 건수 대조와 덤프 여러 장으로 보완한다.
- 같은 "CPU 100% + HashMap"도 공격·나쁜 키·공유 손상으로 갈린다. 덤프 여러 장에서 프레임이 진행하는지 멈췄는지가 가장 싼 구분이다.
- 한도(`-Xss`·`-Xmx`·용량)를 올리는 것은 경계를 미룰 뿐이다. 깊이·크기를 입력과 떼어 놓는 구조 변경이 처방이다.

## 관련 주제·근거

- 선행: 이 영역 leaf 전체([curriculum.md](../curriculum.md)). 링크 표기 `이름 k`는 각 leaf 「장애 시나리오와 대처」의 k번째 시나리오다.
- leaf 노트(이 노트가 가장 많이 가리키는 것)
  - [01-data-structures-basics](../01-data-structures-basics/2-summary.md) · [02-adt-and-cost-contracts](../02-adt-and-cost-contracts/2-summary.md) — 비용 계약
  - [01-dynamic-array](../01-dynamic-array/2-summary.md) · [02-linked-list](../02-linked-list/2-summary.md) · [03-stack](../03-stack/2-summary.md) · [04-queue-deque](../04-queue-deque/2-summary.md) · [25-ring-buffer](../25-ring-buffer/2-summary.md) — 선형 구조
  - [05-hashmap](../05-hashmap/2-summary.md) · [29-open-addressing](../29-open-addressing/2-summary.md) · [31-consistent-hashing](../31-consistent-hashing/2-summary.md) — 해시
  - [07-heap](../07-heap/2-summary.md) · [26-timer-structures](../26-timer-structures/2-summary.md) · [10-lru-cache](../10-lru-cache/2-summary.md) · [29-concurrent-data-structures](../29-concurrent-data-structures/2-summary.md) — 시스템 구조
  - [systems/thrashing](../../systems/thrashing/2-summary.md) — resize thrashing(커리큘럼 ds 28)
- 후속: [44-ds-incidents](../44-ds-incidents/2-summary.md) — 해시 성능 절벽(HashDoS 2011)과 공유 HashMap 무한 루프의 실사건
- 다른 영역 색인: [algorithm/42-alg-symptom-index](../../algorithm/42-alg-symptom-index/2-summary.md)(복잡도·정렬 계약·재귀·정규식·이진 탐색) · [reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md) · [os/37-os-symptom-index](../../os/37-os-symptom-index/2-summary.md)
- 운영 쪽 정본: [reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md) · [reliability/29-cache-stampede](../../reliability/29-cache-stampede/2-summary.md) · [reliability/34-tail-latency-and-stragglers](../../reliability/34-tail-latency-and-stragglers/2-summary.md) · [reliability/36-profiling](../../reliability/36-profiling/2-summary.md) · [reliability/37-memory-leak-and-heap-analysis](../../reliability/37-memory-leak-and-heap-analysis/2-summary.md) · [os/13-oom-and-memory-limits](../../os/13-oom-and-memory-limits/2-summary.md)
- 근거 문서
  - OpenJDK 21 `ArrayList` Javadoc — fail-fast "cannot be guaranteed", "best-effort basis"([29-concurrent-data-structures](../29-concurrent-data-structures/2-summary.md) 6절에서 인용)
  - OpenJDK 21 `HashMap.java` — `TREEIFY_THRESHOLD = 8`, `MIN_TREEIFY_CAPACITY = 64`, "Note that this implementation is not synchronized." <https://github.com/openjdk/jdk21u/blob/master/src/java.base/share/classes/java/util/HashMap.java>
  - `jcmd` 도구 문서(JDK 21) <https://docs.oracle.com/en/java/javase/21/docs/specs/man/jcmd.html>
  - 표의 수치·메시지는 각 leaf의 실험 출력과 인용을 따른다(OpenJDK 21.0.12 temurin, 2026-09-28~10-05 판). "원본 README 실측"은 그 leaf가 인용한 원고의 측정이다.
- 실험 목록
  - `SoeTrace.java` — `StackOverflowError` 트레이스 길이 대 실제 깊이. eclipse-temurin:21-jdk(OpenJDK 21.0.12), `docker run --rm --network none --cpus=2 … java SoeTrace.java` 두 번(깊이 21,667·19,972, 트레이스 1024 두 번). 같은 이미지에서 `java -XX:+PrintFlagsFinal -version`으로 `MaxJavaStackTraceDepth`·`ThreadStackSize` 기본값 확인.
  - 해시 절벽 수치(2절 2행)는 [44-ds-incidents](../44-ds-incidents/2-summary.md) 실험 A에서 옮겼다. 나머지 수치는 leaf 실험 출력에서 옮겼다(새로 돌리지 않음).
