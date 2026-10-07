# data-engineering/15-data-mesh-and-data-products — 데이터 메시와 데이터 제품: 도메인 소유·제품으로서의 데이터·셀프서비스 플랫폼·연합 계산 거버넌스 — 정리 (힌트)

## 해결하는 문제

회사에 분석 데이터를 만드는 중앙 데이터 팀이 하나 있다.\
원천 팀은 데이터를 던지고, 소비 팀은 줄을 선다. 가운데 팀은 양쪽 업무를 다 모른다.

```text
  원천 도메인                중앙 데이터 팀(병목)                    소비 도메인
  주문팀   ─ 이벤트 ─┐                                            ┌─ 매출 리포트 (대기 3주)
  재생팀   ─ 로그   ─┼──>  수집 → 정제 → 변환 → 서빙  ──>  backlog ┼─ 추천 모델 (대기 5주)
  결제팀   ─ DB     ─┘   (도메인 지식 없음, 품질 책임만 짐)          └─ 정산 (대기 2주)
                         원천 팀: 하류가 뭘 쓰는지 모름 → 컬럼을 예고 없이 바꿈
```

- Dehghani(2019)가 든 중앙 플랫폼의 실패 모드 셋
  1. *중앙 집중·모놀리식*: 모든 원천의 수집·정제·서빙을 한 플랫폼이 한다.
  2. *파이프라인 단계별 분해*: 수집·처리·서빙으로 팀을 나눠, 새 기능 하나가 모든 단계를 건드린다.
  3. *사일로화된 초전문 소유*: 플랫폼 엔지니어가 원천·소비 도메인과 떨어져 있다. "의미 있고 정확한 데이터를 줄 동기가 없는 팀"에게서 데이터를 받는다.
- 데이터 메시의 답: 분석 데이터도 **그 데이터를 만드는 도메인이 소유하고 제품처럼 내놓는다.** 공통 인프라는 플랫폼으로, 공통 규칙은 자동화된 정책으로 준다.
  - *데이터 메시(data mesh)*: Zhamak Dehghani가 2019년 글에서 제안한 분석 데이터 아키텍처·조직 방식. 2020년 글에서 네 원칙으로 정리했다.
  - *데이터 제품(data product)*: 도메인이 다른 팀에게 내놓는 분석 데이터 단위. 데이터뿐 아니라 그것을 만드는 코드·메타데이터·인프라를 포함한다(2020).

쉬운 예: 회사 식당 하나 vs 푸드코트다.
- 식당 하나는 메뉴를 늘릴수록 주방 하나가 막힌다.
- 푸드코트는 가게마다 자기 메뉴를 책임진다. 대신 계산대·위생 기준·식판 규격은 건물이 정한다.
- 기준 없이 가게만 늘리면 식판이 안 맞고, 주인 없는 빈 가게가 생긴다.

똑같은 구조다.\
"가게" = 도메인의 데이터 제품, "건물 설비" = 셀프서비스 플랫폼, "위생 기준" = 연합 거버넌스다.

실무 예:
- 데이터 요청이 중앙 팀 backlog에서 몇 주씩 기다린다.
- 경영 회의에서 "활성 사용자"가 성장팀·콘텐츠팀 보고서마다 다르다(이 노트의 실험).
- 팀마다 데이터를 내놓기 시작했는데, 1년 뒤 아무도 주인을 모르는 테이블이 수백 개다.

## 동작·원리

### 1. 네 원칙 (Dehghani 2020 "Data Mesh Principles and Logical Architecture")

```text
  ① 도메인 소유          분석 데이터의 책임을 원천에 가장 가까운 도메인으로
  ② 제품으로서의 데이터   소비자를 고객으로. 찾기·이해·신뢰를 제품 품질로
  ③ 셀프서비스 플랫폼     도메인이 인프라 전문가 없이 제품을 만들고 운영하게
  ④ 연합 계산 거버넌스    도메인 대표들이 정한 전역 규칙을 플랫폼이 코드로 자동 적용

  ①만 하면 → 사일로·호환 불가        ②가 품질·발견 문제를 막고
  ③이 도메인마다 인프라 복제 비용을 막고   ④가 상호운용·규정 준수 문제를 막는다
```

- 글은 네 원칙이 "함께 필요하고 충분하도록" 의도했다고 적는다. 하나만 떼어 도입하는 것을 경계하는 표현이다(해석).
- 책: Dehghani, 『Data Mesh』(O'Reilly, 2022년 3월). 같은 네 원칙을 장 단위로 다룬다(O'Reilly 도서 페이지 목차로 확인, 본문 미열람).

### 2. 데이터 제품의 조건 (Dehghani 2019 "Domain data as a product")

| 조건 | 뜻 | 없으면 |
|---|---|---|
| Discoverable | 카탈로그에 등록돼 찾을 수 있다(소유자·출처·계보·샘플) | 같은 데이터를 팀마다 다시 만든다 |
| Addressable | 전역 규칙을 따르는 고유 주소로 프로그램이 접근한다 | 경로를 사람에게 물어본다 |
| Trustworthy and truthful | 진실성에 대한 SLO를 소유자가 제시한다. 생성 지점에서 정제·무결성 검사 | 소비자가 매번 다시 검증한다 |
| Self-describing | 의미와 문법(스키마)이 설명돼 있고 샘플이 있다 | 소비자가 소유자에게 계속 묻는다 |
| Inter-operable, 전역 표준 준수 | 필드 형식·다의어(polyseme) 식별·주소 규칙·이벤트 형식(CloudEvents 등) 표준 | 도메인 간 조인이 안 된다 |
| Secure, 전역 접근 제어 | 정책은 중앙에서 정의, 제품마다 접근 시점에 적용 | 권한이 제품마다 제각각 |

- *다의어(polyseme)*: 여러 도메인에 다른 속성·식별자로 나타나는 같은 개념. 2019년 글의 예는 '아티스트'(재생 도메인과 정산 도메인이 다르게 식별), 2020년 글의 예는 '팟캐스트 청취자'(사용자 식별은 전역 관심사)다.
- 같은 데이터에서 성격이 다른 제품을 둘 낼 수 있다. 2019년 글의 예: '재생 이벤트' 도메인이 누락·중복이 있는 준실시간 제품과, 늦지만 더 정확한 제품을 따로 낸다. 각 제품이 자기 SLO를 정한다.

### 3. 데이터 제품 = 아키텍처 퀀텀 (2020)

```text
  ┌──────────────── 데이터 제품: "재생 집계" (콘텐츠 도메인) ────────────────┐
  │ 코드      : 파이프라인(소비·변환·서빙), 접근 API, 정책 집행(접근·규정·출처)   │
  │ 데이터·메타: 일별 집계 테이블 + 스키마·의미·품질 지표·SLO                    │
  │ 인프라    : 빌드·배포·실행·저장 (플랫폼이 제공)                               │
  └─ 입력 포트: 재생 이벤트 스트림 ──────────── 출력 포트: 테이블 v2, 이벤트 v1 ─┘
```

- *아키텍처 퀀텀(architectural quantum)*: 독립 배포 가능하고 기능 응집도가 높으며 자기 기능에 필요한 구조 요소를 다 가진 가장 작은 아키텍처 단위(2020 글이 Evolutionary Architecture의 정의를 인용 — 2019 글은 책 『Building Evolutionary Architectures』를 출처로 든다).
- 과거 방식과의 차이: 파이프라인(코드)을 그것이 만드는 데이터와 따로 관리하고, 웨어하우스 인스턴스 같은 인프라를 여러 데이터셋이 공유했다. 메시는 셋을 도메인의 바운디드 컨텍스트 단위로 묶는다(2020). → [domain-modeling/16-bounded-contexts](../../domain-modeling/16-bounded-contexts/2-summary.md)

### 4. 연합 계산 거버넌스 — 무엇을 전역으로, 무엇을 도메인에

```text
  전역(연합 팀이 정하고 플랫폼이 자동 집행)        도메인(각 팀이 정함)
  ─────────────────────────────────────────       ─────────────────────────
  다의어 식별 규칙 (사용자 ID, 아티스트 ID)          자기 도메인의 데이터 모델
  품질을 "어떻게 표현할지"(SLO 형식)               자기 품질 지표의 목표값
  민감도 등급·규제 요구 정의                       제품 분할·서빙 형식
  주소·메타데이터·이벤트 형식 표준
```

- 2020 글의 대조표 일부
  - 중앙 팀이 데이터 품질을 책임진다 → 연합 팀은 "무엇이 품질인지 모델링하는 법"을 정한다.
  - 전역 정규(canonical) 데이터 모델 → 도메인을 넘나드는 다의어만 모델링한다.
  - 사람이 개입하는 수작업 → 플랫폼이 구현한 자동 프로세스.
  - 오류를 막는다 → 오류를 감지하고 플랫폼의 자동 처리로 복구한다.
  - 거버넌스한 테이블 수로 성공을 잰다 → 메시 위의 소비 연결(네트워크 효과)로 잰다.
- "계산(computational)"의 뜻: 규칙을 문서가 아니라 플랫폼의 코드로 집행한다. 데이터 계약 검사([09 data-contracts-and-schema-registry](../09-data-contracts-and-schema-registry/2-summary.md))와 같은 강제 지점이 그 구현 수단이다.

### 5. 서술자 표준 — 표준이 요구하는 것 vs 조직 정책이 요구하는 것

- Bitol의 *ODPS*(Open Data Product Standard, v1.1.0)는 데이터 제품을 YAML로 서술하는 표준이다. 출력 포트마다 *ODCS*(Open Data Contract Standard) 계약을 `contractId`로 가리킬 수 있다.

```yaml
apiVersion: v1.1.0          # 필수
kind: DataProduct           # 필수
id: 064c4630-...            # 필수
status: active              # 선택: proposed, draft, active, deprecated, retired
outputPorts:                # 필수, 최소 1개 ("출력 없는 데이터 제품은 쓸모없다")
  - name: processed-data    # 필수
    version: 1.0.0          # 선택
    contractId: 8765...     # 선택
# team: {name: ...}         # 선택
```

- 위 필수·선택 구분은 ODPS v1.1.0 문서의 Fundamentals·Product Information·Team 필드 표 그대로다.
- 표준은 소유 팀(`team`)과 계약(`contractId`)을 **선택**으로 둔다. "제품마다 소유자와 계약"은 조직의 전역 정책으로 따로 집행해야 한다. 연합 계산 거버넌스가 하는 일이 이것이다.

### 실험: '활성 사용자' 정의 4개, 서술자 정책 검사, 주인 없는 테이블

- 환경: 호스트 Python 3.12.3 표준 라이브러리(합성 데이터 `user_001` 형식, `random.seed(42)` — 두 번 실행해 출력 동일), PostgreSQL 17.11(`postgres:17`, `--network none --cpus=2`).
- **모형이다.** 서술자는 ODPS 모양을 흉내 낸 dict이고, 정책은 이 실험이 정한 예시 규칙이다.

```python
def active(types, days):
    since = AS_OF - dt.timedelta(days=days - 1)
    return {u for (u, t, d) in events if t in types and since <= d <= AS_OF}

def platform_policy(p):          # 이 조직의 전역 규칙(예시) — 표준보다 엄격하다
    errs = []
    if not p.get("team", {}).get("name"): errs.append("소유 팀 없음")
    for port in p.get("outputPorts", []):
        if not port.get("contractId"): errs.append(f"포트 {port['name']}: 데이터 계약 없음")
    if p.get("status") == "active" and "slo" not in p: errs.append("active인데 SLO(신선도) 없음")
    if p.get("status") == "retired":
        for port in p.get("outputPorts", []):
            if consumers.get(port["table"]): errs.append(f"retired인데 소비자 있음: {consumers[port['table']]}")
    return errs
```

출력:

```text
  A. 같은 이벤트 로그, '활성 사용자' 정의별 숫자 (사용자 1000명, 기준일 2026-10-07)
     growth팀  (30일 내 login)              505
     content팀 (30일 내 play)               183
     billing팀 (30일 내 login|payment)      580
     marketing (7일 내 login)              118
     growth에만 있음 322, content에만 있음 0, 둘 다 183
     전역 정의 active_user_30d를 세 팀이 같이 쓰면: [505, 505, 505]
  B. 서술자 검사: 표준 필수 필드 vs 플랫폼 정책
     dp-orders  표준=PASS  정책=PASS
     dp-plays   표준=PASS  정책=['포트 plays_raw: 데이터 계약 없음']
     dp-churn   표준=PASS  정책=['소유 팀 없음', 'active인데 SLO(신선도) 없음']
     dp-legacy  표준=PASS  정책=["retired인데 소비자 있음: ['finance.monthly_close']"]
     카탈로그 테이블 7개 중 어느 제품의 출력 포트도 아닌 것 3개:
       ['tmp.adhoc_export_0412', 'growth.churn_score_backup', 'order.orders_daily_old']
```

- 관찰 A: 오류 하나 없이 같은 로그에서 118~580이 나왔다. 어느 숫자도 "틀린" 계산이 아니다. 정의가 다를 뿐이다. 전역 정의를 하나로 묶자 같은 숫자가 나왔다.
  - "content에만 있음 0"은 합성 데이터를 그렇게 만들었기 때문이다(재생 날짜를 로그인 날짜 이전으로 생성).
- 관찰 B: 네 제품 모두 모형의 표준 검사(`표준=PASS`)는 통과했다. 실제 ODPS 필수 필드 검사 통과가 아니다. 단, 모형의 표준 검사는 `kind`·`id`·`outputPorts` 1개 이상만 본다. 모형 서술자에는 `apiVersion`(ODPS 필수)이 없어서, 실제 ODPS 검증기라면 네 개 모두 그 항목에서 걸린다. 결론(소유자·계약은 표준이 강제하지 않는다)은 `team`·`contractId`가 선택 필드라는 문서 표로 뒷받침한다. 소유자 없음·계약 없음·은퇴했는데 소비자 있음은 조직 정책 검사에서만 잡혔다.

PostgreSQL 쪽 진단(같은 발상, 카탈로그 테이블 대신 DB 통계):

```sql
-- 소유자 표기(테이블 주석 JSON의 owner)가 없거나, 통계 초기화 이후 한 번도 읽히지 않은 테이블
SELECT n.nspname || '.' || c.relname AS table_name,
       obj_description(c.oid, 'pg_class')::jsonb ->> 'owner' AS owner,
       s.seq_scan + coalesce(s.idx_scan, 0) AS scans,
       greatest(s.last_seq_scan, s.last_idx_scan) AS last_read
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_stat_user_tables s ON s.relid = c.oid
WHERE c.relkind = 'r' AND n.nspname NOT IN ('pg_catalog', 'information_schema')
  AND (obj_description(c.oid, 'pg_class')::jsonb ->> 'owner' IS NULL
       OR s.seq_scan + coalesce(s.idx_scan, 0) = 0)
ORDER BY 1;
```

```text
          table_name         | owner | scans | last_read
  ---------------------------+-------+-------+-----------
   growth.churn_score        |       |     0 |
   growth.churn_score_backup |       |     0 |
   tmp.adhoc_export_0412     |       |     0 |
  (owner 주석이 있고 한 번 읽힌 orders.orders_daily는 빠졌다)
```

- `last_seq_scan`·`last_idx_scan` 컬럼은 PostgreSQL 16부터 있다(16판 "Monitoring Database Activity" 문서에는 있고 15판에는 없음을 대조, 17.11에서 실행 확인). 통계는 비정상 종료 뒤 시작(즉시 종료·크래시·베이스 백업·PITR에서 시작)이나 `pg_stat_reset()`으로 초기화될 수 있으니 "0회"는 "통계 기간 안에 0회"다. 정상 종료 뒤 재시작에서는 보존된다(PostgreSQL 17 "The Cumulative Statistics System").

## 쓰이는 자료구조·알고리즘

- 커리큘럼은 이 주제에 고유 자료구조를 두지 않았다(🔧 "—"). 구현에서 쓰이는 것만 적는다.
- **카탈로그 = 색인** — 제품 ID·주소 → 서술자(소유자·계약·SLO·계보). 키 조회와 검색이다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)
- **집합 차집합으로 고아 찾기** — `카탈로그 테이블 − 출력 포트 테이블`. 실험 B의 `orphans`다.
- **제품 의존 그래프** — 입력 포트 → 출력 포트 간선. 은퇴할 제품의 소비자 찾기는 이 그래프의 역방향 탐색이다. [11 data-lineage](../11-data-lineage/2-summary.md), [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md)
- **식별자 매핑 표** — 다의어(사용자·아티스트)를 도메인 로컬 ID ↔ 전역 ID로 잇는다. [domain-modeling/16-bounded-contexts](../../domain-modeling/16-bounded-contexts/2-summary.md)의 같은 구조.
- **규칙 평가(policy as code)** — 서술자마다 규칙 함수 목록을 돌려 위반 목록을 모은다. 아키텍처 규칙 검사기와 같은 모양이다. [software-design/41-architecture-fitness-rules](../../software-design/41-architecture-fitness-rules/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 증상에서 출발

| 증상(숫자·지표) | 원인 후보 | 확인 |
|---|---|---|
| 데이터 요청 리드타임이 수주, 중앙 팀 backlog만 쌓인다 | 중앙 병목, 도메인 지식 부재 | 요청 티켓의 대기 시간 분포, 요청 출처 도메인 |
| 같은 지표가 보고서마다 다르다 | 다의어·지표 정의가 도메인별로 다름 | 지표 정의 SQL을 나란히 비교, 실험 A처럼 같은 로그에 정의별로 계산 |
| 주인 모르는 테이블·버킷이 늘어난다 | 거버넌스 없이 분산 | 위 진단 SQL, 카탈로그 − 출력 포트 차집합 |
| 도메인마다 파이프라인 인프라를 따로 만든다(비용·장애 제각각) | 셀프서비스 플랫폼 없음 | 도메인별 인프라 비용, 중복 도구 수 |
| 은퇴한 테이블을 지웠더니 월말 정산이 깨졌다 | 소비자·계보 미등록 | 제품 의존 그래프, 쿼리 로그의 읽기 주체 |

### 2. 도입 순서 (점진)

1. 지표 정의 충돌부터 고친다. 경영 보고에 쓰는 다의어(활성 사용자·매출·고객)를 전역 정의로 정하고 소유 도메인을 지정한다.
2. 데이터 제품 서술자를 정한다(ODPS 등). 소유 팀·출력 포트 계약·SLO를 조직 정책으로 필수화한다.
3. 정책을 CI·플랫폼의 등록 단계에서 자동 검사한다. 위반이면 등록을 막거나 경고한다(차단 vs 경고는 [10 data-quality-and-data-observability](../10-data-quality-and-data-observability/2-summary.md)).
4. 도메인 하나를 골라 첫 제품을 낸다. 플랫폼은 그 제품이 실제로 필요로 한 것부터 만든다.
5. 주인 없는 테이블을 정기적으로 찾아 소유자 지정·보관·삭제 중 하나로 처리한다.

### 3. 정책 검사를 코드로 (Java 21)

```java
record OutputPort(String name, String table, String contractId) {}
record DataProduct(String id, String status, String team, List<OutputPort> outputPorts, Integer freshnessHours) {}

static List<String> violations(DataProduct p, Map<String, List<String>> consumersByTable) {
    var errs = new ArrayList<String>();
    if (p.team() == null || p.team().isBlank()) errs.add("소유 팀 없음");
    if (p.outputPorts().isEmpty()) errs.add("출력 포트 없음");
    for (var port : p.outputPorts())
        if (port.contractId() == null) errs.add("포트 " + port.name() + ": 데이터 계약 없음");
    if ("active".equals(p.status()) && p.freshnessHours() == null) errs.add("active인데 SLO 없음");
    if ("retired".equals(p.status()))
        for (var port : p.outputPorts())
            if (!consumersByTable.getOrDefault(port.table(), List.of()).isEmpty())
                errs.add("retired인데 소비자 있음: " + consumersByTable.get(port.table()));
    return errs;
}
```

- 실험 B의 Python 규칙을 Java로 옮긴 것이다. 같은 서술자 4개로 실행(JDK 21.0.12)해 Python판과 같은 위반 목록을 얻었다(`dp-orders []`, `dp-plays [포트 plays_raw: 데이터 계약 없음]`, `dp-churn [소유 팀 없음, active인데 SLO 없음]`, `dp-legacy [retired인데 소비자 있음: [finance.monthly_close]]`). 규칙 자체는 조직이 정하는 예시다.

### 4. 언제 맞지 않나 (비용)

- 플랫폼과 도메인 쪽 데이터 역량에 투자해야 한다. 2020 글도 인프라 기술이 전문적이라 도메인마다 복제하기 어렵다는 점을 셀프서비스 플랫폼 원칙의 이유로 든다.
- 도메인이 적고 데이터 소비가 단순하면, 중앙 팀 + 명확한 데이터 계약이 더 싸다(해석).
- 거버넌스 없이 "팀마다 알아서"만 하면 메시가 아니라 사일로가 늘어난다(장애 시나리오 3).

## 장애 시나리오와 대처

### 1. 중앙 팀 병목 → 요청이 수주씩 대기한다

- **현상**: 새 지표 하나에 몇 주. 소비 팀이 원천 DB를 직접 조회하기 시작한다.
- **보이는 형태**: 데이터 요청 티켓 대기 시간 중앙값이 수주(예시). 중앙 팀이 원천 스키마 변경을 사후에 알아 파이프라인이 자주 깨진다.
- **원인**: 원천·소비 도메인 지식 없이 한 팀이 분석 데이터를 도맡는다(Dehghani 2019의 세 실패 모드).
- **대처**: 원천에 가까운 도메인이 데이터 제품을 소유하게 옮긴다. 중앙 팀은 플랫폼 팀이 된다. 한꺼번에가 아니라 도메인 하나씩 옮긴다.

### 2. 도메인마다 "활성 사용자" 정의가 다르다 → 경영 보고 숫자가 서로 다르다

- **현상**: 같은 회의에서 활성 사용자가 505와 183과 580으로 보고된다.
- **보이는 형태**: 오류는 없다. 각 팀의 SQL은 맞다. 실험 A에서 같은 로그로 118~580이 나왔다.
- **원인**: 도메인을 넘나드는 다의어를 전역으로 정하지 않았다. 2020 글은 다의어 모델링을 연합 거버넌스의 책임으로 둔다.
- **대처**: 전역 정의(이름·식·소유 도메인)를 하나 정해 공유 함수·지표 계층으로 제공한다. 팀 고유 지표는 다른 이름을 쓰게 한다(`active_user_30d` vs `content_player_30d`).

### 3. 거버넌스 없이 분산 → 아무도 소유하지 않는 테이블이 쌓인다

- **현상**: 테이블 수와 저장 비용이 계속 는다. 삭제 요청([12 data-retention-and-erasure](../12-data-retention-and-erasure/2-summary.md))을 처리할 때 어디에 복제됐는지 모른다.
- **보이는 형태**: 진단 SQL에 owner 주석 없음·읽기 0회 테이블. 실험 B에서 카탈로그 7개 중 3개가 어느 제품의 출력 포트도 아니었다.
- **원인**: 도메인 소유만 도입하고 연합 계산 거버넌스(전역 규칙의 자동 집행)를 빠뜨렸다. 표준 서술자만으로는 소유자가 선택 필드라 못 막는다(ODPS v1.1.0).
- **대처**: 등록 단계에서 소유자·계약 필수 정책을 자동 검사한다. 주인 없는 테이블은 기한을 두고 소유자 지정 → 보관 → 삭제 순으로 처리한다.

### 4. 셀프서비스 플랫폼 없이 분산 → 도메인마다 인프라를 다시 만든다

- **현상**: 팀마다 다른 스케줄러·저장소·품질 도구를 쓴다. 장애 대응 방식도 제각각이다.
- **보이는 형태**: 도메인별 인프라 비용 합이 중앙 플랫폼 시절보다 크다. 같은 종류 도구가 여러 개다.
- **원인**: 인프라 기술은 전문적이라 도메인마다 복제하기 어렵다(2020 글). 플랫폼이 고수준 추상화를 주지 않으면 도메인이 각자 만든다.
- **대처**: 데이터 제품의 생성·배포·관측·등록을 플랫폼의 공통 경로로 제공한다. 도메인은 제품 로직에 집중한다.

### 5. 은퇴한 데이터 제품을 지웠다 → 하류 정산이 깨진다

- **현상**: 월말 정산 잡이 테이블 없음으로 실패하거나, 이전 값으로 조용히 계산한다.
- **보이는 형태**: 실험 B의 `retired인데 소비자 있음: ['finance.monthly_close']` 같은 위반이 미리 있었다.
- **원인**: 소비자 등록·계보가 없어 은퇴 영향 범위를 몰랐다.
- **대처**: 상태를 `deprecated` → `retired`로 단계적으로 옮기고, 소비자가 0이 될 때까지 지우지 않는다. 계보 그래프로 소비자를 찾는다([11 data-lineage](../11-data-lineage/2-summary.md)).

## 핵심 문장

- 데이터 메시는 분석 데이터의 소유를 중앙 팀에서 그 데이터를 만드는 도메인으로 옮기고, 데이터를 소비자가 있는 제품으로 다룬다.
- 네 원칙(도메인 소유·제품으로서의 데이터·셀프서비스 플랫폼·연합 계산 거버넌스)은 함께 있어야 한다. 소유만 나누면 사일로가 는다.
- 연합 거버넌스는 전역으로 정할 것(다의어 식별·품질 표현 형식·보안 등급)과 도메인이 정할 것(자기 모델·목표값)을 나누고, 전역 규칙을 플랫폼 코드로 자동 집행한다.
- "활성 사용자"처럼 도메인을 넘나드는 정의가 갈리면, 오류 없이 경영 숫자가 서로 달라진다.
- 서술자 표준은 소유자·계약을 선택으로 두기도 한다. "제품마다 소유자"는 조직 정책으로 따로 강제해야 주인 없는 테이블이 쌓이지 않는다.

## 관련 주제·근거

- 선행
  - [09 data-contracts-and-schema-registry](../09-data-contracts-and-schema-registry/2-summary.md) — 출력 포트의 계약
  - [11 data-lineage](../11-data-lineage/2-summary.md) — 제품 사이 의존·영향 분석
  - [domain-modeling/16-bounded-contexts](../../domain-modeling/16-bounded-contexts/2-summary.md) — 데이터 제품 경계 = 바운디드 컨텍스트
- 연결
  - [domain-modeling/18-context-mapping](../../domain-modeling/18-context-mapping/2-summary.md) — 도메인 사이 관계와 번역, Conway 법칙 인용
  - [distributed/20-data-ownership-and-cross-service-queries](../../distributed/20-data-ownership-and-cross-service-queries/2-summary.md) — 운영 데이터의 소유와 조회
  - [software-design/41-architecture-fitness-rules](../../software-design/41-architecture-fitness-rules/2-summary.md) — 규칙을 코드로 검사
  - [13-data-vault](../13-data-vault/2-summary.md) — 중앙 통합 모델(반대쪽 선택지), [14-lakehouse-table-formats](../14-lakehouse-table-formats/2-summary.md) — 플랫폼의 저장 계층
  - [data-analysis](../../data-analysis/README.md) — 제품을 소비하는 분석 쪽
- 근거
  - Zhamak Dehghani, "How to Move Beyond a Monolithic Data Lake to a Distributed Data Mesh", martinfowler.com, 2019-05-20(최종 연재일) <https://martinfowler.com/articles/data-monolith-to-mesh.html> — 세 실패 모드, 도메인 데이터 제품의 조건 6가지, 다의어(아티스트) 예.
  - Zhamak Dehghani, "Data Mesh Principles and Logical Architecture", martinfowler.com, 2020-12-03 <https://martinfowler.com/articles/data-mesh-principles.html> — 네 원칙, 아키텍처 퀀텀(코드·데이터와 메타데이터·인프라), 연합 계산 거버넌스 대조표.
  - Zhamak Dehghani, 『Data Mesh』, O'Reilly, 2022-03 — 출판 정보·목차만 확인(Internet Archive의 O'Reilly 도서 페이지).
  - Bitol Open Data Product Standard v1.1.0 <https://bitol-io.github.io/open-data-product-standard/latest/> — Fundamentals(필수 apiVersion·kind·id), Product Information(outputPorts 필수 1개 이상, contractId 선택), Team(선택). Open Data Contract Standard <https://bitol-io.github.io/open-data-contract-standard/latest/>(v3.1.0부터 절별 페이지).
  - PostgreSQL 17 문서 — `pg_stat_user_tables`(`last_seq_scan`·`last_idx_scan`), `obj_description`, `COMMENT`.
- 실험 목록(2026-10-07)
  - Python 3.12.3 표준 라이브러리(호스트): 사용자 1000명 합성 이벤트에서 '활성 사용자' 정의 4개 비교, 전역 정의 공유. 서술자 4개에 표준 필수 필드 검사 vs 조직 정책 검사, 카탈로그 − 출력 포트 차집합.
  - Java 21(`eclipse-temurin:21-jdk`, JDK 21.0.12): 같은 정책 검사의 Java판 — Python판과 같은 위반 목록.
  - PostgreSQL 17.11(`postgres:17`, `--network none --cpus=2`): 테이블 주석 JSON의 owner·`pg_stat_user_tables` 읽기 횟수로 주인 없는·안 읽히는 테이블 찾기.
