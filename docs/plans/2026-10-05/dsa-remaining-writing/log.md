# log — dsa-remaining-writing

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-10-05 | 인터뷰(자료구조·알고리즘 잔여 21편 · 원고 보강 방식 · 검증 앞과 같게 · 합의 auto) → 명세 작성 직후 승인 기록 · 브랜치 docs/dsa-remaining-writing(main cf3b4e73) · 폴더 = 커리큘럼 번호 NN-slug(생성기 규칙·기존 외부 링크와 일치, myway 폴더와 번호 접두 겹침 허용) | SPEC=1·MODE=auto |
| 2026-10-05 | 브리핑 3종(engineering-practice판 이식 + 번호 대응 주의·DSA 실험 예시·이미지 빌드 금지·호스트 gcc/python/압축 도구) · 집필 발사(Opus 5병렬, 17편): ds-01(ds 01·02, alg 01·02) / ds-25(ds 25·26·29) / alg-03(alg 03·09·11, ds 19) / alg-12(alg 12·39·40·41) / alg-33(alg 33·34) — 종합 ds 43·44, alg 42·43 후속 | 회수 대기 |
| 2026-10-05 | 집필 회수 1/5: alg 33·34(2 PASS, 각 10문항, [?] 1 — Brotli 서버 모듈 기본 품질) — 실험: 허프만 vs H0·1비트 하한(rANS p=0.9 0.47bit), ABRACADABRA 23비트·정규 부호, LZ77 겹침 복사·체인 깊이, DEFLATE 작은 입력 팽창·폭탄 1029:1·상한 예외, gzip 예외 문구 3, zstd/gzip/xz 레벨별 시간·비율(호스트 zstd 1.5.5), 사전 압축 1.10→3.03배·Dictionary mismatch, FCS 생략·윈도 초과 거부, 재압축 팽창 · lz4·brotli는 문서 근거 · 다른 영역 network/39·43·44의 33·34 '미작성' 표기는 정합 단계 목록 · 사실 점검 발사 | 2 PASS |
| 2026-10-05 | 집필 회수 2/5: alg 12·39·40·41(4 PASS, 각 9문항, [?] Sipser 정리 번호) — 실험(OpenJDK 21.0.12): 충돌 키 String 트리화 32~37ms vs 비Comparable 16.6~19.2s(n=16384), 유니버설 해시 최대 칸 10000→12, CRC32 선형성, abs(hashCode) 음수 인덱스, CPython siphash13·PYTHONHASHSEED, 고정 피벗 n(n-1)/2 vs 무작위·McIlroy 시드 적대자, Fermat vs MR 거짓말쟁이·isProbablePrime certainty별 오류, 저수지 균등, 3-SAT→독립집합 500/500·2-근사 최대 2.000, 걸음 상한 판정기 대각선 실패, javac 확정 대입 오탐 · 사실 점검 발사 | 4 PASS |
| 2026-10-05 | 집필 회수 3/5: alg 03·09·11 + ds 19 보강(4 PASS, 각 10문항, [?] 2 — GNU sort 기본값·Cassandra 전략 변경 재병합) — 실험: -Xss별 재귀 깊이(-Xint thin 1782~46465)·HotSpot/V8 꼬리 호출 미제거·fib 호출 ×2.618, 비교자 계약 위반 예외 빈도·예외 없이 틀린 순서·n<32 무예외, TimSort 적응성, 안정 정렬 다중 키·페이지네이션 중복(시뮬), -Xmx64m 128MB 외부 정렬 팬인별 패스, k-way 선형 vs 힙, 대체 선택 런 길이, LSM 레벨 vs 티어 WA·SA(시뮬) · 원본 정정 2(레벨당 run 1개·FTL 과장) · 사실 점검 발사 | 4 PASS |
| 2026-10-05 | 집필 회수 4/5: ds 01·02 + alg 01·02(보강 2 포함, 4 PASS, [?] 0) — 실험: pop(0) 큐 O(n²) vs deque, 원본 코드 버그 재현(후위 순회·remove·중복·정렬 입력 BST 높이 n), ArrayList/LinkedList/int[] 메모리, get(i) 루프 O(n²)·jcmd 스택(LinkedList.node:582), ArrayDeque vs LinkedList, 이진 탐색 비교 ⌊log2 n⌋+1·원본 매번 sort, (lo+hi)/2 오버플로, 삽입 정렬 경우별 비교 수, 분할 상환 1.5배 확장 복사 합·+10칸 n²·add 스파이크 = G1 Humongous 431ms, 두 배 비율 · 원본 정정 9(참고 줄) · 사실 점검 발사 | 4 PASS |
| 2026-10-05 | 사실 점검 회수 alg 33·34: 중대 0·중간 2(압축 폭탄 '1KB→1GB'는 DEFLATE 1032:1 한계 위반 → 1MB, PostgreSQL TOAST 기본 pglz) · 경미 ~12 · 실험 재실행 12 전부 결정값 일치 · [?] 1→1 · 웹 표본 6 → codex 2차 발사(33·34) | 2 PASS |
| 2026-10-05 | codex(high) 2차 회수 alg 33·34 — 판정은 다른 묶음과 함께 | 대기 |
| 2026-10-05 | 집필 회수 5/5: ds 25·26·29(3 PASS, [?] 6 — 원인 미분석 측정 흔들림 등 명시) — 실험: 링 가득 참 판정 3방식·마스크·ABQ 네 응답·SPSC 링 vs ABQ·생산자 2개 무예외 유실·int 넘침 인덱스, 힙 vs 휠(512/131072칸)·PQ.remove O(n)·STPE removeOnCancel 누수·휠 틱 지연, HashMap 동시 put 유실·TreeNode 무한 루프 2/16·CHM get+put vs merge, ABA 재현(Java·C free/malloc 같은 주소)·CME best-effort·큐 처리량 · **17편 집필 완료** → 사실 점검 ds-25 + 종합 4편 집필 발사 | 3 PASS |
| 2026-10-05 | 사실 점검 회수 alg 12·39·40·41: 중대 0·중간 3(oCERT 대상 언어 목록·HashMap 트리화 조건(9번째 삽입·split 때 6 이하)·McIlroy 동결 규칙 반대로 서술) · 경미 ~10 · 실험 재실행 10 결정값 일치·범위 확장 · [?] +1(Sipser 문제 번호) · 05-hashmap과 정합 · 웹 표본 12 → codex 2차 발사 | 4 PASS |
| 2026-10-05 | codex(high) 2차 회수 alg 12·39·40·41(6·6·4·5) + 앞의 33·34(4·6) → 판정 2워커 발사(33·34 / 12·39·40·41) | 회수 대기 |
| 2026-10-05 | 사실 점검 회수 ds 01·02 + alg 01·02: 중대 0·중간 5(Sedgewick 1.3 성능 목표 [?]·ArrayDeque vs LinkedList n=1M 승자 재실행 불일치 → 회차마다 다름·Bloch '무한 루프' 근거 없음·DualPivotQuicksort 44 '미만'+혼합 삽입 65·두 배 실험 범위) · 원본 정정 9건 원본 줄과 대조 일치 · 실험 재실행 12 · [?] +1 · 웹 표본 12 → codex 2차 발사 | 4 PASS |
| 2026-10-05 | 사실 점검 회수 ds 25·26·29: 중대 0·중간 4(Logback neverBlock 기본은 80% 이후 INFO 이하 폐기·io_uring u32 head/tail·Varghese–Lauck 계층 휠 예를 원문 예로·wait-free = 상한 있는 단계) + 새 사실 1(ASan heap-use-after-free 확인, quarantine으로 주소 재사용 ABA 숨김) · 경미 ~14 · 실험 재실행 13 결정값 일치 · Disruptor 표 2 원문 일치 · [?] 6→4 · 웹 표본 9 → codex 2차 발사 | 3 PASS |
| 2026-10-05 | 판정 회수 alg 33·34(codex 지적 10): 채택 9·부분 1·기각 0 — DEFLATE 부호 길이 전송은 동적 블록만·gzip 헤더 최소 10B·permessage-deflate 컨텍스트 협상·zstd 레벨 매개변수 비단조·해제 = 엔트로피 복호·repeat offset 예외·Dictionary_ID 선택 필드 · 판정 실험 1(32KB 밖 반복: gzip 200,060B → zstd 100,125B) | 2 PASS |
| 2026-10-05 | 판정 회수 alg 12·39·40·41(codex 지적 21): 채택 15·부분 6·기각 0 — Comparable 키 compareTo=0이면 트리도 선형·유니버설 보장 조건·SHA-256 vs HMAC·CPython 빌드 옵션·중복 키 퀵정렬 n(n-1)/2·McIlroy는 무작위 피벗에도 실행 중 적용·passesLucasLehmer = 일반 Lucas 판정·결정 문제 정의·NP-hard 정의·라이스 정리 = 언어 성질 · 메인 후속: 41 장애·핵심 문장 2곳도 '언어의 성질'로 정합 | 4 PASS |
| 2026-10-05 | codex(high) 2차 회수 ds 01·02·alg 01·02 → 판정 발사 | 회수 대기 |
| 2026-10-05 | 사실 점검 회수 alg 03·09·11 + ds 19: 중대 0·중간 4(Jackson 깊이 예외 문구 판마다 다름(2.15 vs 2.16+)·PG 9.6 대체 선택은 replacement_sort_tuples 미만 첫 런만·확인 안 되는 메일링 리스트 출처 삭제·ds19 Cassandra 기본값 노트 안 모순) · 경미 ~10 · 실험 재실행 16 결정값 일치 · 128MB 파일 삭제 · [?] 2→2 · 영역 밖: data-structure/03-stack:529 '수천 줄'(MaxJavaStackTraceDepth 1024) · 웹 표본 12 → codex 2차 발사 | 4 PASS |
| 2026-10-05 | codex(high) 2차 회수 ds 25·26·29 → 판정 발사 | 회수 대기 |
| 2026-10-05 | 판정 회수 ds 01·02·alg 01·02(codex 지적 10, 파일 계수 11 중 1은 머리말): 채택 9·부분 1·기각 0 — Stack 비판은 비용 아닌 인터페이스 범위·ArrayDeque 분할상환·AbstractList 반복자 예외·contains O(1) 예외(nCopies)·CopyOnWriteArrayList clear·C int 폭 구현 정의·장애 제목 실험과 모순·트리화 최악 보장 조건·평균 경우 = 표본·초기 용량 공식 넘침(재현: IAE -2147483648 → HashMap.newHashMap) | 4 PASS |
| 2026-10-05 | codex(high) 2차 회수 alg 03·09·11·ds 19 → 판정 발사 · **17편 codex 2차 완료** | 회수 대기 |
| 2026-10-05 | 판정 회수 ds 25·26·29(codex 지적 17): 채택 15·부분 2·기각 0 — 순진한 링 덮임 1·2만·마스크 = 나머지는 seq≥0·bitCount MIN_VALUE·TCP 재전송 실패 시 중단·취소 STPE 작업은 callable null(요청 객체 미보유)·누적은 취소율×타임아웃에서 포화·Netty 틱 상한 아님·틱 비용 평균·HashMap 키 실제 유실 재실험(containsKey 255379~394417, size와 어긋남)·CHM putAll/clear 비원자·stamp 코드 실제 코드와 맞춤 | 3 PASS |
| 2026-10-05 | 판정 회수 alg 03·09·11·ds 19(codex 지적 18): 채택 13·부분 5·기각 0 — 재귀 정당성 종료 전제·Jackson 상한 조건·중복 부분문제 ≠ 지수 일반·DP = 상태 수×상태당·프레임 수 그림 불일치·minGallop 조정·정답 6 실험 출력 모순·키셋 부등호 방향·compaction 스냅숏 보존·PG 최종 병합 on-the-fly·원소 보존 검증·lazy leveling 블룸 전제·레벨 SA 조건·접두사 블룸 · **17편 판정 완료(지적 76: 채택 61·부분 15·기각 0)** | 4 PASS |
| 2026-10-05 | 집필 회수 종합 4편: ds 43·44, alg 42·43(4 PASS, Q/A 8·9·8·10, [?] 2) — 실험: SOE 트레이스 1024 프레임 절단(깊이 ~2만)·HashDoS 32768 충돌 키 String 51~68ms vs 비Comparable 31.7~32.1s·Python 해시 랜덤화·JDK7 transfer 순환(시뮬레이션 명시)·두 배 비율·(low+high)>>1 오버플로 n=2^30+1·\\s+$ O(n²)·[^=]*= find O(n²)·U+200C 비공백 · 원문 오류 발견: Stack Overflow 사후 보고 합계 199,990,000(실제 200,010,000) · 커리큘럼 28C3 제목 'Efficient'→실제 'Effective' · 사실 점검 발사 + 웹 교차 표본(17편) 발사 | 4 PASS |
| 2026-10-05 | 웹 교차 표본 회수(17편): 76건 — 일치 75·불일치 1(alg 02:286 28C3 제목 'Efficient'→'Effective', SipHash 논문 참고문헌 [24]의 오인용이 출처) → 메인이 수정 · 관찰 5(Stack '동기화 오버헤드'는 해석·JDK 버그 트래커 불가로 커밋 대조·bpo-34561 Versions 필드 3.8·eprint 차단·missing return은 JLS 8.4.7) · web-cross-sample.md 저장 | V5 충족 |
| 2026-10-05 | 사실 점검 회수 종합 4편: 중대 0·중간 6(ds44 작은 n '두 배마다 2배' 재현 불가·전체 배율 쓸 수 없음·HashMap size vs 키 유실 구분·JDK-6423457 평가 원문(Doug Lea)·ds43 수치 범위·alg42 Jackson 문구 판별) · 경미 ~8 · leaf 링크 135 전수(깨짐 0) · 사고 원문 7건 대조 · U+200C 0 · [?] 2→1 · 메인 후속: alg 09 legacy 문구 3곳(17회 틀린 순서는 기본 TimSort, legacy 순서 미검사) → codex 2차(종합 4) 발사 | 4 PASS |
| 2026-10-05 | codex(high) 2차 회수 종합 4편(6·4·4·4) · **21편 codex 2차 완료** → 판정(종합 4) + 정합 패스(21편) 한 워커 발사(scratchpad/dsa/consistency-prompt.md) | 회수 대기 |
| 2026-10-05 | 판정 + 정합 회수: 종합 4 codex 지적 18 채택 16·부분 2·기각 0(List.copyOf 비동기 복사·불변이면 미복사 실험·트리화 비Comparable tieBreakOrder·PEP 456 FNV 예외·PYTHONHASHSEED 0만 끔·두 배 실험 = 의심·8퀸 n!·midLong 조건·.NET \\s 집합·Bloch C 오타) · 정합: alg 01 2^30+1·alg 03 소스 실행기가 트레이스 끝을 잘라 1019(javac 1024, launcher Main.java invocationFrames)·ds 43 증가 배율 1.5배·alg 09 Contract2 값 범위 차이 명시 · 링크 업그레이드 3 · 상대 링크 745 깨짐 0 · 영역 밖 목록 22곳(보고만) | 21 PASS |
| 2026-10-05 | 정정: 위 '집필 회수 종합 4편' 행의 '커리큘럼 28C3 제목 Efficient'는 틀린 서술 — 커리큘럼(263행)은 제목을 적지 않는다. 'Efficient'는 메인이 쓴 집필 브리핑 §1(SipHash 논문 참고문헌 [24]의 오인용을 옮김)에서 왔다 · 노트는 모두 'Effective'로 정정됨 | 기록 정정 |
| 2026-10-05 | 메인 마감: 21 PASS · 정리 확인(sn-dsa 컨테이너 0·dangling 26·루트 새 파일 0·리프 md만) · 생성 문서 재생성(data-structure 초안 44·algorithm 초안 43, 두 curriculum.md만 변경) | 노트 커밋 d292d2d1 |
| 2026-10-05 | 사용자 확인 "main 병합 + push" → main ff 0310d6cb..d9bc037c(cf3b4e73 포함), push | origin/main = d9bc037c |

## 리뷰 ledger

| 대상 | 리뷰어 | 중대 | 중간 | 경미 | [?] 전→후 | 비고 |
|---|---|---|---|---|---|---|
| alg 33·34 | Opus 독립 | 0 | 2 | ~12 | 1→1 | 웹 표본 6 · 실험 재실행 12 |
| alg 12·39·40·41 | Opus 독립 | 0 | 3 | ~10 | 2→3 | 웹 표본 12 · 실험 재실행 10 |
| ds 01·02·alg 01·02 | Opus 독립 | 0 | 5 | ~12 | 0→1 | 웹 표본 12 · 실험 재실행 12 |
| ds 25·26·29 | Opus 독립 | 0 | 4 | ~14 | 6→4 | 웹 표본 9 · 실험 재실행 13 |
| alg 33·34 판정 | Opus(codex 지적 10) | 채택 9 | 부분 1 | 기각 0 | | 재실험 1 |
| alg 12·39·40·41 판정 | Opus(codex 지적 21) | 채택 15 | 부분 6 | 기각 0 | | 재실험 0 |
| alg 03·09·11·ds 19 | Opus 독립 | 0 | 4 | ~10 | 2→2 | 웹 표본 12 · 실험 재실행 16 |
| ds 01·02·alg 01·02 판정 | Opus(codex 지적 10) | 채택 9 | 부분 1 | 기각 0 | | 재실험 1 |
| ds 25·26·29 판정 | Opus(codex 지적 17) | 채택 15 | 부분 2 | 기각 0 | | 재실험 1 |
| alg 03·09·11·ds 19 판정 | Opus(codex 지적 18) | 채택 13 | 부분 5 | 기각 0 | | 재실험 0 |
| 웹 교차 17편 | Opus 독립 | 불일치 1(수정) | 확인 불가 0 | 관찰 5 | | 76건 |
| ds 43·44·alg 42·43 | Opus 독립 | 0 | 6 | ~8 | 2→1 | 웹 표본 12 · 실험 재실행 8 |
| 종합 4 판정 + 정합 | Opus(codex 지적 18) | 채택 16 | 부분 2 | 기각 0 | | 재실험 3 · 정합 모순 5 교정 |

## 생략한 검증

- 없음(빚 0). 참고 한계: 교재 본문(CLRS 3판·Sipser 3판·Knuth·Sedgewick 1.3 세부)은 열지 못해 장·절 단위 또는 `[?]` · JDK 버그 트래커는 실시간 접근 불가로 Internet Archive 사본·openjdk 커밋으로 대조 · lz4·brotli는 CLI 없어 문서·RFC 근거만 · JDK7 동시 resize는 시뮬레이션(JDK7 이미지 없음) · alg 43 Safer.java(2분+)와 39 중복 키 n(n-1)/2는 재실행 안 함 · 정합 패스는 지시 축 표적 대조.

## 완료 요약

- 산출: 자료구조 8(01 보강·02·19 보강·25·26·29·43·44) + 알고리즘 13(01 보강·02·03·09·11·12·33·34·39·40·41·42·43), 폴더 = 커리큘럼 번호(myway 폴더와 접두 겹침 허용) · 생성 문서 2개 재생성. 원본(foundations 2·lsm-merge-model)은 읽기만 — 원본 오류 11건은 새 노트 "참고:" 줄.
- 검증: V1 21 PASS · V1b/V2 Opus 사실 점검(중대 0·중간 24, 실험 재실행 6묶음 전부) · V3 codex(high) 21/21, 지적 94 → 채택 77·부분 17·기각 0 · V4 정합(모순 5 교정·링크 745 깨짐 0) · V5 웹 76건(불일치 1 수정) + 사실 점검 웹 표본 ~60.
- 핵심 diff (실파일에서 복사):
  - `cs/data-structure/curriculum.md` before `> 현황: 미작성 6 · 원고 있음 2 · 초안(Claude) 36 · 검수 완료 0` → after `> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 44 · 검수 완료 0`
  - `cs/algorithm/curriculum.md` before `> 현황: 미작성 12 · 원고 있음 1 · 초안(Claude) 30 · 검수 완료 0` → after `> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 43 · 검수 완료 0`
- 발견(영역 밖, 보고만 → NEXT): 다른 영역·myway 노트 22곳이 이번 21편을 "미작성"으로 가리킴 · `data-structure/03-stack:529` "수천 줄"(트레이스 기본 1024) · `foundations/data-structures-basics` §7 "스택 오버플로"(CPython은 RecursionError) · 커리큘럼 284행 alg 03 ⚠ "중복 부분문제 → 지수 시간" 과일반화 · Stack Overflow 사후 보고 합계 오기(원문, 노트에 명시).
- 사고: 메인이 종합 지시문을 따옴표 없는 heredoc으로 만들어 백틱이 셸 명령으로 확장됨(경로·수식 조각 — 전부 실패로 끝나 부작용 없음) → 지시문 재작성. 교훈: 지시문 생성은 Write 도구 또는 `<<'EOF'`.
- CS 이슈 아카이브: 0건(문서 작업 — 이슈 카드 대상 없음).
