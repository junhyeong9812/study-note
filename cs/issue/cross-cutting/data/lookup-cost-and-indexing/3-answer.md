# cs/issue/data/lookup-cost-and-indexing — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **역검색은 O(n), 역인덱스는 O(1).** 해시맵은 key 를 해시해 버킷을 바로 찾으므로 key→value 가 O(1)이다.\
   value 쪽에는 아무 색인이 없으니 value→key 를 찾으려면 모든 항목을 순회해야 한다(O(n)).\
   이 역검색을 레코드마다 부르면 전체는 **호출 수 × n** 이 된다 — 실측으로 180만 항목 사전을 호출마다 훑어 건당 206ms, 535만 건 기준 약 12.8일이 걸렸다.\
   초기화 때 `value → [key...]` 역인덱스를 **한 번** 만들어 두면 조회가 `.get()` O(1)이 되어 건당 0.58ms(약 355배)로 줄었다.\
   대가는 메모리(+50~100MB)와 초기화 시간(+약 1초)이다 — 사전이 불변이고 조회가 빈번할 때 맞는 교환이다.
   > **역인덱스(inverted index)** — 원래 매핑의 값을 키로 뒤집어, 값으로 원래 키를 O(1)에 찾게 만든 보조 색인.

2. **upsert = 조회 + 쓰기.** upsert 는 "이 키가 이미 있나"를 매 건 먼저 조회한다.\
   조회 키에 인덱스가 없으면 그 조회가 컬렉션 풀스캔이고, 컬렉션은 적재할수록 커지므로 전체가 1+2+…+n = **O(n²)** 가 된다 — 실측에서 적재가 80% 지점에서 18시간 정체했다.\
   빈 컬렉션을 비우고 **순수 insert** 로 넣으면 존재 확인이 없어 건당 비용이 상수가 되고(63만 건 7초), 인덱스는 적재가 끝난 뒤 한 번에 만든다.\
   전제: 대상이 비어 있어 중복 판정이 필요 없어야 한다.

3. **평탄한 페이지 비용 = 고정비, 순차 진행 = 굶는 워커.** 페이지 비용이 OFFSET 과 무관하게 일정하다면 비용이 "몇 행을 건너뛰나"가 아니라 **매 페이지 반복되는 고정 작업**에 지배된다는 뜻이다 — 조인/IN 조건 컬럼에 인덱스가 없어 매 페이지가 수억 행 자식 테이블을 풀스캔하고 있었다.\
   워커 12개가 있어도 일감을 공급하는 **동기 리더 1개**가 페이지당 18분씩 걸리면 워커는 할 일이 없어 기다리고, 결과적으로 직렬처럼 보인다(64코어로 옮겨도 0.4 docs/s).\
   확정은 `EXPLAIN` 으로 한다 — `type=ALL`(풀스캔)·filesort·temporary 가 찍히면 인덱스 부재가 원인이다.\
   조인 키에 인덱스를 건 뒤 페이지 읽기가 6.8분 이상에서 0.06초로 떨어졌다.

4. **OFFSET 은 건너뛸 행을 매번 읽는다.** `LIMIT 500 OFFSET 800000` 은 앞의 80만 행을 실제로 읽고 버린 뒤 500행을 준다 — 페이지가 깊어질수록 비용이 선형으로 는다.\
   keyset 은 `WHERE key > :lastKey ORDER BY key LIMIT n` 으로 **직전 페이지의 마지막 키에서 인덱스를 바로 타고 들어가** 버리는 행이 없다.\
   결과적으로 모든 페이지 비용이 첫 페이지와 같아진다(인덱스 + keyset 후 약 2400 docs/s, 1400만 건 완주).
   > **keyset(seek) 페이징** — 오프셋 대신 "마지막으로 본 정렬 키" 이후를 조회하는 커서 방식.

5. **인덱스가 있어도 못 타는 쿼리.** B-tree 는 키가 정렬돼 있어 **접두**가 정해질 때만 범위를 좁힐 수 있다.\
   `LIKE 'kw%'` 는 접두가 고정이라 인덱스 범위 탐색이 되지만, `LIKE '%kw%'` 는 첫 글자가 무엇이든 될 수 있어 정렬 순서를 쓸 수 없고 결국 전체를 훑는다(`lower(col)` 처럼 컬럼에 함수를 씌워도 같은 이유로 못 탄다).\
   또 utf8mb4 긴 VARCHAR 는 인덱스 키 길이 한도를 넘으므로 `col(191)` 같은 **접두 길이 인덱스**로만 만들 수 있다.\
   부분일치 성능이 목적이면 B-tree 가 아니라 전문 검색(FULLTEXT) 인덱스를 검토해야 한다 — 이 사례는 원리만 기록되고 실측은 후속 과제로 남았다.

6. **1차 군집화 — 자료구조의 성질.** 정수의 기본 해시가 값 그대로(항등)면 연속 키 0..199999 가 슬롯 0..199999 를 **빈틈없이** 채운다.\
   선형 탐사는 충돌 시 다음 칸을 보므로, 이 덩어리 안으로 떨어진 "없는 키" 조회는 **덩어리 끝까지** 탐사해야 미스를 확정한다.\
   같은 용량에서 체이닝 120ms vs 선형 탐사 약 75초(약 625배)였다 — 알고리즘(O(n) twoSum)은 맞고, 느려진 것은 해시 × 키 분포 × 충돌 해결 방식의 조합이다.\
   대응은 성능 입력을 흩뿌려(`i * 4001`) 알고리즘을 공정하게 재고, 군집화 자체는 별도 테스트로 한계를 문서화하는 것이었다.
   > **1차 군집화(primary clustering)** — 선형 탐사에서 점유 슬롯이 연속 덩어리를 이뤄 탐사 길이가 급증하는 현상.

7. **입력 크기 × 호출 수를 함께 본다.** "O(n) 루프"는 루프 본문이 O(1)이라는 가정 위에서만 참이다.\
   본문 안의 조회가 컬렉션 크기에 비례하면 전체는 곱이 된다 — 그런데 코드는 짧고 정상 동작하므로 눈으로는 안 보인다.\
   그래서 프로파일링(한 함수가 전체 시간의 99.9%)이나 EXPLAIN(type=ALL)으로 **측정해 특정**한 뒤 고친다 — 다른 함수는 모두 0.1ms 미만이었다는 기록처럼, 병목은 대개 한 곳에 몰려 있다.

## 문제 구조 (추상화 코드)

### 변형 A — 값→키 역검색을 매 호출 전체 순회
```python
# ① 문제
def lookup_keys(self, value):
    result = []
    for k, v in self.table.items():      # 180만 항목 / 호출
        if v == value:
            result.append(k)
    return result

# ② 고친 코드
def __init__(self, table):
    self.table = table
    self.reverse = defaultdict(list)     # 초기화 때 1회 구축
    for k, v in table.items():
        self.reverse[v].append(k)

def lookup_keys(self, value):
    return list(self.reverse.get(value, []))
```
무엇이 깨졌나: 호출마다 O(n) 순회 → 전체 O(호출 수 × n), 배치가 수일로 늘어남.\
같은 구조: 군집 생성 단계에서 id 매핑을 매번 전체 순회하던 것도 역인덱스로 O(1) 전환.

### 변형 B — 인덱스 없는 upsert 로 대량 적재
```text
# ① 문제
for doc in docs:                                  # n건
    collection.update_one({"key": doc.key},       # key 인덱스 없음 → 건당 풀스캔
                          {"$set": doc}, upsert=True)

# ② 고친 코드
collection.drop()
bulk_insert(collection, docs, workers=4)          # 존재 확인 없는 순수 insert
collection.create_index("key")                    # 인덱스는 적재 후 1회
```
무엇이 깨졌나: 적재가 커질수록 건당 조회가 느려져 O(n²) — 80%에서 장시간 정체.

### 변형 C — 조인 키 인덱스 부재 + OFFSET 페이징
```sql
-- ① 문제: 페이지마다 자식 테이블 풀스캔(인덱스 없음) + 깊은 OFFSET
SELECT DISTINCT p.key FROM parent p JOIN child c ON c.key = p.key
ORDER BY p.key LIMIT 500 OFFSET :n;

-- ② 고친 코드
ALTER TABLE child ADD INDEX idx_key (key), ALGORITHM=INPLACE, LOCK=NONE;  -- 작은 테이블부터
SELECT DISTINCT p.key FROM parent p JOIN child c ON c.key = p.key
WHERE p.key > :lastKey ORDER BY p.key LIMIT 500;                          -- keyset
```
```text
reader(동기, 페이지당 18분) ──▶ queue ──▶ worker × 12   # 워커는 대부분 대기 = 사실상 직렬
```
무엇이 깨졌나: 페이지 비용이 고정 풀스캔에 지배되고, 느린 동기 리더가 병렬 워커를 굶겼다; 인덱스 후엔 OFFSET 이 선형 병목으로 드러남.\
부수: 대형 테이블 온라인 인덱스 생성 중 저장 공간 부족(`table is full`)이 나 공간 확보 후 재시도 — DDL 전 디스크 여유 확인이 필요하다.

### 변형 D — 인덱스를 추가했지만 쿼리가 못 탐
```sql
-- ① 문제
CREATE INDEX idx_name ON t (name);                       -- 긴 VARCHAR: 키 길이 한도
SELECT * FROM t WHERE lower(name) LIKE CONCAT('%', :kw, '%');   -- 선행 와일드카드

-- ② 고친 코드(생성) + 후속 과제
CREATE INDEX idx_name ON t (name(191));                  -- 접두 길이 인덱스
-- 부분일치 성능은 FULLTEXT 인덱스를 데이터량 확인 후 검토
```
무엇이 깨졌나: "인덱스 추가 = 검색 빨라짐" 가정 — B-tree 는 접두 없는 패턴에 쓰이지 않는다.

### 변형 E — 항등 해시 + 연속 키 + 선형 탐사
```text
# ① 문제
hash(i) = i,  keys = 0..199999,  capacity = 524288
slots:  [0][1][2] ... [199999][ ][ ] ...        # 빈틈없는 한 덩어리
miss lookup(k in 0..199999 범위로 떨어짐) → 덩어리 끝까지 탐사

# ② 고친 코드(측정 입력)
keys = [i * 4001 for i in range(200000)]        # 흩뿌린 키로 알고리즘 측정
test sequential_keys_cluster()                  # 군집화 한계는 별도 테스트로 문서화
```
무엇이 깨졌나: 같은 O(n) 알고리즘이 충돌 해결 방식에 따라 약 625배 차이 — 복잡도 표기 뒤에 숨은 상수가 자료구조 성질이었다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
