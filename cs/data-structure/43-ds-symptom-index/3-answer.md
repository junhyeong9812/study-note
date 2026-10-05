# data-structure/43-ds-symptom-index — 정답

## 정답

### 1. 여섯 층과 "그때의 n"

- 층과 증상
  - 구조의 일관성(순회·공유): `ConcurrentModificationException`, 예외 없는 건너뛰기, 같은 줄에 멈춘 스레드.
  - 연산 비용 계약: 해시 성능 절벽(특정 요청만 CPU 100%).
  - 호출 스택: `StackOverflowError`.
  - 용량: 무한 큐 OOM, 힙 우상향.
  - 분할 상환의 "그 한 번": resize 스파이크(p99·최대만 튐).
  - 지역성 가정: 캐시 적중률 절벽.
- n을 먼저 보는 이유: 이 영역 증상의 대부분은 n이 어떤 경계를 넘을 때 처음 보인다.
  - 예 1: 균형 없는 트리에 정렬된 키를 넣으면 높이 = n이다. 원본 실측에서 1만 200개는 되고 1만 300개에서 `StackOverflowError`([persistent 1](../26-persistent/2-summary.md)). n을 모르면 "가끔 터진다"로만 보인다.
  - 예 2: LRU는 워킹 셋이 용량보다 조금 크면 적중률이 0%까지 떨어진다(용량 3·키 4개 → 0%, 용량 4 → 첫 네 번의 적재 미스 뒤 100%, [lru-cache 2](../10-lru-cache/2-summary.md)). 고유 키 수(n)와 용량을 비교해야 원인이 보인다.

### 2. CPU 100% + `HashMap`의 세 갈래

- 후보
  1. 해시 충돌 공격(HashDoS): 요청 하나의 파라미터·키가 수만 개, 같은 해시.
  2. 비동기화 `HashMap` 공유: 동시 `put`·리사이즈로 구조가 순환·손상.
  3. 나쁜 자체 키: 좁은 `hashCode` + 비`Comparable` — 공격 없이 특정 데이터에서만.
- 가르는 순서(싼 것부터)
  1. 덤프를 2~5초 간격으로 2~3장 뜬다. 같은 스레드가 **같은 줄**에 머물면 2번(멈춤)을 먼저 의심한다. 프레임이 바뀌며 진행하면 1·3번 쪽이다. 덤프는 순간 사진이라 이것만으로 단정하지 않는다 — 그 스레드의 CPU 시간·처리 건수가 느는지, 그 맵이 여러 스레드에 공유되는지 코드로 확인한다.
  2. 느린 요청의 파라미터·키 수를 본다. 수만 개면 1번이다.
  3. 키 클래스를 본다. 자체 클래스이고 `Comparable`이 아니며 `hashCode`의 서로 다른 값이 적으면 3번이다.
- 처방과 leaf
  - 1번: 요청당 파라미터·키 수 상한, 키 있는 해시(CPython) 유지, Java는 트리화 + 상한 — [hashmap 1](../05-hashmap/2-summary.md), [hash-functions 1](../../algorithm/12-hash-functions/2-summary.md), [44-ds-incidents](../44-ds-incidents/2-summary.md).
  - 2번: `ConcurrentHashMap`으로 교체. 멈춘 프로세스는 재시작 외에 풀 방법이 없다 — [concurrent-data-structures 1](../29-concurrent-data-structures/2-summary.md).
  - 3번: `hashCode`가 `equals`에 쓰는 필드를 모두 섞게 고치고, 충돌하는 서로 다른 키를 `compareTo`가 구별하게 `Comparable` 구현 — [hash-functions 2](../../algorithm/12-hash-functions/2-summary.md).

### 3. 잘린 트레이스

- 0-1 실험(OpenJDK 21.0.12, 기본 `-Xss`): 실제 깊이 21,667과 19,972인데 트레이스 프레임 수는 두 번 다 1024였다. `-XX:+PrintFlagsFinal`의 `MaxJavaStackTraceDepth = 1024 {default}`와 맞다.
- 함의
  1. 트레이스 맨 아래가 재귀의 시작점이 아니다. 실험에서도 맨 아래가 `down`이고 `main`은 없었다. 진입점은 로그·요청 ID로 찾는다.
  2. 반복되는 프레임 **묶음**을 찾는다. 하나면 직접 재귀, 둘셋이 번갈아 나오면 상호 재귀다.
- 덧붙여 `StackOverflowError`는 `Exception`이 아니므로(`instanceof Exception = false`) `catch (Exception e)`를 지나 올라간다.

### 4. fail-fast는 최선 노력

- `ArrayList` 반복자는 `next()`에서 수정 횟수(`modCount`)를 확인한다.
- `b`(중간)를 지우면 다음 `next()`가 불리고 수정을 발견해 예외를 던진다.
- `c`(끝에서 두 번째)를 지우면 크기가 3이 되고 커서도 3이다. `hasNext()`가 `false`라 `next()`가 불리지 않는다. 검사 지점에 닿지 않아 예외 없이 끝나고 `d`는 처리되지 않는다(실험 출력 `[a, b, d]`, [concurrent-data-structures](../29-concurrent-data-structures/2-summary.md) 6절).
- 그래서 정확성은 예외가 아니라 **삭제 방식과 건수 대조**로 지킨다. 단일 스레드는 `Iterator.remove`·`removeIf`, 처리 건수 = 입력 건수 확인(적용 3의 `forEachChecked`).

### 5. OOM 지점 ≠ 원인

- OOM은 마지막으로 할당을 시도한 곳에서 난다. 힙을 채운 구조는 다른 곳일 수 있다. 그 줄을 고쳐도 다음 할당 지점에서 또 난다.
- 볼 것: `jcmd <pid> GC.class_histogram` 상위, 힙 덤프의 소유자 사슬, 큐 길이·생산률·소비률 추세.
- 의심할 갈래(4절)
  - 소비 < 생산인 상한 없는 큐([queue-deque 1](../04-queue-deque/2-summary.md))
  - 취소한 타이머가 남음 — STPE 기본 `removeOnCancel=false`([timer-structures 2](../26-timer-structures/2-summary.md), [heap 2](../07-heap/2-summary.md))
  - `add`만 하는 배열, 지운 칸의 참조([dynamic-array 2·3](../01-dynamic-array/2-summary.md)), 개수 기준 캐시 용량([lru-cache 4](../10-lru-cache/2-summary.md))
- 상한을 두면 증상이 OOM → 멈춤(블로킹, 덤프에 `ArrayBlockingQueue.put` `WAITING`) → 드롭(오류 없이 데이터가 빔)으로 바뀐다. 어느 쪽을 고를지는 데이터의 성격으로 정하고, 드롭이면 카운터를 지표로 낸다([ring-buffer 1·2](../25-ring-buffer/2-summary.md)).

### 6. 평균이 가리는 두 증상

- p99만 튐 — resize 스파이크
  - 갈래: 크기가 일정 배율(두 배, `ArrayList`는 약 1.5배)로 커질 때마다 튀면 확장 복사, 경계 근처에서 계속 튀면 확장·축소 경계가 붙은 thrashing, GC 로그에 `G1 Humongous Allocation`이 같이 찍히면 큰 배열 할당 + GC.
  - 첫 진단: 튀는 시점의 컬렉션 크기, `-Xlog:gc`의 같은 시각 정지.
- 어느 날 DB가 넘침 — 적중률 절벽
  - 갈래: 배치 시각에만이면 스캔 오염([lru-cache 1](../10-lru-cache/2-summary.md)), 임계를 넘은 뒤 계속이면 워킹 셋 > 용량([lru-cache 2](../10-lru-cache/2-summary.md)).
  - 첫 진단: 기간별 고유 키 수 대 용량, 접근 로그로 그린 용량-적중률 곡선.
- 평균이 가리는 이유: 확장은 n번 중 한 번만 비싸서 평균에 거의 안 보인다. 적중률은 용량 근처에서 0%와 100% 사이로 급변하므로, 임계 직전까지 평균이 거의 안 변한다(해석).

### 7. 같은 해시 키 32,768개

- 실험 A(OpenJDK 21.0.12, `--cpus=2`, 집필 두 번): `String` 키 68 ms·51 ms, 같은 `hashCode`의 비`Comparable` 키 32,101 ms·31,737 ms. 같은 개수의 보통 키는 13 ms·11 ms. 사실 점검 재실행 두 번은 `String` 46·64 ms, 비`Comparable` 32,688·35,324 ms, 보통 키 12·17 ms였다(시간은 실행마다 다르다).
- 갈리는 이유: JDK 8+ `HashMap`은 한 버킷이 8개를 넘고 표가 64칸 이상이면 버킷을 레드-블랙 트리로 바꾼다(JEP 180). 트리는 같은 해시의 키를 `compareTo`로 가른다. `String`은 `Comparable`이고 서로 다른 문자열의 `compareTo`가 0이 아니라 O(log n)으로 찾는다. 비`Comparable` 키도 트리는 만들어지지만(클래스 이름·`identityHashCode`로 동률 깨기), 찾을 때 방향을 정할 수 없어 `TreeNode.find`가 양쪽 서브트리를 다 뒤진다. 삽입 하나가 O(n), 전체가 O(n²)이다(측정 비율이 4배를 넘는 것은 상수 영향으로 보인다 — [44-ds-incidents](../44-ds-incidents/2-summary.md) 실험 A 해석).
- 교훈: 자체 키 클래스는 `hashCode`가 `equals`에 쓰는 필드를 모두 섞게 하고(`Objects.hash`, `record`), 가능하면 충돌하는 서로 다른 키를 구별하는 `Comparable`을 구현한다. 키가 외부에서 오면 개수 상한을 둔다.

### 8. 공통 패턴과 기록

- 공통 패턴: **증상을 끄는 처방(삼키기·한도 올리기·증설·감)과 원인을 고치는 처방(구조·정책·측정)을 구분하라.** 여섯 항목 모두 왼쪽 열이 경계를 미루거나 신호를 지운다.
- 한도를 올렸다면 남길 것
  - 올린 값과 이유, 그때의 n과 증상 원문
  - 그 한도에 다시 닿을 n의 계산(예: 깊이 ∝ n이면 n이 두 배일 때)과 그때 볼 지표
  - 원인 처방(명시적 스택·상한 있는 큐·초기 용량)으로 바꿀 작업 항목과 기한
