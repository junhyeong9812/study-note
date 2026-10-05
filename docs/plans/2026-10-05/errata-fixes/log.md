# log — errata-fixes

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-10-05 | 인터뷰(4묶음 전부: 낡은 미작성 링크·사실 오류(원본·myway 포함)·커리큘럼 오기·legal 법령 갱신 · 검증 가볍게, 합의 auto) → 명세 작성 직후 승인 기록 · 브랜치 docs/errata-fixes · T4 법령은 stakes 중간으로 codex 1회 추가(명세 §5에 명시) · 규모: "미작성" 337곳/207파일(대상 실재 여부 미확인) | SPEC=1·MODE=auto |
| 2026-10-05 | T3 커리큘럼(메인): 6건 교정 — §7 02행 '12로'→'10으로'(10-fragmentation-mtu-pmtud)·§7 44행 '47의 사이드채널'→43(compression-side-channels)·§13 Horizon 1999~→2000~(판결 [1])·§16 06 🔧 IndexedDB 구현 표현·§3 alg 03 ⚠ 과일반화·§12 56행 GAO-14-694 [?] 제거 · **기각 3**(NEXT N0-e의 data-structure/13-radix-trie·41-rope·algorithm/04-binary-search는 커리큘럼 번호 규칙(§0 22행 예시와 같음)상 맞는 참조 — 폴더 번호로 바꾸면 오히려 틀림) · 생성기 재실행: 요지 칸만 생성되므로 domain-modeling/curriculum.md 1줄만 변경 · T1·T2·T4 워커 3 병렬 발사 | 진행 |
| 2026-10-05 | T2 사실 오류 회수: 7항목·10파일 — Knight(reliability/04 2곳·3-answer·ops-patterns) SEC ¶1·¶17 기준 · 03-stack 트레이스 1024(globals.hpp·실측 javac 1024/소스 실행기 1019) · foundations/data-structures-basics 정정 3줄 + 코드 3(후위 순회·insert 중복 return·remove None) · foundations/algorithm-basics 조건 3 + binary_search sort 제거·bubble 조기 종료(실행 확인) · lsm-merge-model run 1개·FTL 과장 · os/31 → reliability/36·20 실링크 · operational-standards straggler → systems/straggler · 링크 66 깨짐 0 · os/31:132 math/10은 대상 없음(math README뿐)이라 유지 | 완료 |
| 2026-10-05 | T1 링크 회수: 검토 346곳 → 실재 대상 191곳 링크화(136파일, 링크 226 추가) · 남김 155(대상 없음 149·상태 어휘 5·애매 1 → 메인이 bloom-filter 07-hashmap = 05-hashmap으로 처리) · 링크 2,454 깨짐 0 · check FAIL 43은 HEAD와 동일(옛 형식) · T4 법령 회수: 법률 제21445호·시행령 제36671호 등 7개 원문(law.go.kr DRF API, OC=test)과 글자 단위 대조 — 2-summary 13곳·provisions.md 11곳 교체/신설(제26·29·30의3·34·64의2조, 시행령 39·39의2·39의3·40조), 일치 확인 조문 다수 · 메인: provisions.md 낡은 ※ 주기 정정 · codex 법령 리뷰 발사 | 진행 |
| 2026-10-05 | codex(high) 법령 diff 리뷰: 원문 파일 9개(blk_law 26·29·30의3·34·64의2, blk_dec 39·39의2·39의3·40) 열람 확인 후 **no findings** · 메인 검증: 변경 파일 전체 상대 링크 2,602 깨짐 0 · T1 대상 파일의 삭제 줄 전부 "미작성" 포함(의도 외 변경 0) · 커밋 4(a3549a23 법령·d7fc2deb 사실·eb91962e 커리큘럼·5d86293b 링크) | 완료 |
| 2026-10-05 | 사용자 확인 "main 병합 + push" → main ff d9bc037c..8121ff99, push | origin/main = 8121ff99 |

## 리뷰 ledger

| 대상 | 리뷰어 | 결과 | 비고 |
|---|---|---|---|
| T2 사실 7항목 | Opus 워커(1차 출처·실행) | 10파일 교정 | SEC 사본·globals.hpp·RocksDB wiki·CPython 실측 |
| T4 법령 | Opus 워커 → codex(high) | 24곳 교체/신설 · codex 0건 | law.go.kr DRF 원문 7종 글자 단위 대조 |
| T1 링크 | Opus 워커 + 메인 전수 검사 | 192곳 · 깨짐 0 | 남김 149(대상 없음) |

## 생략한 검증

- T1·T2·T3는 사용자 선택("가볍게")대로 codex 생략 — 링크·문구 교정, 사실 수정은 1차 출처 대조로 대신. T4만 codex 1회. provisions.md 새 앵커의 GitHub 렌더링은 미확인(NEXT N0-s).

## 완료 요약

- T1 낡은 "미작성" 표기 192곳 → 실제 링크(137파일) · 남김 149(대상 영역 미작성)
- T2 사실 오류 7항목(Knight·트레이스 1024·foundations 2편 코드/조건·LSM run·os/31 소속·straggler 링크)
- T3 커리큘럼 오기 6건 정정, 3건 기각(커리큘럼 번호 규칙상 맞음)
- T4 legal-standards: 2026-09-11 시행 개인정보 보호법(법률 제21445호)·시행령(제36671호) 반영 — 제34조 ② 유출 가능성 통지, 시행령 제39조의2·3, 제64조의2 가중 10%, 제30조의3 신설 · codex 0건
- 핵심 diff(실파일에서 복사): `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` before `기저 누락 → \`StackOverflowError\`; 중복 부분문제 → 지수 시간` → after `기저 누락 → \`StackOverflowError\`; 중복 부분문제가 지수적으로 쌓이면 지수 시간`
- CS 이슈 아카이브: 0건(문서 정정).
