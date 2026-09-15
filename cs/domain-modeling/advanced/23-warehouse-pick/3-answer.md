# domain-modeling-advanced/23-warehouse-pick — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 작성 방식: **2-summary를 닫고 기억만으로** 쓴다 → 실제 코드/원전으로 검증 → 틀린 부분만 수정.
> 기준 소스는 문서가 아니라 코드다 (`/home/jun/project/myway/domain-modeling-advanced/23-warehouse-pick/impl/`).

⚠️ 정답은 Claude 초안(2026-09-15) — 원본 impl 코드·README 측정 기준. 본인 검토 후 이 줄 삭제

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. -->

### A. 과제

#### 0. 한 줄 규칙이 안 말해주는 것

- 안 말해주는 자리 셋(원본 `Picker` javadoc 그대로):

```text
 안 말해준 것            가능한 읽기
 "어느 창고에서"     →  가까운 곳인가 재고 많은 곳인가
 "여러 창고에 걸치면" →  나눠 보내나 한 곳에 다 있을 때만 보내나
 "어느 주문부터"     →  먼저 온 것부터인가 지금 채울 수 있는 것부터인가
```

- 재고 0인 창고: **뺀다.**\
  `sitesFor` 가 `available > 0` 인 창고만 후보로 담는다.\
  테스트가 `sitesFor("앨범", NEAREST) == [대전]`(서울·부산은 0)과 `sitesFor("없는것", …).isEmpty()` 로 못 박았다.
- 순위가 같은 창고: **창고 번호(id)가 작은 쪽.**\
  `thenComparing(Site::id)` 다. "나·가·다" 세 창고는 두 규칙 다 `[가, 나, 다]`.
- 못 보내는 주문: **아무것도 안 뺀다.**\
  `WHOLE_ONLY` 에서 다 있는 창고가 없으면 `Pick(id, List.of(), 주문 줄 전부)` 를 그대로 돌려준다.
- "채울 수 있다": **규칙마다 다른 뜻이다.**\
  `WHOLE_ONLY` 면 "어느 한 창고가 통째로 채우나", `ALLOW_SPLIT` 이면 "합계가 충분한가".
- 채울 수 있는 주문이 하나도 없으면: **멈추지 않고 먼저 온 것을 그냥 처리한다.**\
  `index` 가 0인 채로 남아 제일 앞 주문이 뽑힌다.
- 목록의 담긴 순서: **안 믿는다.**\
  `run` 이 받자마자 `placedAt` → `id` 로 다시 세운다.
- "합계는 충분한데 한 창고에는 모자란다"가 늘 생기는 이유: **재고가 창고마다 따로 있고 주문은 줄이 여러 개**라서다.\
  줄이 셋이면 한 창고가 셋을 다 갖고 있어야 하는데, 그 확률은 줄이 늘수록 급히 떨어진다.\
  측정이 그 값을 보여준다 — `WHOLE_ONLY` 충족 3,646 대 `ALLOW_SPLIT` 4,135.
- "셋이 서로 간섭한다"의 뜻: **한 갈래를 바꾸면 다른 갈래의 효과 크기가 바뀐다.**\
  `WHOLE_ONLY` 로 놓으면 처리 순서 설정이 값을 하나도 안 바꾼다(3,646 / 3,646 / 451,830 완전 동일).\
  같은 순서 설정이 `ALLOW_SPLIT` 에서는 충족을 370건 바꾼다.
- enum 세 개로 올리면: **여덟 조합을 같은 코드로 돌려 지표를 나란히 잴 수 있다.**\
  그래야 "이 설정이 실제로 일하는지"를 세어보고 안다.

> **설정을 값으로 올린다(externalized policy)** — 코드 안에 조건문으로 숨긴 선택을 밖에서 바꿀 수 있는 값(enum·설정)으로 꺼내는 것.\
> 예: "가까운 곳부터"를 `if` 로 박아두는 대신 `SiteChoice` enum 으로 빼면, 재고 많은 곳부터 판과 나란히 돌려 상자 수를 비교할 수 있다.

#### 1. TODO 1 — sitesFor

정답 코드 (impl/Picker.java):

```java
List<Site> candidates = new ArrayList<>();
for (Site site : warehouse.sites()) {
    if (warehouse.available(site.id(), sku) > 0) {
        candidates.add(site);
    }
}
Comparator<Site> order = siteChoice == SiteChoice.NEAREST
        ? Comparator.comparingInt(Site::distanceKm)
        : Comparator.comparingInt(
                (Site site) -> warehouse.available(site.id(), sku)).reversed();
candidates.sort(order.thenComparing(Site::id));
return candidates;
```

- 후보 조건: **그 상품의 재고가 1개 이상인 창고만.**
- 0인 창고를 남기면: `NEAREST` 가 **가장 가까운 빈 창고를 먼저 고르고** 0개를 뽑은 뒤 다음으로 넘어간다.\
  그 사이 그 창고 앞으로 출고 지시가 한 장 나간다.\
  **사람이 선반까지 가서 없는 것을 확인한다** — 대가가 코드 밖에서 치러진다.
- 정렬 기준: `NEAREST` 는 `distanceKm` 오름차순, `MOST_STOCK` 은 **그 상품의 재고** 내림차순.
- `reversed()` 가 붙는 이유: `comparingInt` 는 오름차순인데 "재고 많은 곳부터"는 **내림차순**이라서다.
- 붙이는 자리가 중요하다 — `comparingInt(...).reversed().thenComparing(id)` 이지 `.thenComparing(id).reversed()` 가 아니다.\
  뒤로 붙이면 id 도 같이 뒤집혀 동순위가 `[다, 나, 가]` 가 된다.\
  테스트가 `[가, 나, 다]` 로 못 박았으니 그 변종은 잡힌다.
- 타이브레이크가 없으면: 같은 자료를 두 번 돌려도 **다른 창고가 뽑힐 수 있다.**\
  그러면 "어제 왜 그 창고에서 나갔는지"를 설명할 수 없다.

> **타이브레이크(tie-break)** — 1순위 기준이 같을 때 순서를 정하는 2순위 기준.\
> 예: 거리가 셋 다 100 km 면 창고 번호가 작은 "가"를 먼저 본다.

> **결정성(determinism)** — 같은 입력에 늘 같은 결과가 나오는 성질.\
> 예: 타이브레이크가 없으면 정렬이 동순위를 어떻게 놓느냐에 따라 출고 창고가 달라져, 어제 기록을 재현할 수 없다.

- "나·가·다" 세 창고(거리 100, 재고 5 동일): **두 규칙 다 `[가, 나, 다]`.**
- 목록을 돌려주는 이유: **한 창고로 모자랄 수 있어서**다.\
  `ALLOW_SPLIT` 은 이 목록을 위에서부터 훑으며 남은 수량을 채운다.
- `MOST_STOCK` 이 보는 재고 시점: **부를 때의 남은 재고**다.\
  `pick` 이 줄마다 `sitesFor` 를 새로 부르므로, 앞 줄이 뺀 만큼 반영된 상태에서 다시 정렬된다.

```text
 창고 목록        ─ 재고 0 거르기 ─▶  후보      ─ 정렬 ─▶  우선순위
 서울(10km) 0                        대전(150)   거리       [대전]
 대전(150km) 5                                    또는
 부산(400km) 0                                   재고↓ + id
```

#### 2. TODO 2 — canFillWhole

정답 코드:

```java
for (Map.Entry<String, Integer> line : order.lines().entrySet()) {
    if (warehouse.available(siteId, line.getKey()) < line.getValue()) {
        return false;
    }
}
return true;
```

- 보는 범위: **주문의 모든 줄.** 한 줄이라도 수량이 모자라면 즉시 `false`.
- `> 0` 으로 쓰면 틀리는 것: **수량을 무시한다.**\
  앨범 5개를 달라는데 창고에 1개만 있어도 "다 채울 수 있다"가 되어, `pick` 이 그 창고를 고르고 1개만 뽑는다.\
  `WHOLE_ONLY` 의 계약("통째로 나가거나 아예 안 나간다")이 깨진다.
- `totalAvailable` 로 짜면 잘못 통과하는 주문: **여러 창고에 흩어진 주문.**\
  서울 앨범 3 + 부산 포카 5 에서 앨범1+포카1 주문이 "된다"로 잡히는데, 실제로는 어느 한 창고에서도 못 채운다.
- public 인 이유: **`fillableNow` 가 다시 쓴다.**\
  `WHOLE_ONLY` 의 "지금 채울 수 있나" 판정이 곧 "어느 한 창고가 통째로 채우나"라서, 같은 함수를 창고마다 돌린다.

```text
 앨범 1 + 포카 1 주문을 창고마다 물어본다

   서울   앨범 3 ≥ 1  ✓    포카 0 ≥ 1  ✗  →  false
   대전   앨범 0 ≥ 1  ✗                   →  false
   부산   앨범 0 ≥ 1  ✗                   →  false
                                    통째로 되는 창고 없음
```

#### 3. TODO 3 — pick

정답 코드 (한 곳에만 보내는 갈래):

```java
if (splitting == Splitting.WHOLE_ONLY) {
    String chosen = null;
    for (Site site : orderedSites(order, siteChoice)) {
        if (canFillWhole(order, site.id())) {
            chosen = site.id();
            break;
        }
    }
    if (chosen == null) {
        return new Pick(
                order.id(), List.of(), Map.copyOf(order.lines()));
    }
    Map<String, Integer> picked = new LinkedHashMap<>();
    for (Map.Entry<String, Integer> line : order.lines().entrySet()) {
        picked.put(
                line.getKey(),
                warehouse.take(chosen, line.getKey(), line.getValue()));
    }
    bySite.put(chosen, picked);
    return new Pick(order.id(), shipments(bySite), Map.of());
}
```

정답 코드 (나눠 보내는 갈래):

```java
for (Map.Entry<String, Integer> line : order.lines().entrySet()) {
    int left = line.getValue();
    for (Site site : sitesFor(line.getKey(), siteChoice)) {
        if (left == 0) {
            break;
        }
        int taken = warehouse.take(site.id(), line.getKey(), left);
        if (taken == 0) {
            continue;
        }
        bySite.computeIfAbsent(site.id(), key -> new LinkedHashMap<>())
                .merge(line.getKey(), taken, Integer::sum);
        left -= taken;
    }
    if (left > 0) {
        unfilled.put(line.getKey(), left);
    }
}
return new Pick(order.id(), shipments(bySite), Map.copyOf(unfilled));
```

- 못 찾으면 반환하는 것: **출고 없는 `Pick`** — `shipments` 는 빈 목록, `unfilled` 는 **주문 줄 전부**.\
  `warehouse.take` 를 한 번도 안 부르므로 재고가 한 개도 안 준다.
- `unfilled` 에 들어가는 것: 주문의 모든 줄 그대로.\
  테스트가 `pick.unfilled() == {앨범 1, 포카 1}` 로 못 박았다.
- 잠긴 재고를 선반에 다시 올리는 것: **사람이 한다**(테스트 주석 원문).\
  코드가 조용히 만든 일을 사람이 손으로 되돌린다.

> **재고 잠김(stock lock)** — 어느 주문에도 못 쓰이는 채로 붙잡혀 있는 재고.\
> 예: 앨범1+포카1 주문에서 앨범만 먼저 빼두면, 포카가 들어올 때까지 그 앨범은 다른 주문에도 안 나가고 창고에도 없다.

> **원자성(atomicity)** — 통째로 되거나 통째로 안 되거나 둘 중 하나여야 한다는 성질.\
> 예: `WHOLE_ONLY` 는 모든 줄을 한 창고에서 다 빼거나, 한 개도 안 뺀다. "앨범만 빼둔 상태"를 안 남긴다.

- 훑는 순서가 `sitesFor` 와 다른 이유: `sitesFor` 는 **상품 하나** 기준이고, `WHOLE_ONLY` 는 **주문 전체**를 한 창고에서 봐야 해서다.\
  그래서 `orderedSites(order, siteChoice)` 라는 다른 정렬을 쓴다.
- `orderedSites` 가 재고 0 창고를 안 빼는 이유: **어차피 `canFillWhole` 이 거른다.**\
  "그 상품"이 아니라 "그 주문"이 기준이라 상품 하나로 거를 수도 없다.
- `stockScore` 가 더하는 값: **그 주문에 나오는 모든 상품의, 그 창고 재고 합.**\
  주문 전체를 채울 창고를 고르는 자리라 상품 하나만 봐서는 순위가 안 나온다.

```java
private int stockScore(PickOrder order, String siteId) {
    int sum = 0;
    for (String sku : order.lines().keySet()) {
        sum += warehouse.available(siteId, sku);
    }
    return sum;
}
```

- 한 줄을 채우는 루프가 멈추는 때: `left == 0` 이거나 **후보 창고를 다 훑었을 때.**
- `taken == 0` 이면 `continue` 인 이유: 그 창고에 실제로 없었다는 뜻이라 **상자를 만들면 안 된다.**\
  `break` 로 쓰면 뒤에 재고가 있는 창고가 남아 있어도 그 줄을 포기해, 채울 수 있는 주문이 미충족이 된다.
- 여러 줄이 같은 창고에서 나오면: **상자는 하나**다.\
  `bySite` 가 창고 id 로 묶고 `shipments()` 가 창고마다 `Shipment` 하나를 만든다.
- 서울 앨범 2 + 대전 앨범 3, 앨범 5개 주문 (`NEAREST`, `ALLOW_SPLIT`) 손계산:

```text
 sitesFor("앨범", NEAREST) = [서울(10), 대전(150)]   ← 부산은 재고 0 이라 빠짐
 left = 5
   서울   take(서울, 앨범, 5) → 있는 만큼 2  → left = 3
   대전   take(대전, 앨범, 3) → 3           → left = 0
 상자 [서울, 대전] 2 개,  거리 10 + 150 = 160 km,  충족
```

- 서울 앨범 3 + 부산 포카 5, 앨범1+포카1 주문 손계산:

```text
 ALLOW_SPLIT   앨범 → 서울에서 1,  포카 → 부산에서 1
               상자 2,  거리 10 + 400 = 410 km,  충족
               남은 재고  서울 앨범 2,  부산 포카 4

 WHOLE_ONLY    통째로 되는 창고 없음 → chosen == null
               상자 0,  거리 0,  미충족(unfilled = 앨범1 + 포카1)
               남은 재고  서울 앨범 3,  부산 포카 5   ← 그대로
```

- 재고를 실제로 빼는 것의 뜻: **부작용이 있는 함수**다.\
  같은 `pick` 을 두 번 부르면 두 번째는 재고가 줄어 다른 답이 나온다 — **멱등이 아니다.**\
  그래서 규칙끼리 비교하려면 `Warehouse.copy()` 로 같은 출발점을 복제해야 한다.

> **부작용(side effect)** — 함수가 값을 돌려주는 것 말고 바깥 상태까지 바꾸는 것.\
> 예: `pick` 은 `Pick` 을 돌려주면서 창고 재고도 실제로 줄인다.

> **멱등(idempotent)** — 같은 호출을 여러 번 해도 결과가 한 번 한 것과 같은 성질.\
> 예: `canFillWhole` 은 몇 번 불러도 같은 답이지만, `pick` 은 부를 때마다 재고가 줄어 답이 달라진다.

#### 4. TODO 4 — run

정답 코드:

```java
List<PickOrder> pending = new ArrayList<>(orders);
pending.sort(Comparator
        .comparingLong(PickOrder::placedAt)
        .thenComparing(PickOrder::id));

List<Pick> picks = new ArrayList<>();
List<String> unfilledOrders = new ArrayList<>();

while (!pending.isEmpty()) {
    int index = 0;
    if (orderSequence == OrderSequence.FILLABLE_FIRST) {
        for (int i = 0; i < pending.size(); i++) {
            if (fillableNow(pending.get(i), splitting)) {
                index = i;
                break;
            }
        }
    }
    PickOrder order = pending.remove(index);
    Pick pick = pick(order, siteChoice, splitting);
    picks.add(pick);
    if (!pick.filled()) {
        unfilledOrders.add(order.id());
    }
}
return new Run(List.copyOf(picks), List.copyOf(unfilledOrders));
```

- 먼저 정렬하는 이유: **받은 목록의 순서는 조회 쿼리가 준 순서**라서 믿을 게 못 된다.\
  정렬 키는 `placedAt`(들어온 순서), 그다음 `id`.
- `id` 를 2순위로 두는 이유: `placedAt` 이 같은 주문이 있으면 **순서가 흔들리기 때문**이다.\
  창고 타이브레이크와 같은 이유 — 어제 결과를 재현할 수 있어야 한다.
- 정렬을 안 하면: 우선순위가 **조회 쿼리의 `ORDER BY` 를 바꾸는 날 같이 바뀐다.**\
  테스트가 목록에 `o2` 를 먼저 담아 넘기고도 처리 순서가 `[o1, o2]` 임을 확인한다.
- `FILLABLE_FIRST` 가 매번 다시 훑는 이유: **"지금 채울 수 있나"는 재고가 줄면 바뀌기 때문**이다.\
  앞 주문이 뽑고 나면 뒤 주문의 판정이 달라져서, 한 번 세워둔 순서는 금세 틀린 순서가 된다.
- 하나도 못 채우면 `index` 는: **0 그대로** — 안쪽 for 문이 한 번도 `index` 를 안 바꾼다.
- 그때 멈추지 않는 이유: 멈추면 **남은 재고가 다음 입고 때까지 잠긴 채로 있고 아무것도 안 나간다.**\
  못 채워도 처리는 한다 — 부분 출고가 안 나가는 것보다 낫다(테스트 주석 원문).
- `unfilledOrders` 에 들어가는 것: **`filled()` 가 false 인 주문 전부** — 하나도 못 받은 주문과 **일부만 받은 주문 둘 다**.
- 서울 앨범 3 · o1(앨범5) · o2(앨범1) · o3(앨범1), `ALLOW_SPLIT` 손계산:

```text
 FIFO
   o1  앨범 5 요청 → 서울에서 3 만  → 2 모자람   (미충족, 상자 1)
   o2  후보 창고 없음(서울 0)       → 미충족
   o3  후보 창고 없음               → 미충족
   충족 0 건.  한 주문도 제대로 안 나갔다.  미충족 [o1, o2, o3]

 FILLABLE_FIRST
   fillableNow: o1 (3 < 5) false / o2 true  → o2 먼저   서울 3 → 2
   fillableNow: o1 false / o3 true          → o3        서울 2 → 1
   남은 것이 o1 뿐 → 채울 수 있는 것이 없으니 index 0 → o1, 1 개만
   충족 2 건.  처리 순서 [o2, o3, o1].  미충족 [o1]
```

- 밀린 주문: **제일 먼저 온 주문 o1** 이다.\
  공평함(선착순)을 버려서 총 출고량을 산 것이다.

> **기아(starvation)** — 우선순위 규칙 때문에 특정 요청이 계속 뒤로 밀리는 것.\
> 예: 앨범 5개짜리 큰 주문은 "지금 다 채울 수 있는 것"에 늘 못 들어서, 작은 주문들이 다 나간 뒤에야 처리된다.

- `picks` 가 "처리한 순서"인 것이 계약인 이유: **순서 설정이 일했는지를 그것으로만 확인할 수 있어서**다.\
  측정 다섯은 `picks` 안의 **위치(index)** 로 큰 주문의 평균 순번 9.31 → 9.85 를 잰다.\
  테스트도 `[o2, o3, o1]` 처럼 순서 자체를 assert 한다.

#### 5. 주어진 것 — fillableNow · take · Warehouse

- `fillableNow` 가 `Splitting` 을 받는 이유: **"채울 수 있다"의 뜻이 규칙마다 다르기 때문**이다.

```java
if (splitting == Splitting.WHOLE_ONLY) {
    for (Site site : warehouse.sites()) {
        if (canFillWhole(order, site.id())) {
            return true;
        }
    }
    return false;
}
for (Map.Entry<String, Integer> line : order.lines().entrySet()) {
    if (warehouse.totalAvailable(line.getKey()) < line.getValue()) {
        return false;
    }
}
return true;
```

- 같은 이름이 다른 뜻이어야 한다는 말: `WHOLE_ONLY` 의 "채울 수 있다"는 **한 창고 기준**, `ALLOW_SPLIT` 의 그것은 **합계 기준**이다.\
  판정 이름이 같다고 계산까지 같게 만들면, 한쪽에서 거짓말을 하게 된다.
- 합계로만 판정하면: 못 보낼 주문이 "채울 수 있는 것"으로 잡혀 **먼저 처리되고 아무것도 안 뽑고 끝난다.**\
  테스트가 `fillableNow(앨범1+포카1, ALLOW_SPLIT) == true`, `… WHOLE_ONLY == false` 와 처리 순서 `[o2, o1]` 로 둘 다 못 박았다.
- `take` 가 있는 만큼만 빼는 이유: **재고를 음수로 안 만들기 위해서**다.

```java
int have = available(siteId, sku);
int taken = Math.min(have, Math.max(0, quantity));
stock.get(siteId).put(sku, have - taken);
return taken;
```

- 음수가 되면 어긋나는 것: **그 뒤의 모든 판정**이다(javadoc 원문).\
  `available > 0` 후보 추리기, `canFillWhole` 비교, `totalAvailable` 합계가 전부 거짓이 된다.\
  `take` 가 **실제로 뺀 수**를 돌려주기 때문에 부르는 쪽이 부분 충족을 알아챌 수 있다.
- `Warehouse.copy()` 가 있는 이유: `pick` 이 재고를 실제로 바꾸므로, **두 규칙을 견주려면 같은 출발 재고를 복제**해야 한다(javadoc: "규칙끼리 견줄 때 쓴다").
- `PickOrder` 가 막는 것 셋: **빈 주문 번호 · 빈 주문 줄 · 수량이 1보다 작은 줄.**\
  그리고 받은 `lines` 를 `new LinkedHashMap<>(lines)` 로 복사해 밖에서 못 바꾸게 한다.
- `Site` 가 막는 것: **빈 창고 번호**와 **음수 거리**.

> **방어적 복사(defensive copy)** — 밖에서 넘어온 컬렉션을 그대로 안 들고, 복사본을 들고 있는 것.\
> 예: 주문을 만든 뒤 호출자가 자기 `Map` 에 줄을 하나 더 넣어도, 이미 복사해뒀으니 주문은 안 바뀐다.

### B. 개념

#### 6. 함정 (원본 README "함정")

- 넷: ① **재고가 0인 창고를 후보로 남기는 것** ② **못 보내는 주문에서 있는 것만 먼저 빼두는 것** ③ **목록 순서로 처리하는 것** ④ **"채울 수 있다"를 합계로 판정하는 것.**
- ①의 대가가 치러지는 곳: **창고 현장.**\
  코드는 아무 에러도 안 내고 출고 지시가 한 장 더 나간다 — "없는 것을 가지러 사람이 간다."\
  로그에도 예외에도 안 남는 비용이다.
- ②가 잠김인 이유: 뺀 재고는 **창고에도 없고 주문에도 안 붙은 상태**가 된다.\
  다른 주문이 그 앨범을 못 쓰고, 원래 주문도 포카가 들어올 때까지 안 나간다.\
  그리고 되돌리는 것은 사람 손이다.
- ③이 조회 쿼리와 엮이는 이유: 받은 `List` 는 대개 **DB 조회 결과**라 순서가 `ORDER BY` 에 달려 있다.\
  정렬 없이 그대로 쓰면 우선순위가 **쿼리를 손대는 날 같이 바뀐다** — 피킹 코드는 한 줄도 안 고쳤는데.
- ④가 틀린 뜻이 되는 이유: `WHOLE_ONLY` 는 **한 창고에서만** 보내는 규칙인데, 합계 판정은 "여러 창고를 합쳐 되나"를 묻는다.\
  묻는 질문 자체가 규칙과 다르다.

> **조용한 실패(silent failure)** — 예외 없이 정상처럼 끝나는데 결과만 틀린 실패.\
> 예: 합계로 판정한 `fillableNow` 는 에러 없이 돌지만, 못 보낼 주문을 먼저 처리하고 아무것도 안 뽑은 채 끝난다.

#### 7. 측정이 알려준 것

- 전제: **서울 10 km · 대전 150 km · 부산 400 km** 세 창고, **상품 8종**, 재고 10, 흩어짐 70 %, 주문 **20건씩 300회 = 6,000건**.
- 하나. `ALLOW_SPLIT` 대비 `WHOLE_ONLY`:

```text
                 충족     상자     거리        남은 재고
 나눠 보내기     4,135    8,367   1,296,710      4,553
 한 곳에만       3,646    3,646     451,830     12,385
                 -489    절반 이하   1/3         2.7 배
```

- 배송비만 보면 이길 수 없는데, 대가는 **요금표 밖에** 적혀 있다 — 충족 489건과 남은 재고다.
- 남은 재고 2.7배가 "그냥 재고 많음"이 아닌 이유: 그 재고는 **주문이 들어왔는데 못 나간 재고**, 곧 **팔 수 있었던 재고**다.\
  창고에 그대로 있으니 손실로 잡히지도 않는다.
- 둘. `WHOLE_ONLY` 에서 두 순서: **충족 3,646 / 상자 3,646 / 거리 451,830 — 둘이 완전히 같다.**
- 같은 이유: `WHOLE_ONLY` 는 주문이 **통째로 나가거나 아예 안 나간다.**\
  부분 출고가 없으니 앞 주문이 뒤 주문 몫을 조금씩 갉아먹는 일이 없고, 순서를 바꿔도 나가는 것과 나가는 양이 안 바뀐다.\
  (처리 목록의 순서는 바뀐다. 지표만 안 바뀐다.)
- `ALLOW_SPLIT` 에서는 같은 설정이 충족을 **370건** 바꾼다(4,135 → 4,505).
- 설정 화면을 만드는 사람에게 주는 뜻: **한쪽 설정에서는 이 스위치가 죽어 있다.**\
  "순서 설정을 바꿨는데 숫자가 안 변한다"는 문의를 버그로 오해하기 딱 좋고, 반대로 진짜 죽은 스위치를 "원래 그런가 보다"로 넘기기도 쉽다.

> **죽은 설정(dead switch)** — 어떤 조합에서는 값을 하나도 안 바꾸는 설정.\
> 예: `WHOLE_ONLY` 를 켜두면 `FIFO` 와 `FILLABLE_FIRST` 의 충족·상자·거리가 완전히 같아서, 순서 설정이 아무 일도 안 한다.

- 셋. 창고 고르기:

```text
                   충족     상자     거리
 가까운 곳부터     4,135    8,367   1,296,710
 재고 많은 곳부터  4,135    8,307   1,346,190
                   같음    -60 개   +49,480 km
```

- 충족이 같은 이유: **어느 창고에서 뽑든 총 재고가 같기 때문**이다.\
  창고 고르기는 "어디서 뽑나"만 바꾸고 "얼마나 있나"를 안 바꾼다.
- 상자와 거리가 반대로 움직이는 뜻: **한쪽을 줄이면 다른 쪽이 는다.**\
  재고 많은 곳에서 뽑으면 한 창고로 뭉쳐져 상자가 60개 줄지만, 그 창고가 멀어서 거리가 49,480 km 는다.
- 위험한 이유: 충족률만 띄운 화면에서는 이 설정이 **아무 일도 안 하는 것처럼 보인다.**\
  실제로는 배송비를 움직이고 있는데, 보는 지표에 안 나와서 "꺼도 되는 설정"으로 오해된다.

> **관측 가능성(observability)** — 시스템이 실제로 무엇을 하고 있는지 밖에서 볼 수 있는 정도.\
> 예: 충족률만 보는 대시보드는 창고 고르기 설정의 효과(상자·거리)를 하나도 못 보여준다.

- 넷. 흩어짐별 충족:

```text
 흩어짐      나눠 보내기   한 곳에만
   0 %          4,147       3,055
  30 %          4,150       3,335
  70 %          4,135       3,646
 100 %          4,146       3,938
```

- "몰아두면 쉬워진다"가 틀린 이유: **몰아둔다는 것이 "상품마다 어느 한 창고"라는 뜻**이라서다.
- 그래서 세 상품짜리 주문이 **세 창고에 흩어진다** — 한 창고에서는 못 채운다.

```text
 흩어짐 0 %        앨범 → 서울 10개    포카 → 부산 10개   키링 → 대전 10개
                   앨범+포카+키링 주문 = 세 창고.  한 곳에만 규칙으로는 못 나감

 흩어짐 100 %      앨범 3/4/3  포카 2/5/3  키링 4/3/3  (서울/대전/부산)
                   한 창고가 셋 다 조금씩 갖고 있을 확률이 오른다
```

- 흩어져 있어야 확률이 오르는 이유: `WHOLE_ONLY` 에 필요한 것은 "많이"가 아니라 **"한 창고에 다 같이"** 라서다.\
  상품이 골고루 퍼져 있으면 어느 창고든 주문의 모든 상품을 조금씩은 갖게 된다.
- `ALLOW_SPLIT` 은 흩어짐을 **거의 안 탄다**(4,135 ~ 4,150).\
  합쳐서만 있으면 되니 어디에 있든 상관이 없다.
- 다섯. `FILLABLE_FIRST`: 충족 **4,135 → 4,505(+370)**, 큰 주문 평균 순번 **9.31 → 9.85**.
- 순번이 반 칸밖에 안 밀린 이유: **큰 주문도 결국 다 처리되기 때문**이다.\
  주문 20건을 끝까지 돌리므로 순번이 무한정 밀릴 수 없다.
- "밀린다"의 뜻: 영영 안 나간다가 아니라 **재고가 더 줄어든 뒤에 나간다.**\
  그래서 못 채운 큰 주문 수는 **940 → 807** 로 줄지만 0이 되지는 않는다.
- 여섯. 한 줄짜리 주문 + 넉넉한 재고: **2,100번 비교에서 0건**이 갈린다(300회 × 7비교).
- 같아지는 이유 셋: **줄이 하나면 나눌 일이 없고**(Splitting 무의미), **재고가 넉넉하면 순서가 필요 없고**(OrderSequence 무의미), **상품마다 창고가 하나면 고를 창고도 하나다**(SiteChoice 무의미).
- 테스트 설계에 주는 시사: **개발용 자료가 대개 이렇게 생겼다.**\
  그런 자료로만 돌리면 여덟 조합이 전부 같은 답을 내서 **어떤 설정도 검증되지 않는다** — 통과하는 테스트가 아무것도 안 지키고 있다.

#### 8. 변종 검증에서 고친 것 (원본 README)

- 변종 검증이란: 구현을 일부러 틀리게 고친 판(변종)을 만들어 **테스트가 그것을 잡는지** 보는 것.\
  안 잡히면 잘못은 변종이 아니라 테스트에 있다.

> **변종 검증(mutation testing)** — 코드를 일부러 망가뜨려 테스트가 실패하는지 확인하는 방법.\
> 예: 정렬 한 줄을 지운 판을 만들었는데 테스트가 다 통과하면, 그 정렬은 사실 아무도 안 지키고 있던 것이다.

- 하나. 통과한 변종: **`run` 의 정렬을 지운 판.**\
  통과한 이유는 테스트가 주문 목록을 **늘 들어온 순서대로** 넘겨줘서, 정렬을 해도 안 해도 결과가 같았기 때문이다.
- 잡은 방법: 실제 목록은 조회 쿼리가 주는 순서이므로, **목록을 뒤집어 넘겼다.**\
  `[o2, o1]` 을 주고도 처리 순서가 `[o1, o2]` 여야 한다는 테스트가 그 변종을 잡는다.
- 둘. 통과한 변종: **`fillableNow` 가 `Splitting` 을 무시하고 늘 합계로 판정하는 판.**
- 실제로 돌면: 못 보낼 주문(앨범1+포카1)이 "채울 수 있는 것"으로 잡혀 **먼저 처리되고 아무것도 안 뽑고 끝난다.**\
  지표는 조용히 나빠지고 예외는 안 난다.
- 잡은 방법: **처리 순서를 확인하는 테스트.**\
  `WHOLE_ONLY` + `FILLABLE_FIRST` 에서 처리 순서가 `[o2, o1]` 이어야 한다고 못 박으니, 합계 판정 판은 `[o1, o2]` 를 내며 실패한다.
- 약함의 공통 무늬: **테스트가 결과 숫자만 보고 "어떤 순서로, 어떤 입력에서" 를 안 봤다.**\
  둘 다 *입력을 늘 편한 모양으로만 줬거나*(정렬된 목록), *중간 결정을 안 관찰했다*(처리 순서).\
  실제 운영에서 들어오는 모양을 흉내 내니 둘 다 잡혔다.

#### 9. 생각해볼 것

*(원본 README는 질문만 던지고 답을 안 준다 — 아래는 코드 구조에 근거한 내 추론이다.)*

- 나눠 보낸 배송비를 누가 내나: 코드는 `Pick.shipmentCount()` 와 `distanceKm()` 로 **비용을 세기만 하고 누구에게 물릴지는 안 정한다.**\
  고를 수 있는 길은 셋 — 가게가 흡수(고객 경험 우선), 고객에게 상자 수만큼 청구(그러면 고객이 `WHOLE_ONLY` 를 고르고 싶어진다), 주문 접수 단계에서 **"나눠 보내도 되나"를 고객에게 물어 주문 속성으로 저장**. 셋째가 제일 정직한데, 그러려면 `Splitting` 이 전역 설정이 아니라 **주문마다의 값**이 되어야 한다 — 지금 시그니처는 `run(orders, …, splitting, …)` 로 전체 공통이라 그 변경은 계약 표면을 바꾼다. (원본에 근거 없음 — 내 추론)
- 가까운 창고가 먼저 마르면 재보충은 언제: `NEAREST` 는 **서울 재고를 먼저 0으로 만든다**(테스트가 `available("서울","앨범") == 0` 으로 확인). 재보충 시점을 정하려면 이 코드에 없는 값 둘이 필요하다 — **입고 리드타임**과 **창고별 소진 속도**. 지금 `Warehouse` 는 `put` 과 `take` 만 있고 시간 개념이 없으므로, 재보충은 이 모델 밖(별도 보충 계획 계층)의 일이다. 측정 셋이 시사하는 절충은 **평소엔 `NEAREST`(거리 1,296,710), 서울이 마를 때만 `MOST_STOCK`(거리 1,346,190)** 으로 섞는 것이고, 대가는 거리 49,480 km 다. (원본에 근거 없음 — 내 추론)
- 못 보낸 주문을 잡아두나 취소하나: 지금 `run` 은 **못 채운 주문을 `unfilledOrders` 에 이름만 남기고 끝낸다** — 재고를 안 잡으므로 "잡아두기"가 아예 구현되어 있지 않다. 잡아두려면 예약(reservation) 개념이 필요한데, 그건 곧 **함정 ②가 말한 재고 잠김을 의도적으로 하는 것**이다. 그래서 선택은 "잡아두기 vs 취소"가 아니라 **"누구의 재고를 얼마나 오래 잠글 것인가"** 다. 이 박스의 설계는 잠금을 피하는 쪽으로 기울어 있다. (원본에 근거 없음 — 내 추론)
- 큰 주문을 언제 강제로 올리나: 측정 다섯이 말하듯 큰 주문은 **영영 안 밀리고 평균 반 칸(9.31 → 9.85)만 밀린다** — 하루치가 끝나면 어차피 처리된다. 문제는 **날을 넘겨 계속 밀릴 때**인데, 지금 모델은 하루치 배치라 그 상태를 못 본다. 올리는 기준을 넣는다면 `PickOrder` 에 **대기 일수**를 두고 `fillableNow` 판정보다 먼저 보는 것이 자연스럽다 — 즉 `FILLABLE_FIRST` 를 "N일 넘게 밀린 주문은 무조건 맨 앞"으로 감싸는 형태다. 대가는 충족 370건 중 일부를 되돌려주는 것이다. (원본에 근거 없음 — 내 추론)

#### 10. 연결

- 세는 것의 차이: 알고리즘 트랙은 **비교 횟수**(같은 답으로 가는 비용)를 셌다.\
  여기서 세는 것은 **답 자체가 갈린 결과** — 충족 건수·상자 수·거리·남은 재고다.\
  답이 여럿이라 "빠른가"가 아니라 "무엇을 잃고 무엇을 얻나"를 잰다.
- "설정이 죽어 있다"는 무늬: 21장의 죽은 스위치와 같은 자리다(서머리가 그렇게 연결해둔다).\
  한 설정이 다른 설정의 값에 따라 효과가 0이 되는 구조다.
- "전부 아니면 전무": 데이터베이스의 **트랜잭션 원자성(commit/rollback)** 과 같다.\
  반쯤 뽑아둔 재고는 커밋 안 된 채 잠긴 행과 같은 모양이다.
- `FILLABLE_FIRST` 의 밀림: 운영체제 스케줄러의 **SJF(짧은 작업 우선)와 기아 문제**와 같다.\
  처리량은 오르고 긴 작업이 밀린다 — 그래서 실무 스케줄러는 **대기 시간에 따라 우선순위를 올리는 에이징**을 붙인다.
- 조회 쿼리 순서를 안 믿는 습관이 막는 버그: **`ORDER BY` 없는 쿼리에 의존한 순서 버그.**\
  DB 가 인덱스·실행계획을 바꾸는 날, 애플리케이션 코드는 한 줄도 안 바뀌었는데 우선순위가 바뀐다.
- 여덟 조합이 전부 같았던 테스트 자료: **테스트 자료가 분기를 구별하지 못하면 통과는 아무 뜻이 없다**는 원칙의 사례다.\
  변종 검증이 이걸 잡는 도구고, 여기서는 측정 여섯이 같은 사실을 숫자(2,100 비교 중 0)로 보여준다.

## 근거

- 기준 소스: `/home/jun/project/myway/domain-modeling-advanced/23-warehouse-pick/impl/com/domain/pick/Picker.java`
- 문제 원문: `/home/jun/project/myway/domain-modeling-advanced/23-warehouse-pick/src/main/java/com/domain/pick/Picker.java`(클래스 javadoc의 세 갈래 · TODO 1~4 javadoc · `fillableNow`), `/home/jun/project/myway/domain-modeling-advanced/23-warehouse-pick/src/main/java/com/domain/pick/Warehouse.java`(`take`·`copy`·`Site` 검증), `/home/jun/project/myway/domain-modeling-advanced/23-warehouse-pick/src/main/java/com/domain/pick/PickOrder.java`(주문 검증), `/home/jun/project/myway/domain-modeling-advanced/23-warehouse-pick/README.md`(함정 넷 · 측정 여섯 · 변종 검증 둘 · 생각해볼 것 넷)
- 계약·수치(테스트): `/home/jun/project/myway/domain-modeling-advanced/23-warehouse-pick/src/test/java/com/domain/pick/PickerTest.java` — 거리 10 / 400 · 재고 0 창고 제외 · `[가, 나, 다]` · 상자 2 거리 410 · `unfilled == {앨범 1, 포카 1}` · 서울 앨범 3·부산 포카 5 그대로 · `[서울, 대전]` 거리 160 · 충족 0건 vs 2건 · 처리 순서 `[o2, o3, o1]` · `[o1, o2]` 상자 1 · `[o2, o1]` · 잘못된 입력 5종 예외
- 측정 수치: `/home/jun/project/myway/domain-modeling-advanced/23-warehouse-pick/src/test/java/com/domain/pick/MeasurementTest.java` — 4,135 / 8,367 / 1,296,710 / 4,553 · 3,646 / 3,646 / 451,830 / 12,385 · 8,307 / 1,346,190 · 흩어짐 4,147·4,150·4,135·4,146 대 3,055·3,335·3,646·3,938 · 4,505 · 940 → 807 · 평균 순번 931 → 985(×100) · 2,100 비교 중 0
