# software-design/09-comments-and-conventions — 주석이 필요한 자리와 관례로 논쟁 없애기 — 정리 (힌트)

## 해결하는 문제

코드는 **무엇을 어떻게** 하는지는 말하지만, **왜** 그렇게 했는지와 **어떻게 써야 하는지**는 말하지 못한다.\
그 빈칸을 주석이 채운다. 반대로 코드와 같은 말을 되풀이하는 주석은 코드가 바뀔 때 거짓말이 된다.

```text
 코드가 담는 것                        코드가 못 담는 것 (주석의 자리)
 ─────────────────                    ──────────────────────────────
 MAX_ATTEMPTS = 5                      왜 5인가? (하류 SLA, 장애 번호 #1234)
 tryAcquire(key, permits)              key끼리 허용량을 공유하나? false면 상태가 바뀌나?
 binarySearch 대신 선형 탐색             "측정해 보니 이 크기에선 선형이 빨랐다"
```

- *인터페이스 주석*: 함수·클래스를 **쓰는 사람**에게 주는 계약(무엇을 하나, 인자 조건, 반환 의미, 부작용).
- *구현 주석*: 본문 안에서 **고치는 사람**에게 주는 설명(왜 이 방법인가, 무엇이 놀라운가).

쉬운 예: 냉장고 문에 붙은 메모 "우유 유통기한 10/5"는 우유를 보면 안다. "이 칸은 아기 이유식 전용, 날것 넣지 마세요"는 보고도 모른다. 둘째 메모가 필요한 메모다.\
똑같은 구조다.\
실무 예: 재시도 횟수를 3에서 5로 올리면서 주석 "최대 3회, 실패까지 약 0.3초"를 그대로 뒀다. 장애 때 온콜이 주석을 믿고 "0.3초 안에 실패할 것"이라 판단했지만 실제로는 1.5초를 기다렸다(아래 실험 B).

이 주제는 [06-clean-code](../06-clean-code/2-summary.md)에서 나눴다. 이름([07-naming](../07-naming/2-summary.md))과 시그니처([08-function-design](../08-function-design/2-summary.md))가 담지 못한 정보가 주석으로 온다.

## 동작·원리

### 1. 주석이 필요한 자리 vs 불필요한 주석

```text
 필요한 자리                                     불필요한 주석
 ┌──────────────────────────────────────┐      ┌──────────────────────────────────┐
 │ 왜: 결정·제약·외부 사정·버그 번호          │      │ what 반복: // i를 1 증가          │
 │ 인터페이스 계약: 인자 조건·반환·부작용       │      │ 주석 처리된 코드 (git이 기억한다)    │
 │ 놀라운 동작: "O(태그 × 깊이)라 중첩 주의"   │      │ 낡은 주석: 코드와 반대 말을 함        │
 │ 큰 그림: 이 파일이 무엇과 무엇을 잇나       │      │ 나쁜 이름을 변명하는 주석            │
 └──────────────────────────────────────┘      └──────────────────────────────────┘
```

- Ousterhout(APOSD 2판 13장 제목): "Comments Should Describe Things that Aren't Obvious from the Code". 여기서 "obvious"는 작성자가 아니라 **처음 읽는 사람** 기준이다. 리뷰어가 분명하지 않다고 하면 분명하지 않은 것이다(13.8).
- Google eng-practices "What to look for in a code review": 주석은 대개 코드가 **왜** 있는지를 설명할 때 쓸모 있고, 무엇을 하는지를 설명해서는 안 된다. 정규식·복잡한 알고리즘은 예외다. 클래스·함수의 **문서**(목적, 사용법, 동작)는 이 구현 주석과 다르다고 구분한다.
- Boswell–Foucher(『The Art of Readable Code』 5장 "Knowing What to Comment", 발췌 PDF 확인):
  - "Don't comment on facts that can be derived quickly from the code itself."
  - 나쁜 이름을 주석으로 변명하지 말고 이름을 고친다(`CleanReply` → `EnforceLimitsFromRequest`).
  - 남길 것: "director commentary"(측정 결과·의도적 타협), 코드의 결함(TODO·FIXME·HACK·XXX), 예상되는 함정(외부 호출이라 느림, O(n·깊이)), 큰 그림.
  - "what·why·how 중 무엇을 주석하나"에는 단순한 규칙 대신 "읽는 사람을 돕는 것이면 무엇이든"이라고 답한다.
- *낡은 주석(stale comment)*: 코드가 바뀌었는데 따라 바뀌지 않은 주석. 컴파일러가 검사하지 않으므로 조용히 거짓이 된다.

### 2. 두 입장 — 주석은 실패인가

- Martin(『Clean Code』, APOSD 12.6에 인용): 주석은 기껏해야 필요악이고, 코드로 의도를 표현하지 못한 실패를 보상하는 것이다.
- Ousterhout(APOSD 12.6 "A different opinion: comments are failures"): 주석이 담는 정보는 코드와 종류가 달라 코드로 대신할 수 없다. 메서드를 쪼개 이름으로 주석을 대신하면 `isLeastRelevantMultipleOfNextLargerPrimeFactor` 같은 긴 이름이 생긴다.
- 대담 요약(2024-09~2025-02): Ousterhout는 같은 코드에 5~10배 많은 주석을 쓸 것이라 했다. 둘은 공개 API에는 주석이 필요하다는 데 동의했다. 팀 내부 인터페이스에 주석이 필요한지에서 갈렸다(Martin은 필요가 적다고 봤다). 주석 전반의 가치 평가도 다르다. Ousterhout는 "빠진 주석"을, Martin은 "나쁜 주석"을 더 큰 비용으로 본다.
- 공통 지점: 구현 코드 안의 주석은 코드가 분명하지 않을 때만 필요하다.
- Fowler·Beck(『Refactoring』 1판 3장 "Comments", Pearson 샘플 PDF): 주석은 나쁜 냄새가 아니라 좋은 냄새다. 다만 나쁜 코드를 덮는 탈취제(deodorant)로 쓰이는 일이 많다. 먼저 리팩터링으로 주석이 필요 없게 해 보고, "A comment is a good place to say why you did something."

### 3. 주석과 코드의 중복 = DRY 위반

```text
 // 최대 3회 시도. 백오프 100ms부터 2배. 실패까지 약 0.3초.   ← 지식 사본 1
 static final int MAX_ATTEMPTS = 3;                             ← 지식 사본 2
                │
     MAX_ATTEMPTS = 5 로 변경 ──> 사본 2만 바뀐다 ──> 주석은 거짓말
```

- Hunt–Thomas(『The Pragmatic Programmer』 20주년판 Topic 9 「Duplication in Documentation」): 주석이 함수 본문의 규칙을 그대로 옮겨 적으면, 의도가 두 번 적힌 것이다. 규칙이 바뀌면 둘 다 고쳐야 한다.
- 대처는 둘 중 하나다. 주석에서 **값을 빼고 이유만** 남기거나(`// 하류 SLA 2초 안에 포기하도록 맞춘 값 (#1234)`), 값을 코드로 계산해 보여 준다(`maxWait()` 메서드와 테스트).

### 4. 관례 — 사람이 아니라 도구가 정한다

```text
 관례 없음                                    관례를 도구에 위임
 리뷰 코멘트 절반이 "중괄호 위치", "탭 vs 공백"     포매터가 저장·커밋 때 정렬
 diff 절반이 포매팅 → 진짜 변경이 묻힘             diff = 동작 변경만
 blame이 포매팅 커밋을 가리킴                      CI가 --dry-run으로 어긋난 파일을 막음
```

- APOSD 17장 "Consistency": 비슷한 것은 비슷하게, 다른 것은 다르게. 일관성은 한 곳에서 배운 것을 다른 곳에서 바로 쓰게 하는 "cognitive leverage"이고, 실수를 줄인다. 그 투자에는 관례를 정하고 자동 검사기를 만드는 일이 포함된다(17.4).
- Google eng-practices: 스타일 가이드에 없는 개인 취향으로 변경을 막지 않는다("Nit:"를 붙인다). 큰 스타일 변경은 기능 변경과 섞지 말고 별도 CL로 보낸다. 섞으면 무엇이 바뀌었는지 보기 어렵고 병합·롤백이 복잡해진다.
- *포매터(formatter)*: 코드 모양을 정해진 규칙으로 다시 쓰는 도구. google-java-format은 Google Java Style에 맞춰 재포매팅하고, 알고리즘 설정을 일부러 두지 않는다("There is no configurability … a deliberate design decision", README).
- *린터(linter)*: 모양보다 의미 쪽 규칙(미사용 변수, 위험한 패턴)을 검사하는 도구. PMD·Checkstyle·ESLint 등.

### 실험 A: 동작 변경 1줄에 포매팅이 섞이면

`RetryClient.java`(30줄)는 손으로 맞춘 스타일(탭, 다음 줄 중괄호)이다. 요구는 `MAX_ATTEMPTS = 3` → `5` 한 줄이다.\
noisy: 개발자의 IDE가 저장할 때 파일 전체를 다시 포매팅했다(google-java-format으로 재현).\
consistent: 저장소가 처음부터 같은 포매터 결과로 고정돼 있다.

(실험, google-java-format 1.37.0, JDK 21.0.12 temurin `--cpus=2`, git 2.43.0, 2026-10-02, `scratchpad/sd/06/e09/run-format.sh`)

```text
== [noisy] 동작 변경 1줄 + IDE 전체 재포매팅: git diff --stat
   RetryClient.java | 56 +++++++++++++++++++++++++++++++-------------------------
   1 file changed, 31 insertions(+), 25 deletions(-)
== [noisy] git diff -w --stat (공백 무시)
   RetryClient.java | 38 ++++++++++++++++++++++----------------
   1 file changed, 22 insertions(+), 16 deletions(-)
== [consistent] 동작 변경 1줄 + 같은 포매터: git diff --stat
   RetryClient.java | 2 +-
   1 file changed, 1 insertion(+), 1 deletion(-)
  -  static final int MAX_ATTEMPTS = 3;
  +  static final int MAX_ATTEMPTS = 5;
== [consistent] 포매터 검사(CI용): --dry-run 은 포맷이 어긋난 파일 이름을 출력
  formatted repo: (출력 없음 = 통과)
  어긋남: /tmp/R.java
```

- 관찰 1 — 같은 1줄 변경이 noisy에서는 56줄 diff가 됐다. 리뷰어는 56줄 중 동작이 바뀐 1줄을 찾아야 한다.
- 관찰 2 — 공백을 무시해도(`git diff -w`) 38줄이 남는다. 중괄호 위치·줄 나눔은 공백 변경이 아니기 때문이다.
- 관찰 3 — 포매터가 고정된 저장소에서는 diff가 정확히 그 1줄이다.
- 관찰 4 — `--dry-run`은 포맷이 어긋난 파일 이름만 출력한다. CI에서 "출력이 있으면 실패"로 쓰면 관례가 리뷰 대상에서 빠진다.

### 실험 B: 낡은 주석 — 장애 때 잘못된 판단

실험 A의 consistent 결과물 그대로다. 코드는 5회로 바뀌었지만 주석은 바뀌지 않았다.

(실험, 같은 환경, `run-format.sh`의 09-B 부분 — 경과 시간은 실행마다 다르다. 기록한 5회 실행 1,513~1,537ms)

```text
== [09-B] 주석: // 최대 3회 시도한다. 백오프 100ms부터 2배. 실패까지 약 0.3초.
== [09-B] 실행
  attempt 1 failed, sleep 100ms
  attempt 2 failed, sleep 200ms
  attempt 3 failed, sleep 400ms
  attempt 4 failed, sleep 800ms
  gave up after 1537ms: downstream 503
```

- 주석 기준 기대: 3회, 대기 100+200 = 300ms 뒤 포기.
- 실제: 5회, 대기 100+200+400+800 = 1,500ms 뒤 포기. 주석보다 약 5배 오래 기다린다.
- 해석 — 주석 속 **숫자**는 코드의 사본이다. 상위 타임아웃을 1초로 잡은 사람이 이 주석을 믿었다면, 재시도가 끝나기 전에 상위가 먼저 끊긴다(타임아웃 예산은 [reliability/08-time-budget-allocation](../../reliability/08-time-budget-allocation/2-summary.md)).
- 실험 A의 consistent diff가 1줄이었다는 점도 같이 본다. 리뷰어는 바뀐 1줄 바로 위의 주석이 거짓이 된 것을 볼 수 있었다. diff가 56줄이었다면 놓치기 쉬웠다.

### 실험 C: 도구는 주석의 "있음"만 본다

같은 인터페이스에 주석 없음 / 이름을 되풀이한 주석 / 계약을 적은 주석 세 가지를 두고 `javadoc -Xdoclint:all`을 돌렸다.

```java
// echo: 이름을 되풀이
/** Try acquire. @param key the key @param permits the permits @return true or false */
// contract: 계약
/** 허용량이 남아 있으면 즉시 차감하고 true, 없으면 기다리지 않고 false.
 *  @param key 제한 단위. 같은 key끼리 허용량을 공유한다.
 *  @param permits 1 이상. 0 이하면 IllegalArgumentException.
 *  @return 차감했으면 true. false여도 상태는 바뀌지 않는다. */
```

(실험, JDK 21.0.12 javadoc, 같은 환경, `scratchpad/sd/06/e09/run-doclint.sh`)

```text
== [none] javadoc -Xdoclint:all
RateLimiter.java:3: warning: no comment
RateLimiter.java:4: warning: no comment
2 warnings
  (경고·오류 줄 수: 2)
== [echo] javadoc -Xdoclint:all
  (경고·오류 줄 수: 0)
== [contract] javadoc -Xdoclint:all
  (경고·오류 줄 수: 0)
```

- doclint는 주석이 없으면 경고하지만, "Try acquire. / the key"처럼 아무 정보 없는 주석과 계약을 적은 주석을 구별하지 못한다(둘 다 0건).
- "공개 메서드마다 Javadoc" 같은 존재 규칙만 두면 echo형 주석이 늘어난다. Boswell–Foucher가 말한 "주석을 위한 주석"이다. 내용은 리뷰가 본다.

## 쓰이는 자료구조·알고리즘

- **최장 공통 부분 수열(LCS) 기반 diff**: git diff는 두 파일의 줄 열에서 공통 부분 수열을 찾고 나머지를 추가·삭제로 보인다(git 기본 diff 알고리즘은 Myers). 포매팅이 줄을 쪼개고 합치면 공통 부분이 줄어 diff가 커진다(실험 A 56줄). `-w`는 줄을 비교할 때 공백만 무시하므로 줄 경계가 바뀐 곳은 남는다.
- **AST 기반 재출력**: 포매터는 소스를 구문 트리(AST)로 읽은 뒤 정해진 규칙으로 다시 찍는다. 같은 AST면 같은 텍스트가 나오므로, 저장소가 포매터 결과로 고정되면 동작 변경만 diff에 남는다.
- **blame과 무시할 커밋 목록**: `git blame`은 줄마다 마지막으로 바꾼 커밋을 찾는다. 대량 포매팅 커밋은 `--ignore-rev`·`--ignore-revs-file`(또는 `blame.ignoreRevsFile` 설정)로 건너뛸 수 있다(git 2.43 `git blame -h`로 확인).

## 적용 — 풀어나가는 법

### 1. 주석을 쓸지 정하는 순서

1. 이 정보가 **이름·타입·시그니처로** 표현되나? 되면 코드를 고친다(07·08·24).
2. 처음 읽는 사람이 코드를 보고 **빨리** 알 수 있나? 알 수 있으면 쓰지 않는다.
3. 남은 것을 쓴다: 왜(결정·제약·티켓 번호), 계약(인자 조건·반환·부작용·스레드 안전), 놀라운 점(성능 특성·외부 호출), 큰 그림.
4. 주석에 **코드에 있는 숫자·이름을 복사하지 않는다**. 이유와 출처만 남긴다.
5. "건드리지 마세요"를 쓰고 싶으면 **이유와 확인 방법**을 함께 쓴다.

```java
// 나쁨: 숫자 사본, 이유 없음
// 최대 3회 시도. 실패까지 약 0.3초.
static final int MAX_ATTEMPTS = 5;

// 나음: 이유와 출처, 숫자는 코드에만
// 결제 게이트웨이 SLA가 "2초 안 응답"이라 마지막 시도가 2초 전에 끝나게 잡은 값 (#1234).
// 바꾸면 RetryBudgetTest를 함께 고친다.
static final int MAX_ATTEMPTS = 5;

// 나쁨:  // 건드리지 마세요
// 나음:  // 이 순서(lock → 재고 차감 → 이벤트 발행)를 바꾸면 이중 차감이 난다 (2025-03 장애 #881).
//        재현: StockConcurrencyTest.doubleDecrement
```

### 2. 관례를 도구에 맡기기

1. 포매터 하나를 정한다(Java: google-java-format·Spotless 등, JS/TS: Prettier).
2. **포매팅만 하는 커밋** 하나로 저장소 전체를 맞춘다. 이 커밋을 `.git-blame-ignore-revs`에 넣는다.
3. CI에서 검사한다: google-java-format `--dry-run`(어긋난 파일 이름 출력) 또는 Spotless `check`.
4. 이후 리뷰에서 스타일 코멘트는 "Nit:"로만, 스타일 가이드에 없는 취향으로는 막지 않는다(Google eng-practices).

```bash
# 포맷 어긋난 파일 찾기 (출력이 있으면 실패)
java -jar google-java-format-1.37.0-all-deps.jar --dry-run $(git ls-files '*.java')

# 리뷰 중: 공백 변경을 빼고 보기 (중괄호·줄 나눔은 남는다 — 실험 A)
git diff -w --stat

# 대량 포매팅 커밋을 blame에서 제외
echo <포매팅 커밋 해시> >> .git-blame-ignore-revs
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

- 실험 스크립트는 `--add-exports=jdk.compiler/...` 옵션을 붙여 돌렸다. 같은 1.37.0 all-deps jar는 JDK 21에서 옵션 없이 `--dry-run`도 동작했다(추가 확인 실행). README의 `--add-exports` 안내는 IDE(IntelliJ·Eclipse)에서 돌릴 때와 JDK 16+에서 라이브러리로 쓸 때용이다. 명령줄 all-deps jar 절에는 이 안내가 없다.

### 3. 낡은 주석 찾기

- 리뷰에서 바뀐 줄 **위아래 주석**을 함께 읽는다(APOSD 16.5 "Maintaining comments: check the diffs").
- 숫자가 든 주석을 검색해 코드 값과 대조한다: `grep -rnE '//.*[0-9]+ *(회|초|ms|건|%)' src`.

## 장애 시나리오와 대처

### 1. 주석과 코드가 반대 → 장애 때 잘못된 판단 (⚠ 커리큘럼)

- 현상: 주석은 "재시도 3회, 약 0.3초", 코드는 5회. 상위 서비스가 1초 타임아웃으로 먼저 끊는다.
- 보이는 형태: 상위 로그에 타임아웃, 하위 로그에는 "attempt 4 failed" — 실험 B `gave up after 1537ms`. 온콜은 주석을 믿고 "재시도는 0.3초면 끝난다"며 다른 곳을 찾는다.
- 원인: 주석이 코드의 숫자를 복사했고(지식 사본), 값 변경 때 함께 고치지 않았다.
- 대처: 주석에서 숫자를 빼고 이유·출처만 남긴다. 총 대기 시간은 코드로 계산하고 테스트로 고정한다. 리뷰에서 바뀐 줄 근처 주석을 함께 본다.

### 2. `// 건드리지 마세요`만 있고 이유 없음 → 아무도 못 고침 (⚠ 커리큘럼)

- 현상: 느린 코드인데 아무도 손대지 않는다. 몇 년째 그대로다.
- 보이는 형태: 같은 파일 주변에만 우회 코드(래퍼·복제 메서드)가 쌓인다. 리뷰에서 "원래 이유를 아는 사람?"에 답이 없다.
- 원인: 경고는 있고 **왜**가 없다. 작성자가 떠나면 근거가 사라진다.
- 대처: git log·blame·티켓으로 원래 이유를 찾아 주석에 적는다(장애 번호·재현 테스트 이름). 이유를 못 찾으면 특성화 테스트로 현재 동작을 고정한 뒤 고친다([51-legacy-change-techniques](../51-legacy-change-techniques/2-summary.md)). 결정 수준의 이유는 ADR로(47).

### 3. 파일마다 스타일이 다름 → diff의 절반이 포매팅 (⚠ 커리큘럼)

- 현상: 1줄 수정 PR이 56줄 diff로 올라온다. 리뷰어가 동작 변경을 놓친다.
- 보이는 형태: 실험 A noisy `31 insertions(+), 25 deletions(-)`. 병합 충돌이 잦다. blame이 포매팅 커밋을 가리킨다.
- 원인: 팀 포매터가 없고, 각자 IDE 설정으로 저장 시 재포매팅된다.
- 대처: 포매터 고정 + 일괄 포매팅 커밋 + CI `--dry-run` 검사 + blame 무시 목록. 이후 같은 변경은 1줄 diff(실험 A consistent).

### 4. 주석 처리된 코드 → 죽은 코드가 살아 있는 척

- 현상: `// oldCalculate(order);` 블록이 수십 줄. 누가 다시 살렸다가 옛 규칙이 적용됐다.
- 보이는 형태: 정산 차이. 주석 해제 커밋이 "임시 복구"라는 메시지로 남아 있다.
- 원인: 지운 코드를 주석으로 남겼다. 그 코드는 컴파일·테스트되지 않아 이미 낡았다.
- 대처: 지운다. git이 기억한다. 되살릴 필요가 생기면 git 이력에서 꺼내 테스트와 함께 들인다([54-designing-for-deletion](../54-designing-for-deletion/2-summary.md)).

### 5. 문서 규칙만 강제 → 정보 없는 주석이 늘어남

- 현상: 공개 메서드마다 Javadoc이 있는데 읽을 게 없다.
- 보이는 형태: "@param key the key"가 대부분. doclint 경고는 0건(실험 C echo).
- 원인: 도구는 주석의 존재만 검사하고 내용은 보지 않는다.
- 대처: 공개 API에는 계약(조건·반환·부작용)을 요구하고, 내부 코드에는 존재 강제를 걸지 않는다. 내용은 리뷰 검사표로 본다.

## 핵심 문장

- 주석은 코드가 담지 못하는 것 — 왜, 계약, 놀라운 동작, 큰 그림 — 을 쓰는 자리다. 코드에서 빨리 읽히는 사실은 쓰지 않는다.
- 주석에 코드의 숫자를 복사하면 사본이 생긴다. 실험에서 코드가 5회로 바뀐 뒤에도 주석은 "3회, 약 0.3초"였고 실제 포기까지 약 1.5초가 걸렸다.
- 관례는 사람이 아니라 포매터가 정한다. 같은 1줄 변경이 재포매팅과 섞이자 56줄 diff가 됐고, 포매터가 고정된 저장소에서는 1줄이었다.
- 문서 검사 도구는 주석의 있음만 본다. "Try acquire. / the key"도 통과한다.
- 주석의 양은 저자마다 다르다(Ousterhout는 Martin보다 5~10배 더 쓴다고 했다). 둘 다 공개 API 계약에는 주석이 필요하다고 본다.

## 관련 주제·근거

- 선행
  - [08-function-design](../08-function-design/2-summary.md) — 시그니처가 담는 것과 못 담는 것
  - [47-architecture-decision-records](../47-architecture-decision-records/2-summary.md) — 함수 수준의 "왜"는 주석, 구조 수준의 "왜"는 ADR
- 후속·연결
  - [06-clean-code](../06-clean-code/2-summary.md) — 비중복(N): 주석과 코드의 중복
  - [10-code-smells](../10-code-smells/2-summary.md) — Fowler 2판 3장의 마지막 스멜이 "Comments"다
  - [14-tidy-first](../14-tidy-first/2-summary.md)(구조 변경과 동작 변경 분리) · [51-legacy-change-techniques](../51-legacy-change-techniques/2-summary.md) · [54-designing-for-deletion](../54-designing-for-deletion/2-summary.md)
  - [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md) · [reliability/08-time-budget-allocation](../../reliability/08-time-budget-allocation/2-summary.md) — 실험 B의 재시도·시간 예산
- 글·문서
  - John Ousterhout, 『A Philosophy of Software Design』 2판 12장 "Why Write Comments? The Four Excuses"(12.6 comments are failures), 13장 "Comments Should Describe Things that Aren't Obvious from the Code", 16장 "Modifying Existing Code"(16.5 check the diffs — 절 제목만), 17장 "Consistency" — 2판 커뮤니티 번역 사이트 영문판으로 장 도입·결론 확인 <https://yingang.github.io/aposd2e-zh/en/ch12.html>
  - Ousterhout·Martin 대담 「Comments Summary」 <https://github.com/johnousterhout/aposd-vs-clean-code>
  - Dustin Boswell·Trevor Foucher, 『The Art of Readable Code』 5장 "Knowing What to Comment" — 발췌 PDF로 본문 확인 <https://www.cs.hmc.edu/cs70/homework/homework-03/pdfs/styleboswell.pdf> · 6장 "Making Comments Precise and Compact"는 장 제목만 확인 [?]
  - Google eng-practices "What to look for in a code review"(Comments·Style·Consistency) <https://github.com/google/eng-practices/blob/master/review/reviewer/looking-for.md>
  - Hunt·Thomas, 『The Pragmatic Programmer』 20주년판 Topic 9 「Duplication in Documentation」 발췌 <https://media.pragprog.com/titles/tpp20/dry.pdf>
  - google-java-format README(설정 없음 원칙, `--dry-run`) <https://github.com/google/google-java-format> · Google Java Style Guide(블록 들여쓰기 +2, 열 제한 100) <https://google.github.io/styleguide/javaguide.html>
- 실험 목록 (코드: scratchpad `sd/06/e09/`, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, google-java-format 1.37.0 all-deps jar(Maven Central), git 2.43.0)
  - A 포매팅 섞인 diff vs 포매터 고정 — `run-format.sh` (diff --stat, `-w`, `--dry-run`)
  - B 낡은 주석과 실제 재시도 시간 — `run-format.sh` 09-B (기록한 5회 실행 1,513~1,537ms)
  - C doclint의 주석 검사 범위 — `run-doclint.sh`
