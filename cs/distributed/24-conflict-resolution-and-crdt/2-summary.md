# distributed/24-conflict-resolution-and-crdt — LWW·버전 벡터·CRDT — 정리 (힌트)

## 해결하는 문제

여러 복제본이 각자 쓰기를 받으면(다중 리더·리더리스), 같은 키에 서로 모르는 쓰기가 생긴다. 어느 값을 남길지 정해야 한다.

```text
  복제본 A: 주소 = 서울  (B의 쓰기를 모른 채)
  복제본 B: 주소 = 부산  (A의 쓰기를 모른 채)
        ── 동기화 ──>  ?
  ① 하나만 남긴다(LWW)    ② 둘 다 남겨 사람·앱이 고른다(형제)    ③ 자료형이 정한 규칙으로 합친다(CRDT)
```

- 이 노트의 질문: "동시인 두 쓰기를 어떻게 정리하나". 동시인지 알아내는 법은 05번(벡터 시계)이다.
  - *충돌(conflict)*: 같은 데이터에 대해 서로를 모르는(동시) 쓰기가 두 개 이상 있는 상태.

쉬운 예: 가족 공유 장보기 목록.
- 엄마는 "우유"를 지우고, 아빠는 같은 순간 "우유"를 다시 넣었다.
- 둘 중 하나만 살리면 누군가의 의도가 사라진다. "넣기가 이긴다" 같은 규칙을 정해 두면 모두 같은 목록을 본다.

똑같은 구조다.\
규칙이 자료의 뜻에 맞으면 조율 없이 수렴하고, 안 맞으면 조용히 데이터를 잃는다.

실무 예:
- Cassandra는 컬럼마다 타임스탬프가 큰 쓰기가 이긴다(LWW). 노드 시계가 앞서 있으면 "옛 쓰기"가 이긴다.
- Amazon Dynamo 장바구니는 동시 버전을 모두 돌려주고 앱이 합집합으로 합쳤다. 그래서 지운 상품이 되살아날 수 있었다(DeCandia 외 2007).
- 좋아요 수·온라인 접속자 집합·공동 편집 문서(33번)는 CRDT로 합친다.

## 동작·원리

### 1. LWW(last-writer-wins) — 하나만 남긴다

```text
  실제 순서:  A가 1000ms에 blue 씀 ──(B가 그것을 읽음)──> B가 1050ms에 green 씀
  B 시계가 100ms 느림 → B의 타임스탬프 950
  LWW 병합: max(1000 blue, 950 green) = blue      ← 나중 쓰기(green)가 졌다
```

- 규칙: 값마다 타임스탬프(+ 동률 깨기용 노드 id)를 붙이고 큰 쪽을 남긴다. 병합이 교환·결합·멱등이라 수렴은 한다.
- 대가 두 가지
  - **동시 쓰기 중 하나가 흔적 없이 사라진다.** 실패 응답도 없다.
  - **시계가 틀리면 인과적으로 나중인 쓰기도 진다.** 위 그림이 그 경우다.
- Cassandra 5.0 문서(Dynamo 아키텍처): 모든 변경(삭제 포함)에 타임스탬프를 붙이고 최신이 이긴다. 타임스탬프는 클라이언트가 주거나, 없으면 코디네이터 노드 시계다. "정확성이 시계에 의존하니 NTP를 돌려라". 컬럼마다 따로 LWW라서 CQL 행 단위로 보면 LWW-Element-Set CRDT라고 문서가 부른다.
  - *코디네이터*: 클라이언트 요청을 받아 복제본들에 전달하는 노드.

### 2. 버전 벡터 + 형제 — 둘 다 남긴다

```text
  v0 {A:1}  ─┬─ A가 고침 → vA {A:2}
             └─ B가 고침 → vB {A:1, B:1}
  vA vs vB: 서로 큰 칸이 있음 → CONCURRENT → 둘 다 보존(형제, siblings)
  읽는 쪽이 [vA, vB]를 받아 합친 뒤 씀 → vM {A:2, B:2}  → vA·vB 둘 다 대체(AFTER)
```

- 복제본마다 칸을 둔 벡터(버전 벡터)를 값에 붙인다. 05번의 벡터 비교로 "덮어써도 되는지(BEFORE)"와 "동시(CONCURRENT)"를 가린다.
  - *형제(siblings)*: 동시라서 어느 쪽도 버릴 수 없어 함께 저장된 여러 버전.
- 읽을 때 형제를 모두 받아 **앱이 합치고**, 합친 값을 두 벡터의 칸별 max(+ 자기 칸 +1)로 다시 쓴다.
- Dynamo(2007): 장바구니가 이 방식이다. 합치기가 합집합이라 "담기"는 사라지지 않지만 **지운 상품이 되살아날 수 있다**고 논문이 적는다. 24시간 측정에서 요청의 99.94%가 버전 1개를 봤다.
- Riak KV: 버킷 타입의 `allow_mult=true`면 CRDT가 아닌 쓰기의 동시 갱신에서 형제를 만든다. `false`면 형제를 클라이언트에 돌려주지 않고 Riak이 하나를 고른다(내부에선 버전 벡터를 계속 쓰고 형제가 생길 수도 있다). 쓰기 때 이력을 무시하고 늦은 타임스탬프로 덮어쓰는 진짜 LWW는 별도 속성 `last_write_wins=true`다(Riak KV 2.2 "Conflict Resolution"). 문서는 `true`를 권하고, 2.0부터 형제 수를 줄이는 dotted version vector를 권한다.

### 3. CRDT — 자료형이 합치는 규칙을 가진다

```text
  상태 기반(CvRDT)                         연산 기반(CmRDT)
  복제본 상태 전체(또는 델타)를 보낸다          연산을 보낸다
  merge = 최소 상계(join)                     동시 연산끼리 교환 가능해야 한다
  교환·결합·멱등 → 중복·순서 뒤바뀜 무해          전달은 인과 순서(causal delivery)·정확히 한 번 처리 필요
```

- Shapiro 외(2011)의 정의
  - *강한 최종 일관성(SEC)*: 같은 갱신들을 받은 정상 복제본은 **곧바로** 같은 상태다(최종 일관성 + strong convergence). 충돌 후 되돌리기(rollback)나 합의가 필요 없다.
  - 상태 기반: 상태 집합이 *반격자(join semilattice)*를 이루고, 갱신이 상태를 단조 증가시키고, merge가 최소 상계(LUB)를 계산하면 SEC다(Theorem 2.1, 최종 전달·종료 가정). LUB는 정의상 교환·결합·멱등이다.
    - *반격자*: 임의의 두 원소에 "둘 다보다 크거나 같은 것 중 가장 작은 것(최소 상계)"이 있는 부분 순서.
  - 연산 기반: 인과 순서 전달을 가정하고 동시 연산이 교환 가능하면 SEC다(Theorem 2.2).
- 두 방식은 서로 흉내 낼 수 있다(같은 논문 §3).

### 4. 대표 CRDT

```text
  G-Counter   노드별 칸 {A:3, B:5, C:2}     merge = 칸별 max     값 = 합 10
  PN-Counter  G-Counter 두 개 (P, N)         값 = ΣP − ΣN
  2P-Set      추가 집합 A + 삭제 집합 R(툼스톤)  한 번 지운 원소는 다시 못 넣음 → 삭제 승
  LWW-Element-Set  원소별 (add 시각, remove 시각)  큰 쪽이 이김 → 시계 의존
  OR-Set      add마다 고유 태그, remove는 "본" 태그만 지움 → 동시 add/remove면 add 승
```

- OR-Set 동작

```text
  A: add(사과)#A:1 ──동기화──> B
  B: remove(사과) → 본 태그 {A:1}을 지움
  A: (동시에) add(사과)#A:2
  병합: 태그 {A:1, A:2} − 지움 {A:1} = {A:2} → 사과 있음
```

- 비용: 상태 기반 OR-Set은 지운 태그(툼스톤)를 들고 있어야 늦게 온 옛 add가 되살아나지 않는다. Shapiro 외 TR(2011)의 연산 기반 OR-Set은 인과 전달을 가정해 툼스톤 없이 설명되고, Bieniusa 외(2012) "An optimized conflict-free replicated set"는 버전 벡터로 툼스톤을 없앤다.
  - *툼스톤(tombstone)*: "지웠다"는 기록. 지운 값 대신 남겨 두는 표식.

### 실험: LWW 유실, 버전 벡터, G-Counter·PN-Counter·OR-Set 병합

- 코드: `Crdt.java`(핵심만). LWW·버전 벡터 비교·G-Counter·PN-Counter·OR-Set·LWW 원소 집합을 각각 몇 줄로 구현했다.

```java
GCounter merge(GCounter o) {                       // 칸별 max = 최소 상계
    GCounter r = new GCounter(); r.p.putAll(p);
    o.p.forEach((k, v) -> r.p.merge(k, v, Math::max)); return r;
}
void remove(String e) { removed.addAll(adds.getOrDefault(e, Set.of())); }   // OR-Set: 지금 본 태그만
```

(실험, eclipse-temurin 21 JDK 컨테이너, 2026-10-01)

```text
== 1. LWW: 시계가 어긋난 두 노드의 쓰기 ==
A=Lww[value=blue, ts=1000, node=A]  B=Lww[value=green, ts=950, node=B]  → 병합 결과 blue (실제로 나중 쓰기는 green)
동시 쓰기 주소=서울 / 주소=부산 → 주소=부산 (다른 하나는 흔적 없이 사라짐)

== 2. 버전 벡터: 덮어쓰기 vs 형제 보존 ==
v0 vs vA: BEFORE  (덮어써도 됨)
vA vs vB: CONCURRENT  (둘 다 보존 → 형제)
vM vs vA: AFTER, vM vs vB: AFTER  (합친 값이 둘 다를 대체)

== 3. G-Counter: 어떤 순서·중복으로 합쳐도 같다 ==
1000가지 순서(중복 포함) 병합 결과 집합: [10]  상태 {A=3, B=5, C=2}
같은 칸 A를 두 인스턴스가 씀: 4 + 6 = 10이어야 하지만 병합 값 6
나이브 합(중복 포함 5개 상태를 더함): 18  (참값 10)
PN-Counter: A(+10−3) ⊔ B(+2−4) = 5, 반대 순서 5, 자기 자신과 다시 병합 5

== 4. OR-Set: 동시 add/remove는 add가 이긴다 ==
A=[사과] B=[] → 병합(A,B)=[사과] 병합(B,A)=[사과]
같은 상황을 LWW 원소 집합으로(add=105, remove=110): []
add/remove 1000회 반복: 원소 0개, 태그+툼스톤 2000개
```

- 관찰
  - LWW: B 시계가 100ms 느려 인과적으로 나중인 green이 졌다. 동시 쓰기에서는 서울이 에러 없이 사라졌다.
  - G-Counter: 상태 5개(중복 2개 포함)를 1000가지 순서로 합쳐도 결과는 10 하나. 더하기로 합치면 18이 된다.
  - 같은 칸(A)을 두 인스턴스가 쓰면 max가 한쪽 증가(4)를 삼킨다. 칸의 주인은 유일해야 한다.
  - OR-Set은 양쪽 병합 순서와 무관하게 [사과]. 같은 상황을 시계 기반 LWW 원소 집합으로 풀면, 다시 담은 쪽 시계가 느려 사과가 사라졌다.
  - 툼스톤: 이 구현(상태 기반, 정리 없음)은 원소 0개에 태그·툼스톤 2000개를 들고 있다.

## 쓰이는 자료구조·알고리즘

- **반격자와 최소 상계(join)** — 칸별 max, 집합 합집합. 교환·결합·멱등이 정의에서 나온다.
- **벡터 시계·버전 벡터** — 동시 판정. [05-logical-clocks](../05-logical-clocks/2-summary.md)
- **노드 → 카운터 맵** — G-Counter. 벡터 시계와 모양이 같고 읽는 법(합)만 다르다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **고유 태그(노드, 순번)** — OR-Set의 add 식별. 13번의 (worker, 순번)과 같은 생각.
- **툼스톤** — LSM 삭제 표식과 같은 개념. [data-structure/24-lsm-tree](../../data-structure/24-lsm-tree/2-summary.md) · [database/38-lsm-storage-engine](../../database/38-lsm-storage-engine/2-summary.md)
- **Merkle 트리** — 복제본 간 차이를 빨리 찾는 anti-entropy(09번). [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 자료의 뜻으로 해결 방식을 고른다

| 자료 | 동시 쓰기의 올바른 결과 | 방식 |
|---|---|---|
| 조회수·좋아요 | 증가분을 모두 더한 값 | G-Counter / PN-Counter |
| 태그·장바구니·접속자 | 넣기와 빼기 중 정한 쪽이 이김 | OR-Set(add 승) / 2P-Set(삭제 승) |
| 프로필 사진 하나 | 하나만 남아도 괜찮음 | LWW(시계 신뢰 조건) |
| 주소·메모처럼 둘 다 의미 있는 값 | 사람이 고르거나 앱이 합침 | 버전 벡터 + 형제 |
| 잔액·재고(0 미만 금지) | 불변식을 지켜야 함 | PN-Counter로 불가 → 합의·단일 리더(11번), 또는 차감 권한을 미리 나눠 주는 bounded counter |

- 잔액이 안 되는 이유: PN-Counter는 두 복제본이 각자 "잔액 100에서 70 차감"을 허용하면 합쳐서 −40이 된다. 동시 갱신을 합치는 규칙은 있어도 "0 미만 금지" 같은 전역 조건을 지킬 수단이 없다.
- 예외: *bounded counter*(Balegas 외 2015)는 "차감할 수 있는 권한"을 복제본에 미리 나눠 준다(escrow 발상). 자기 몫 안의 차감은 합의 없이 처리하고, 몫이 모자라면 거절하거나 다른 복제본에서 권한을 넘겨받는다. 그래서 하한을 지킨다.

### 2. Java — 형제를 받아 합치는 읽기-수정-쓰기

```java
// 저장소가 형제를 돌려주는 API라고 가정 (Riak 클라이언트·직접 구현한 버전 벡터 저장소 등)
Versioned<Cart> read = store.get(key);                 // values: [cart1, cart2], context: 합쳐진 버전 벡터
Cart merged = read.values().stream()
        .reduce(Cart.empty(), Cart::union);            // 앱 규칙: 장바구니는 합집합
merged = merged.add(item);                             // 이번 수정
store.put(key, merged, read.context());                // 받은 context를 함께 보내야 두 형제를 대체한다
```

- `context`(버전 벡터)를 빼고 쓰면 저장소는 새 쓰기를 또 하나의 동시 버전으로 보고 형제를 늘린다.

### 3. 진단

```sql
-- Cassandra(CQL): 컬럼마다 이긴 쓰기의 타임스탬프(µs)를 본다
SELECT id, address, WRITETIME(address) FROM users WHERE id = ?;
-- 미래 시각이면 시계가 앞선 노드·클라이언트가 쓴 것이다. 그 뒤의 정상 쓰기는 모두 진다.
```

- Riak: 읽기 결과의 형제 수를 지표로 남긴다. 계속 늘면 context 없이 쓰는 경로가 있다.
- CRDT 라이브러리: 상태 크기(직렬화 바이트)와 툼스톤 수를 지표로 낸다.

## 장애 시나리오와 대처

### 1. LWW → 동시 쓰기의 조용한 유실 (커리큘럼 ⚠)

- **현상**: 두 사용자가 거의 동시에 같은 레코드를 고쳤고, 한쪽 수정이 사라졌다. 둘 다 성공 응답을 받았다.
- **보이는 형태**: 에러·로그 없음. 진 쪽 값은 어디에도 남지 않는다. 실험의 `주소=서울 / 주소=부산 → 주소=부산`.
- **원인**: LWW는 동시인 두 값 중 하나를 버리는 규칙이다. 동시 감지 자체를 하지 않는다.
- **대처**
  - 잃으면 안 되는 필드는 버전 벡터 + 형제, 또는 자료에 맞는 CRDT로 바꾼다.
  - 값을 불변으로 만든다(갱신 대신 새 키로 추가). 덮어쓰기가 없으면 버릴 쓰기도 없다.
  - 한 키를 한 곳에서만 쓰게 라우팅한다(키 단위 단일 리더).

### 2. 시계 어긋남 → 최신 쓰기가 짐 (커리큘럼 ⚠)

- **현상**: 방금 고친 값이 저장되지 않는다. 다시 고쳐도 옛 값이 남는다. 특정 노드·클라이언트 쪽에서만 재현된다.
- **보이는 형태**: Cassandra `WRITETIME()`이 현재보다 미래인 값이 있다. 그 컬럼에 대한 이후 쓰기가 모두 무시된다. 실험 1의 `blue`가 이긴 모양.
- **원인**: LWW 타임스탬프는 벽시계다. 앞선 시계로 쓴 값은 그 시각이 될 때까지 모든 쓰기를 이긴다. 느린 시계의 쓰기는 인과적으로 나중이어도 진다.
- **대처**
  - NTP 감시와 노드 시계 오프셋 알람(04번).
  - 클라이언트 타임스탬프를 쓰면 클라이언트 시계까지 감시 대상이다. 가능하면 서버 측 한 곳에서 매긴다.
  - 인과가 중요한 필드는 HLC(26번)나 버전 벡터로 순서를 정한다.

### 3. 지운 항목이 되살아남

- **현상**: 장바구니에서 지운 상품이 다시 나타난다.
- **보이는 형태**: 형제를 합집합으로 합친 직후. 또는 툼스톤을 정리한 뒤 오래 끊겼던 복제본이 옛 데이터를 다시 퍼뜨렸다.
- **원인**: 합집합 병합은 삭제를 표현하지 못한다(Dynamo 논문이 명시). 툼스톤 없이 지우면 늦게 온 옛 add가 이긴다.
- **대처**: 삭제를 표현하는 자료형(OR-Set·2P-Set)을 쓴다. 툼스톤 정리는 모든 복제본이 그 삭제를 받은 것이 확인된 뒤에만 한다. Cassandra 5.0은 툼스톤마다 유예 기간 `gc_grace_seconds`(기본 864000초 = 10일)를 두고, 그보다 오래 끊겼던 노드가 돌아와 지운 데이터를 다시 퍼뜨리는 것을 "zombie"라 부른다. 유예 기간은 응답 없던 노드가 회복해 툼스톤을 정상 처리할 시간이다(Cassandra 문서 Tombstones). 노드가 그보다 오래 끊겨 있었다면 다시 합류시키기 전에 따로 조치해야 한다.

### 4. 형제·툼스톤 누적 → 크기·지연 증가

- **현상**: 특정 키의 읽기가 점점 느려지고 응답이 커진다.
- **보이는 형태**: 형제 수가 수십 개, CRDT 상태가 실제 원소보다 훨씬 크다. 실험의 `원소 0개, 태그+툼스톤 2000개`.
- **원인**: 버전 context 없이 쓰는 클라이언트, 정리 규칙이 없는 상태 기반 OR-Set.
- **대처**: 쓰기에 항상 읽은 context를 붙인다. Riak은 dotted version vector를 쓴다. 툼스톤 없는 최적화 OR-Set(Bieniusa 외 2012)이나 델타 CRDT를 검토한다.

### 5. 칸 주인(actor id) 중복 → 증가분 유실

- **현상**: 이미지 복제로 인스턴스를 늘린 뒤 카운터가 실제보다 작다.
- **보이는 형태**: 두 인스턴스가 같은 노드 칸을 올린다. 실험의 `4 + 6 = 10이어야 하지만 병합 값 6`.
- **원인**: G-Counter의 칸 하나 = 주인 하나라는 전제가 깨졌다. max가 한쪽을 삼킨다.
- **대처**: actor id를 인스턴스 기동 때 새로 발급한다(13번 worker ID 배정과 같은 문제).

## 핵심 문장

- 동시 쓰기를 푸는 방법은 셋이다: 하나만 남기기(LWW), 둘 다 남기기(형제), 규칙으로 합치기(CRDT).
- LWW는 수렴은 하지만 동시 쓰기 중 하나를 에러 없이 버리고, 시계가 틀리면 인과적으로 나중인 쓰기도 버린다.
- 버전 벡터는 동시를 감지해 형제로 남긴다. 합치는 책임은 앱에 있고, 합집합 병합은 삭제를 되살린다.
- 상태 기반 CRDT는 반격자 위의 최소 상계로 합치므로 순서·중복과 무관하게 같은 상태가 된다(SEC).
- CRDT는 합치는 규칙이 자료의 뜻과 맞을 때만 쓴다. "0 미만 금지" 같은 전역 불변식은 단순 PN-Counter로는 못 지킨다. 합의·단일 리더로 직렬화하거나, 권한을 미리 나누는 bounded counter를 쓴다.

## 관련 주제·근거

- 기초: [ops-patterns/15-crdt](../../ops-patterns/15-crdt/2-summary.md) — NaiveCounter·GCounter·OrSet 구현과 성질 테스트. 이 노트는 LWW·버전 벡터·형제, 제품(Cassandra·Riak·Dynamo) 동작, 장애·진단, 실험을 보탠다.
  - 참고: 원본은 OR-Set이 "지운 태그를 영원히 들고 있어야 한다"고 쓴다. 정리 규칙 없는 상태 기반 구현에서는 맞지만, 인과 전달을 가정한 연산 기반 OR-Set(Shapiro 외 TR 2011 §3.3.5)과 버전 벡터로 툼스톤을 없앤 최적화 OR-Set(Bieniusa 외 2012)이 있다.
- 선행: [05-logical-clocks](../05-logical-clocks/2-summary.md), [06-replication-strategies](../06-replication-strategies/2-summary.md) — 다중 리더·리더리스
- 후속·연결
  - [33-collaborative-editing-ot-and-sequence-crdt](../33-collaborative-editing-ot-and-sequence-crdt/2-summary.md) — 시퀀스 CRDT
  - [26-hybrid-clocks-and-truetime](../26-hybrid-clocks-and-truetime/2-summary.md) — LWW 타임스탬프를 인과에 맞추는 시계
  - [13-distributed-id-generation](../13-distributed-id-generation/2-summary.md) — 유일한 태그·actor id
  - [07-consistency-models](../07-consistency-models/2-summary.md) — 최종 일관성·인과 일관성
  - [09-quorums](../09-quorums/2-summary.md)(anti-entropy, read repair)
  - [database/32-replication-leader-follower](../../database/32-replication-leader-follower/2-summary.md) · [database/55-distributed-databases](../../database/55-distributed-databases/2-summary.md)
- 논문
  - M. Shapiro, N. Preguiça, C. Baquero, M. Zawirski, "Conflict-free Replicated Data Types", SSS 2011 (INRIA RR-7687) — SEC 정의, CvRDT·CmRDT 정리 2.1·2.2, 상호 흉내 <https://inria.hal.science/inria-00609399>
  - 같은 저자, "A comprehensive study of Convergent and Commutative Replicated Data Types", INRIA RR-7506, 2011 — G/PN-Counter, 2P-Set, LWW-element-Set, OR-Set(§3.3.5) <https://inria.hal.science/inria-00555588>
  - V. Balegas 외, "Extending Eventually Consistent Cloud Databases for Enforcing Numeric Invariants", 2015(arXiv 1503.09052) — bounded counter <https://arxiv.org/abs/1503.09052>
  - A. Bieniusa 외, "An optimized conflict-free replicated set", 2012 — 툼스톤 없는 OR-Set <https://arxiv.org/abs/1210.3368>
  - G. DeCandia 외, "Dynamo", SOSP 2007 — §4.4 버전 벡터·장바구니 합집합·삭제 부활, §6.3 버전 분포(99.94%) <https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf>
- 제품 문서
  - Apache Cassandra 5.0 Tombstones — `gc_grace_seconds` 기본 864000초, zombie <https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/tombstones.html>
  - Apache Cassandra 5.0 "Dynamo" 아키텍처 — Data Versioning(LWW, 클라이언트·코디네이터 시계, NTP, 컬럼별 타임스탬프, LWW-Element-Set) <https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html>, CQL DML `WRITETIME` <https://cassandra.apache.org/doc/latest/cassandra/developing/cql/dml.html>
  - Riak KV 2.2 "Conflict Resolution" — `allow_mult=false`(형제 미반환, 버전 벡터 유지) vs `last_write_wins=true`(타임스탬프로 덮어씀) <https://docs.riak.com/riak/kv/2.2.0/developing/usage/conflict-resolution.1.html>
  - Riak KV "Causal Context" — `allow_mult`, 형제, vector clock vs dotted version vector <https://docs.riak.com/riak/kv/latest/learn/concepts/causal-context/index.html>
- 교재: DDIA 1판 5장 "Handling Write Conflicts"·"Detecting Concurrent Writes"(LWW, 형제 병합, 버전 벡터, CRDT 언급)
- 실험 목록
  - `Crdt.java` — LWW(시계 −100ms, 동시 쓰기), 버전 벡터 비교, G-Counter 1000가지 순서·중복 병합, actor id 중복, PN-Counter, OR-Set vs LWW 원소 집합, 툼스톤 누적. eclipse-temurin 21 JDK 컨테이너.
