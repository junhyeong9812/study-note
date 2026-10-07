# log — data-engineering-writing

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-10-07 | 인터뷰(데이터 공학 17편 — 전부 신규·원고 없음 · 앞과 같게, 합의 auto · 사용자 추가 지시 "에이전트 최대 5개씩", "병렬로 순차처리" → 동시 서브에이전트 ≤5, 끝난 자리에 다음 단계 이어 띄움) → 명세 작성 직후 승인 기록 · 브랜치 docs/data-engineering-writing(main f8f8fe35) | SPEC=1·MODE=auto |
| 2026-10-07 | 브리핑 3종(architecture판 이식 + 데이터 공학 1차 출처 URL 목록·도구/버전 한정·모형≠실물·합성 데이터·postgres/kafka 실행 규칙) · 집필 발사(Opus 4병렬 — 동시 ≤5 지시 준수, 15편): 01(01~04) / 05(05~08) / 09(09~12) / 13(13~15) — 종합 16·17은 빈 자리에 후속, 끝난 묶음부터 사실 점검 이어 띄움 | 회수 대기 |
| 2026-10-07 | 집필 회수 1/4: 01~04(4 PASS, Q/A 8·8·9·9, [?] 3 — DDIA 절 제목은 O'Reilly 목차 IA 사본으로 확인) — 실험(postgres 17.11·JDK 21): 원천 로그 폴드 재구축 digest 동일·파생본 직접 수정 소실, 리포트 동시 실행 시 점 조회 p99 0.4→1.5~2.8ms, ETL 조용한 스킵 36행·raw 재처리, grain 혼합 2.00배·inner join 누락·비율 SUM, Type 1 소급 변경·Type 2 겹침/빈틈·EXCLUDE 거부·as-of 조회 · 02의 Java 변환 코드는 미실행(코드 모양) → 사실 점검 fc-01 발사(동시 4) | 4 PASS |
| 2026-10-07 | 집필 회수 2/4: 13~15(3 PASS, Q/A 9·10·9, [?] 3 — 책은 목차만, Iceberg 1.12·Delta PROTOCOL·ODPS v1.1.0) — 실험: Hub 정규화 누락 3행 vs 2행·Satellite 조인 6행/한도 4배·PIT, Satellite 수 k=2→32 계획 1→60ms·마트 1.6ms, Java strip vs PG trim 해시 차이, Java 모형(Iceberg 아님) CAS 커밋 유실 0 vs 무검사 덮어쓰기 74~94/400·compaction 검증 누락 시 지운 행 부활·만료 후 time travel 실패·파일 수별 계획 시간, '활성 사용자' 정의 4개 505/183/580/118 · 정리 점검 중 21:35:50 익명 볼륨 3개(Kafka 이미지 VOLUME 3개로 추정, 05 워커) 발견 → 05 워커에 확인·자기 것만 삭제 요청(dangling 기준선 39) → 사실 점검 fc-13 발사(동시 4) | 3 PASS |
| 2026-10-07 | 집필 회수 3/4: 09~12(4 PASS, Q/A 9·9·9·10, [?] 1) — Confluent 8.3·ODCS v3.2.0·OpenLineage 1.53·GDPR(EUR-Lex 본문 빈 응답 → gdpr-info.eu 2차 사본 명시)·EDPB 02/2025 v1.1·Kafka 4.1 compaction 문서 · 실험: 필드 집합 호환성 모형 = Confluent Avro 표 일치·비transitive 재생 실패, 이름 변경 → 하류 region 100% NULL·inner join 매출 누락, INSERT 0 0 + exit 0·NULL 40%인데 합계 동일, 볼륨 감시 규칙 6종 탐지/오경보, 계보 BFS 테이블 vs 컬럼 수준·pg_depend는 INSERT..SELECT 의존 0, 원천 삭제 후 사본 5곳 잔존, AES-GCM 키 폐기 후 복호 불가 · 영역 밖 '미작성' 후보 7곳 보고 → 사실 점검 fc-09 발사(동시 4) | 4 PASS |
| 2026-10-07 | 집필 회수 4/4: 05~08(4 PASS, Q/A 9·8·9·8, [?] 4) — Debezium 3.7·PG 17·MySQL 8.4(IA)·Kafka 4.1·CloudEvents 1.0.2·Kreps/Marz·Beauchemin 2018-01-08(IA) · 실험: test_decoding(롤백 제외·DEFAULT vs FULL·DDL 없음), 스냅샷/슬롯 순서로 누락·중복 vs EXPORT_SNAPSHOT, 비활성 슬롯 pg_wal 48→160MB·max_slot_wal_keep_size로 lost, 집계 기준 KST/처리 시각/UTC 1000 vs 998 vs 375·ID dedup 2040→2000, Kafka 보존 30→7일 earliest 2120·재처리 880건 에러 없음, append 재실행 2배·백필 현재 요율 75,000 vs 90,000·덮어쓰기 분리 커밋 시 0행 노출 · 볼륨 3개는 이 워커가 docker create 후 rm -v 없이 남긴 것 — 본인이 확인 후 그 3개만 삭제(남은 dangling 기준선 복귀 확인) · **15편 집필 완료** → 사실 점검 fc-05 + 종합 16·17 집필 발사(동시 5) | 4 PASS |
| 2026-10-07 | 사실 점검 회수 13·14·15 (3 PASS, 중대 0 / 중간 5: 13 hashdiff 정의(payload+키, AutomateDV Satellites), 14 Delta vacuum 7일은 구현 기본값·Iceberg 행 삭제 operation은 overwrite/delete(replace 아님)·모형 실험 범위(lake1 혼입 → 5회 범위), 15 ODPS apiVersion 필수 누락 한계 / 경미 5, [?] 0 증감, 실험 재실행 일치(A·D 범위 확대)) → codex 2차 발사 | 3 PASS |
| 2026-10-07 | 사실 점검 회수 01~04 (4 PASS, 중대 0 / 중간 3: 02 p99 간섭 해석(I/O 몫 배제 못 함, CPU 대조 실험 추가)·02 Java 조각 '실행하지 않은 예시'·04 Type 2 적재 SQL 재실행 시 현재 행 2개(멱등 아님 — CTE판 추가) / 경미 3, [?] −2(DDIA 3부 서론 IA 사본), 실험 재실행 일치) → codex 2차 발사 | 4 PASS |
| 2026-10-07 | 사실 점검 회수 09~12 (4 PASS, **중대 1**: 12 EDPB 02/2025는 확정판 v2.0(2026-07-07)이 이미 나옴 — v1.1 공개 의견판 인용·§5.2 위치 오류 → v2.0 §4.2 문단 50·51 / 중간 7: Confluent defaultToGlobal, psql ERROR에도 종료 코드 0(ON_ERROR_STOP=1이면 3), dbt warn_if/error_if 예시, GX 근거가 0.18 문서였음 → 1.23.2, EDPB '체인 밖' → '일반적으로 권하지 않음', 제17조 의무 주체 controller / 경미 다수, [?] −1, 실험 9 재실행 일치, EUR-Lex IA 사본으로 원문 대조) → codex 2차 발사 | 4 PASS |
| 2026-10-07 | codex(high) 2차 회수 13·14·15 → 판정 발사(adj-13, 동시 3) | 회수 대기 |
| 2026-10-07 | codex(high) 2차 회수 01~04 → 판정 발사(adj-01, 동시 4) | 회수 대기 |
| 2026-10-07 | 판정 회수 13·14·15 (18건 — 워커 요약은 채택 11·부분 7이었으나 표 행 집계로 **채택 10·부분 8·기각 0**(13: 2/5, 요약 3/4는 오기), 표를 정본으로 기록. 3 PASS. 14 포맷별 커밋 방식 병기(CAS를 전 포맷 일반화 금지)·Hudi 완료 파일명·Iceberg 데이터 파일 Parquet/Avro/ORC, 15 그림 효과 문구 뒤집힘 해소·PG 통계는 정상 종료 시 보존, 13 Multi-Active Satellite 예외) | 회수 |
| 2026-10-07 | 판정 회수 01~04 (지적은 codex out 파일 대조로 **14건**(5·3·3·3) — 워커 요약 '15건, 채택 13'은 오기, 표 기준 **채택 12·부분 2·기각 0**, 14건 전부 판정됨. 4 PASS. 01 본문 rebuild_view와 refunded 출력 모순 해소·EXCEPT 한 방향·중복 제거, 02 데이터 마트 종속/독립·ETL 변환 장소·복제 지연 지표를 LSN 차로, 03 주기 스냅샷 grain·플래너가 조인 고름, 04 부분 유일 인덱스는 '최대 하나'·마지막 행만 닫힌 멤버 빈틈 진단 추가(재현)·자연 키 불변 가정) | 회수 |
| 2026-10-07 | 사실 점검 회수 05~08 (4 PASS, 중대 0 / 중간 3: 05 Debezium 'Possible duplicates'는 블로킹 스냅샷 절, 07 Kafka 보존 실험 범위(880~995건·9~10일·세그먼트 6~8)·Kreps 인용 왜곡(HDFS 재처리는 Kreps 제안 아님) / 경미 3, [?] −2(roll 판정 Kafka 4.1.0 LogSegment.shouldRoll, speed layer = Marz·Warren 책 3부), 08 수정 없음, 실험 재실행 일치(07 B만 범위)) → codex 2차 발사 | 4 PASS |
| 2026-10-07 | codex(high) 2차 회수 09~12(지적 5·8·3·4 = 20) → 판정 발사(adj-09, 동시 2) | 회수 대기 |
| 2026-10-07 | 종합 집필 회수 16·17 (2 PASS, Q/A 8·9, [?] 1) — 16: leaf 장애 시나리오 70개 전부 색인·수치 43개 현 leaf 대조 / 17: PHE(GOV.UK 2020-10-04·Hansard API·MS .xls 65,536행, XLS·템플릿 설명은 BBC 2차 출처로 분리), Unity(SEC 8-K·10-Q 2022-05-10, 원문상 별개 문제 2개 — 커리큘럼 행 표기와 다름 → NEXT 후보), Equifax(2022-08-02 성명·10-K FY2022/FY2024, CFPB 원문 403·IA 없음, 2017 침해와 구분) · 실험: Reconcile 7모양 분류, xls_cap 모형 누락 15,465(PHE 수치와 유사는 우연 명시), LoadGuards 행 수 대조·출처별 관문·그림자 비교 → 사실 점검 fc-syn 발사(동시 2) | 2 PASS |
| 2026-10-07 | 판정 회수 09~12 (20건: 채택 15·부분 5·기각 0 — out 파일 개수·표 합계 대조 일치, 4 PASS. 09 레지스트리 검사 범위(Data Contracts 규칙 예외)·역직렬화 실패는 고정 reader 스키마일 때만·transitive 검사 API, 10 dbt unique/relationships NULL 제외·severity는 롤백 아님·Count-Min은 상위 목록 못 줌, 11 sql은 Job facet·pg_rewrite 쿼리 규칙 혼입 재현 수정, 12 tombstone은 compact 토픽만·사용자별 금액도 개인정보) | 회수 |
| 2026-10-07 | codex(high) 2차 회수 05~08(지적 7·5·3·3 = 18) → 판정 발사(adj-05, 동시 2) | 회수 대기 |
| 2026-10-07 | 사용자 지시: '남은 커리큘럼도 전부 진행 계획에 넣어서 쭉 진행' → 순서 **네트워크 원고 1 → 언어 27 → 데이터 분석 28**, push는 **영역마다 커밋만, 마지막에 한 번 묻기**(데이터 공학 포함) | 계획 |
| 2026-10-07 | 사실 점검 회수 16·17 (2 PASS, 중대 0 / 중간 5: 16 09-3 Avro 문구 조건·02-2 복제 지연 지표 LSN 차·07-2 범위, 17 PHE 날짜 축(배경 절은 25 Sep~2 Oct, 24 Sep~1 Oct는 표 위 문장)·Unity 두 문제 분리 / 경미 8, 실험 재실행 일치, 진단 SQL PG 17.11 실행 확인, 09~12 판정 후 16 재대조 필요 → 정합 단계) → codex 2차 발사 | 2 PASS |
| 2026-10-07 | 판정 회수 05~08 (18건: 채택 13·부분 5·기각 0 — out 개수·표 합계 일치, 4 PASS. 05 DEFAULT before는 PK만·binlog 만료는 '삭제될 수 있다'(auto_purge)·재스냅샷은 지운 키를 못 지움, 06 CloudEvents time 조건·now()는 트랜잭션 시작 시각, 07 auto.offset.reset 기본 latest(조용한 앞부분 누락은 earliest일 때), 08 재실험: 동시 덮어쓰기 2행·last_run_at 늦은 커밋 누락·원천 대조 쿼리 중복 계산 오류 → 수정) | 회수 |
| 2026-10-07 | codex(high) 2차 회수 16·17(지적 7·4) → 판정 + 정합 패스 발사(16 색인 재대조·노트 간 정합·영역 안 링크·영역 밖 '미작성' 링크 교정) | 회수 대기 |
| 2026-10-07 | 판정·정합 회수: 16·17 지적 11(채택 11·부분 0·기각 0, out 개수·표 일치 — 16 Reconcile 0 나눗셈 재현·수정, 17 CFPB 동의 명령 IA 사본으로 처음 열람: Equifax 종료일 4/8·테스트 코드 운영 반영·날짜 속성 오계산) · 16 색인 재대조 2곳(04-3 진단 (4), 06-5) · 01의 distributed/22 절 표기 정정 · 노트 간 모순 0 · 영역 안 링크 21 · **영역 밖 링크 교정 19곳/13파일**(git word-diff로 링크·'미작성' 표기만 확인) · 링크 801 깨짐 0 · 17 PASS + B4 13 PASS · 남은 영역 밖: database/19:199 슬롯 상한 양자택일 단순화, testing/13:158·api-design/07:200 '필드 집합 비교' 일반화(→ NEXT) → 웹 교차 표본 발사 | 17 PASS |
| 2026-10-07 | 웹 독립 교차 표본 회수: **59건 일치 58·불일치 1·확인 불가 0**(11 근거 링크가 _RETURN 문장 없는 pg_rewrite 페이지 → rules-views 병기로 수정) · 관찰 1(10 Micrometer 재등록은 '무시' — 문서 문구로 수정) → web-cross-sample.md 저장 · README 재생성(data-engineering만 변경, 초안(Claude) 17) · 정리: sn-de 컨테이너·네트워크 0, dangling 볼륨 36(기준선 39에서 w05 누수 3개 정리)·이미지 26, 리프 md만 · 17 PASS | 17 PASS |

## 리뷰 ledger

| 대상 | 리뷰어 | 중대 | 중간 | 경미 | [?] 전→후 | 비고 |
|---|---|---|---|---|---|---|
| 13·14·15 | Opus 독립 | 0 | 5 | 5 | 3→3 | 웹 표본 9 · 실험 재실행 8 |
| 01~04 | Opus 독립 | 0 | 3 | 3 | 4→2 | 웹 표본 12 · 실험 재실행 10 |
| 09~12 | Opus 독립 | 1 | 7 | ~10 | 1→0 | 웹 표본 12 · 실험 재실행 9 |
| 13·14·15 판정 | Opus(codex 지적 18) | 채택 10 | 부분 8 | 기각 0 | | 재실험 0 · 요약 합계 오기 → 표 기준 |
| 01~04 판정 | Opus(codex 지적 14) | 채택 12 | 부분 2 | 기각 0 | | 재실험 1(빈틈 진단) · 요약 합계 오기 → out 파일·표 기준 |
| 05~08 | Opus 독립 | 0 | 3 | 3 | 4→2 | 웹 표본 12 · 실험 재실행 11 |
| 09~12 판정 | Opus(codex 지적 20) | 채택 15 | 부분 5 | 기각 0 | | 재실험 1(pg_rewrite 규칙 혼입) |
| 16·17 | Opus 독립 | 0 | 5 | 8 | 1→1 | 웹 표본 7 · 실험 재실행 4 |
| 05~08 판정 | Opus(codex 지적 18) | 채택 13 | 부분 5 | 기각 0 | | 재실험 4(동시 덮어쓰기·늦은 커밋·대조 쿼리) |
| 16·17 판정 | Opus(codex 지적 11) | 채택 11 | 부분 0 | 기각 0 | | 재실험 1(Reconcile 0 나눗셈) |

## 생략한 검증

- 없음(빚 0). 참고 한계: DDIA·Toolkit·Data Vault 책 본문은 목차(출판사 페이지·IA 사본)까지만 — 장·절 번호 외 세부는 `[?]` · Debezium·Schema Registry·Iceberg·dbt·OpenLineage 런타임은 없어 Java/Python 모형 + 1차 문서로 대신(노트에 '모형' 표기) · MySQL binlog·Kafka tombstone compaction은 실물 실험 없이 문서 · EUR-Lex·SEC·Medium·CFPB 직접 요청 차단 → Internet Archive 사본(SEC는 연락처 User-Agent 요구라 개인정보 규칙상 직접 요청 안 함) · 데이터 분석 영역(18) 미작성이라 관련 링크는 영역 표로.

## 완료 요약

- 산출: `cs/data-engineering/01~17` 17편(전부 신규 — 원고 없음, 종합 16 증상 색인(장애 시나리오 70개)·17 실사건 3건(PHE 2020·Unity 2022·Equifax 2022)) + 영역 표 재생성 + 영역 밖 '미작성' 링크 교정 19곳(13파일).
- 검증: V1 17 PASS · V1b/V2 Opus 사실 점검 5묶음(중대 1 — EDPB 지침 확정판 v2.0 미반영, 중간 ~23, 실험 재실행 전 묶음 — 04 Type 2 적재 SQL이 재실행 시 현재 행 2개를 만드는 결함 발견) · V3 codex(high) 17/17, 지적 81 → 채택 61·부분 20·기각 0(판정 재실험 8) · V4 정합(16 ↔ leaf 재대조, 노트 간 모순 0, 영역 안 링크 21) · V5 웹 독립 59건(불일치 1 수정) + 사실 점검 웹 표본 ~50 · 링크 801 깨짐 0.
- 관측: 데이터 공학 지적의 대부분은 **한 도구 동작의 일반화**(Iceberg CAS를 전 포맷으로, Confluent 기본값, dbt NULL 처리)와 **진단 쿼리 자체의 결함**(대조 쿼리 중복 계산·빈틈 진단 누락·pg_rewrite 규칙 혼입) — 실험으로 진단 SQL을 직접 돌린 판정이 효과적이었다. 판정 워커 요약 합계 오기 2회(표 기준으로 기록) → 이후 지시에 편별 지적 수를 넣어 해소.
- 핵심 diff(실파일에서 복사): `cs/data-engineering/README.md` before `> 현황: 미작성 17 · 원고 있음 0 · 초안(Claude) 0 · 검수 완료 0` → after `> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 17 · 검수 완료 0`
- CS 이슈 아카이브: 0건(문서 작업).

