# log — language-writing

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-10-07 | 연속 진행 계획(네트워크 원고 1 완료 → **언어 27** → 데이터 분석 28, push는 끝에 한 번) · 명세·브리핑 3종(data-engineering판 이식 + 언어 실험·1차 출처 URL) · 브랜치 docs/language-writing(749279e4에서) | SPEC=1·MODE=auto |
| 2026-10-07 | 집필 발사(Opus 5병렬 = 동시 상한, 25편): 01(01~04·22) / 05(05~08·17·18) / 09(09~13) / 14(14·15·23~25) / 16(16·19~21) — 종합 26·27과 사실 점검은 끝난 자리부터 이어 띄움 | 회수 대기 |
| 2026-10-08 | 집필 회수 1/5: 05·06·07·08·17·18(6 PASS, [?] ~14 — Rust·tsc·mypy 없음은 문서 인용으로 명시) — 실험(JDK 21·node 22·Go 1.23·gcc 13·CPython 3.12): 소거·힙 오염 CCE·checkedList·공변 배열 ASE, 알고리즘 W 축소판, Integer 캐시 127/128·AutoBoxCacheMax, 가변 기본 인자, structuredClone, PEP 683 불멸 객체 refcount, var/let 클로저·V8 Context 공유 누수 152MiB, finally return이 예외 삼킴(3언어), 예외 비용(스택 채움 608~732ns vs 값 21~29ns)·OmitStackTraceInFastThrow 5,181번째부터, equals 오버로드로 HashSet 실패·remove(int) vs remove(Object), 추측 탈가상화(gcc)·메가모픽 4종부터 10ns·PrintInlining, 스트림 두 번 소비 ISE·count가 map 건너뜀 · 원고 정정 3(C 포인터 '참조 전달'·4바이트·인터닝) · 영역 밖 '미작성' 후보 software-design·web-platform 12곳 보고 → 사실 점검 fc-05 발사(동시 5) | 6 PASS |
| 2026-10-08 | 집필 회수 2/5: 16·19·20·21(4 PASS, Q/A 각 9, [?] 3) — 실험: 무한 큐 풀 OOM(큐 ~3,8xx)·Abort/CallerRuns, 풀 크기별 처리량, 공용 풀 블로킹 1,001ms·병렬도<2면 작업마다 새 스레드, submit/runAsync 예외 소실, ThreadLocal 누출, 불변 스냅샷 교체 / 다이아몬드 NoSuchMethodError(클래스패스 순서 5가지)·npm 두 판 공존·Go MVS(GOPROXY=off·replace)·락 없는 캐럿 해석 변화·sys.path 섀도잉 / UB null 검사 삭제·x+1>x 컴파일러·옵션별·넘친 뒤 검사 무력·Cloudbleed 모양 합성 오버런(자기 버퍼·40바이트 제한) ASan 탐지 한계 / 언어별 실패 등급 표·기동 시간 C 3~4ms ~ Java 59~93ms · 원고 정정 2(Rust 경계 위반 컴파일 거부 아님, Go 다중 워드 레이스 메모리 손상 가능) · 커리큘럼 19행 선행 data-structure/32 → 실제 34 · 영역 밖 미작성 후보 9곳 → 사실 점검 fc-16 발사(동시 5) | 4 PASS |
| 2026-10-08 | 집필 회수 3/5: 09~13(5 PASS, Q/A 각 10) — 실험: CPython 순환 1000쌍 20.4MB·gc.collect 2,011개, getrefcount 불멸 여부가 3.12.3/3.12.14에서 다름, UAF 재사용·ASan·-Wuse-after-free, GC 4종(Serial STW 149~192ms·ZGC STW 0.063ms vs 앱 지연 12~16ms·G1 Evacuation Failure→Full GC), GC overhead limit(Parallel 예외 vs G1은 heap space), 컨테이너 한도별 기본 GC·힙(1791 Serial/1792 G1·200MiB 50%), humongous 600KB vs 400KB, 객체 크기·필드 재배치·List<Long> 3.5배·탈출 분석 0B vs 32B/call·객체 풀링 반패턴(Young GC 45~51ms), SB 리트머스 모드별·C race TSan·-O2 무한 루프 · 원고 정정 3 · 영역 밖 미작성 후보 7곳 → 사실 점검 fc-09·fc-16 발사(동시 5) | 5 PASS |
| 2026-10-08 | 집필 회수 4/5: 01~04·22(5 PASS, Q/A 9·10·10·10·10) — 실험: 계층 컴파일 -Xint 50~160배·PrintCompilation level 3→4 OSR→made not entrant, ReDoS Py/node 지수 vs Go 선형 vs **Java (a+)+$ 평평(메모이제이션)·역참조 변형은 수 초**, V8 실험적 선형 엔진, Thompson NFA, 재귀 하강 깊이 한계·-Xss, JSON 깊이 Py 9,997 vs node 10⁶, parse_qsl 마지막 값 vs URLSearchParams 첫 값(파서 불일치), var/let·UnboundLocalError·late binding, DCE·SCEV 최종 값 치환 0ns 벤치·UB null 검사 삭제(gcc -O2 0 vs clang -1) · 원고 정정 6 · **영역 밖 사실 불일치 후보: algorithm/13 'Java (a+)+$ 한 글자마다 두 배'(JDK 21 실험은 평평)** · 미작성 후보 8곳 → 사실 점검 fc-01·fc-09 발사(동시 5) | 5 PASS |
| 2026-10-08 | 집필 회수 5/5: 14·15·23·24·25(5 PASS, Q/A 각 10, [?] 4) — 실험: 가상 스레드 507ms vs 고정 풀 200 5,083ms·synchronized pinning 5,029ms vs ReentrantLock 121ms, node 동기 블로킹 타이머 지연 171ms, Go 채널 누수, GIL CPU 스레드 무이득·프로세스 1.04~1.30s·SMT 쌍에선 이득 없음·g+=1 경쟁 재현 조건, 역최적화 2→24→6us, CDS/AppCDS 기동 179→84ms, Native Image 없음 → 도달성 BFS 모형, LTO 인라인·full LTO 링크 0.28→168s·비대표 PGO 2배 느림·strip · CodeCache full 재현 실패(소스 근거만) · 원고 정정 2(GIL §9 수치·§10) · **25편 집필 완료** → 종합 26·27 집필 발사(동시 5), fc-14는 빈 자리에 | 5 PASS |
| 2026-10-08 | 사실 점검 회수 05·06·07·08·17·18 (6 PASS, **중대 2**: 06 PEP 683 범위 오인(인턴 문자열 불멸은 PEP 본문 아님 — 3.12.3 vs 3.12.14 실측 차, gh-113993), 17 '3종 이상 → 인라인 없음' 단정(주 수신 타입 90%면 인라인 시도, doCall.cpp) / 중간 6: JLS 5.1.7은 상수 식만·valueOf 캐시는 API 보장·AutoBoxCacheMax는 Integer만, JDK 18 this$0 근거, Race 1라운드 2,000,000(단정 수정), Go 1.22는 go.mod 버전 조건, 예외 비용 호출당·절반 실패 / 경미 다수, [?] 15→10, 실험 재실행 결정적 출력 일치 · 규칙 이탈 1: GOFLAGS=-mod=mod 1회(--network none이라 무해) · 06↔09 getrefcount 서술 정합 필요) → codex 2차 발사 + fc-14 발사 | 6 PASS |
| 2026-10-08 | 사실 점검 회수 01~04·22 (5 PASS, 중대 0 / 중간 6: 01 계층 그림 level 1=trivial·level 2=C2 큐 밀림, 실험 범위 6회(-Xint 대비 40~210배), 02 엔진 비교 범위(Java (a+)+$ 평평 vs 역참조 지수 재현), 03 CPython json 9,997 = C_RECURSION_LIMIT 10000 해석([?] 해소)·Jackson 메시지 버전별 / 경미 다수, 실험 재실행 일치(비결정 값 범위 확대)) → codex 2차 발사 | 5 PASS |
| 2026-10-08 | 사실 점검 회수 16·19·20·21 (4 PASS, 중대 0 / 중간 9: 16 스냅샷·풀 크기 실험 범위·해석(반쪽 관측 3.9만~337만, 40 vs 80 실행마다 바뀜), 19 Cox Version SAT 해석 표시·npm도 네 가정 성립·go mod graph 실제 출력, 20·21 C arr[5] 값 실행마다 다름, 21 Math.addExact 예제 컴파일 오류(자기 초기화) 수정·기동 시간 범위 / 경미 다수, overrun.c 안전 확인(자기 버퍼·40바이트), [?] 증감 ±0, 실험 재실행 결정적 출력 일치) → codex 2차 발사 | 4 PASS |
| 2026-10-08 | 사실 점검 회수 09~13 (5 PASS, **중대 2**: 10 GC 실험 범위가 좁음 → 5회 범위(ZGC STW 0.063~0.145ms·앱 12~30ms 등), 13 'race 없으면 SC'를 C11 조건 없이 단정(seq_cst·뮤텍스만일 때) / 중간 ~7: 09 UAF ≠ Cloudbleed·Heartbleed 원인, getrefcount 패치 차 gh-113993 근거, 10 Full GC 로그 줄 오인, 11 humongous 범위·to-space exhausted 확정, 12 32GB 경계 확정, 13 SB 범위 / [?] 14→3, 실험 재실행 일치) → codex 2차 발사 | 5 PASS |
| 2026-10-08 | 종합 집필 회수 26·27(2 PASS, Q/A 9·9) — 26: leaf 장애 시나리오 117개 전부 색인(누락 0), JDK 21 증상별 첫 줄·맨 위 프레임 실측(NPE 상세 메시지·SOE 1,024프레임 잘림·NoSuchMethodError 서술자) / 27: Cloudbleed(2017-02-23 원문)·Heartbleed(NVD API, security/30과 같은 원문)·left-pad(npm 블로그 IA, 272 패키지·2.5시간) + 2019 ReDoS 한 단락, 실험: 공유 버퍼 offset 오용 시 Java에서도 누출(합성 데이터)·left-pad 의존 모형 · [?] 신규 0 → 사실 점검 fc-syn 발사 | 2 PASS |
| 2026-10-08 | 사실 점검 회수 14·15·23·24·25 (5 PASS, 중대 0 / 중간 ~7: 15 abs(0) 레이스 범위 180만~370만·원고 §9 재현 5~25%, 23 CodeCache full 뒤 '전체 인터프리터'·'회복 안 됨' 단정 → UseCodeCacheFlushing·maybe_restart_compiler 조건, 역최적화 비율 11~17배, 24 PGO 없는 AOT 근거(GraalVM PGO 문서)·PGO는 CE에 없음, 25 호스트 측정 라벨 / [?] 4개 해소·잔여 2, 실험 재실행 일치(25 실험 2는 재실행 안 함 — 노트 명시)) → codex 2차 발사 | 5 PASS |
| 2026-10-08 | codex(high) 2차 회수 16·19·20·21(지적 8·7·5·8 = 28) → 판정 발사(adj-16, 동시 2: fc-syn·adj-16) | 회수 대기 |
| 2026-10-08 | codex(high) 2차 회수 09~13(지적 7·6·7·4·2 = 26) → 판정 발사(adj-09, 동시 3) | 회수 대기 |
| 2026-10-08 | codex(high) 2차 회수 01~04·22(지적 6·4·5·3·6 = 24) → 판정 발사(adj-01, 동시 4) | 회수 대기 |
| 2026-10-08 | 판정 회수 16·19·20·21 (28건: 채택 19·부분 9·기각 0 — out 개수·표 합계 일치, 4 PASS. 16 CallerRuns 종료 시 버림·Active Object 변형·Snapshot 그림을 코드 쓰기 순서로, 19 다이아몬드 '해 없음' 모순·JVMS 해소 시점 허용 범위·Cox 그래프 비순환 가정 금지·-X importtime은 경로 안 보임(실측), 20 ++p>=pe도 UB·넘침 검사식 len>INT_MAX-add·ASan 범위, 21 CPython 3.12 JIT 아님·Number("")=0 통과(실측)·strtol endptr(실측)·safe Rust 한정·BCE · 한계: JVMS 5.4·JLS 17.5·npm peer·Python import·Kotlin when·Rust Reference는 재열람 없이 판정 → 웹 표본에서 우선 대조) | 회수 |
| 2026-10-08 | codex(high) 2차 회수 05·06·07·08·17·18(지적 8·4·8·8·8·7 = 43) → 판정 발사(adj-05, '출처는 직접 열 것' 지시 추가, 동시 4) | 회수 대기 |
| 2026-10-08 | 판정 회수 01~04·22 (24건: 채택 21·부분 3·기각 0 — out 개수·표 합계 일치, 5 PASS. 01 닫힌 세계는 AOT 일반 아님·CPython 평가 루프는 computed goto·JDK 21에 AOT 캐시 없음(JEP 483=24), 02 DFA 그림 수정·Go regexp에 DFA 없음(소스)·Java 문자 클래스 반복은 루프·split fastpath, 03 PEG 왼쪽 재귀 허용·Clang ParenExpr·&& 조건부 평가, 04 LOAD_FAST_CHECK(실측)·클래스 본문 스코프 예외, 22 -O0도 GIMPLE(실측)·LLVM 기본 할당기 Greedy·NP-hard vs NP-완전·JMH 상수 접기) | 회수 |
| 2026-10-08 | 판정 회수 09~13 (26건: 채택 18·부분 6·기각 2 — out 개수·표 합계 일치, 5 PASS. 09 3.12.7 체인지로그 두 항목 상충 → C API 문서 따름(interned 불멸 아님)·free 뒤 포인터 값 불확정·safe Rust 한정, 10 nextInt(256) 64~319·G1 카드/기억 집합 구분·GC overhead 전형 원인은 '겨우 들어감', 11 Evacuation Failure 원인·Mixed 후보 회수 효율 순·로그 값은 영역 수, 12 AoS/SoA 재계산, 13 race 정의 쓰기 조건 · 기각 2(11 해석 2건)은 재실행으로 근거 보강 · **06↔09 interned 문자열 서술 정합 필요** → 정합 단계) | 회수 |
| 2026-10-08 | 사실 점검 회수 26·27 (2 PASS, 중대 0 / 중간 ~16: 26 색인 수치를 사실 점검·판정 후 leaf 값으로 대량 갱신(10-3·10-1·11-4·23·25·21·07·15·13 등)·JLS 5.1.7 vs API 혼동·SOE 깊이 범위·<local1> 이유(JEP 358), 27 '세 사건 모두 로그 이상 없음' 오류(left-pad는 빌드 로그에 바로 보임)·>= 수정도 UB 단서·1.0.1g 수정식·커밋 출처 / [?] 증감 0, 실험 재실행 일치, Echo.java 안전 확인 · leaf 내부 문제 보고: 11 시나리오 5 수치 낡음·10 시나리오 3 예시가 '오름'을 못 보임·12 시나리오 2 표현 → 정합 단계) → codex 2차 발사 | 2 PASS |
| 2026-10-08 | codex(high) 2차 회수 14·15·23·24·25(지적 6·4·7·3·6 = 26) → 판정 발사(adj-14, 동시 2) | 회수 대기 |
| 2026-10-08 | 판정 회수 05·06·07·08·17·18 (43건: 채택 36·부분 7·기각 0 — out 개수·표 합계 일치, 6 PASS, 출처 전부 직접 열람. 05 int/size_t 비교 조건·시나리오 4 실험과 모순 해소·와일드카드 엄밀 읽기 전용 아님, 06 identityHashCode로 공유 판정 금지, 07 '나은 예'가 인스턴스 메서드로 this 재캡처 → static, 08 Go 에러는 관례상 마지막·Rust panic abort 전략, 17 HotSpot vtable은 Method* 배열·IC 상태 의미·타입 수만으로 인라인 단정 금지, 18 순수성만으로 생략 불가(증명 조건)) | 회수 |
| 2026-10-08 | codex(high) 2차 회수 26·27 (지적 8·4) → 판정 + 정합 패스는 adj-14 판정이 끝난 뒤 발사(26 색인이 14·15·23~25 판정 결과를 반영해야 함) | 대기 |
| 2026-10-08 | 판정 회수 14·15·23·24·25 (26건: 채택 13·부분 13·기각 0 — out 개수·표 합계 일치, 5 PASS, 출처 전부 직접 열람. 14 await 중단은 언어별(JS는 항상, C#/Rust는 완료 시 안 멈춤)·Netty 루프는 등록 채널만, 15 3.12 인터프리터당 GIL·참조 카운트 증감 조건·__iadd__ 예외, 23 타입 프로파일 ≠ 인라인 캐시·역최적화가 전부 버리지 않음·감속 원인 미분리, 24 기본 CDS 아카이브·비어 있지 않은 디렉터리, 25 -fprofile-arcs는 신장 트리 밖 간선만·--gc-keep-exported·size text에 읽기 전용 데이터 포함) → **01~25 판정 완료** → 26·27 판정 + 정합 패스 발사 | 회수 |
| 2026-10-08 | 판정·정합 회수: 26·27 지적 12(채택 9·부분 3·기각 0, out 개수·표 일치) · 26 색인 현 leaf 재대조 갱신 ~13곳 · 06↔09 interned 일치(C API 문서) · leaf 내부 3건 수정(11 수치·10 바닥선 실제 로그 54→62M·12 탈출 분석 명시) · 노트 간 모순: 영역 밖 4건 보고(algorithm/13·42 Java (a+)+$ 두 배·security/25 의존성 DAG·architecture/14 final 조건) · 영역 안 링크 52 · **영역 밖 링크 교정 54곳/37파일**(git word-diff로 링크·'미작성' 표기만 확인) · 링크 1,968 깨짐 0 · 27 PASS + B4 34 PASS/1 FAIL(data-structure/34 기존 FAIL — HEAD도 같음) → 웹 교차 표본 발사 | 27 PASS |
| 2026-10-08 | 웹 독립 교차 표본 회수: **79건 일치 79·불일치 0·확인 불가 0**(판정이 재열람 없이 넘긴 6곳 전부 원문 일치) · 관찰 반영 4(05 MS Learn 변성 문서 근거 추가, 20 N3220 §6.5.7 병기, 21 Kotlin 1.7+ when 조건, 21 Rust release 넘침은 Reference상 구현 재량) → web-cross-sample.md 저장 · README 재생성(language만, 초안(Claude) 27) · 정리: sn-lang 컨테이너·네트워크 0, dangling 볼륨 36·이미지 26, 리프 md만 · 27 PASS | 27 PASS |

## 리뷰 ledger

| 대상 | 리뷰어 | 중대 | 중간 | 경미 | [?] 전→후 | 비고 |
|---|---|---|---|---|---|---|
| 05·06·07·08·17·18 | Opus 독립 | 2 | 6 | ~8 | 15→10 | 웹 표본 18 · 실험 재실행 6묶음 |
| 01~04·22 | Opus 독립 | 0 | 6 | ~10 | −1 | 웹 표본 15 · 실험 재실행 12 |
| 16·19·20·21 | Opus 독립 | 0 | 9 | ~8 | 3→3 | 웹 표본 12 · 실험 재실행 14 |
| 09~13 | Opus 독립 | 2 | ~7 | ~10 | 14→3 | 웹 표본 15 · 실험 재실행 12 |
| 14·15·23·24·25 | Opus 독립 | 0 | ~7 | ~10 | 6→2 | 웹 표본 15 · 실험 재실행 14 |
| 16·19·20·21 판정 | Opus(codex 지적 28) | 채택 19 | 부분 9 | 기각 0 | | 재실험 3(Number(""), strtol, importtime) |
| 01~04·22 판정 | Opus(codex 지적 24) | 채택 21 | 부분 3 | 기각 0 | | 재실험 3(Python 바이트코드, Go 소스, gcc -O0 덤프) |
| 09~13 판정 | Opus(codex 지적 26) | 채택 18 | 부분 6 | 기각 2 | | 재실험 3(humongous 사전 컴파일, Eden 영역 수, javap) |
| 26·27 | Opus 독립 | 0 | ~16 | ~8 | 1→1 | 웹 표본 6 · 실험 재실행 4 |
| 05·06·07·08·17·18 판정 | Opus(codex 지적 43) | 채택 36 | 부분 7 | 기각 0 | | 재실험 0(원출력 대조 1) |
| 14·15·23·24·25 판정 | Opus(codex 지적 26) | 채택 13 | 부분 13 | 기각 0 | | 재실험 0 |
| 26·27 판정 | Opus(codex 지적 12) | 채택 9 | 부분 3 | 기각 0 | | 재실험 0 |

## 생략한 검증

- 없음(빚 0). 참고 한계: Dragon Book·TAPL·GC Handbook·JCIP·POSA2·Sipser 본문은 목차까지만 — 장·절 번호 외 세부는 `[?]` · GraalVM Native Image·JOL·JMH·jcstress·Rust·tsc·mypy·free-threaded Python은 호스트에 없어 문서·모형·대체 측정(Unsafe 오프셋·직접 시간 측정)으로 · CodeCache full 경고 재현 실패(소스 근거만) · 25 실험 2(61파일 full LTO)는 사실 점검 재실행 생략(수 분, 생성 파일 미보존 — 노트 명시) · bugs.openjdk.org(JDK-8271623)는 403/429 → JDK 18 릴리스 노트로 대체 · JIT·GC 측정은 부하가 있는 호스트(load avg 최대 ~10)라 범위로만.

## 완료 요약

- 산출: `cs/language/01~27` 27편(보강 10: 01~04·06·07·09·15·20·21 — 원고 compiler-pipeline·variables-and-memory·process-thread·languages/* 읽기만, 원고 오류 ~16건은 leaf "참고:" 줄) · 종합 26 증상 색인(시나리오 117개)·27 실사건(Cloudbleed·Heartbleed·left-pad) + 영역 표 재생성 + 영역 밖 '미작성' 링크 교정 54곳(37파일).
- 검증: V1 27 PASS · V1b/V2 Opus 사실 점검 6묶음(중대 4 — PEP 683 범위·메가모픽 인라인 단정·GC 실험 범위·C11 DRF-SC 조건, 중간 ~51, 실험 재실행 전 묶음) · V3 codex(high) 27/27, 지적 159 → 채택 116·부분 41·기각 2 · V4 정합(26 ↔ leaf 재대조, 06↔09, 노트 간 모순 0 + 영역 밖 오류 4 보고, 영역 안 링크 52) · V5 웹 독립 79건 전부 일치 + 사실 점검 웹 표본 ~80 · 링크 1,968 깨짐 0.
- 관측: 언어 영역 지적의 대부분은 **한 런타임·버전의 동작을 언어 일반으로**(CPython 패치 차이, HotSpot 기본값, Kotlin 1.6/1.7, JS vs C# await)와 **명세 vs 구현 vs 관례 혼동**(JLS 5.1.7 vs valueOf API, UB 결과를 확정처럼). 판정 워커가 출처를 기억으로 판정한 1회 → 이후 지시에 "직접 열 것" 추가, 웹 표본이 그 6곳을 원문으로 확인.
- 핵심 diff(실파일에서 복사): `cs/language/README.md` before `> 현황: 미작성 17 · 원고 있음 10 · 초안(Claude) 0 · 검수 완료 0` → after `> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 27 · 검수 완료 0`
- CS 이슈 아카이브: 0건(문서 작업).
