# api-design/12-filtering-sorting-search — 정답

## 정답

### 1. 파라미터 = 쿼리 모양 선택권

- `?order_by=…&filter=…`가 바뀌면 서버가 DB에 보내는 SQL의 `WHERE`·`ORDER BY`가 바뀐다. 어떤 모양은 인덱스로 20행만 읽고, 어떤 모양은 전체를 읽고 정렬한다.
- 사서 비유: "제목순 20권"은 제목 카드 목록(인덱스)이 있어 앞 20장만 넘기면 된다. "표지 색깔순 20권"은 목록이 없어 서고 전체를 꺼내야 한다. 받을 수 있는 주문(허용 목록)을 정해 두고 나머지는 창구에서 거절(400)한다.

### 2. 출처별 규칙

- AIP-132: `order_by`는 쉼표 구분 필드, 기본 오름차순, `" desc"` 접미사, 남는 공백 무시, 하위 필드 `.`.
- AIP-160: 비교·논리·부정·탐색 연산자(should), `:`(has, must). 문법·스키마에 안 맞는 필터(없는 필드·타입이 다른 값 등)는 `INVALID_ARGUMENT`(should). 검증을 완화하면 그 차이를 문서화(must). 추가 구조·제한(예: 논리 연산자 개수 — "queries of death" 방지)을 둘 수 있고(may), 그 제한은 문서화해야 한다(must).
- JSON:API 1.1: `sort=-created,title`(`-`는 내림차순, MUST). 지원하지 않는 정렬이면 400(MUST). `filter` 파라미터 이름 묶음만 예약하고 전략은 정하지 않는다.
- 공통: 서버가 지원 목록을 정하고, 밖은 400.

### 3. 계획 비교

실험 A(PostgreSQL 17.11, 100만 행, `work_mem` 4MB):

| 쿼리 | 계획 | 시간 |
|---|---|---|
| `ORDER BY created_at DESC, id DESC LIMIT 20` | `Index Scan using product_created`, rows=20 | 0.139 ms |
| `ORDER BY name, id LIMIT 20` | `Parallel Seq Scan`(작업자당 333,333행) → `Sort Method: top-N heapsort Memory: 27kB` | 366.446 ms |
| 위 + `OFFSET 200000` | `Sort Method: external merge Disk: 16880kB`(작업자 둘도 17312kB·15760kB) | 2,879.601 ms |

- top-N heapsort는 상위 N개만 힙에 남겨 메모리가 작지만, 읽기는 전체다.
- offset이 깊으면 offset + limit개를 담을 힙이 메모리 한도(`work_mem`)를 넘는다. 그러면 top-N heapsort를 포기하고, 각 작업자가 받은 행 **전체**를 디스크 병합 정렬한다(작업자당 333,333행, 합 약 50MB). 200,020개만 정렬하는 것이 아니다.

### 4. 이웃 효과

실험 B(pgbench, 2 CPU 제한, 각 10초 1회):

```text
[단독 idx] latency average = 1.150 ms
[단독 idx] tps = 3479.636069 (without initial connection time)
[noidx 4개와 동시 idx] latency average = 6.554 ms
[noidx 4개와 동시 idx] tps = 610.347837 (without initial connection time)
```

- 정상 요청의 평균 지연이 약 5.7배, 처리량이 약 6분의 1이 됐다. 비싼 쿼리가 CPU·I/O를 나눠 가져가기 때문이다.
- 단독 비교로는 인덱스 정렬 2,980 tps vs 비인덱스 정렬 2.5 tps(동시 8)였다.
- 사실 점검 재실행(각 5초)도 같은 경향이었다: 단독 idx 1.024ms·3,906 tps → noidx 4개와 동시 5.438ms·736 tps. 수치는 실행마다 다르다.

### 5. 정렬을 바인딩하면

- 결과는 `1, 2, 3, 4` — 내림차순이 아니다. `EXPLAIN`에 Sort 노드도 없다(실험 C).
- `$1`은 **값** 자리다. `'id DESC'`라는 문자열 상수로 정렬하는 것이 되고, 상수는 행마다 같아 정렬 효과가 없다. 문법상 문제가 없으니 에러가 안 난다.

### 6. 식별자와 값

- 식별자(열 이름·정렬 방향·연산자): 바인딩할 수 없다. 허용 목록에서 꺼낸 **고정 문자열**로만 SQL에 넣는다.
- 값(`'open'`, `1000`): 타입을 검사한 뒤 `?`로 바인딩한다.
- 허용 목록이 막는 위험
  - SQL 인젝션: `order_by=price; DROP TABLE product--`(실험 C에서 400).
  - 인덱스 없는 정렬·필터로 인한 DB 과부하: `order_by=name`(실험 C에서 400, 지원 목록 안내).

### 7. 복합 인덱스와 조합

- `filter=category=7&order_by=price` → 인덱스 `(category, price, id)`. B+Tree에서 category가 같은 행끼리 price, id 순으로 붙어 있으므로 "category=7 구간을 앞에서부터 20개"가 범위 스캔 하나다(실험 Q4: `Index Only Scan`, 0.236ms).
- 순서가 `(price, category)`면 category=7 행들이 price 전 범위에 흩어져 있어 범위 스캔 하나로 그 구간만 읽을 수는 없다. 대신 price 순서로 훑으며 인덱스 안에서 거를 수 있다. 흔한 값(category=7, 5%)은 금방 20개를 채워 0.188ms였고, 없는 값(category=99)은 전체 훑기 + 정렬로 82.851ms였다(실험 A 관찰 6). 비용이 값의 빈도에 좌우된다.
- `filter=price=12345&order_by=created_at desc`: price 단독(또는 선두) 인덱스가 없어 전체를 훑으며 필터했다(`Parallel Seq Scan`, `Rows Removed by Filter: 333330`, 결과 10건에 76ms). 정렬 인덱스만으로는 드문 필터를 빨리 못 찾는다.

### 8. 부분 문자열 검색

- B+Tree는 값의 **앞부분**으로 정렬돼 있다. `'%abc12%'`처럼 앞이 열린 패턴은 시작 위치를 정할 수 없어 범위 스캔이 안 된다.
- 실험 Q6: 인덱스 없이 `Rows Removed by Filter: 333322`(작업자당), 1,299.773ms. `pg_trgm` GIN 뒤 `Bitmap Index Scan on product_name_trgm`(후보 41행) → `Bitmap Heap Scan`(재검사로 7행 탈락), 4.046ms.
- 뽑을 트라이그램이 없는 패턴(아주 짧은 검색어 등)은 인덱스 전체 스캔으로 퇴화한다(PostgreSQL 17 F.33). 검색어 최소 길이를 두는 이유다.

### 9. 정렬과 커서

- 커서에는 **현재 정렬의 키 전부 + 동률 깨기 키**가 들어가야 한다. `order_by=price`면 `(price, id)`.
- 토큰에 필터·정렬을 함께 묶어, 다음 쪽 요청에서 바뀌면 400(AIP-158). 정렬이 바뀌었는데 옛 커서를 쓰면 엉뚱한 위치에서 이어진다.

### 10. "아무 열이나 정렬" 뒤 DB 포화

- 보는 것
  - `pg_stat_statements`·느린 쿼리 로그에서 `ORDER BY <인덱스 없는 열>` 쿼리의 호출 수·평균 시간.
  - 그 쿼리의 `EXPLAIN (ANALYZE)`에 `Seq Scan` + `Sort`(top-N heapsort·external merge).
  - 다른 정상 엔드포인트 지연이 같이 올랐는지(이웃 효과, 실험 B).
- 대처
  - 응급: 해당 정렬 비활성화 또는 엔드포인트 속도 제한, `statement_timeout`.
  - 근본: 허용 정렬 목록을 정하고 밖은 400. 필요한 정렬은 `(필터 열, 정렬 열, id)` 인덱스를 만든 뒤 목록에 추가. 뒤쪽 페이지는 커서로.
