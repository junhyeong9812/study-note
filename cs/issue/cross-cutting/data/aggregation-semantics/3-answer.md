# cs/issue/data/aggregation-semantics — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **counter vs gauge.** 누적 카운터는 여러 관측을 더한 값(지금까지 얼마나)이고, 게이지는 마지막 관측 시점의 크기(지금 얼마나)다.\
   한 턴 안에서 툴 호출이 왕복할 때마다 모델에 전체 프롬프트가 다시 들어가므로, 턴 동안의 입력 토큰을 **더하면** 같은 컨텍스트가 여러 번 세어져 창 크기를 넘어선다 → 100% 초과.\
   현재 점유는 **최신 메시지 1건의 입력 크기**(입력 + 캐시 읽기 + 캐시 생성)로, 매 메시지마다 덮어써야 한다.
   > **게이지(gauge)** — 합산하면 안 되는, 한 시점의 상태 값(점유율·온도·큐 길이).

2. **기본값 vs 숨김.** 식별자가 없거나 다른 계열 모델인데 창 크기를 200k로 가정하면, 계산은 돌아가고 게이지도 그려져 **"그럴듯하지만 틀린"** 수치가 된다 — 사용자는 틀렸다는 걸 알 수 없다.\
   분모를 모르면 용량을 0으로 두고 게이지를 **숨긴다**. 무표시는 "모름"을 정직하게 전하지만, 기본값은 결함을 정상 수치로 위장한다.

3. **DISTINCT 합.** 10시 버킷에 1, 13시 버킷에 1로 세어지고 다른 방문자 1명이 더 있으면 버킷 합은 3, 실제 고유 방문자는 2 — **과대집계**된다.\
   `COUNT(DISTINCT)`는 집합의 크기라 부분 집합 크기의 합이 전체 크기와 같으려면 부분이 서로 겹치지 않아야 한다. 버킷 사이에 같은 원소가 나타날 수 있으므로 **가산적이지 않다**.\
   합계 행은 원 데이터에서 전체 기간 **별도 DISTINCT 쿼리**로 구한다.
   > **가산적(additive) 집계** — 부분 결과를 더하면 전체 결과가 되는 집계(SUM·COUNT). DISTINCT·중앙값은 아니다.

4. **차원과 집계 함수.** 이 사례의 지표(연도별 발생량 같은 유량)에서 "전체"라는 차원은 모든 연도의 **합**을 뜻하는데, 연도별 값에 "마지막 값"을 적용하면 **최신 연도만** 남아 과소집계된다.\
   (반대로 연말 잔액·보유 수 같은 재고성(게이지) 지표라면 "전체"에 합이 아니라 최신값이 맞을 수 있다 — 함수는 지표의 의미가 정한다.)\
   함수는 정상 동작하고 결과도 숫자라 오류가 드러나지 않는다 — 차원의 의미와 함수 선택이 어긋난 것은 코드가 아니라 의미 층의 결함이다.

5. **덮어쓰는 로그 파서.** 파서가 `Success: N`을 읽을 때마다 상태를 덮어쓰면, 워커의 배치 단건 라인(~1000)과 메인의 누적 라인이 번갈아 이겨 **값이 1000 근처에 고정되거나 깜빡인다**.\
   병렬 워커 프로세스는 메인과 메모리를 공유하지 않으므로 누적은 메인이 워커 반환값으로만 만들 수 있다. 그래서 메인 루프가 누적 카운터를 소유하고 통일 포맷(`Progress: a/b (p%) | Success: n | ...`)으로 찍고, 파서는 `Progress:` 라인에서만 읽는다.\
   선택하지 않은 방법: 파서 쪽 누적 — 로그 스트림을 재시작하면 과거 라인이 다시 흘러와 **중복 합산**된다.

6. **반열린 구간.** 날짜 끝을 포함하는 `BETWEEN`은 시각이 있는 컬럼에서 마지막 날의 대부분을 빠뜨리거나(자정까지만), 경계를 두 구간이 공유해 **중복·누락**을 만든다.\
   `ts >= from AND ts < to + 1일`은 인접 구간이 겹치지 않고 빈틈도 없다. 타임존도 명시한다.\
   이 역시 틀려도 "조금 다른 숫자"만 나올 뿐이라 집계 의미 결함과 같은 계열이다.

## 문제 구조 (추상화 코드)

### 변형 A — 누적 합을 게이지로 사용 + 미상 분모에 기본값

```rust
// 문제
self.turn_tokens.add(&usage);                       // 턴 누적
let pct = self.turn_tokens.input as f64 / ctx_window(model.unwrap_or(DEFAULT)) as f64; // 200k 가정

// 고침: 누적은 누적대로, 게이지는 최신 1건 overwrite, 분모 모르면 숨김
self.turn_tokens.add(&usage);
self.last_usage = Some(usage);                      // overwrite (not add)
self.model = msg.model.or(self.model.take());       // last-wins
let occ = u.input + u.cache_read + u.cache_creation;
match ctx_window(model) { 0 => hide_gauge(), w => show(min(100, occ * 100 / w)) }
```
무엇이 깨졌나: 툴 왕복이 많은 턴에서 게이지가 100%를 넘었고, 모르는 모델에서도 틀린 %가 정상처럼 그려졌다.\
선택하지 않은 방법: "마지막 턴 누적 + 100% 클램프" — 툴이 많은 턴에서 여전히 과대 표시.

### 변형 B — DISTINCT를 버킷 합으로

```sql
-- 문제: 합계 = Σ 버킷별 DISTINCT
SELECT hour, COUNT(DISTINCT visitor) FROM page_views GROUP BY hour;   -- 앱에서 합산

-- 고침: 합계는 원 데이터에서 별도 DISTINCT, 기간은 반열린 구간
SELECT COUNT(DISTINCT visitor) FROM page_views
 WHERE ts >= :from AND ts < :toExclusive;
```
무엇이 깨졌나: 유니크 방문자 합계 행이 과대집계됐다. 통합 테스트로 "버킷 합 3 ≠ 실제 2"를 고정했다.\
곁가지: append 로그에는 멱등성이 없으므로 "중복 기록 제거"(dedup 키)와 "고유 방문 세기"(DISTINCT)는 서로 다른 축으로 처리한다.

### 변형 C — 차원 의미와 어긋난 집계 함수

```js
// 문제: "전체" = 마지막 값(최신 연도)
const total = last(perYear);
// 고침: 차원 의미에 맞게 합
const total = sum(perYear);
```
무엇이 깨졌나: "전체" 탭이 최신 연도만 합산해 과소 표시됐다.

### 변형 D — 같은 로그 패턴에 서로 다른 의미 + 덮어쓰기 파서

```python
# 문제: 워커(배치 단건)와 메인(누적)이 같은 패턴, 파서는 매 줄 덮어씀
SUCCESS_RE = re.compile(r"[Ss]uccess:\s*([\d,]+)")
for line in stream:
    if m := SUCCESS_RE.search(line): state["success"] = int(m[1].replace(",", ""))

# 고침: 누적은 메인이 소유(워커 반환값으로), 포맷 통일, 파서는 지정 라인에서만
for fut in as_completed(futures):
    ok, fail = fut.result(); ok_count += ok; fail_count += fail
    log.info(f"Progress: {done}/{n} ({pct}%) | Success: {ok_count} | Failed: {fail_count} | Rate: {r}")
# 파서
if "Progress:" in line: state["success"] = parse_success(line)
```
무엇이 깨졌나: 대시보드의 성공 수가 항상 ~1000에 고정되고 값이 깜빡였다. 다른 형식(`N/M batches`)은 퍼센트 정규식과도 맞지 않았다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
