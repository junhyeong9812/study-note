# log — testing-writing

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-10-03 19:05 | 사전: 모든 로컬·원격 브랜치 main 포함 확인(미병합 0) · dm push 기록 1줄 docs/dm-push-record → main ff 07f855e3 → push(사용자 승인) | origin/main = main |
| 2026-10-03 19:10 | 인터뷰(검증 앞 영역과 같게 · 합의 auto · dm 기록 push 지금) → 명세 작성 직후 승인 기록 · 브랜치 docs/testing-writing(main 07f855e3) | SPEC=1·MODE=auto |
| 2026-10-03 19:20 | 브리핑(dm판 이식 + 테스트 실험 예시·Testcontainers 규칙·파일 소유권 -u) · A1 스모크: maven 컨테이너에서 JUnit 5.13.4·surefire 3.5.3 받아 1 테스트 통과(scratchpad/ts/smoke) — root 소유 target 발생 → chown 복구·-u 규칙 추가 | A1 확인 |
| 2026-10-03 19:30 | 집필 발사(Opus 5병렬, 19편): 01·02·04·12 / 03·05·06·11 / 07·14·15·16 / 08·13·18·19(Testcontainers 스모크 A2 선행) / 09·10·17 — 종합 20·21 후속 · 프롬프트 scratchpad/ts/writer-prompt.md | 회수 대기 |
| 2026-10-03 | 집필 회수 1/5: 08·13·18·19(4 PASS, [?] 0) — **A2 확인**: Testcontainers 2.0.5 + postgres:17 + ryuk:0.14.0, pull 없음, 라벨 컨테이너 전후 4→4(기존 남의 mysql Exited 4 — 건드리지 않음) · 실험: 08 H2 vs PG17(ON CONFLICT 42000·오류 뒤 계속 25P02·NOWAIT HYT00 vs 55P03·같은 테스트 H2 통과/PG 실패), 13 Pact JVM 4.7.5 rename/타입 변경 실패 메시지, 18 jsdom+Testing Library 마크업 개편 구조 선택자 4/4 실패 vs 역할 0/4, 19 k6 체크 exit 99·카나리 z-검정 오탐 4.7~6.5% vs 순진 40~52%·섀도 부수 효과 · 사고: Pact 첫 실행이 네트워크 열린 채 익명 사용 통계 전송 가능(개인정보 없음) → 브리핑에 pact_do_not_track·--network none 추가 | 4 PASS |
| 2026-10-03 | 사실 점검 브리핑(factcheck-briefing.md — dm판 이식, 테스트 도구 기본값·저자별 정의·Testcontainers/Pact 규칙) · 점검 1/5 발사: 08·13·18·19 | 회수 대기 |
| 2026-10-03 | 집필 회수 2/5: 09·10·17(3 PASS, [?] 3 — 17 WELC 본문 미열람 절) — 실험: 09 공유 정적 상태 무작위 순서 12/20 실패→@BeforeEach 0/20·고정 sleep 부하 0/2/4개에 실패 0~1/8~13/30~32 vs Future.get 0·재시도 없이 9/12 실패 vs rerun 3회 6/6 SUCCESS(Flakes 1 은폐), 10 자정·월말·DST 가짜 Clock·TTL 2101ms vs ~2ms·check-then-act 중복 55~213 vs computeIfAbsent 0, 17 골든 마스터 refactorB 105줄 중 15줄 차이(손 테스트 3개는 통과)·스크러버 · Luo FSE 2014 원문 57% vs 표 54% 병기 · 17→16 링크는 정합에서 · 루트 아닌 scratchpad/ts 직하 임시 파일 1(이동) | 3 PASS |
| 2026-10-03 | 집필 회수 3/5: 07·14·15·16(4 PASS, [?] 0, 해석 표시 1) — 실험: 07 경계 결함 4개를 분할 대표 0/4·2값 경계 4/4·무작위 ~0.04%, pairwise 216→13행·3-way 47.5%, 14 fast-check 4.10.2 축소 반례·생성기 선택(rle chars 0/200 vs runs 200/200), 15·16 JUnit 5.13.4·JaCoCo 0.8.14·PIT 1.20.4: NoAssert 라인·분기 100% 변이 7% / Weak 79%(경계 변이 생존) / Strong 100%·등가 변이체 · ISTQB CTFL 4.0.1(pairwise는 CTAL-TA 3.1.2 → 커리큘럼 [?] 해소) · **jqwik 1.10 Anti-AI Usage Clause** 발견 → jqwik 실행 결과 폐기·fast-check로 대체, 브리핑에 사용 조항 존중 규칙 추가 | 4 PASS |
| 2026-10-03 | 집필 회수 4/5: 03·05·06·11(4 PASS, 각 10문항, [?] 2 — GOOS 그림 번호·Walking Skeleton 어원) — 실험: 03 Stub 초록 vs 계약 지킨 Fake·H2 빨강(11 중 실패 2·오류 2)·Mockito 5.24.0 기본 응답·UnnecessaryStubbingException, 05 TDD 커밋 12개·계산 결과 붙여 넣기 8104 고정 → 고친 구현과 충돌, 06 조립 누락은 인수 테스트만 잡음·드라이버 고칠 자리 5 vs 2·거짓 통과, 11 공유 픽스처 시드 12/20 실패 vs 0·생성자 인자 추가 컴파일 오류 직접 6/마더 3/빌더 1 · Canon TDD 2023-12-11·Dan North BDD 2006(커리큘럼 [?] 해소) | 4 PASS |
| 2026-10-03 | 집필 회수 5/5: 01·02·04·12(4 PASS, [?] 5 — Khorikov 본문·GOOS 장 번호) — 실험: 01 small 1,001개 2.2~2.9s vs PG17 medium 1개 1.2~1.5s(+기동 5.7s)·IS NOT NULL 누락은 Fake small 통과/PG medium 실패·경계 결함은 small만, 02·04 묶음 D·L·C에 리팩터링 2·버그 4: 거짓 양성 D3/L2/C0·검출 D3/L3/C4·B1 빨강 L1/C4, 12 단언 스타일 8종(룰렛 1 vs assertAll 3·조건부 단언 결함인데 초록) · **집필 19편 완료**, 종합 20·21 발사 · 사실 점검 5/5 발사 | 19 PASS |
| 2026-10-03 | 사실 점검 회수 1/5: 08·13·18·19 — **중대 2**(08 Fowler 좁은 통합 테스트 정의 = 상대 서비스는 더블(노트 실험은 실제 엔진이라고 구분), 08 Boot @AutoConfigureTestDatabase.replace 기본 v3.3 ANY → v3.4+ NON_TEST(@ServiceConnection 교체 안 함) 판 조건), 중간 3(H2 호환 원문 'small subset', 13 pending pacts는 enablePending·제공자 브랜치별, 18 Wacker 원문 '기능 완료 조건'·7일 뒤 89.54%), 경미 ~7(Ryuk 재연결 10s·기동 시간 범위 확대·해석 표시) · 재실행 7종 결정적 출력 전부 일치(Pact JSON diff 0) · Testcontainers 라벨 4→4 | 4 PASS |
| 2026-10-03 | 2차 리뷰: codex 한도(10-04 08:53 리셋) → 명세 V3대로 Opus 적대 리뷰 — 1/5 발사: 08·13·18·19(프롬프트 scratchpad/ts/review/opus-reviewer-prompt.md, 지적만 기록) | 회수 대기 |
| 2026-10-03 | 사실 점검 회수 2/5: 09·10·17 — 중대 0, 중간 4(09 Luo 5.2절 '제품 코드도 함께' 38/161, waitFor 완전 제거는 23/42(55%)·나머지는 확률 감소, 실험 B 범위 확대(무부하 0~4·부하2 8~15), 10 실험 E 범위 55~96/169~243·computeIfAbsent 0 ×7), 경미 4(Clock.fixed javadoc 원문 문구, 실험 C·D 범위, 17 'Feathers가 만든 용어' 2차 출처 표기, 16 링크 실재로) · 재실행 7종 결정적 출력 일치 · [?] 3→3 | 3 PASS |
| 2026-10-03 | Opus 적대 리뷰 회수 08·13·18·19: 사실 오류 0 · 낡은 미작성 링크 2(08→11, 19→20) → 정합 패스로 · 13 pending 해제 조건 단순화 메모 → 메인이 Pact 문서 원문 확인('first successful verification … by a particular branch' / 'pending for all branches … until the first successful verification') — 노트 문구가 원문 범위 안이라 유지(판정: 수정 없음) | 판정 0 |
| 2026-10-03 | 사실 점검 회수 3/5: 01·02·04·12 — 중대 0, 중간 7(01 불안정 1%·0.15%는 Case Study 절·재실행 허용 뉘앙스(SWE@G 'only delaying'), 02 Brittle 절 원문 요지·Khorikov 인용 출처 오귀속(블로그 아님 → 2차 요약)·SWE@G 'state-changing' vs Khorikov '비관리 프로세스 밖' 기준 분리, 12 룰렛 실무 예와 실험 출력 불일치·Custom Assertion은 failWithMessage에서 멈춰 합계 검사 미실행), 경미 ~9(SWE@G 절 이름·GOOS 8장 확인 [?] 해소·Mockito 기본 응답 경로) · 재실행 4종 결정적 출력 일치 · [?] 순증감 0 | 4 PASS |
| 2026-10-03 | 사실 점검 회수 4/5: 07·14·15·16 — 중대 0, 중간 3(14 sort 반례 '큰 수 둘' → 부호 반대·차이 ~2^31 쌍(시드 1~30 재실행), 16 PIT 4/5 vs JaCoCo 4/4 해석 → 확인(PIT LineMapper는 private 생성자 줄 포함·JaCoCo 0.8.0 필터, 생성자 지운 사본 대조), 16 MC/DC 'n+1행으로 덮는다' → '일반적으로 최소 n+1(하한)' NASA TM 2.3.5), 경미 ~7(07 AETG 비유 근거 없음, 15 FLOGCALL, 16 줄 색 = 명령+분기 합(LineImpl), GTB 'paramount'·SWE@G 작은 테스트 커버리지) · 재실행 8종 일치 · jqwik 미실행 | 4 PASS |
| 2026-10-03 | Opus 적대 리뷰 회수 09·10·17: 지적 3(편당 1) — 09 F.4 34%는 'sleep or waitFor'(4.2.1절), 10 isBefore→isAfter 예는 sleep 판도 잡음(경계 2000ms에서만 갈리는 결함으로), 17 정확히 .5 입력은 105조합에 있음 — 양수 반값은 Math.round=HALF_UP, 음수 반값에서 갈리고 refactorB 음수→0에 가려짐 · 판정 브리핑(adjudicate-briefing.md, dm판 이식) + 판정 발사 | 판정 대기 |
| 2026-10-03 | 판정 회수 09·10·17(Opus 지적 3): 채택 3 — 09 F.4 74건 중 25건 sleep·waitFor(4.2.1절), 10 변형 실험(TtlVariants): !isAfter는 sleep·가짜 시계 모두 FAIL, now.isAfter(exp)(경계 1칸)는 sleep PASS·가짜 시계 FAIL → 해석 교체 + 출력, 17 RoundProbe: 정확히 .5 총액 17개 중 음수 3개만 Math.round≠HALF_UP, refactorB .max(ZERO)가 덮음 → 관찰·장애 5·정답 5·질문 5 전제 문구 | 3 PASS |
| 2026-10-03 | 집필 회수 종합 20·21(2 PASS, [?] 0) — 20: 01~19 장애 시나리오 90개 전부 링크(render20.py 누락·불일치 0)·사실 점검 반영분 재추출 동기화·인용 메시지 36개 현행 확인, 21: goto fail(Apple HT205762 날짜·NVD·Security-55471 vs .14 태그 diff 한 줄·Langley) + CrowdStrike PIR/RCA(21 정의 vs 20 입력·와일드카드 시험 12) · 실험: 기존 이미지에 C 컴파일러 없음 → Java(unreachable statement)·JUnit 음성 테스트 3 실패·JS 커버리지·CF291 모형 · **21편 집필 완료** · 사실 점검 20·21 발사 | 2 PASS |
| 2026-10-03 | Opus 적대 리뷰 회수 07·14·15·16: 지적 1(07 Kuhn 97% 일반화)·14·15·16 지적 0 → 메인 판정 채택: NIST 프리프린트 Table 1 직접 확인(1~2-way 누적: 의료기기 97·브라우저 76.1·서버 70.3·NASA 93.3) → 2-summary에 데이터셋별 값·3-way 이상 3~30% 하위 항목, 3-answer 8 단서 | 5 PASS |
| 2026-10-03 | 사실 점검 회수 5/5: 03·05·06·11 — 중대 0, 중간 2(03 verify 대상은 Meszaros 분류로 Test Spy에 가깝다(§1 정의와 모순 해소), 05 Canon TDD 인용 'one at a time' 잘림), 경미 ~8(Mockito boolean false·STRICT_STUBS는 확장/Runner/Session에서만 — 새 실험 D, TDD by Example 25장 쪽수(Pearson 견본), GOOS 2장 절 제목, 06 HttpApiTest 실패 포함) · 11 수정 0 · 재실행 12종 일치 · 노트 간: 02 '저장소는 Fake' vs Khorikov 관리형 의존 실제 사용(03) → 정합으로 · **사실 점검 19+ 완료** | 4 PASS |
| 2026-10-03 | Opus 적대 리뷰 회수 01·02·04·12: 지적 3(01 1·04 2)·02·12 지적 0 → 메인 판정 채택 3: 01 SWE@G 11장 원문 'we tend to aim … very rough guideline' 확인 → '목표가 아니라 결과'를 노트 해석으로 표시, 04 jmock.org PDF 표제 'Freeman, Pryce, Mackinnon, Walnes'·참고문헌 [10] Endo-Testing(XP2000) 확인 → 저자 순서 2곳·'원천 논문' → '대표 논문' + 원 논문 명시 | 2 PASS |
| 2026-10-03 | Opus 적대 리뷰 회수 03·05·06·11: 지적 4(03 spy()는 감싸기 아닌 복사본(javadoc 13절), 05 8105 vs 8104는 넷째 빨강·'테스트는 지우지 않는다' 단정(TDDbE 32장 deleting tests), 11 PER_CLASS 초기화는 조건부(UG 2.12))·06 지적 0 → 판정 발사 · **01~19 2차 리뷰 완료** | 판정 대기 |
| 2026-10-03 | 판정 회수 03·05·11(Opus 지적 4): 채택 3·부분 1·기각 0 — 03 spy() 복사본(Mockito 5.24.0 javadoc 13절 + 실험: Counter real=1·spied=2, ArrayList 얕은 복사로 내부 배열 공유 주의), 05 넷째 빨강(git log red 4개)·'테스트는 남는다' → 기본적으로·TDDbE 32장 색인 deleting tests 198 [?](부분), 11 PER_CLASS 초기화 조건부(UG 2.12) | 3 PASS |
| 2026-10-03 | 사실 점검 회수 20·21: 중대 0, 중간 2(20 'expected 90000L but was 0L'은 04 R2 거짓 경보이기도(04-1과 모순 해소), 21 Langley 'attacker gets to choose the ciphersuite'는 DHE 문맥 → TLS 1.2 문맥 원문으로), 경미 8(20 경계 행·09-3 원인·14-3 비율·시드 키는 MethodOrderer.Random javadoc, 21 -Wall은 축약 코드·HT205762 리다이렉트·3-05는 PIR 날짜) · 재실행 5종 일치 · 20은 md 직접 수정(render20.py 재실행 금지) · leaf 쪽 보고: 14-3 '열에 한 번' vs 47/200, 11-1 원인 reserveFive 누락, 12-5 예시 → 정합으로 · 웹 교차 표본 워커 발사(01~19, 26+) · 20·21 2차 리뷰 발사 | 2 PASS |
| 2026-10-03 | Opus 적대 리뷰 회수 20·21: 지적 3(20 혼동 행렬 '교환' 근거가 표본 수만 바꾼 수치(교환은 같은 n에서 규칙 비교 40.7/71.4 vs 5.5/23.7)·Testcontainers 첫 진단에 메서드 수, 21 '운영 배포 네 번'은 원문에 없음(인스턴스 4개)) · **21편 2차 리뷰 완료** → 판정 20·21 + 정합 패스 한 워커로 발사(scratchpad/ts/consistency-prompt.md — 보고된 노트 간 불일치 5·미작성 링크·20 참조 재대조·링크 해소, render20.py 재실행 금지) | 회수 대기 |
| 2026-10-03 | 웹 교차 표본 회수: 40건(01~19 편당 2, 11·19는 3, 사실 점검 표본과 겹침 회피) — 일치 40·불일치 0·확인 불가 0 · 참고 1(11:247 Surefire runOrder '클래스' 순서 — 문서 문구는 'tests', Surefire는 테스트 클래스 단위로 순서를 정하므로(balanced 설명도 classes) 유지) · 산출 web-cross-sample.md | 40/40 |
| 2026-10-03 | 판정+정합 회수: 판정 20·21 채택 3(20 맞교환은 같은 n=200 규칙 비교 40.7/71.4 vs 5.5/23.7·n 늘리면 둘 다 개선, Testcontainers 진단 '클래스 수인가 메서드 수인가'(08 시나리오 3 동기화), 21 '운영 배포 네 번' → '인스턴스 네 개'(PIR 3-05 1 + 4-08~24 3)) · 정합: 모순 4 정정(02 저장소 Fake vs Khorikov 관리형 의존 실제 인스턴스, 14 '열 번에 한 번' → 약 23.5%, 11-1 reserveFive 포함, 12-5 예시 표시) + 20 Flakes 출력 형식 · 미작성→링크 3(남은 9는 폴더 없는 영역) · 20 [NN-k] 184 깨짐 0 · 링크 522 깨짐 0 · 영역 밖 낡은 'testing 미작성' 20곳 → NEXT | 21 PASS |
| 2026-10-03 | 마감: 노트 커밋 a27e05fe(85파일 = 21×4 + README) · check 21 PASS · 컨테이너 sn-ts 0·Testcontainers 라벨 4(기존 남의 것) · 루트 파일 0 · 완료 요약·생략한 검증·NEXT(N0-l·N0-c)·측정로그 · 아카이브 0건 | 커밋 |
| 2026-10-04 | 사용자 승인 → main fast-forward + push(07f855e3..8dfaf3c4) | 완료 |

## 리뷰 ledger

| 대상 | 리뷰어 | 중대 | 중간 | 경미 | [?] 전→후 | 비고 |
|---|---|---|---|---|---|---|
| 08·13·18·19 | Opus 독립 | 2 | 3 | ~7 | 0→0 | 웹 표본 12 · 실험 재실행 7 |
| 09·10·17 | Opus 독립 | 0 | 4 | 4 | 3→3 | 웹 표본 9 · 실험 재실행 7 |
| 08·13·18·19 판정 | 메인(Opus 2차 지적 0 + 메모 1) | 채택 0 | 부분 0 | 기각 1 | | 링크 2는 정합으로 |
| 01·02·04·12 | Opus 독립 | 0 | 7 | ~9 | 5→5 | 웹 표본 12 · 실험 재실행 4 |
| 07·14·15·16 | Opus 독립 | 0 | 3 | ~7 | 0→0 | 웹 표본 12 · 실험 재실행 8 |
| 09·10·17 판정 | Opus(Opus 2차 지적 3) | 채택 3 | 부분 0 | 기각 0 | | 재실험 2 |
| 07·14·15·16 판정 | 메인(Opus 2차 지적 1) | 채택 1 | 부분 0 | 기각 0 | | 14·15·16 지적 0 |
| 03·05·06·11 | Opus 독립 | 0 | 2 | ~8 | 2→2 | 웹 표본 12 · 실험 재실행 12 |
| 01·02·04·12 판정 | 메인(Opus 2차 지적 3) | 채택 3 | 부분 0 | 기각 0 | | 02·12 지적 0 |
| 03·05·11 판정 | Opus(Opus 2차 지적 4) | 채택 3 | 부분 1 | 기각 0 | | 06 지적 0 · spy 실험 |
| 20·21 | Opus 독립 | 0 | 2 | 8 | 0→0 | 웹 표본 6 · 실험 재실행 5 |
| 20·21 판정 | Opus(Opus 2차 지적 3) | 채택 3 | 부분 0 | 기각 0 | | 정합 패스와 함께 |

## 생략한 검증

- 빚 없음(긴급 아님). 명세 V3 대체: codex 한도(10-04 08:53 리셋)로 21편 전부 Opus 적대 리뷰 — codex 대비 누락률 미측정(NEXT).
- 원문 미열람: Khorikov 책 본문(02·04 — livebook 서두·목차·블로그·2차 요약 범위만, `[?]` 3), GOOS 본문(06 `[?]` 2), TDDbE 본문(05 32장 198쪽 `[?]`), WELC 본문(17 `[?]` 3). jqwik은 Anti-AI Usage Clause로 실행하지 않음(문서 인용만).

## 완료 요약

- 결과: `cs/testing/` 21편(전부 신규, 종합 20·21) + 영역 README 재생성(초안(Claude) 21) — 커밋 a27e05fe(브랜치 docs/testing-writing, main 07f855e3에서).
- 검증: check 21 PASS · 1차 Opus 점검 6묶음(중대 2·중간 ~21, 실험 재실행 ~43, 결정적 출력 전부 일치·범위 확대 다수) · 2차 Opus 적대 리뷰 21편 → 지적 14 + 메모 1 → 판정 채택 13·부분 1·기각 1(메모) · 정합(모순 4·미작성→링크 3·20 참조 184·링크 522 깨짐 0) · 웹 40/40.
- 환경 확인: A1 maven 컨테이너 JUnit 스모크, A2 Testcontainers 2.0.5 + 기존 postgres:17·ryuk 0.14.0(pull 0, 라벨 컨테이너 4→4 기존 남의 것).
- 운영 사건: root 소유 파일(스모크) → chown·`-u` 규칙 · Pact 첫 실행 익명 사용 통계 전송 가능 → `pact_do_not_track`·`--network none` 규칙 · jqwik Anti-AI 조항 발견 → 실행 결과 폐기·fast-check 대체·규칙화 · 기존 이미지에 C 컴파일러 없음(21은 Java/JS 모형).
- 대표 diff(2차 리뷰 채택, `cs/testing/07-test-design-techniques/2-summary.md:200`):
  - before: `- 근거로 드는 관찰(CTAL-TA 3.1.2가 인용한 Kuhn 외 2004의 제한된 연구): 실패의 약 97%가 조건 하나 또는 두 개의 상호작용으로 일어났다. 그래서 pairwise가 효과적이라고 본다.`
  - after: `- 근거로 드는 관찰(CTAL-TA 3.1.2가 인용한 Kuhn 외 2004): 실패의 약 97%가 … 그래서 pairwise가 효과적이라고 본다.` + 하위 항목 `  - 단, 97%는 원 논문 Table 1의 **의료기기 리콜 109건** 값이다. … Mozilla 브라우저 76.1%, Apache 서버 70.3%, NASA 분산 DB 93.3% … 약 3~30%다(100−97 … 100−70.3).`
- CS 이슈 아카이브: 0건 — 발견 사실은 노트 본문 반영, 도구 사용 조항·텔레메트리·파일 소유권은 운영 규칙(브리핑)으로 반영.
