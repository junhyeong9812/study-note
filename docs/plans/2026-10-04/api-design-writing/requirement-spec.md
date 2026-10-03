# 요구사항 명세서 — api-design-writing

> 작성일: 2026-10-04 · 작업 폴더: `docs/plans/2026-10-04/api-design-writing/` · 브랜치: main(8dfaf3c4, origin과 같음)에서 `docs/api-design-writing`.
> 선행: network·os·database·distributed·reliability·software-design·domain-modeling·testing(모두 main 반영·push). 브리핑·실험 규칙·도구는 testing판을 재사용한다.
> **동시 실행 금지**: 같은 작업 트리에서 다른 실행이 이 영역을 진행하지 않는다는 전제. 착수·회수마다 `git log`·`git branch`·파일 mtime으로 다른 실행의 흔적을 확인하고, 있으면 멈추고 사용자에게 묻는다.

## 0. 요구사항 원문 (인터뷰)

- 원문: "진행하자"
- Q/A (2026-10-04): 영역 **API 설계**(`cs/api-design/`, 커리큘럼 §15) · 기존 사례 6편 **번호를 22~27로 이름 변경**(사용자 선택 — 새 leaf 01~06과의 번호 충돌 해소) · 검증 **앞 영역과 같게**, **명세 합의, auto**

## 1. 목표·대상 (필수)

- **T0 이름 변경(별도 커밋, 먼저)**: `cs/api-design/{01-order-point,02-coupon-issue,03-stock-deduct,04-settlement-report,05-delivery-webhook,06-refund}` → `{22-case-order-point,23-case-coupon-issue,24-case-stock-deduct,25-case-settlement-report,26-case-delivery-webhook,27-case-refund}` (`git mv`, 내용 무변경 — 단 폴더 안 자기 참조 링크만 갱신).
  - 이 폴더를 가리키는 링크를 **경로 해석으로** 찾아 새 경로로 고친다: `cs/**`, `cs/api-design/index.md`, `project/myway/README.md`. 같은 이름의 다른 폴더(예: `domain-modeling/advanced/04-refund`)는 건드리지 않는다.
  - 커리큘럼 §15.4 「기존」 칸 6개를 새 경로로 바꾸고 생성기 재실행.
  - `docs/plans/<과거 날짜>/**` 작업 기록은 당시 사실이므로 고치지 않는다.
- **T1 새 leaf 23편**: `cs/api-design/NN-slug/{1-question,2-summary,3-answer,metadata}.md` — 커리큘럼 §15 01~21·28·29(전부 신규). 종합 28·29는 마지막.
- 생성 문서 `cs/api-design/curriculum.md` 재생성: 29행 전부 `초안(Claude)`.

## 2. 경계·불변식 (필수)

- **I0 이름 변경 무손실**: 변경 전후 깨진 링크 수가 늘지 않는다(전체 cs·project 링크 검사 전후 비교), 6폴더의 파일 내용은 링크 경로 외 바이트 동일.
- **I1 형식**: 7절 골격, Q/A 6~10, 제목 아래 머리말·표식 없음, metadata 단계 `초안`.
- **I2 근거**: Fielding 2000 5장, RFC 9110·9111·9457·8594·9745·8259·6585·draft-ietf-httpapi-idempotency-key-header·draft-ietf-httpapi-ratelimit-headers, Google AIP(aip.dev), DDIA 4장, Stripe API 문서, Hyrum's Law(hyrumslaw.com·SWE@G 1장), Fowler "Richardson Maturity Model", Winand(use-the-index-luke), Protobuf·Avro 문서, Standard Webhooks 명세, gRPC 문서, GraphQL 명세·graphql/dataloader, OpenAPI 3.1, AMQP·MQTT·Kafka 프로토콜 문서, Azure 아키텍처 패턴(Gateway·BFF·Valet Key), 사고 원문(Twitter 2010 공지·OAIC/의회 자료). 책 원문을 못 열면 장 단위·`[?]`.
- **I3 커리큘럼 일치**: §15 각 행의 요지·⚠·🔧·📚 전부, 선행 링크(network 33~38·46, database, distributed, reliability, security, software-design 실재 경로 확인).
- **I4 기존 보존**: 사례 6편 본문·다른 영역 노트는 링크 경로 갱신(T0) 외 수정 금지.
- **I5 링크·트리**: 새로 깨는 링크 0, 리프에 md만.
- **I6 재현 안전**: testing과 같음 — 전용 일회용 `sn-ad-w<NN>-*`(`--cpus=2`, `-u $(id -u):$(id -g) -e HOME=/tmp`, 포트 미개방 또는 127.0.0.1), 이미지 pull·rmi·prune 금지(있는 것만: eclipse-temurin:21-jdk, maven:3.9-eclipse-temurin-21, postgres:17, redis:7-alpine, node:22-*, nginx:alpine, apache/kafka:4.1.0, grafana/k6:1.2.3), 라이브러리는 maven/npm으로 scratchpad에, 사용 조항·텔레메트리 존중, 개인정보 금지, 저장소 루트 파일 금지.
- **I7 실험 근거 우선 — API 해석**: 편마다 실행 가능한 핵심 주장 1개 이상을 실험의 실제 출력으로 보인다(28·29 제외 가능) — 예: Hyrum(응답 필드 순서·정렬에 의존한 클라이언트가 "무해한" 변경에 깨짐), 상태 코드별 클라이언트 재시도 동작, Problem Details 응답, Idempotency-Key 재시도·같은 키 다른 본문, offset vs keyset 페이지(PG 17 EXPLAIN·삽입 중 중복/누락), 필드 추가·enum 추가에 엄격 역직렬화 실패(Jackson FAIL_ON_UNKNOWN_PROPERTIES), JS 2^53 정밀도 손실·Protobuf 필드 번호 재사용, 웹훅 HMAC 서명·재전송·순서 역전, ETag/If-Match 412, 202 + 작업 자원 폴링, 429 + Retry-After, gRPC 데드라인, GraphQL N+1과 DataLoader, OpenAPI 명세-구현 불일치 검출. 출력은 실제 실행만.

## 3. 기준소스 (필수)

- curriculum.md §15, `cs/api-design/curriculum.md`, I2 출처, 기존 사례 6편

## 4. 금지영역 (필수)

- api-design 밖 노트(T0 링크 경로 갱신 외 읽기만), 커리큘럼 본문(T0의 「기존」 칸 6개 외 — 필요 시 NEXT), 과거 작업 기록(`docs/plans/<과거 날짜>/**`)
- 생성 문서 수기 수정 · 이번 작업이 만들지 않은 컨테이너·볼륨·이미지

## 5. 검증 방법 (필수)

- V0 이름 변경: 전체 링크 검사 전후 비교(깨짐 수 비증가), 6폴더 diff가 링크 경로뿐, 생성 표 22~27이 새 폴더를 가리킴
- V1 check_new · V1b 사실 점검이 편당 실험 1개+ 재실행 · V2 Opus 사실 점검 · V3 codex(high) 2차 리뷰(한도 해제 확인 후), 한도 시 Opus 적대 리뷰 → 판정 · V4 정합(network·database·distributed·reliability·testing·사례 6편 포함) · V5 웹 교차 24+, 링크 신규 깨짐 0, 생성 문서 재생성, 정리 확인

## 6. stakes (필수)

- **중간** — 새 학습 자료 23편 + 저장소 전역 링크 경로 변경(되돌릴 수 있음: git mv·링크 치환은 한 커밋), 사실 오류(RFC·도구 기본값) 위험.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 링크 경로 치환은 "상대 링크를 파일 위치 기준으로 해석해 대상이 옛 6폴더일 때만" 바꾸는 스크립트로 정확히 된다(이름이 같은 다른 폴더 오치환 0) — 착수 직후 dry-run 목록으로 확인.
- **A2**: API 실험은 JDK 21 단일 파일 HTTP 서버(com.sun.net.httpserver)·Spring 없는 소규모 maven 프로젝트·Node·PG 17 일회용 컨테이너로 충분하다. gRPC·GraphQL은 maven/npm 의존성으로 컨테이너 안에서 받는다.

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| T0 | 사례 6편 이름 변경 + 링크 갱신 + 커리큘럼 「기존」 칸 + 재생성 | V0, 별도 커밋 |
| 01 | 브리핑(testing판 이식 + API 실험 예시) | 브리핑 |
| 02 | 집필(Opus 병렬 5, 워커당 4~5편), 종합 28·29 후속 | 23 PASS |
| 03 | 사실 점검 + 실험 재실행 | packet |
| 04 | 2차 리뷰 → 판정 → 정합 → 웹 | V3~V5 |
| 05 | 생성 문서·정리·커밋·(확인 후) push·log·NEXT·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변(2026-10-04)
- [x] auto
