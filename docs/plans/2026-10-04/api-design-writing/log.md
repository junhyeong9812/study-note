# log — api-design-writing

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-10-04 04:15 | 상태 확인: 다른 실행 흔적 없음(최신 8dfaf3c4 = origin/main) · 빈 디렉터리 docs/plans/m2(10-03 21:29, testing 워커가 상대 경로로 만든 것) 삭제 | |
| 2026-10-04 04:20 | 인터뷰(영역 API 설계 · 기존 사례 6편 22~27로 이름 변경 · 검증 앞과 같게 · 합의 auto) → 명세 작성 직후 승인 기록 · 브랜치 docs/api-design-writing(main 8dfaf3c4) | SPEC=1·MODE=auto |
| 2026-10-04 04:40 | **T0 이름 변경** 커밋 861c50e6: git mv 6폴더(01~06 → 22-case-*~27-case-*, R100 18·R098 6) · 링크 치환 스크립트(scratchpad/ad/t0/relink.py — 상대 링크를 파일 위치 기준으로 해석해 대상이 옛 6폴더일 때만, dry-run 62건 확인 후 적용: cs 다른 영역 25파일·index·myway README·폴더 안 상호 링크) · 커리큘럼 「기존」 칸·연결 언급 8곳 · 생성기 재실행(22~27 → 새 폴더) · **V0**: 전체 링크 검사 전후 깨짐 75 → 75(diff 0), 6폴더 diff는 링크 경로뿐 · 참고: 사례 6편은 원래 형식(질문을 A./B. 절로)이라 check_new는 이름 변경 전에도 6 FAIL(질문 수 0) — 기존 그대로 | V0 통과 |
| 2026-10-04 04:50 | 브리핑(testing판 이식 + API 실험 예시·표준 vs 초안 vs 회사 관례 구분·사례 6편 읽기만) · 집필 발사(Opus 5병렬, 21편): 01~04 / 05·06·11·12 / 07·08·15·16 / 09·10·13·14 / 17~21 — 종합 28·29 후속 · 프롬프트 scratchpad/ad/writer-prompt.md | 회수 대기 |
| 2026-10-04 | 집필 회수 1/5: 17~21(5 PASS, [?] 1 — graphql-java API 형태) — 실험: 17 graphql-js 16.14.2 N+1 SQL 11/51/101 vs DataLoader 2·깊이 3에 응답 261B→275KB·SQL 1112·깊이 제한 규칙 거절·부분 성공 errors, 18 nginx 1.31.6 GET MISS HIT×4 vs POST 캐시 없음(백엔드 1 vs 5), 19 게이트웨이 401·최장 접두사·limit_req 200×3 429×3·집계 순차 3.16s vs 예산 307ms 부분 응답, 20 Kafka 4.1.0 커밋 없는 그룹 재전달 vs 자동 커밋 LAG 4(MQTT·AMQP 브로커 이미지 없음 → 명세로), 21 swagger-parser·ajv 명세-구현 불일치 4건 · WebFetch 요약이 RFC 9110 9.2.3을 틀리게 요약 → txt 원문 확인(사실 점검 브리핑에 반영) · 사실 점검 브리핑 작성·1/5 발사 | 5 PASS |
| 2026-10-04 | 집필 회수 2/5: 09·10·13·14(4 PASS, [?] 3 — 정보통신망법 시행령·국가법령정보센터 미대조·collapse 키) — 실험: 09 Standard Webhooks 시험 벡터 서명 일치·위조/재직렬화/10분 전 재전송 거부·중복 DUPLICATE·덮어쓰기 PAID vs seq 비교 SHIPPED, 10 PG17 outbox: 롤백 후 직접 발송 1통 vs outbox 0·멱등 키 없음 3통 vs 1통·야간 보류, 13 nginx proxy_read_timeout 3s 동기 504×2 리포트 2개 vs 202+op 1개, 14 Retry-After 무시 84건(429 64) vs 준수 23건·IP 키 300명 중 267 차단 vs API 키 0·테넌트별 한도 · 사고: 멈춘 자기 컨테이너 rm -f 후 재실행 · 사실 점검 2/5 발사 | 4 PASS |
| 2026-10-04 | 집필 회수 3/5: 07·08·15·16(4 PASS, [?] 4) — 실험: 07 Jackson 2.19.2 필드 추가 UnrecognizedProperty·enum 추가 InvalidFormat·삭제는 조용히 0, **Jackson 3.0.0은 FAIL_ON_UNKNOWN 기본 false**(enum은 여전히 실패)·Deprecation/Sunset 헤더, 08 varint 300=08 ac 02·int32 -1 11B vs sint32 2B·필드 번호 재사용 조용한 오역·reserved 컴파일 오류·unknown 보존·Avro 해석·JS 2^53, 15 grpc-java 1.72.0 데드라인 없음 무한 대기 vs 500ms DEADLINE_EXCEEDED·grpc-timeout 전파·4MiB·pick_first 100/0 vs round_robin 50/50, 16 스트림 취소 미확인 onNext 19회·중간 에러 삼킴·백프레셔 blind RSS 82→294MB vs ready 90MB · 사실 점검 3/5 발사 | 4 PASS |
| 2026-10-04 | 집필 회수 4/5: 05·06·11·12(4 PASS, 각 10문항, [?] 2 — Stripe v2 칸) — 실험: 05 JDK 21 HttpClient 기본 재시도는 GET만(MultiExchange.isIdempotentRequest)·멱등 키 없음 4건 vs 같은 키 1건·다른 본문 422·누락 400·동시 10 → 201×1 409×9, 06 PG17 100만 행 offset 999,980에 395~516ms vs keyset 0.13~0.35ms·페이지 사이 쓰기 중복 40/누락 33 vs 커서 0, 11 If-Match 없음 lost update·낡은 ETag 412·없음 428·W/ 412·check-then-write 동시 200 1~14개 vs 조건부 UPDATE 1개, 12 인덱스 없는 정렬 366ms·offset 20만 external merge 2.88s·pgbench 2,980 vs 2.5 tps·pg_trgm GIN 1.3s→4ms·ORDER BY $1 바인딩 무효 · 사실 점검 4/5 발사 | 4 PASS |
| 2026-10-04 | 집필 회수 5/5: 01~04(4 PASS, [?] 0) — 실험: 01 Hyrum 무해한 변경 3종(Map 구현·레코드 필드 순서·404 문구) 12명 중 클라이언트 조용히 깨짐·JVM 10회 Map 순서 6/4·Jackson 2.19.2 FAIL_ON_UNKNOWN true, 02 nginx GET 캐시 vs POST·JDK HttpClient 재시도 GET만(enableAllMethodRetry), 03 상태 코드 방식별 도착 13/10/19·200+에러 바디 실패 5건 은폐, 04 Spring Boot 4.1.1: 에러 형식 2종 혼재·server.error.* 4.0 폐기(spring.web.error.*)·trace 노출 4622자·problemdetails 부분 적용 · 확인 필요: 02 'RFC 10008 QUERY(2026-06)' → 사실 점검에서 rfc-editor 원문 확인 · **집필 21편 완료**(사례 22~27 합쳐 27) · 사실 점검 5/5 + 종합 28·29 발사 | 21 PASS(신규) |
| 2026-10-04 | 사실 점검 회수 1/5: 17~21 — 중대 0, 중간 4(17 GraphQL over HTTP draft 5.4: data+errors는 294 Partial Success SHOULD·2xx MUST(옛 '200'), 19 실험 관찰과 출력 불일치(/orders/1 1회 도달), 20 RabbitMQ heartbeat 60은 서버 제안 기본·권장 5~20초, 18 Fielding 5.1.5 서술), 경미 ~9(17 graphql-java API [?] 해소, 19 BFF 용어 Newman 원문·카나리 출처 분리, 21 OAS 3.2.1 판·ajv strict 거부 실험·info.version, 시간 범위 확대, 미작성→링크) · 재실행 6종 일치 · [?] 1→0 | 5 PASS |
| 2026-10-04 04:55 | 2차 리뷰: codex 한도(10-04 08:53 리셋, 현재 04:50) → 명세 V3대로 Opus 적대 리뷰 — 1/5 발사 17~21 · 리뷰·판정 프롬프트(scratchpad/ad/review/)·판정 브리핑(adjudicate-briefing.md) 작성 | 회수 대기 |
| 2026-10-04 | 사실 점검 회수 2/5: 09·10·13·14 — 중대 0, 중간 4(10 정보통신망법 시행령 제61조②: 야간 예외 매체 = 전자우편(law.go.kr 원문) → 워커 조건 channel != EMAIL·[?] 해소, 10 FCM 문서 제목·stale 정의 원문, 13 Azure 가이드 패턴별 202/201+operation-location, 14 OWASP 지수 잠금은 권고 아님), 경미 9(09 검사 순서 모순·명세는 순서 미정, 13 RFC 9110 'ought to'·AIP-151 must·시간 범위, 14 GitHub 1차/2차 재시도 분리·실험 범위) · 재실행 6종 결정적 일치 · [?] 3→0 · 담당 밖: network/51:160 api-design/10 '미작성' → NEXT | 4 PASS |
| 2026-10-04 | Opus 적대 리뷰 회수 17~21: 지적 7(17 errors path MUST·locations SHOULD(2021 §7.1.2)·294는 graphql-response+json일 때만·인트로스펙션 끄기는 자사 클라이언트 API 한정, 18 '캐시 키에 본문 없음'은 nginx 기본 키 한정, 19 Azure 게이트웨이 패턴은 셋(Gatekeeper·Valet Key 별도), 20 g-auto는 처리 후 커밋 경로(유실은 가정), 21 '네 가지 불일치' 내부 모순(드리프트 3 → 오류 4)) → 판정 발사 | 판정 대기 |
| 2026-10-04 | 사실 점검 회수 3/5: 07·08·15·16 — 중대 0, 중간 ~10(07 Jackson 3.0 FAIL_ON_UNKNOWN false 소스·릴리스 노트 근거 + FAIL_ON_NULL_FOR_PRIMITIVES true·Sunset 실험 날짜가 IMF-fixdate 위반, 08 JSON 출력 손으로 고친 흔적({id,amount} 순서) 정정·proto3 unknown 보존 3.5.0 CHANGES.txt [?] 해소, 15 투명 재시도 조건·데드라인 전파 끝 상태 비결정(CANCELLED/DEADLINE_EXCEEDED)·RetryCfg 문구 비결정, 16 버려진 onNext 19~20·Stream closed 경고는 ready에서도·373은 보낸 총수·autoFlowControl 기본 true(1MiB는 시작값)), 경미 ~6 · 재실행 12종(결정적 일치, 비결정 범위 확대) · [?] 2→1 · 담당 밖: database/31:60 FAIL_ON_UNKNOWN 기본 true 버전 미한정 → NEXT | 4 PASS |
| 2026-10-04 | 사실 점검 회수 4/5: 01~04 — 중대 0, **RFC 10008 QUERY 실재 확인**(rfc-editor txt: Standards Track, June 2026, §2.7 캐시 키 MUST incorporate content) · Spring Boot 4.0 server.error.* → spring.web.error.*(v4.0.0 메타데이터 deprecation level error)·Framework 7 UNPROCESSABLE_CONTENT 확인 · 중간 3(01 Jackson 3.x SORT_PROPERTIES_ALPHABETICALLY true·FAIL_ON_UNKNOWN false 버전 한정(Boot 4.1.1 BOM 기본 Jackson 3.1.5), 04 RFC 9457 §3 예시에 status 추가한 것을 '그대로'로 표기 정정), 경미 ~5(Fielding 'authors' preferred version', AIP-136 문구·saved search 출처 오귀속, Map.of 비율 비결정) · 03 수정 0 · 재실행 9종 결정적 일치 | 4 PASS |
| 2026-10-04 | 사실 점검 회수 5/5: 05·06·11·12 — 중대 0, 중간 3(05 JDK 재시도 GET·HEAD 제한은 ConnectionExpired에만·ConnectException·HTTP/2 unprocessed는 메서드 무관(MultiExchange), 11 check-then-write 동시 200 범위 1~15·매번 새는 것 아님, 12 AIP-160 문서화 must 조항 오독 → 두 규칙 분리), 경미 ~9(RFC 9110 SHOULD NOT 조건·프록시 MUST NOT·nginx non_idempotent, count(*) 62~139ms, AIP-158 0개 페이지 조항·base64 경고, AIP-154 INVALID_ARGUMENT, 출력 생략 줄 명시) · 재실행 10종(결정적 일치) · 12 pgbench 원 스크립트 없음 → 재구성 · 담당 밖: 02도 ConnectException 무관 재시도 미기재 → 정합 · **사실 점검 21편 완료** | 4 PASS |
| 2026-10-04 | 판정 회수 17~21(Opus 지적 7): 채택 4·부분 3·기각 0 — 17 errors path MUST·locations SHOULD(2021 §7.1.2)·294와 legacy 문단 관계는 해석 표시(부분)·인트로스펙션 끄기는 자사 클라이언트 API 한정, 18 nginx 기본 키 조건 + RFC 9110 §9.3.3(부분), 19 Azure 게이트웨이 패턴 셋 + 관련 둘, 20 g-auto는 '커밋 위치가 다음 시작점'까지만(재실행 대신 문구), 21 드리프트 3 → 검증 오류 4 | 5 PASS |
| 2026-10-04 | Opus 적대 리뷰 회수 09·10·13·14: 지적 5(09 받는 쪽 코드가 저장 전 seen.add → 503 뒤 재전송이 DUPLICATE 200으로 유실·id 보관 ≥ 허용 오차 2배(±300s), 10 '큐 전에 거른다' vs 워커 검사 모순·SENT 사전 확인 코드 없음, 13 Azure PUT 생성 201/교체 200·result는 액션형만)·14 지적 0 → 판정 발사 | 판정 대기 |
| 2026-10-04 | Opus 적대 리뷰 회수 07·08·15·16: 지적 1(16 GOAWAY last stream ID 정의)·07·08·15 지적 0 → 메인 판정 채택: RFC 9113 txt §6.8 원문('might have taken some action on or might yet take action on') 확인 → 정의·재시도 안전 조건으로 수정 | 1 PASS |
| 2026-10-04 | 판정 회수 09·10·13(Opus 지적 5): 채택 5 — 09 실험 D(Wh2.java): 나쁜 순서 503 뒤 재전송 200·저장 0 vs inbox UNIQUE INSERT 저장 1 → 코드 교체·실험 E: id 보관 300초면 490초 뒤 재전송 ACCEPT, 600초면 DUPLICATE(WebhookBase ±300s), 10 '공급자에 보내기 전에 거른다'로 정합·D 출력은 println 문구라 재실행 출력으로 교체·isSent 사전 확인 추가, 13 Azure PUT 생성 201/교체 200·result는 성공한 액션형 LRO만 | 3 PASS |
| 2026-10-04 | Opus 적대 리뷰 회수 05·06·11·12: 지적 6(05 PATCH는 RFC 5789, 06 keyset 경계가 offset 페이지 첫 행 → 한 행 어긋남(999,980에서 19행), 11 If-Match:* 412는 조건(404 우선 규칙), 12 Q3 스필은 bound가 work_mem 초과 시 전체 외부 정렬·(price,category) 단정·AIP-160 should/must 구분) → 판정 발사(06 재측정·12 tuplesort 소스+EXPLAIN) | 판정 대기 |
| 2026-10-04 | Opus 적대 리뷰 회수 01~04: 지적 4(01 CHM 순서 섞임 원인은 12번째 삽입 resize(16→32)+spread XOR — '+22 점프' 설명 틀림(재현), 02 JDK 재시도 단정에 ConnectException·isUnprocessedByPeer 경로 누락, 03 CannotGetJdbcConnectionException은 NonTransient 계열 → 503 처리기와 본문 불일치, 04 RFC 9457 §5 우선순위 'not clear' vs 'HTTP 상태가 기준' 단정) · **21편 2차 리뷰 완료** → 판정 발사 | 판정 대기 |
| 2026-10-04 | 판정 회수 01~04(Opus 지적 4): 채택 4 — 01 재실험(T.java, JDK 21.0.12): n=11까지 table=16 삽입 순서 그대로, n=12에 table=32·순서 1001@0 1012@0 … 1009@24(원 실험 v2와 일치) → 원인 서술 교체, 02 MultiExchange RETRY_CONNECT 기본·isUnprocessedByPeer(REFUSED_STREAM·GOAWAY) 예외 추가, 03 CannotGetJdbcConnectionException → NonTransient 계열 → 처리기에 명시 추가, 04 RFC 9457 §5 우선순위 미정·§3.1.2 status 용도 | 4 PASS |
| 2026-10-04 | 판정 회수 05·06·11·12(Opus 지적 6): 채택 6 — 05 PATCH는 RFC 5789 §2, 06 keyset 경계 OFFSET N-1로 재측정(same-rows yes 5깊이, 999,980: offset 379~454ms vs keyset 0.111~0.123ms), 11 If-Match:* 412는 새로 만들 PUT일 때만·DELETE/PATCH는 404(§13.2.1), 12 Q3 tuplesort.c(PG17): bound가 메모리 넘으면 전체 외부 정렬(trace 'switching to external sort', Disk 49.9MB) vs OFFSET 2000 top-N 339kB·(price,category,id) 인덱스는 흔한 값 0.188ms/없는 값 Seq+Sort 82.9ms·AIP-160 거절은 should | 4 PASS |
| 2026-10-04 | 집필 회수 종합 28·29(2 PASS, 각 10문항) — 28: 01~21 시나리오 106 + 사례 22~27 24 = 130 링크(check_links.py 누락·오류 0)·재추출 동기화(06 재측정 수치·04-4)·인용 65개 원문 확인, 29: Twitter 2010 Matt Harris 공지(08-24·10-19)·snowflake-2010 IdWorker·X IDs 문서 / Optus 2022 보도자료·고객 서한·OAIC 2025-08-08(ACMA는 접속 불가 → 2차 보도) · 실험 A JS 정밀도(61비트 1000개 → 5개로 뭉침)·B 순번 ID 무인가 999명 노출 vs 무작위·소유자 검사 · [?] 8(29) · 커리큘럼 '무인증 API 열거' 원문 근거 약함 → 제목 조정 · 사고: 저장소 루트 out.txt(10번 집필 워커, 05:01) → scratchpad/ad/stray로 이동 · 사실 점검 28·29 발사 | 2 PASS |
| 2026-10-04 | 웹 교차 표본 회수: 44건(01~21 전부, 편당 1~3, 사실 점검 표본과 겹침 회피) — 일치 44·불일치 0·확인 불가 0 + 추가 대조 4 일치 · RFC는 rfc-editor txt·초안은 ietf archive txt · 별도 보고: 14:89 04 '미작성' → 정합으로 · 산출 web-cross-sample.md | 44/44 |
| 2026-10-04 | 사실 점검 회수 28·29: 중대 0, 중간 3(29 OAIC 목록은 '보유' 정보 목록이지 노출 건수 아님, ~41bit 길이 → 10-20 후속 Q&A('24 days after Snowflake starts counting')로 [?] 해소, Optus 답변서 반박 추가(2차)), 경미 ~8 · 28 링크 130·인용 전수·수치 ~45 현행 leaf와 일치(v2와 diff 0) · 재실행 3종 일치 · [?] 29 9→8 · ACMA·연방법원 접속 불가(2차 출처 유지) · 2차 리뷰 28·29 발사 | 2 PASS |
| 2026-10-04 | Opus 적대 리뷰 회수 28·29: 지적 5 + 참고 3(28 '구 앱 크래시' 원인에 필드 삭제(07은 예외 없음)·Unrecognized field를 07-1에 매핑·20-2 근거 g-auto, 29 twepoch는 2010-11-04 커밋에서 정해짐(태그는 2014)·'unsigned 64비트' vs Q&A 'signed 64bit') · **23편 2차 리뷰 완료** → 판정 28·29 + 정합 패스 한 워커로 발사(scratchpad/ad/consistency-prompt.md) | 회수 대기 |
| 2026-10-04 | 판정+정합 회수: 판정 28·29 채택 7·확인 1·기각 0(28 필드 삭제는 크래시 아님→07-2·07-3, Unrecognized→07-3, 20-2 근거 문구, 29 제목 표현·Jackson 판 목록, 29 twepoch 이력 GitHub API: 태그 2014-05-29·'another twepoch' 2010-11-04 커밋으로 [?] 일부 해소·signed 64bit 정정·iTnews 화자) · 정합: 05 정답 isUnprocessedByPeer 보강·14 미작성→04 링크·남은 미작성 13(폴더 없는 영역)·정의 일치(294·9457 §5·412/428·429·409/422) · 28 링크 130 재대조 0 깨짐 · 링크 762 깨짐 0 · 22~27 diff 0 · 영역 밖 'api-design 미작성' 20줄 + 사례 4줄 → NEXT | 23 PASS |
| 2026-10-04 | 마감: 노트 커밋 325ade7e(93파일 = 23×4 + 영역 표) · check 새 23 PASS · 전역 링크 75→75 · 컨테이너 sn-ad 0 · 루트 파일 0 · 완료 요약·생략한 검증·NEXT(N0-m·N0-c)·측정로그 · 아카이브 0건 | 커밋 |

## 리뷰 ledger

| 대상 | 리뷰어 | 중대 | 중간 | 경미 | [?] 전→후 | 비고 |
|---|---|---|---|---|---|---|
| 17~21 | Opus 독립 | 0 | 4 | ~9 | 1→0 | 웹 표본 15 · 실험 재실행 6 |
| 09·10·13·14 | Opus 독립 | 0 | 4 | 9 | 3→0 | 웹 표본 12 · 실험 재실행 6 |
| 07·08·15·16 | Opus 독립 | 0 | ~10 | ~6 | 2→1 | 웹 표본 12 · 실험 재실행 12 |
| 01~04 | Opus 독립 | 0 | 3 | ~5 | 0→0 | 웹 표본 12 · 실험 재실행 9 |
| 05·06·11·12 | Opus 독립 | 0 | 3 | ~9 | 2→2 | 웹 표본 12 · 실험 재실행 10 |
| 17~21 판정 | Opus(Opus 2차 지적 7) | 채택 4 | 부분 3 | 기각 0 | | codex 한도로 Opus 2차 |
| 07·08·15·16 판정 | 메인(Opus 2차 지적 1) | 채택 1 | 부분 0 | 기각 0 | | 07·08·15 지적 0 |
| 09·10·13 판정 | Opus(Opus 2차 지적 5) | 채택 5 | 부분 0 | 기각 0 | | 14 지적 0 · 재실험 2 |
| 01~04 판정 | Opus(Opus 2차 지적 4) | 채택 4 | 부분 0 | 기각 0 | | 재실험 1 |
| 05·06·11·12 판정 | Opus(Opus 2차 지적 6) | 채택 6 | 부분 0 | 기각 0 | | 재측정 3 |
| 28·29 | Opus 독립 | 0 | 3 | ~8 | 9→8 | 웹 표본 6 · 실험 재실행 3 |
| 28·29 판정 | Opus(Opus 2차 지적 5+참고 3) | 채택 7 | 부분 0 | 기각 0 | | 정합 패스와 함께 |

## 생략한 검증

- 빚 없음(긴급 아님). 명세 V3 대체: codex 한도(10-04 08:53 리셋, 2차 리뷰 시점 04:50~)로 23편 전부 Opus 적대 리뷰 — codex 대비 누락률 미측정(NEXT).
- 원문 미열람(노트에 표기): ACMA·호주 연방법원 문서(접속 불가 → 2차 보도), Snowflake 발표 블로그(403), Optus 2022-10-03 원문, DDIA 4장 본문, 07 brownout 수치. MQTT·AMQP는 브로커 이미지가 없어 실험 대신 명세로.
- 사례 22~27(옛 형식)은 check_new 6 FAIL — 이름 변경 전부터의 형식 차이(본문 무변경 원칙).

## 완료 요약

- 결과: T0 사례 6편 이름 변경(01~06 → 22~27, 링크 62곳·커리큘럼 8곳, 커밋 861c50e6) + `cs/api-design/` 새 leaf 23편(01~21·28·29) + 영역 표 재생성(초안(Claude) 29) — 커밋 325ade7e(브랜치 docs/api-design-writing, main 8dfaf3c4에서).
- 검증: check 새 23 PASS · 전역 링크 깨짐 75 → 75(T0 전·후·최종 동일) · 1차 Opus 점검 6묶음(중대 0·중간 ~27, 실험 재실행 ~46, 결정적 출력 일치·비결정 범위 확대) · 2차 Opus 적대 리뷰 23편 → 지적 28 + 참고 3 → 판정 채택 27·부분 3·기각 0(재측정 다수: 06 keyset 경계·12 tuplesort·01 CHM resize·09 웹훅 유실·10 outbox) · 정합(미작성→링크·정의 일치·28 링크 130) · 웹 44/44.
- 확인된 의외 사실: RFC 10008 QUERY(2026-06 Standards Track) 실재 · Jackson 3.0 FAIL_ON_UNKNOWN_PROPERTIES 기본 false·SORT_PROPERTIES_ALPHABETICALLY true · Spring Boot 4.0 server.error.* → spring.web.error.* · 정보통신망법 시행령 제61조②(야간 예외 매체 = 전자우편).
- 운영 사건: 저장소 루트 out.txt 1(10번 집필 워커 → scratchpad로 이동) · 멈춘 자기 컨테이너 1(rm 후 재실행).
- 대표 diff(2차 리뷰 채택 재측정, `cs/api-design/06-pagination/2-summary.md:84`):
  - before: keyset 경계를 `OFFSET $off LIMIT 1`(offset 페이지 첫 행)로 잡아 한 행 어긋남 — 999,980에서 19행, offset 394.901~515.670ms
  - after: `| 999,980 | 379.114 ~ 454.388 ms | 0.111 ~ 0.123 ms |` (경계 OFFSET N-1, 5깊이 same-rows yes)
- CS 이슈 아카이브: 0건 — 발견 사실은 노트 본문 반영.
