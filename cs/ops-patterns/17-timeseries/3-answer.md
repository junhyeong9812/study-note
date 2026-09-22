# ops-patterns/17-timeseries — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 작성 방식: **2-summary를 닫고 기억만으로** 쓴다 → 실제 코드/원전으로 검증 → 틀린 부분만 수정.
> 기준 소스는 문서가 아니라 코드다.

⚠️ 정답은 Claude 초안(2026-09-14) — 원본 impl 코드·README 기준. 본인 검토 후 이 줄 삭제

## 정답

<!-- 1-question.md 의 절·번호와 1:1 대응. 질문 하나 = A 하나. -->

### A. 문제 (구현 대상: RawSeries TODO 1\~2 · RollingSeries TODO 3\~6)

#### 1. RawSeries — summarize / quantile (TODO 1\~2)

**정답 코드** (impl/RawSeries.java):

```java
public Bucket summarize(long from, long to) {
    Bucket bucket = Bucket.empty(from);
    for (Point point : points) {
        scanned++;                                   // 훑은 점을 센다 = 비용의 자
        if (point.at() >= from && point.at() < to) { // 끝은 안 들어간다: [from, to)
            bucket = bucket.add(point.value());
        }
    }
    return bucket;
}

public double quantile(long from, long to, double q) {
    /* ... [from, to) 값 수집, 비면 NaN ... */
    values.sort(null);
    int index = (int) Math.round(q * (values.size() - 1));  // 0분위=최소, 1분위=최대
    return values.get(index);
}
```

- **왜 반열린 [from, to) 인가?**\
  → 이어 붙인 구간들이 겹치지도 새지도 않게 하려고.\
  [0,60)+[60,120) 은 매 시각이 정확히 한 구간에 속하지만, 닫힌 [0,60]+[60,120] 은 60 시각의 값이 두 구간 모두에 들어간다.\
  04번 고정 창에서 본 것과 같은 자리다.

> **반열린 구간 [from, to)** — 시작 포함, 끝 제외. 이어 붙여도 두 번 세어지지 않는 나누기.\
> 예: [0,60)+[60,120) 은 60 시각의 값이 정확히 한 구간에만 들어간다.

- **닫힌 구간으로 하루를 더하면?**\
  → 24개 시간 구간을 더할 때 매 경계(23곳)의 값이 두 번 세어져 합계가 실제보다 크다.\
  오차가 경계에서만 나서 눈에 잘 안 띈다.
- **scanned 의 목적?**\
  → 이 구현의 비용을 재는 자.\
  RawSeries 는 어떤 조회든 전부 훑으므로 scanned 가 점 수만큼 는다 — RollingSeries 와 나란히 놓고 "무엇을 사서 무엇을 아꼈나"를 숫자로 비교하는 기준선 역할이다(32번 역색인의 전수 조사와 같은 자리).
- **인덱스를 한 칸 틀리면?**\
  → `q * size` 로 계산하면 q=1 에서 인덱스가 size 가 되어 넘치거나, 나머지 연산으로 감으면 한 바퀴 돌아 **최소가 나온다.**\
  99분위를 보는 이유가 바깥값(최악 지연)을 잡으려는 것인데 그때 제일 작은 값이 나오니, 가장 필요한 순간에 가장 안심되는 거짓말을 하는 최악의 방향이다.\
  정답은 `q * (size - 1)` 을 반올림 — 0분위=values[0]=최소, 1분위=values[size-1]=최대.

> **분위수(quantile)** — 정렬했을 때 q 위치의 값. 중앙값(0.5), 99분위(0.99).\
> 예: 0분위 = values[0] = 최소, 1분위 = values[size-1] = 최대.

- **분위수가 RawSeries 에만 있는 이유?**\
  → 분위수는 원본이 있어야만 되는 질문이다.\
  버킷의 넷(개수·합·최소·최대)으로는 못 만들고, 두 구간의 분위수를 합칠 수도 없다(B-5).

> **버킷(bucket)** — 한 시간 구간의 요약 상자. 여기서는 시작시각·개수·합·최소·최대.\
> 예: `0: 60개 평균 100.0 (0.0 ~ 6000.0)` 처럼 한 구간을 넷으로 요약한다.

- **순서를 가정하지 않는 이유?**\
  → 뒤늦게 도착하는 값이 실제로 있다(네트워크 지연·재전송).\
  그래서 그냥 리스트에 붙이고 조회 때 시각으로 거른다.

#### 2. RollingSeries — record / rollUp (TODO 3\~4)

**정답 코드** (impl/RollingSeries.java):

```java
public void record(long at, double value) {
    long cutoff = ticker.nowMillis() - fineRetentionMillis;
    if (at < cutoff) {
        // 이 구간은 이미 굵게 접혔다. 지금 넣으면 가는/굵은 버킷이 어긋난다.
        lateDrops++;                                 // 버리되, 버린 수를 센다
        return;
    }
    long start = bucketStart(at, fineBucketMillis);
    fine.merge(start, Bucket.empty(start).add(value),
            (existing, added) -> existing.add(value));
}

public int rollUp() {
    long cutoff = bucketStart(ticker.nowMillis() - fineRetentionMillis, fineBucketMillis);
    List<Long> expired = new ArrayList<>(fine.headMap(cutoff, false).keySet());
    //                                              ^ false: 컷오프에 딱 걸린 버킷은 제외
    for (long start : expired) {
        Bucket bucket = fine.remove(start);          // 접은 뒤 가는 쪽에서 지운다
        long coarseStart = bucketStart(start, coarseBucketMillis);
        coarse.merge(coarseStart, bucket,
                (existing, incoming) -> existing.mergeWith(incoming));
        rolledUp++;
    }
    return expired.size();
}
```

- **늦은 값을 버리는 이유?**\
  → 그 시각 구간의 가는 버킷은 이미 굵은 버킷으로 접혀 사라졌다.\
  지금 가는 버킷을 새로 만들어 넣으면 같은 구간의 값이 가는 쪽과 굵은 쪽에 갈라져, 요약할 때 같은 구간이 두 번 세어지거나 두 갈래 답이 나온다.

> **접기/롤업(roll-up)** — 가는 버킷 여럿을 굵은 버킷 하나로 합치고 원본(가는 쪽)을 지우는 것. 되돌릴 수 없다.\
> 예: 보존 기간이 지난 1분 버킷들을 1시간 버킷 하나에 mergeWith 로 합치고 가는 쪽에서 지운다.

- **lateDrops 를 세는 이유?**\
  → 버리는 것도 손실이라 조용히 버리면 안 된다.\
  이 값이 0 이 아니면 "값이 접힌 뒤에도 도착하고 있다" = **보존 기간이 실제 지연보다 짧다**는 운영 신호다.

> **lateDrops** — 이미 접힌 구간으로 늦게 도착해 버린 값의 수. 손실을 세어 신호로 만든다.\
> 예: 버린 수를 세어 두어야 보존 기간이 짧다는 것을 운영에서 알아챌 수 있다.

- **컷오프에 딱 걸린 버킷을 접으면?**\
  → ① 보존 기간이 약속보다 한 버킷 짧아진다 ② 그 버킷 구간으로 아직 도착 중인 늦은 값들이 그 순간부터 버려지기 시작한다(lateDrops 증가).\
  그래서 `headMap(cutoff, false)` — 컷오프 미만만 접는다.

> **보존 기간(retention)** — 가는 버킷을 그대로 들고 있는 기간. 지나면 접는다.\
> 예: 1분 버킷을 보존 1시간으로 두면 1시간이 지난 버킷부터 굵게 접힌다.

- **접은 버킷을 안 지우면?**\
  → 같은 값이 가는 버킷과 굵은 버킷 양쪽에 남아, summarize 가 둘 다 보므로 두 번 세어진다.
- **배수가 아니면?**\
  → 굵은 버킷 하나의 경계가 가는 버킷 중간을 지나가, 가는 버킷 하나를 접을 때 그 값이 두 굵은 버킷에 나뉘어 들어갈 자리가 생긴다 — 버킷은 통째로만 합칠 수 있으므로(분포가 없다) 어느 한쪽에 통째로 들어가고 합계가 틀린다.
- **왜 생성자에서 검사?**\
  → 이 조건은 값이 아니라 설정의 성질이라 객체가 만들어지는 순간 판정할 수 있다.\
  생성자에서 던지면 잘못된 설정이 아예 존재하지 못하고, rollUp 때마다 검사하면 이미 쌓인 데이터가 틀린 뒤에야 드러난다.

#### 3. RollingSeries — summarize / bucketStart (TODO 5\~6)

**정답 코드** (impl/RollingSeries.java):

```java
public Bucket summarize(long from, long to) {
    Bucket result = Bucket.empty(from);
    for (Map.Entry<Long, Bucket> e : fine.subMap(from, true, to, false).entrySet()) {
        result = result.mergeWith(e.getValue());     // 가는 쪽: 시각으로 바로 찾는다
    }
    for (Map.Entry<Long, Bucket> e : coarse.entrySet()) {
        long start = e.getKey();
        long end = start + coarseBucketMillis;
        if (end > from && start < to) {              // 실제로 겹칠 때만 (초과/미만)
            result = result.mergeWith(e.getValue()); // 겹치면 통째로 — 접기의 대가
        }
    }
    return new Bucket(from, result.count(), result.sum(), result.min(), result.max());
}

static long bucketStart(long at, long width) {
    return Math.floorDiv(at, width) * width;         // 음수에서도 바닥으로 내린다
}
```

- **겹침 조건 식?**\
  → 버킷 [start, end) 와 조회 [from, to) 가 실제로 겹친다 = `end > from && start < to` (둘 다 **초과/미만**).
- **이상/이하로 쓰면?**\
  → `end >= from` 이면 조회 시작점에서 정확히 끝나는(안 겹치는) 왼쪽 옆 버킷이, `start <= to` 면 조회 끝점에서 정확히 시작하는 오른쪽 옆 버킷이 통째로 딸려온다.\
  시간별 그래프에서 **한 칸이 옆 칸 값을 그대로 베끼는** 증상으로 나타난다.
- **왜 통째로 넣는가?**\
  → 굵은 버킷 안의 분포(어느 시각에 어떤 값이 있었는지)는 접을 때 이미 사라졌다.\
  부분만 잘라낼 정보가 없으니 겹치면 통째로 넣는 수밖에 없다 — 버킷 폭보다 좁게는 못 자른다(한 시간이 통째로 접혔으면 앞 10분을 물어도 한 시간치가 나온다).\
  구간을 정확히 잘라내려면 원본이 있어야 한다.
- **그냥 나눗셈이면?**\
  → 자바의 `/` 는 0 쪽으로 자른다.\
  `-30 / 60 = 0` 이라 `bucketStart(-30, 60) = 0` — 음수 시각 -30 이 [0,60) 버킷에 들어간다.\
  맞는 답은 [-60, 0) 의 시작 **-60** 이다.
- **해결 함수?**\
  → `Math.floorDiv(at, width) * width` — 바닥 나눗셈은 음의 무한대 쪽으로 내리므로 `floorDiv(-30, 60) = -1`, 시작 -60.

> **floorDiv(내림 나눗셈)** — 음수에서도 아래쪽으로 내리는 나눗셈.\
> 예: `floorDiv(-30, 60) = -1` 이라 bucketStart(-30, 60) 이 -60 이 된다.

- **원점이 임의라는 뜻?**\
  → epoch(1970년) 같은 원점은 약속일 뿐이라, 원점 이전 시각이나 상대 시각(테스트의 임의 기준점)을 쓰면 밀리초 값이 음수로 실제로 나온다는 뜻이다.

### B. 개념

#### 4. 무엇을 얻고 무엇을 잃는가

- **점 개수?**\
  → 원본 86,400점 vs 구간(1분 버킷을 1시간으로 접으면) 24버킷.
- **조회 비용?**\
  → 원본은 600분치 600점을 **다 훑고**(scanned 600), 구간은 TreeMap 에서 시각으로 바로 찾는다(subMap — 해당 버킷만).

> **TreeMap** — 키(시작 시각) 순서로 정렬된 맵. 범위 조회를 전부 훑지 않고 바로 찾게 해준다.\
> 예: 원본은 600점을 다 훑지만 버킷 쪽은 subMap 으로 해당 버킷만 본다.

- **구별하려면?**\
  → 최소·최대가 있어야 한다.\
  `0: 60개 평균 100.0 (0.0 ~ 6000.0)` — 평균 100만 보면 모르지만 max 6000 이 "한 번 튀었다"를 보여준다.\
  안 담았으면 아예 못 봤다.

> **바깥값(outlier)** — 대부분과 동떨어진 값. 최대·99분위로 잡는다 — 평균에는 묻힌다.\
> 예: 59분이 0이고 1분만 6000이면 평균 100에는 안 보이지만 max 6000 이 보여준다.

- **살아남는 기준?**\
  → **합칠 수 있는가.**\
  개수·합은 더하면 되고 최소·최대는 각각 고르면 된다 — 접어도(mergeWith) 의미가 보존된다.\
  중앙값·99분위는 합칠 수 없어서 못 담는다.

> **합칠 수 있는 값(mergeable)** — 부분 요약 둘을 합쳐도 정확한 값 — 개수·합·최소·최대.\
> 예: 중앙값·99분위는 합칠 수 없어서 버킷에 못 담는다.

- **평균 대신 개수+합?**\
  → 평균끼리 평균 내면 틀린다 — 평균 100(1개)과 평균 0(4개)을 합치면 (100+0)/5 = **20**이지 50이 아니다.\
  개수가 다르면 가중치가 달라야 하는데 평균만으로는 그 정보가 없다.\
  개수와 합을 들면 평균은 언제든 sum/count 로 나온다.
- **0 대신 NaN?** → 0 을 주면 "값이 0이었다"(측정됨)와 "값이 없었다"(측정 안 됨)가 구별이 안 된다.\
  빈 구간의 평균은 값이 아니라 "없음"이어야 한다 — `Bucket.average()` 도 count==0 이면 NaN.

> **NaN** — "숫자 없음".\
> 예: 빈 구간의 평균은 0 이 아니라 NaN 이어야 "값이 없었다"와 "값이 0이었다"가 구별된다.

#### 5. 분위수는 왜 합칠 수 없는가

- **숫자?**\
  → 전체 100개(1 이 90개 쪽) 중앙값 = **1**.\
  두 중앙값의 평균 = (1+100)/2 = **50.5**.\
  완전히 다르다.
- **왜 함정인가?**\
  → 값이 균등하게 퍼진 데이터로 테스트하면 두 답이 우연히 가까워 "합쳐도 되네"라고 잘못 결론 내리게 된다.\
  성질이 성립하는 게 아니라 입력이 우연히 관대했던 것 — 치우친 분포(90:10)로 검사해야 거짓이 드러난다.
- **분위수가 필요하면?**\
  → 원본을 들거나(RawSeries), 근사 자료구조(t-digest 류 확률적 집계)를 쓴다.\
  (원본 README·Bucket javadoc 은 "19번 확률적 집계"를 가리키는데, 현재 저장소의 19번은 graceful-shutdown 이다 — 원본의 낡은 참조로 보인다.)

#### 6. 연결 — 앞뒤 챕터와의 다리

- **04번?**\
  → 고정 창(fixed window)의 경계 문제 — 창 경계에서 두 번 세어지거나 빠지는 자리가 반열린 구간 규칙과 같은 자리다.
- **32번?**\
  → 역색인의 전수 조사(grep 기준선) — 정확하지만 비싼 구현을 기준선으로 두고, 빠른 구현의 답이 맞는지 그것으로 검증한다.\
  RawSeries 가 같은 역할이다.
- **16번과의 태도 차이?**\
  → 이벤트 소싱은 사건을 **전부, 영원히** 들고 있었다(지우지 않는 것이 가치 — 감사 로그가 원본).\
  시계열은 오래된 것을 **접어서 줄여가며** 들고 있다(다 들 수 없는 것이 전제 — 요약이면 충분).
- **18번으로의 다리?**\
  → 여기서는 접어서 버린 것을 **되돌릴 수 없었다**(불가역이 대가).\
  18번은 아예 **못 바꾸게** 만든다 — 바꾸면 티가 나게(불가역이 목적).
- **살아남은 변종 넷의 공통점?**\
  → **전부 경계 조건**이었다 — 반열린 구간, 겹침 판정의 등호, 컷오프 등호, 음수 나눗셈.\
  정확한 경계를 밟는 테스트를 따로 만들어야 잡혔다.\
  경계에서만 나는 오차는 눈에 잘 안 띈다는 것이 이 상자의 교훈이다.
