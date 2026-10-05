# 도메인 모델링 — `cs/domain-modeling/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §13에서 `docs/plans/2026-09-28/cs-restructure/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 28 · 검수 완료 0

> 기초(도메인 vs 애플리케이션) → 전술 설계 → 전략 설계 → 연습 트랙. 기존 basic 30·advanced 30 연습 문제는 **컬렉션 그대로 유지**하고 leaf 15·26가 가리킨다.
> 뼈대: Evans 『Domain-Driven Design』(2부 Building Blocks, 4부 Strategic Design), Evans 『DDD Reference』 2015, Vernon 『Implementing DDD』, Vernon "Effective Aggregate Design" 2011.

## 13.1 기초

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `domain-vs-application-logic` | 도메인 규칙과 애플리케이션 흐름의 경계 | 필수 | 초안(Claude) | [01-domain-vs-application-logic](01-domain-vs-application-logic/) · [domain-vs-application-logic](domain-vs-application-logic/) |
| 02 | `pojo-and-persistence-ignorance` | 프레임워크 독립 도메인 객체 | 권장 | 초안(Claude) | [02-pojo-and-persistence-ignorance](02-pojo-and-persistence-ignorance/) · [pojo](pojo/) |
| 03 | `ubiquitous-language` | 코드·대화·문서의 단일 언어 | 필수 | 초안(Claude) | [03-ubiquitous-language](03-ubiquitous-language/) |
| 07 | `domain-logic-patterns-and-service-layer` | Transaction Script·Table Module·Domain Model 3택의 선택 기준(복잡도 곡선), Service Layer = 유스케이스·트랜잭션 경계·권한 검사 위치, 명령-조회 분리(CQS) | 필수 | 초안(Claude) | [07-domain-logic-patterns-and-service-layer](07-domain-logic-patterns-and-service-layer/) |

## 13.2 전술 설계

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 04 | `entities-and-value-objects` | 식별성 vs 값 동등성 | 필수 | 초안(Claude) | [04-entities-and-value-objects](04-entities-and-value-objects/) |
| 05 | `aggregates-and-invariants` | 일관성 경계·불변식·Vernon 4규칙 | 필수 | 초안(Claude) | [05-aggregates-and-invariants](05-aggregates-and-invariants/) |
| 06 | `anemic-vs-rich-model` | 빈약한 도메인 모델 vs 풍부한 모델 | 필수 | 초안(Claude) | [06-anemic-vs-rich-model](06-anemic-vs-rich-model/) |
| 08 | `domain-services-and-policies` | 엔티티에 안 맞는 규칙·정책 객체 | 권장 | 초안(Claude) | [08-domain-services-and-policies](08-domain-services-and-policies/) |
| 09 | `domain-events` | 도메인 이벤트 발행·처리 | 필수 | 초안(Claude) | [09-domain-events](09-domain-events/) |
| 10 | `repositories-and-factories` | 영속성 추상·생성 캡슐화 | 권장 | 초안(Claude) | [10-repositories-and-factories](10-repositories-and-factories/) |
| 11 | `state-machines-in-domain` | 상태·전이·가드로 수명 주기 모델링 | 필수 | 초안(Claude) | [11-state-machines-in-domain](11-state-machines-in-domain/) |
| 12 | `time-money-and-units` | 금액(정밀 소수·반올림)·통화·시간대·기간·단위 — 개관(시간 심화는 13, 금액 심화는 14) | 필수 | 초안(Claude) | [12-time-money-and-units](12-time-money-and-units/) |
| 13 | `instant-vs-local-time-and-tz-rules` | Instant·LocalDateTime·LocalDate 구분, 미래 일정은 "현지 시각 + tz ID"로 저장, DST 공백·중복, tzdata 갱신, 기간(Period)과 지속시간(Duration) | 필수 | 초안(Claude) | [13-instant-vs-local-time-and-tz-rules](13-instant-vs-local-time-and-tz-rules/) |
| 14 | `money-arithmetic-rounding-allocation` | 정밀 소수·통화별 소수 자릿수(ISO 4217), 반올림 모드와 **반올림 위치**, 배분(1원 나머지 처리), 세금·할인 계산 순서, 직렬화 | 필수 | 초안(Claude) | [14-money-arithmetic-rounding-allocation](14-money-arithmetic-rounding-allocation/) |

## 13.3 전략 설계

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 16 | `bounded-contexts` | 모델의 유효 경계 | 필수 | 초안(Claude) | [16-bounded-contexts](16-bounded-contexts/) |
| 17 | `subdomains` | 핵심·지원·일반 서브도메인과 투자 배분 | 권장 | 초안(Claude) | [17-subdomains](17-subdomains/) |
| 18 | `context-mapping` | Partnership·Shared Kernel·Customer/Supplier·Conformist·ACL·OHS·Published Language·Separate Ways | 권장 | 초안(Claude) | [18-context-mapping](18-context-mapping/) |
| 19 | `anti-corruption-layer` | 외부 모델 번역 계층 | 권장 | 초안(Claude) | [19-anti-corruption-layer](19-anti-corruption-layer/) |
| 20 | `event-storming` | 이벤트 중심 협업 모델링 | 권장 | 초안(Claude) | [20-event-storming](20-event-storming/) |
| 21 | `cqrs` | 명령과 조회 모델 분리 | 권장 | 초안(Claude) | [21-cqrs](21-cqrs/) · [../systems/server-design/03-data-layer.md](../systems/server-design/03-data-layer.md) |

## 13.3b 추적 가능한 도메인 — 결정·버전·원장·대사 (2026-09-28 추가)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 22 | `decision-log-and-provenance` | 결정 기록: 입력 스냅샷(또는 참조 + 버전)·적용 규칙 ID와 버전·중간 산출·결과·결정 시각을 한 레코드로. 재현 가능성 테스트("같은 입력으로 다시 계산하면 같은가") | 필수 | 초안(Claude) | [22-decision-log-and-provenance](22-decision-log-and-provenance/) |
| 23 | `versioned-rules-and-effective-dating` | 요율표·세율·정책·가격표를 버전으로 관리하고 **적용 기준 시각**(주문 시각? 결제 시각?)을 명시한다. 결과 행에 버전 스탬프를 남긴다. 미래 발효 예약 | 필수 | 초안(Claude) | [23-versioned-rules-and-effective-dating](23-versioned-rules-and-effective-dating/) |
| 24 | `double-entry-ledger` | 복식부기 원장: 모든 이동 = 차변·대변 쌍, 잔액은 파생값(= 분개 합), 정정은 역분개(UPDATE·DELETE 금지), 멱등 전표, 잔액 스냅샷 | 필수 | 초안(Claude) | [24-double-entry-ledger](24-double-entry-ledger/) |
| 25 | `reconciliation` | 대사: 내부 원장 vs 외부(PG·은행·파트너) 기록을 키로 맞추고 차이를 분류(누락·중복·금액 불일치·상태 불일치)해 조정 분개로 처리한다. **타임아웃으로 결과를 모르는 요청의 최종 확정 경로** | 필수 | 초안(Claude) | [25-reconciliation](25-reconciliation/) |

## 13.4 연습 트랙

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 15 | `basic-modeling-exercises` | 기초 모델링 연습 30편(주차 요금~배차) — 컬렉션 유지 | 필수 | 초안(Claude) | [15-basic-modeling-exercises](15-basic-modeling-exercises/) · [basic](basic/) |
| 26 | `advanced-modeling-exercises` | 심화 모델링 연습 30편(급여~B2B 등급) — 컬렉션 유지 | 권장 | 초안(Claude) | [26-advanced-modeling-exercises](26-advanced-modeling-exercises/) · [advanced](advanced/) |

## 13.5 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 27 | `dm-symptom-index` | 역색인: 불법 상태 데이터, 1원 정산 차이, 같은 규칙 N벌, 거대 트랜잭션 락, 팀 간 모델 충돌, 미래 예약 1시간 어긋남·DST 알람 누락/중복, 1원 배분 소실, 과거 금액 재계산 불일치, 잔액 원인 불명, 504인데 결제됨(대사) | 필수 | 초안(Claude) | [27-dm-symptom-index](27-dm-symptom-index/) |
| 28 | `dm-incidents` | 실사건: Mars Climate Orbiter 단위 불일치(1999, 파운드·초 vs 뉴턴·초) · 영국 Post Office Horizon 회계 불일치(2000~) | 권장 | 초안(Claude) | [28-dm-incidents](28-dm-incidents/) |
