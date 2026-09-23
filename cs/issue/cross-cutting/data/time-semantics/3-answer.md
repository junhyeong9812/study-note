# cs/issue/data/time-semantics — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **날짜는 타임존의 함수.** 같은 순간이 UTC 로는 5월 8일 23시, KST(UTC+9)로는 5월 9일 8시다 — "몇 일인가"는 어느 타임존의 자정을 기준으로 하느냐에 달렸다.\
   UTC 타임스탬프 앞 10자를 날짜로 쓰면 day-boundary 가 UTC 자정이 되어, 한국 사용자의 오전 9시 이전 사건은 **전날**로 분류된다.\
   교정: 실시간으로 생기는 항목은 로컬 타임존 API 로 로컬 `YYYY-MM-DD` 를 만들고(영속 쪽 로컬 포맷과 일치), 기존 기록을 읽는 매퍼의 UTC 절단은 **수용한 위험으로 명시 기록**했다(이 사례는 예방·수용 기록이며 실제 오분류 관측은 없다).

2. **벽시계는 단조 ID 가 아니다.** ① 역행 — NTP 보정·수동 변경으로 시계가 뒤로 갈 수 있다. ② 해상도 — 같은 해상도 단위(초·나노초) 안의 두 사건은 같은 값을 갖는다. ③ 외부 조작 — 다른 프로세스가 미래 시각의 이름을 만들어 둘 수 있다.\
   그래서 초 단위 백업 이름은 연속 작업에서 **충돌**했고, "새 백업의 값이 항상 최대"라고 가정한 prune 은 시계 역행·미래 타임스탬프 ref·동일 값이 있으면 **방금 만든 백업을 삭제**하고도 성공(`Ok(name)`)을 반환했다 — 안전망이 스스로를 지우고 성공이라 보고한 것이다.\
   교정: 이름에 추가 엔트로피(나노초 + 커밋 short hash)를 넣고, prune 은 새 이름을 **무조건 보호 대상에서 제외**한 뒤 나머지만 정렬해 자른다. 회귀 테스트는 "미래 값 ref 20개가 있어도 새 ref 가 살아남는다"로 고정했다.
   > **단조(monotonic) 시계** — 절대 뒤로 가지 않도록 보장된 시계. 경과 시간 측정용이며 벽시계와 다르다.

3. **해상도 안의 충돌 + 상한 있는 접미사.** 같은 초에 들어온 요청은 같은 키 후보를 만든다. 충돌 회피가 `_2` 까지만이면 3번째 요청은 **기존 키를 덮어쓴다** — 경쟁 조건에서 다른 요청의 산출물이 사라진다.\
   이 사례는 저장 객체가 공개 읽기 권한이라, 덮어쓰기와 겹치면 사용자 간 교차 노출까지 이어질 수 있는 잠재 결함이었다.\
   근본 교정(계획): 시각 대신 **UUID** 를 키에 넣어 충돌을 원천 차단하고, 공개 권한은 비공개 + 서명 URL 로 바꾼다.

4. **TZ 없는 문자열의 해석 차이.** 로그 타임스탬프는 UTC(`Z`)인데, 조회 인자에 타임존이 없으니 CLI 가 **호스트 로컬 시간(KST)** 으로 해석했다 — 조회 구간이 9시간 어긋나 빈 결과가 나왔다.\
   사고 조사에서 빈 결과는 "그 시각에 아무 일도 없었다"로 **오판**되기 쉽다 — 증거가 있는데 없다고 결론 내리는 포렌식 오류다.\
   교정: UTC 값에는 항상 `Z` 접미사를 붙인다(이후 모든 조회에 강제).

5. **다른 시계 도메인의 LWW + 비원자 커서.** 클라이언트 `updatedAt` 은 오프라인 동안의 **편집 시각**(클라이언트 시계)이고, 서버 `now()` 는 **수신 시각**(서버 시계)이다. 둘을 비교하면, 오래전 오프라인 편집이 늦게 올라올 때 서버 쪽 값이 "더 최신"으로 판정돼 편집이 **조용히 버려진다**.\
   교정: 같은 도메인(`client_updated_at` 끼리)만 비교하고, 동일 값은 no-op 으로 둔다. 전송~응답 사이 재편집은 revision claim 으로 보호한다. 단 여러 기기가 같은 항목을 편집하면 `client_updated_at` 끼리도 **기기마다 다른 벽시계**라 시계 차이(skew)만큼의 오판 여지가 남는다 — 강한 보장이 필요하면 서버 발급 revision 번호·하이브리드 논리 시계 같은 순서 기준을 쓴다.\
   또 upsert 와 커서 전진이 갈라져 있으면, 일부만 반영된 뒤 커서만 앞으로 가서 **재시도가 남은 항목을 건너뛴다**. upsert 와 커서를 한 트랜잭션에 넣고 커서를 마지막에 쓴다.
   > **LWW(Last-Writer-Wins)** — 충돌 시 타임스탬프가 가장 늦은 쓰기를 채택하는 병합 규칙.

6. **닫힌 구간은 경계가 겹친다.** `BETWEEN` 은 양 끝을 포함한다. 5월 1일 버킷을 `BETWEEN 5/1 00:00 AND 5/2 00:00` 로 잡으면 5/2 00:00:00 행이 5/1 과 5/2 두 버킷에 **모두** 들어간다.\
   표준 형태는 반열린 구간 `[from, toExclusive)` — `ts >= from AND ts < toExclusive`, `toExclusive = to 다음날 자정`. 인접 구간이 겹치지도 빈틈도 없다.\
   검증은 익일 00:00 행이 제외됨을 확인하는 경계 테스트로 했다.
   > **반열린 구간(half-open interval)** — 시작은 포함, 끝은 제외하는 구간. 연속 축을 빈틈·중복 없이 분할한다.

7. **시간 값에 붙어 다녀야 하는 것.** 숫자 하나만으로는 부족하다.\
   ① **시계 도메인** — 어느 기계의 어떤 시계인가(클라이언트/서버, 벽시계/단조). ② **타임존** — 날짜·자정·문자열 해석의 기준. ③ **해상도** — 이 값이 유일하다고 믿어도 되는 단위인가. ④ **구간 규칙** — 끝을 포함하나.\
   이 정보가 빠진 채 비교·자르기·정렬을 하면, 에러 없이 그럴듯한 결과가 나오므로 틀린 것을 알아채기 어렵다.

## 문제 구조 (추상화 코드)

### 변형 A — 타임존 없는 날짜·문자열
```ts
// ① 문제
const day = event.timestamp.slice(0, 10);          // UTC ISO 앞 10자 = UTC 날짜
const today = new Date().toISOString().slice(0, 10);

// ② 고친 코드
const today = new Date().toLocaleDateString("en-CA");   // 로컬 YYYY-MM-DD(로캘 데이터 의존 — 연·월·일 필드로 직접 조립하는 편이 더 안전)
// 기존 기록 매퍼의 UTC 절단은 수용 — 경계가 UTC 임을 기록
```
```sh
# ① 문제: TZ 없는 인자를 도구가 호스트 로컬로 해석
logs --since 2026-05-09T03:27:30 --until 2026-05-09T03:29:00     # 빈 결과
# ② 고친 코드
logs --since 2026-05-09T03:27:30Z --until 2026-05-09T03:29:00Z
```
무엇이 깨졌나: 같은 순간을 서로 다른 타임존으로 읽어 날짜·구간이 어긋남.

### 변형 B — 벽시계를 식별자·최신순으로
```rust
// ① 문제
let name = format!("backup/{}-{}", branch, now_secs());         // 같은 초 충돌
fn prune(keep: usize) {
    let mut refs = list_backups();
    refs.sort_by_key(|r| ts_of(r));                             // "새 것 = 최대값" 가정
    for r in &refs[..refs.len().saturating_sub(keep)] { delete(r) }   // 새 것이 삭제될 수 있음
}

// ② 고친 코드
let name = format!("backup/{}-{}-{}", branch, now_nanos(), short_head());
fn prune(keep: usize, protect: &str) {
    let mut refs: Vec<_> = list_backups().into_iter()
        .filter(|r| r != protect)                               // 새 것은 무조건 보존
        .map(|r| (ts_of(&r).unwrap_or(0), r))                   // 파싱 실패 = 가장 오래됨
        .collect();
    // 나머지 중 최신 keep-1 개만 유지 ...
}
```
무엇이 깨졌나: 시계 역행·미래 값·동일 값에서 방금 만든 안전망이 삭제되고도 성공 반환.

```python
# ① 문제
key = f"reports/{ts_seconds()}.xlsx"
if exists(key): key = f"reports/{ts_seconds()}_2.xlsx"      # 접미사 상한 → 3번째는 덮어씀

# ② 고친 코드(계획)
key = f"reports/{uuid4()}.xlsx"                              # 충돌 원천 차단
```
같은 구조: 초 단위 키 + 상한 있는 접미사 → 동시 요청 덮어쓰기(잠재 결함).

### 변형 C — 다른 시계를 섞은 LWW + 비원자 커서
```kotlin
// ① 문제
if (incoming.updatedAt > stored.serverModifiedAt) apply(incoming)   // 클라 시계 vs 서버 시계
upsertAll(batch)
advanceCursor(batch.last)          // 별도 커밋 → 부분 적용 후 커서만 전진 가능

// ② 고친 코드
if (incoming.clientUpdatedAt > stored.clientUpdatedAt) apply(incoming)   // 같은 도메인끼리
// 같으면 no-op
transaction {
    upsertAll(batch)
    advanceCursor(batch.last)      // 같은 트랜잭션, 커서는 마지막
}
```
무엇이 깨졌나: 오프라인 편집 무음 유실, 재시도가 미반영분을 건너뜀(설계 중 확인된 교훈).

### 변형 D — 닫힌 구간으로 버킷 분할
```java
// ① 문제
where(createdAt.between(from.atStartOfDay(), to.plusDays(1).atStartOfDay()));

// ② 고친 코드
LocalDateTime toExclusive = to.plusDays(1).atStartOfDay();
where(createdAt.goe(from.atStartOfDay()).and(createdAt.lt(toExclusive)));
```
무엇이 깨졌나: 경계 시점 행이 인접 두 버킷에 이중 집계.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
