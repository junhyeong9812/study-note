# cs/issue/data/boundary-arithmetic — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **오프셋 무시 상한.** `start`에서 시작하면 복사 가능한 양은 `src.length - start`다. `min(length, src.length)`는 이미 건너뛴 `start`만큼을 빼지 않아, `start > 0`이고 `length`가 크면 **배열 끝을 넘어** 읽는다(청크 단위로 긴 텍스트를 읽는 소비자에서 재현).\
   고침: `min(length, src.length - start)`.\
   `max(0, …)`로 감싸 무효 입력(`start > src.length`)을 0으로 자르는 것은 선택하지 않았다 — 계약상 그건 **예외가 맞는 입력**이고, 조용히 0을 돌려주면 호출자 버그를 숨기는 또 다른 버그가 된다.

2. **int overflow 페이지네이션.** 32비트 int 곱셈은 경고 없이 2의 보수로 **감긴다**(wrap). 아주 큰 page에서 `(page-1)*size`가 음수가 되고, `min(offset, size)`는 상한만 막으므로 음수를 그대로 통과시켜 **음수 인덱스 접근 → 500**이 된다.\
   고침: long으로 계산한 뒤 `[0, rows.size()]` **양쪽** clamp.
   > **wrap-around** — 고정폭 정수가 표현 범위를 넘으면 반대쪽 끝으로 돌아가는 것. 예외가 나지 않는다.

3. **합산 overflow → fail-open.** 부호 있는 정수 합이 overflow하면 **음수**가 된다. "lease ≥ 합" 검사에서 합이 음수면 작은 lease도 통과한다 — 가장 위험한 입력이 검사를 우회하는 fail-open.\
   고침: **각 항을 먼저 범위 검증**(개별 상한)하고 나서 합산·비교한다.\
   이 검증 설계는 실제로 작동했다 — 한 단계 사이클(12분)이 lease(6분)보다 길어 기동이 거부됐고, lease를 13분으로 올렸다.

4. **허용 설정 = 분모.** `initial = 0`은 "지연 없이 시작"으로 허용된 설정인데, jitter 계산의 분모로 쓰이면 정수 나눗셈이 **0으로 나누기 예외**를 낸다. `initial = 0, jitter = 0`은 jitter 항이 계산되지 않아 정상이었기 때문에 조합 경계에서만 드러났다.\
   고침: `initial > 0 ? interval / initial : 1`. 허용 범위에 0이 포함된 값이 분모로 가는 곳은 모두 0 분기가 필요하다.

5. **separator와 같은 키.** B+tree에서 separator는 **오른쪽 서브트리의 최소 키**이므로 `key == separator`는 오른쪽으로 가야 한다.\
   `when`의 첫 분기가 `slot == 0 → 가장 왼쪽 자식`이면, 첫 separator와 **같은** 키가 일치 검사에 도달하기 전에 왼쪽으로 보내져 조회가 null을 반환한다(split 이후에만 드러남). 일치 분기를 가장 먼저 두어야 한다.
   > **separator** — B+tree 내부 노드에서 자식 구간을 가르는 키. 보통 오른쪽 자식 구간의 첫 키.

6. **스냅샷 길이 + 가변 버퍼 삭제.** 루프 범위는 스냅샷(불변 문자열)의 길이로 고정돼 있는데, 삭제는 가변 원본에서 하니 삭제할 때마다 원본은 한 칸 줄고 인덱스는 계속 증가한다. **같은 문자가 3개 이상 연속**될 때 두 번 이상 지워져 결국 범위를 넘는다(대량 색인 중 일부 문서만 실패).\
   역방향 순회는 뒤에서 지우므로 **아직 방문하지 않은 앞쪽 인덱스가 밀리지 않는다**. 또는 별도 결과 빌더에 쓰는 방법도 있다.

7. **좌표계 혼용이 숨는 이유.** `"a,b,c"`를 split한 배열의 i와 원 문자열의 i는 다른 좌표다(i=1이면 배열은 `b`, 문자열은 `,`). 짧은 입력에서는 엉뚱한 문자를 읽어도 분기가 대충 맞거나 범위 안이라 **예외 없이** 지나가고, 길이가 길 때만 범위를 넘는다.\
   다중 편집에서도 "삽입은 항상 기준점 위(파일 머리)"라는 암묵 가정이 대부분 맞아, 삽입이 뒤에 오는 경계에서만 커서가 overshoot한다.\
   공통점: 경계 조건이 드물게 나타나 테스트와 일상 사용을 통과한다.

## 문제 구조 (추상화 코드)

### 변형 A — 오프셋을 무시한 복사 길이

```java
// 문제
length = Math.min(length, src.length);                 // start 만큼 덜 뺌
System.arraycopy(src, start, dst, dstStart, length);   // 뒤로 넘쳐 읽음

// 고침
length = Math.min(length, src.length - start);         // 무효 start 는 계약대로 예외
```
무엇이 깨졌나: 긴 텍스트를 청크로 읽는 호출에서 배열 범위 초과 예외가 났다.

### 변형 B — 정수 overflow (곱셈·합산)

```java
// 문제 1: 곱셈 wrap + 상한만 clamp
int from = Math.min((page - 1) * size, rows.size());   // 음수 통과 → get(음수)
// 고침
long offset = (long) (page - 1) * size;
int from = (int) Math.min(Math.max(offset, 0), rows.size());
```

```go
// 문제 2: 합이 음수로 뒤집혀 하한 검증 통과
if lease < a + b + c + slack { return errRefuse }       // 거대한 a → 합 < 0 → 통과
// 고침: 항별 선검증 후 합산
for _, d := range []time.Duration{a, b, c} { if d < 0 || d > maxStep { return errRefuse } }
if lease < a + b + c + slack { return errRefuse }
```
무엇이 깨졌나: 아주 큰 page로 500이 났고(리뷰 권고 단계), 거대한 duration 설정이 lease 하한 검증을 우회할 수 있었다(리뷰 3루프에서 발견, 다른 컴포넌트에도 같은 형태 — 개별 검증 전 합산).\
같은 구조: 테스트 데이터 키를 `(i * 큰 상수) % n`으로 만들다 곱이 int를 넘쳐 기대보다 적은 키만 생성됨 → 곱수를 작은 소수로 교체.

### 변형 C — 허용된 설정이 분모가 됨

```java
// 문제
long j = jitter * (interval / initial);                 // initial = 0 허용 → / by zero
// 고침
long j = jitter * (initial > 0 ? interval / initial : 1);
```
무엇이 깨졌나: "0 지연 + jitter" 조합에서 다음 백오프 계산이 예외를 던졌다.

### 변형 D — 비교 분기 순서 (같음의 방향)

```kotlin
// 문제: slot == 0 이 먼저 → separator 와 같은 키가 왼쪽으로
val child = when {
    slot == 0 -> node.leftmost
    node.keyAt(slot) == key -> node.valueAt(slot)
    else -> node.valueAt(slot - 1)
}
// 고침: 일치 검사를 먼저 (separator = 오른쪽 서브트리 최소 키)
val child = when {
    slot < node.keyCount && node.keyAt(slot) == key -> node.valueAt(slot)
    slot == 0 -> node.leftmost
    else -> node.valueAt(slot - 1)
}
```
무엇이 깨졌나: split 후 첫 separator와 같은 키 조회가 null을 반환했다(재오픈 후에도). 이 결함을 되살리는 변형 테스트가 3개 실패로 잡히게 고정.

### 변형 E — 좌표계 혼용 (스냅샷 vs 가변 버퍼, 배열 vs 원 문자열, 편집 기준점)

```java
// 문제 1: 스냅샷 길이로 순회, 삭제는 원본에서
String snap = buf.toString();
for (int j = 0; j < snap.length() - 1; j++)
    if (snap.charAt(j) == snap.charAt(j + 1)) buf.deleteCharAt(j);   // 3연속 이상에서 범위 초과
// 고침: 원본을 역방향으로
for (int j = buf.length() - 1; j > 0; j--)
    if (buf.charAt(j) == buf.charAt(j - 1)) buf.deleteCharAt(j);

// 문제 2: split 배열 인덱스로 원 문자열 읽기
String[] parts = s.split(",");
for (int i = 0; i < parts.length; i++) if (isUpper(s.charAt(i))) ...   // 구분자를 읽음
// 고침: split 후엔 배열만
for (int i = 0; i < parts.length; i++) if (!parts[i].isEmpty() && isUpper(parts[i].charAt(0))) ...
```

```ts
// 문제 3: 삽입 위치가 기준점 뒤인데도 커서 이동, 빈 prefix 절단
const shift = ins ? ins.insert.length : 0;
const prefix = pkg.slice(0, -1);                 // 패키지 없는 파일에서 이름이 잘림
// 고침: 기준점 앞일 때만 이동, 빈 prefix 는 삽입 생략
const shift = ins && ins.from <= from ? ins.insert.length : 0;
const ins = pkg ? buildImport(pkg, name) : null;
```
무엇이 깨졌나: 대량 색인에서 수백 건 문서만 범위 초과로 누락됐고, 자동 삽입이 잘린 이름을 넣거나 커서를 지나치게 옮겼다.

### 변형 F — 부동소수 누적과 센티넬 산술

```java
// 문제
double tokens = 0; for (...) tokens += 0.1;            // 100회 = 9.999999999999998
long deadline = NO_DEADLINE ? Long.MAX_VALUE : now + t;
if (deadline - System.nanoTime() <= 0) giveUp();       // 단조 시계 원점이 임의 → MAX 와의 산술이 의미를 잃음
int idx = hash % cap;                                  // 음수 해시 → 음수 인덱스

// 고침
long milli = 0; for (...) milli += 100;                // 정수 고정소수점(1/1000 단위)
if (deadline != NO_DEADLINE && deadline - System.nanoTime() <= 0) giveUp(); // 센티넬은 분기로
int idx = Math.floorMod(hash, cap);
```
무엇이 깨졌나: 예산 계산이 경계에서 틀어졌고, "데드라인 없음"인데도 시각 값이 크면 포기했으며, 확률 자료구조(블룸 필터)의 `%`가 음수 인덱스를 만들었다.\
정정 기록: `abs(MIN_VALUE)`는 음수지만 용량이 2의 거듭제곱이면 나머지가 0이라 "우연히" 사고가 안 난다 — 안전해서가 아니라 운이다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
