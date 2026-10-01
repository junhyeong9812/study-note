# 재번호 보고서 — curriculum.md leaf 번호 = 권장 학습 순서 (3차, 원본 재생성)

## 1. 변환 규칙 (구현 그대로)

| # | 대상 | 처리 |
|---|---|---|
| 1 | 행 slug `| NN-name |` | 영역 `권장 학습 순서` 위치(1부터) = 새 번호 |
| 2 | 학습 순서 줄 | 같은 영역 번호를 위치 번호로 치환 → `01 → 02 → … → NN` 순차. 괄호 묶음(`(… 심화)`·`필요 시`)과 교차 영역 참조(`security/03~07`, `(network/29~32)`)는 형태 유지, 교차 참조는 규칙 4로 매핑 |
| 3 | 기존 노트 경로 | `기존` 칸(8번째 셀)의 `area/NN…` 토큰이 `cs/<p>`·`<p>`(+`foundations/languages`→`languages`)로 **실존하면 유지**, 아니면 leaf 참조로 매핑. §19 표 첫 열은 전부 유지 |
| 4 | leaf 참조 `area/NN-slug`·`area/NN`·목록 | 백틱 안팎·모든 셀·산문 공통. slug는 옛 slug와 **정확 일치**해야 매핑(불일치 시 중단 — 0건). 목록 `·`/`~` 연속은 **같은 영역 번호로 항목별 매핑**(구분자 보존). 범위 `AA~BB`는 옛 구간 전체를 매핑한 뒤 연속이면 `A~B`, 아니면 3개 이상 연속 구간만 `~`로 묶고 `·` 나열. 쉼표·`/`는 목록 연속으로 보지 않음(`language/22, 41`의 41은 reliability) |
| 5 | 선행 칸 같은 영역 `NN`·`NN-slug`·`NN~NN` | 행의 영역 기준 매핑. 범위는 집합 매핑 → math 역색인 `01~15`(자기 앞 전체)는 `01~15`로 의미 보존. `전체`·`—` 유지 |
| 6 | 산문·셀 속 같은 영역 맨 번호 | 후보 전수 추출(괄호·목록·백틱 속 번호·맨 slug) → 문맥 판정 → 아래 §3 표. 교재 장·§·L#·Item·RFC·연도·판·개수·노트 번호는 유지 |
| 7 | §20 | 통계 표·합계·"필수만 따라가면 N" 재계산(스크립트), 산문 옛 번호는 새 번호로. "2026-09-28 cs 재편" 노트 줄 1행 추가(현재 파일에서 이식) |

처리량: 영역 접두 토큰 575개 매핑(번호 변경 453·우연히 동일 122) · 선행 칸 같은 영역 항목 694개 · 규칙 6 수동 92개 번호(73건) · 보호(노트 경로) 161개(기존 칸 영역 토큰 78 + §19 첫 열 83) · 줄 수 = 원본 + 1(§20 노트 줄).

## 2. 합격 기준 결과

```text
A PASS leaf 644 — 644
A PASS 영역 19 — 19
A PASS slug·번호 중복 0 — 0
A PASS 학습 순서 = 01..N — []
B PASS dangling 0 — 검사 토큰 1312, dangling 0 []
C PASS 의미 보존(area 토큰) — 419 토큰(수동 92 포함), 불일치 0 []
C PASS 의미 보존(규칙 6 수동) — 불일치 0 []
D PASS 선행 칸 대상 집합 — 644행, 불일치 0 []
E PASS 노트 경로 바이트 동일 — 392 토큰, 불일치 0 []
정렬: 1804 줄 정렬, 추가 줄 1 ['- 2026-09-28 cs 재편: 기초 leaf 2(data-struc']
```

- **A** leaf 644 · 영역 19 · slug·번호 중복 0 · 19영역 전부 학습 순서 = `01..N`.
- **B** dangling 0 — 새 문서 전체(노트 경로 제외) `area/NN-slug`는 새 slug 집합, `area/NN`·목록·범위는 영역 번호 범위 안. 선행 칸 같은 영역 항목 포함 1,312 토큰.
- **C** 의미 보존 — difflib 줄 정렬(1,804줄 1:1 + 추가 1줄) 후 위치별 토큰을 옛 체계/새 체계로 각각 해석해 대상(영역, slug 이름) 비교, 불일치 0. 규칙 6 수동 92개도 옛 대상 = 새 대상 확인. 예외 1: §20 `실무 domain-modeling/24`(갭 리서치 문서의 제안 ID — 이 문서 leaf 아님, 유지).
- **D** 선행 칸 — 644행 모두 원본 대상 집합 = 새 대상 집합.
- **E** 노트 경로 — 기존 칸 실존 경로·§19 첫 열 392개 원본과 바이트 동일.
- 추가: `기존` 칸 주 경로 해석(resolve.py) 원본 195/실패 0 → 새 195/실패 0. slug-map.tsv 644행 = 계산 매핑과 불일치 0.

## 3. 규칙 6 판정 표

### 3.1 바꿈 (73건, 번호 92개)

| 원본 줄 | 영역 | 옛 → 새 | 문맥 | 이유 |
|---|---|---|---|---|
| 88 | software-design | `20`→`46` | Quality→12/20·17 | 12/20 = software-design/20-quality-attributes (·17은 영역 번호) |
| 88 | software-design | `05~06`→`10·13` | Maintenance→12/05~06 | 12/05~06 = software-design/05-code-smells·06-refactoring |
| 576 | network | `15~22`→`15~22` | TCP(15~22) | TCP 단원 leaf 구간 |
| 576 | network | `19·20·21`→`19·20·21` | 본체가 19·20·21이다 | TCP 종료·TIME_WAIT·keepalive leaf |
| 604 | network | `12`→`10` | PMTUD 깨짐(12) | network/12-fragmentation-mtu-pmtud |
| 842 | database | `54`→`22` | (서버 측 한도는 54) | database/54-database-side-timeouts |
| 843 | reliability | `47-cancellation-propagation`→`09-cancellation-propagation` | ·`47-cancellation-propagation` | 앞 토큰 reliability/45 에 이어진 같은 영역 slug |
| 846 | database | `43-key-strategy-surrogate-natural-public-id`→`28-key-strategy-surrogate-natural-public-id` | (연결: `43-key-strategy-surrogate-natural-public-id`) | database 영역 행의 같은 영역 slug |
| 989 | reliability | `46·47`→`08·09` | (심화는 46·47) | 46 예산 분배·47 취소 전파 |
| 1007 | reliability | `06·07·17`→`05·06·34` | 기존 06·07·17은 | 시간 예산 단원 설명 |
| 1007 | reliability | `06`→`05`, `45`→`07`, `07`→`06`, `46`→`08`, `47`→`09`, `17`→`34`, `48`→`32`, `49`→`35` | `06 데드라인 전파` → `45 계층별 타임아웃` → `07 재시도·재시도 예산` → `46 예산 분배` → `47 취소 전… | 백틱 속 순서 목록 |
| 1007 | reliability | `46`→`08`, `07`→`06`, `07`→`06`, `46`→`08` | (46의 선행이 07이라 07을 46 앞에 둔다.) | 순서 근거 |
| 1014 | reliability | `36`→`31` | (설계 본문은 36) | reliability/36-batch-job-restart |
| 1015 | reliability | `12`→`13` | `reliability/06`·`12` | 📚 칸 — 앞 reliability 토큰에 이어진 번호 |
| 1022 | reliability | `40`→`37` | 힙 분석 심화는 40 | reliability/40-memory-leak-and-heap-analysis |
| 1052 | reliability | `50`→`48` | 안티패턴은 50) | reliability/50-performance-and-stability-antipatterns |
| 1054 | reliability | `48-batch-and-job-time-bounds`→`32-batch-and-job-time-bounds` | 시간 한도는 `48-batch-and-job-time-bounds` | 같은 영역 slug |
| 1062 | reliability | `41`→`42` | 느림(language/22, 41) | 41 cold-start (language/22 목록이 아님 — 쉼표) |
| 1062 | reliability | `40`→`37`, `42`→`39`, `49`→`35`, `47`→`09`, `48`→`32` | RSS만 우상향(40) | 역색인 |
| 1062 | reliability | `40`→`37`, `42`→`39`, `49`→`35`, `47`→`09`, `48`→`32` | 더 느림(42) | 역색인 |
| 1062 | reliability | `40`→`37`, `42`→`39`, `49`→`35`, `47`→`09`, `48`→`32` | 결제됨(49· | 역색인 |
| 1062 | reliability | `40`→`37`, `42`→`39`, `49`→`35`, `47`→`09`, `48`→`32` | 계속 돔(47· | 역색인 |
| 1062 | reliability | `40`→`37`, `42`→`39`, `49`→`35`, `47`→`09`, `48`→`32` | 이중 실행(48) | 역색인 |
| 1093 | software-design | `46·47·48`→`07·08·09` | 주석은 46·47·48로 분리 | 46 naming·47 function·48 comments |
| 1093 | software-design | `39`→`11` | 잘못된 추상화(→ 39) | 39 when-to-abstract |
| 1093 | software-design | `09`→`20` | (연결: E ↔ 09, A ↔  | 기존 칸 연결 — 09 oop-fundamentals |
| 1093 | software-design | `39`→`11` | , N ↔ 39) | 기존 칸 연결 — 39 |
| 1095 | software-design | `41`→`14`, `42`→`51`, `45`→`53`, `39`→`11` | (판단층은 41 Tidy First·42 레거시 기법·45 핫스팟·39 추상화 되돌리기) | 판단층 leaf |
| 1099 | software-design | `04`→`06` | 가독성 — 04 분할 | 04-clean-code 분할 |
| 1114 | domain-modeling | `05`→`05`, `10`→`11` | `domain-modeling/04`·`05`·`10` | 기존 칸 연결 — 앞 domain-modeling 토큰에 이어진 번호 |
| 1115 | software-design | `56`→`36` | Plugin은 56) | 56 extension-points-and-plugins |
| 1115 | software-design | `53`→`33` | 프록시 우회는 53) | 53 aop-and-proxies |
| 1140 | software-design | `33`→`29` | 리팩터링 경로는 33) | 33 refactoring-to-patterns |
| 1146 | software-design | `10`→`21` | (취약한 기반 클래스, 10) | 10 composition-over-inheritance |
| 1169 | software-design | `43`→`41` | 자동 검증은 43) | 43 architecture-fitness-rules |
| 1169 | software-design | `43`→`41` | 모듈 분리 불가(→ 43) | 43 |
| 1182 | software-design | `42`→`51` | 변경 기법은 42) | 42 legacy-change-techniques |
| 1183 | software-design | `25-legacy-migration-strangler-fig`→`50-legacy-migration-strangler-fig` | (연결: `25-legacy-migration-strangler-fig`) | 같은 영역 slug |
| 1192 | software-design | `39`→`11`, `29·32`→`25·26`, `28`→`40`, `45`→`53`, `49`→`54`, `31`→`24`, `50`→`18`, `51`→`28`, `53`→`33`, `54`→`34` | 늘어남(39) | 역색인 |
| 1192 | software-design | `39`→`11`, `29·32`→`25·26`, `28`→`40`, `45`→`53`, `49`→`54`, `31`→`24`, `50`→`18`, `51`→`28`, `53`→`33`, `54`→`34` | 도배(29·32) | 역색인 |
| 1192 | software-design | `39`→`11`, `29·32`→`25·26`, `28`→`40`, `45`→`53`, `49`→`54`, `31`→`24`, `50`→`18`, `51`→`28`, `53`→`33`, `54`→`34` | 폴더 4개(28) | 역색인 |
| 1192 | software-design | `39`→`11`, `29·32`→`25·26`, `28`→`40`, `45`→`53`, `49`→`54`, `31`→`24`, `50`→`18`, `51`→`28`, `53`→`33`, `54`→`34` | 어디부터?(45) | 역색인 |
| 1192 | software-design | `39`→`11`, `29·32`→`25·26`, `28`→`40`, `45`→`53`, `49`→`54`, `31`→`24`, `50`→`18`, `51`→`28`, `53`→`33`, `54`→`34` | 코드 누적(49) | 역색인 |
| 1192 | software-design | `39`→`11`, `29·32`→`25·26`, `28`→`40`, `45`→`53`, `49`→`54`, `31`→`24`, `50`→`18`, `51`→`28`, `53`→`33`, `54`→`34` | 상태 행(31) | 역색인 |
| 1192 | software-design | `39`→`11`, `29·32`→`25·26`, `28`→`40`, `45`→`53`, `49`→`54`, `31`→`24`, `50`→`18`, `51`→`28`, `53`→`33`, `54`→`34` | NPE(50) | 역색인 |
| 1192 | software-design | `39`→`11`, `29·32`→`25·26`, `28`→`40`, `45`→`53`, `49`→`54`, `31`→`24`, `50`→`18`, `51`→`28`, `53`→`33`, `54`→`34` | switch 복제(51) | 역색인 |
| 1192 | software-design | `39`→`11`, `29·32`→`25·26`, `28`→`40`, `45`→`53`, `49`→`54`, `31`→`24`, `50`→`18`, `51`→`28`, `53`→`33`, `54`→`34` | 미적용(53) | 역색인 |
| 1192 | software-design | `39`→`11`, `29·32`→`25·26`, `28`→`40`, `45`→`53`, `49`→`54`, `31`→`24`, `50`→`18`, `51`→`28`, `53`→`33`, `54`→`34` | 순서 역전(54) | 역색인 |
| 1199 | domain-modeling | `18·19`→`15·26` | leaf 18·19가 가리킨다 | 연습 컬렉션 leaf |
| 1224 | domain-modeling | `22`→`13`, `23`→`14` | (시간 심화는 22, 금액 심화는 23) | 22 instant-vs-local·23 money |
| 1247 | api-design | `21-case-refund`→`27-case-refund` | ·`21-case-refund` | 앞 api-design/19 토큰에 이어진 같은 영역 slug |
| 1385 | web-platform | `08`→`08`, `15~22`→`13~20` | 측정은 08, 처방은 15~22 | 16.2 제목 — 성능 단원 |
| 1396 | web-platform | `24`→`22` | (설계 관점은 24) | 24 islands-and-micro-frontends |
| 1403 | web-platform | `20`→`18` | 재렌더 비용은 20) | 20 ui-rerender |
| 1404 | web-platform | `21`→`19` | 비용 측면은 21) | 21 hydration-cost |
| 1556 | data-analysis | `12`→`20` | 카이제곱 적합도(12) | 12 categorical-inference |
| 1594 | data-structure | `36·02·03·04·06`→`02·04·05·06·09` | 심화 leaf(36·02·03·04·06,  | data-structure 기초 → 심화 leaf |
| 1595 | algorithm | `31·06·01·03`→`02·04·05·07` | 심화 leaf(31·06·01·03) | algorithm 기초 → 심화 leaf |
| 1610 | web-platform | `03`→`03` | , /03 ↔  | web-platform/03 약식 |
| 1610 | web-platform | `04`→`04` | , /04 ↔  | web-platform/04 약식 |
| 1610 | web-platform | `05`→`05` | , /05 ↔  | web-platform/05 약식 |
| 1641 | reliability | `07·08·09`→`06·10·28` | (+ 07·08·09 패턴 연결) | server-design 06 → reliability/06·11 + 패턴(07 재시도·08 서킷·09 벌크헤드) |
| 1655 | software-design | `46·47·48`→`07·08·09` | 주석은 신규 46·47·48) | 46~48 |
| 1658 | engineering-practice | `13`→`15`, `14`→`16`, `15`→`17` | (quality) · 13 (security) · 14 (operational) · 15 (legal | engineering-practice/12 목록의 이어진 번호 |
| 1703 | api-design | `16~21`→`22~27` | 이동(번호만 16~21로) | 사례 leaf 구간 |
| 1703 | api-design | `16-case-order-point`→`22-case-order-point`, `21-case-refund`→`27-case-refund` | api-design/16-case-order-point ~ 21-case-refund | 범위 양끝 slug |
| 1736 | domain-modeling | `18·19`→`15·26` | (각 leaf 18·19) | 연습 컬렉션 leaf |
| 1738 | network | `46~52`→`39~45`, `41~42`→`33~34`, `24~26`→`16·18·20` | 네트워크 46~52 | 추가 leaf |
| 1738 | algorithm | `46~52`→`39~45`, `41~42`→`33~34`, `24~26`→`16·18·20` | 알고리즘 41~42 | 추가 leaf |
| 1738 | api-design | `46~52`→`39~45`, `41~42`→`33~34`, `24~26`→`16·18·20` | API 24~26 | 추가 leaf |
| 1740 | software-design | `43`→`41` | 아키텍처 테스트 부분은 43) | 43 architecture-fitness-rules |
| 1741 | software-design | `46~48`→`07~09` | 주석을 46~48로 분리 | 46~48 |
| 1769 | software-design | `04-clean-code`→`06-clean-code` | 19 leaf와 04-clean-code 요지 | software-design/04-clean-code |

### 3.2 유지 (100건)

| 원본 줄 | 문맥 | 이유 |
|---|---|---|
| 23 | 13·14·17장 | 교재 장 번호 |
| 75 | server-design/03·04 | 기존 노트(server-design) 번호 — 영역 아님 |
| 76 | ops-patterns 07·08·11~16·18 | 기존 노트 번호 |
| 77 | ops-patterns 01~06·09·10·19 / server-design 01·05·06·08~11 | 기존 노트 번호 |
| 81 | api-design 01~06 | §0.6 「기존 흡수 대상」 = 기존 노트 번호 |
| 87 | AL→2·3 … SE→12~17 … SPD→16 | 영역 번호(§ 번호) |
| 88 | Config Mgmt→17, Models→12·13, Testing→14, Operations→11 | 영역 번호 |
| 175 | PRNG(2008, 키 공간 32,767개) | 수치 |
| 181 | 기존 01~35 번호를 그대로 유지 / 신규는 36번부터 | 재번호 전 설계 서술(기존 노트 번호) — 한계에 기록 |
| 274 | 기존 01~30 유지, 신규 31번부터 | 재번호 전 설계 서술 — 한계에 기록 |
| 681 | `systems/server-design` 02 | server-design 노트 번호(📚) |
| 742 | `29-credentials-and-cookies` | languages/web-api 노트 경로의 연속 |
| 820 | F-01~08 | 실패 카탈로그 항목 번호 |
| 848 | `systems/server-design` 08 | server-design 노트 번호 |
| 852 | `systems/server-design` 04 | server-design 노트 번호 |
| 943 | `systems/server-design` 07 | server-design 노트 번호 |
| 982 | F-01~25 | 카탈로그 항목 번호 |
| 1023 | `systems/server-design` 01 | server-design 노트 번호 |
| 1024 | `systems/server-design` 09 | server-design 노트 번호 |
| 1047 | `systems/server-design` 08 | server-design 노트 번호 |
| 1048 | `systems/server-design` 05 | server-design 노트 번호 |
| 1113 | Item 54·55 | Effective Java 아이템 |
| 1131 | 생성·구조·행위 패턴 23 | GoF 패턴 개수 |
| 1163 | 12-factor | 방법론 이름 |
| 1199 | basic 30·advanced 30 | 편 수 |
| 1226 | 10,000원 | 금액 |
| 1237 | `systems/server-design` 03 | server-design 노트 번호 |
| 1327 | (21~08시) | 시각 |
| 1375 | `39-idle-scheduling` | languages/web-api 노트 경로의 연속 |
| 1374 | `08·09` | languages/web-api 노트 번호 |
| 1451 | §18·§19~§21·18a | 절 번호 |
| 1608 | `c/syntax/44·45` 등 | languages 문법 노트 번호 |
| 1610 | `08·09·10`·`38·39`·`01·15~18·20`·`25~30`·`28·29`·`32·33` | languages/web-api 노트 번호 |
| 1641 | 01 → … 11 → (server-design 편 번호) | server-design 노트 번호 |
| 1663 | (01~19 + 3개 개념 폴더) | ops-patterns 노트 번호 |
| 1739 | 실무 28 · 성능 21 · … 유지보수성 19 | 갭 리서치 leaf 개수 |
| 1740 | 유지보수성 32·33·43·35, 실무 25, #3·#6·#5·#2·#8 | 갭 리서치 문서의 제안 번호 |
| 1740 | 실무 domain-modeling/24 | 갭 리서치(gap-practical.md) 제안 slug ID — 이 문서 leaf 아님 (C 검사 예외) |
| 1765 | 28 leaf·21 leaf·17 leaf·29 leaf·19 leaf | 갭 문서 leaf 개수 |
| 78 | §0.6 표 # 열 12~18 | 영역 번호 |
| 79 |  | 영역 번호 |
| 80 |  | 영역 번호 |
| 82 |  | 영역 번호 |
| 83 |  | 영역 번호 |
| 85 |  | 영역 번호 |
| 190 | ch11~13 | 교재 장 |
| 288 | CLRS 3·17 | 교재 장 |
| 302 | CMU 15-445 L11 | 강의 번호 |
| 318 | 1<<31 | 코드 수치 |
| 371 | OSTEP 36·37·44 | 교재 장 |
| 380 | 64→16비트 | 수치 |
| 421 | 64→16비트 | 수치 |
| 442 | OSTEP 26 · 27 | 교재 장 |
| 443 | OSTEP 7·8·9·10 | 교재 장 |
| 449 | OSTEP 13 · 15 · 16 | 교재 장 |
| 450 | OSTEP 18·19·20 | 교재 장 |
| 451 | OSTEP 14 · 17 | 교재 장 |
| 452 | OSTEP 21 · 22 | 교재 장 |
| 461 | OSTEP 28 · 29 | 교재 장 |
| 473 | OSTEP 40 · 41 | 교재 장 |
| 474 | OSTEP 42 · 43 | 교재 장 |
| 487 | CS:APP 10·11 | 교재 장 |
| 577 | Stevens 13·14·17장 | 교재 장 |
| 699 | OSTEP 53~57 · OWASP Top 10 | 교재 장·목록명 |
| 754 | GDPR Art. 17 | 법 조항 |
| 768 | CMU 15-445 | 강의 코드 |
| 891 | DDIA 5·8·9·10·11장 | 교재 장 |
| 971 | SRE 3·4·6·21·22 | 교재 장 |
| 1037 | 12-factor XI | 방법론 이름 |
| 1053 | SEC 명령 34-70694 | 문서 번호 |
| 1269 | SWE@G 11·12·13·14장 | 교재 장 |
| 1383 | BCP 47 | 표준 번호 |
| 1418 | SWE@G 9·16·18·23·24장 | 교재 장 |
| 1443 | SEC 34-70694 | 문서 번호 |
| 1461 | DDIA 11·12장 | 교재 장 |
| 1489 | EDPB 02/2025 | 문서 번호 |
| 1574 | 약 16,000건 | 수치 |
| 1609 | (60주제) \| 60 | 개수 |
| 1735 | 38 leaf | 개수 |
| 1742 | 349 leaf·(34)·(29)… | 개수 — §20 재계산으로 갱신 |
| 1751 | 17 KA | 개수 |
| 1752 | OSTEP 1~57 | 교재 장 |
| 1753 | L0~L25 | 강의 번호 |
| 1757 | 18 KA | 개수 |
| 1785 | 15-445 | 강의 코드 |
| 1766 | 21 leaf | 개수 |
| 1767 | 17 leaf | 개수 |
| 1768 | 29 leaf | 개수 |
| 1049 | SRE 14·15장 | 교재 장 |
| 1097 | Item 17 | Effective Java 아이템 |
| 1105 | APOSD 12·13장 | 교재 장 |
| 1123 | Item 18 | Effective Java 아이템 |
| 1193 | 1985–87 | 연도 |
| 1323 | 2^53 | 수치 |
| 1364 | §19 | 절 번호 |
| 1431 | SWE@G 23·24장 | 교재 장 |
| 504 | §19 | 절 번호 |
| 59 | §21 | 절 번호 |
| 672 | RFC 9110 §14 | RFC 절 |
| 215~477 | CLRS·OSTEP 장 번호(📚 칸 다수) | 교재 장 |

## 4. 남은 한계

1. **검사의 독립성**: B·C는 변환과 같은 토큰 정규식(`AREA_TOK`)·매핑 표를 쓴다. 정규식이 못 잡는 형태(예: 영역 접두 없는 맨 번호)는 C가 아니라 규칙 6 후보 전수 추출(괄호·목록·백틱 속·맨 slug, 약 400개 → 바꿈 92·유지 판정)로만 덮였다. D(선행 칸 독립 파서)·E(바이트 비교)는 독립.
2. **옛 번호 정책 서술이 사실과 어긋남(번호만 바꾼다는 제약으로 문구 미수정)**: §2 머리말 "기존 01~35 번호를 그대로 유지…신규는 36번부터", §3 머리말 "기존 01~30 유지, 신규 31번부터", §19.6 "유지(번호·폴더명 그대로)"(대상 열은 `data-structure/03~18·20~24·27·30~42`로 매핑됨)·"이동(번호만 22~27로)". 문구 교정은 별도 결정 필요.
3. **`기존` 칸의 실존 노트 경로는 옛 폴더 번호 그대로**: 예 `(연결: \`algorithm/28-number-theory\`)`(leaf는 algorithm/31), `data-structure/35-allocator`(leaf 31), `data-structure/33-filesystem`(leaf 30), `data-structure/34-dependency-resolver`(leaf 32), `algorithm/18-scc`(leaf 21), `api-design/03-stock-deduct` 등 — 규칙 3대로 노트 폴더 경로라 유지. 노트 폴더가 이동·재번호되면 다시 갱신해야 한다.
4. **`기존` 칸 `data-structure/11·25·32`(database/14 행)**: 목록 표기라 실존 경로로 해석되지 않아 규칙 3에 따라 leaf 참조로 보고 `data-structure/20·39·24`로 매핑했다. 같은 내용의 노트 폴더는 11·25·32다.
5. **§20 `실무 domain-modeling/24`**: 갭 리서치 제안 ID라 유지했으나, 새 체계의 domain-modeling/24(double-entry-ledger)와 표기가 겹쳐 오독 소지가 있다.
6. **§20 머리말 "선행 칸 참조 931개(영역/slug 247 + 같은 영역 684)"** 수치는 재계산하지 않았다(642 leaf 시점 값). 표·합계·"필수만 351"은 재계산했고 현재 파일 수치(644·+127·464·180·351·249·44)와 일치.
7. **범위 표기 형식**: 비연속으로 흩어진 옛 범위는 `03~18·20~24·27·30~42`처럼 길어진다(의미는 보존).
