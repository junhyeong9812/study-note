# language/02-lexing-and-regular-languages — 토큰화·정규식·유한 오토마타 — 정리 (힌트)

## 해결하는 문제

컴파일러가 받는 소스는 글자의 줄이다. 파서(03)는 글자가 아니라 **단어**가 필요하다.

```text
  글자:  i f ␠ ( c o u n t ␠ > = ␠ 1 0 )
  토큰:  [IF] [LPAREN] [IDENT count] [GE] [NUM 10] [RPAREN]
```

- *토큰(token)*: 종류(키워드·식별자·숫자·연산자)와 원문 조각(lexeme), 위치를 묶은 단위.
- *렉서(lexer, 어휘 분석기)*: 글자 줄을 토큰 줄로 자르는 프로그램.

"식별자는 글자로 시작해 글자·숫자가 이어진다" 같은 규칙을 적는 말이 **정규식**이고, 그 규칙을 빠르게 실행하는 기계가 **유한 오토마타**다.

쉬운 예: 우편번호 검사기.
- "숫자 5개"라는 규칙을 적는다(정규식).
- 기계는 글자를 하나씩 보며 "지금 몇 번째 숫자인가"라는 **상태** 하나만 기억한다(오토마타).

똑같은 구조다.\
같은 기계가 컴파일러 밖에서도 쓰인다. 입력 검증, 로그 파싱, WAF 규칙, `String.split`. 그리고 구현을 잘못 고르면 **입력 한 줄이 CPU 코어 하나를 다 먹는다(ReDoS).**

실무 예:
- 이메일 검증 정규식 하나가 특정 입력에서 수 초씩 걸려 요청 스레드가 고갈된다.
- Cloudflare 2019-07-02: WAF 규칙에 넣은 정규식 하나가 전 세계 HTTP 처리 CPU를 소진시켜 27분 장애가 났다(원문, 장애 시나리오 1).

## 동작·원리

### 1. 렉서 — 가장 긴 토큰을 고른다

```text
  입력  c o u n t ␠ > = ␠ 1 0
        └──IDENT─┘   └GE┘  └NUM┘
  ">"에서 멈추면 [GT][ASSIGN] 두 개. "가장 길게" 자르면 [GE] 하나.
```

- *최장 일치(maximal munch)*: 지금 위치에서 만들 수 있는 가장 긴 토큰을 고른다는 규칙.
  - JLS 21 §3.2는 이것을 명시한다. "가장 긴 번역을 쓴다. 다른 번역이면 올바른 프로그램이 되더라도." 예로 `a--b`는 `a`, `--`, `b`로 잘린다.
  - 실험(JDK 21.0.12): `int c = a--b;`는 `error: ';' expected`다. `a - -b`로 띄우면 7이 나온다.
  - 예외도 §3.2·§3.5에 있다. 제네릭의 `List<List<String>>`에서 `>>`는 시프트가 아니라 `>` 두 개로 다시 쪼갠다.
- 렉서는 문법이 맞는지 신경 쓰지 않는다. 그건 파서 몫이다(원고 [compiler-pipeline](../../foundations/compiler-pipeline/README.md) §1 "1단계", §6, Python `tokenize` 실습 §7).

### 2. 정규식 = 세 연산

정규 언어는 세 연산으로 만든다.

| 연산 | 정규식 | 뜻 |
|---|---|---|
| 연결 | `ab` | a 다음 b |
| 선택 | `a\|b` | a 또는 b |
| 반복(클레이니 스타) | `a*` | a를 0번 이상 |

- `a+`는 `aa*`, `a?`는 `a|ε`의 줄임이다.
  - *ε(엡실론)*: 빈 문자열. 글자를 하나도 읽지 않고 넘어가는 것.
- 정규식으로 적을 수 있는 언어 = 유한 오토마타로 알아볼 수 있는 언어다(Sipser 1장 `[?]`, Dragon Book 3장 `[?]`).
- **역참조(`\1`)는 이 세 연산 밖이다.** Cox 2007은 "역참조가 있는 정규식은 정규식이 아니다"라고 쓰고, 알려진 최선 구현도 최악에는 지수 탐색이라고 적는다.

### 3. DFA — 상태 하나만 들고 간다

`>=` `>` `=` 세 토큰을 알아보는 DFA:

```text
            '>'               '='
   (시작) ──────▶ ((S1 = GT)) ──────▶ ((GE))
     │ '='
     ▼
  ((ASSIGN))           ※ '>'만 읽은 S1 자체가 수용 상태(GT)다
```

- 겹 동그라미 `(( ))`는 *수용 상태*(여기서 멈추면 토큰 하나가 완성된 상태)다. DFA의 전이는 모두 글자 하나를 소비한다.
- S1에서 `=`가 아닌 글자가 오면 DFA는 더 갈 곳이 없다(그림에서 생략한 *죽은 상태*로 간다). 그때 **렉서**가 마지막으로 지난 수용 상태(GT)로 토큰을 끝내고, 그 글자는 다음 토큰의 첫 글자로 남긴다(최장 일치 처리, JFlex 매뉴얼).

- *DFA(결정적 유한 오토마타)*: 어느 상태에서든 다음 글자 하나에 갈 곳이 **하나뿐**인 기계.
- 입력 n글자면 상태 전이 n번. 표 하나 조회로 끝난다. 그래서 렉서 생성기(lex 계열)는 규칙들을 DFA 하나로 합친다.
- 키워드(`if`·`for`)는 식별자 DFA로 읽은 뒤 키워드 표를 찾거나, 트라이로 같이 넣는다([data-structure/09-trie](../../data-structure/09-trie/2-summary.md)).

### 4. NFA와 Thompson 구성

정규식을 바로 DFA로 만들기는 어렵다. 먼저 NFA를 만든다.

- *NFA(비결정적 유한 오토마타)*: 한 글자에 갈 곳이 여럿이거나, 글자 없이(ε) 움직일 수 있는 기계.
- *Thompson 구성*: 정규식의 각 연산을 작은 NFA 조각으로 바꿔 이어 붙이는 방법(Thompson 1968, Cox 2007 설명).

```text
  글자 a        연결 e1 e2            선택 e1|e2               반복 e*
  ─▶○─a─▶      ─▶[e1]─▶[e2]─▶       ┌ε▶[e1]─┐               ┌──────ε─────┐
                                 ─▶○┤        ├─▶            ▼            │
                                    └ε▶[e2]─┘           ─▶○─ε▶[e]───────┘
                                                            └──ε──▶ (다음)
```

- 조각은 "끝이 아직 안 이어진 화살표"를 들고 다닌다. 다음 조각을 만나면 그 화살표를 잇는다.
- 상태 수는 정규식 길이에 비례한다. 실험에서 `(a|b)*a(a|b)^k`의 NFA는 k=1일 때 9개, k=12일 때 42개였다(선형).

### 5. NFA를 실행하는 두 방법 — 여기서 ReDoS가 갈린다

```text
  (가) 백트래킹: 갈림길에서 하나를 골라 끝까지 가 본다. 실패하면 돌아와 다른 쪽.
       → 길이 하나씩. 경로 수가 지수면 시간도 지수.

  (나) 상태 집합 시뮬레이션(Thompson): 갈 수 있는 상태를 "전부" 집합으로 들고 한 글자씩 전진.
       → 글자마다 집합 갱신 1번. 시간 = O(입력 길이 n × 상태 수 m).
```

`(a+)+$`에 `aaa…a!`(a가 n개)를 넣으면:

```text
  "aaaa"를 바깥 + 몇 덩어리로 나누나?
   (aaaa) (aaa)(a) (aa)(aa) (a)(aaa) (aa)(a)(a) (a)(aa)(a) (a)(a)(aa) (a)(a)(a)(a)
   → n글자의 나눔 = 2^(n-1)가지. 끝의 '!' 때문에 전부 실패해야 "매치 없음"이다.
   백트래킹은 이 2^(n-1)을 다 시도한다. 상태 집합 방식은 "a를 읽는 중" 상태 몇 개만 들고 간다.
```

- Perl·PCRE·Python `re`·Java `java.util.regex`·JS(V8 Irregexp)는 (가)다. 역참조·전후방 탐색 같은 기능을 쉽게 붙일 수 있어서다.
- RE2·Go `regexp`·Rust `regex`는 (나) 계열이다. Go 1.23 `go doc regexp`: "입력 크기에 선형인 시간에 실행됨을 보장한다". 대신 역참조가 없다.

### 6. 부분집합 구성 — NFA를 DFA로

- *부분집합 구성(subset construction)*: "NFA 상태들의 집합" 하나를 DFA 상태 하나로 삼는 변환. (나)의 시뮬레이션에서 나오는 집합들을 미리 다 만들어 두는 것이다.
- 대가: DFA 상태가 최악 2^m개까지 늘 수 있다. 그래서 RE2는 필요한 상태만 실행 중에 만들어 캐시한다(지연 DFA, Cox 2007 "Caching the NFA to build a DFA"). Go 1.23 `regexp`는 DFA 캐시 없이 상태 집합을 글자마다 다시 계산한다(`regexp/exec.go`). 이것도 입력 길이에 선형이다.

### 실험: 백트래킹 엔진 vs 상태 집합 — `(a+)+$`에 `a^n!`

- 환경: 호스트 i7-13700HX. 컨테이너는 모두 `--cpus=2 --network none --pull never`. 매칭 실패 입력 `"a"*n + "!"`.

| 엔진 | n=14 | n=18 | n=20 | n=22 | n=24 | n=28 | 큰 n |
|---|---|---|---|---|---|---|---|
| CPython 3.12.14 `re`(3회) | 3.7~6.2 ms | 56~101 ms | 250~356 ms | 1017~1148 ms | 4245~4725 ms | — | — |
| node 22.23.2 (V8 기본, 2회) | 4.3~5.2 ms | 9.0~10.4 ms | 39~42 ms | 159~173 ms | 606~748 ms | 9,953~11,093 ms | — |
| Go 1.23.12 `regexp`(2회) | 0.081~0.101 ms | — | — | — | — | 0.005~0.041 ms(n=30) | n=10⁶: 150~152 ms |
| Java 21.0.12 `java.util.regex`(4회) | 0.4~0.5 ms | 0.4~0.6 ms | 0.3~0.4 ms | 0.3~0.5 ms | 0.3~0.5 ms | 0.3~0.6 ms | n=30: 0.3~0.6 ms |
| 직접 만든 Thompson 시뮬레이션(Java) | — | — | — | — | — | 0.07~0.29 ms(n=30) | n=10⁵: 82~155 ms |

- 관찰 1 — Python·node는 n이 2 늘 때마다 약 3.2~4.4배다. 한 글자당 약 2배, 2^(n-1) 나눔과 같은 기울기다.
- 관찰 2 — Go와 직접 만든 Thompson 시뮬레이션은 n=10⁵~10⁶에서도 수백 ms 이하다. 길이에 비례한다.
- 관찰 3 — **Java 21은 이 패턴에서 안 터졌다.** 원인은 JDK 소스에 있다. `Pattern.java`(jdk21u)는 바깥 탐욕 반복(`Loop`)이 "이 시작 위치에서 이미 실패했다"를 `IntHashSet`에 기억해 다시 시도하지 않는다. 이 메모이제이션은 **패턴에 역참조가 있으면 꺼진다**(`hasGroupRef`). 상세 해설·JDK 17·25 비교는 [languages/java/syntax/37-regex](../../../languages/java/syntax/37-regex/2-summary.md) (5)절.

같은 Java 21에서 모양만 조금 바꾼 패턴(4회 실행 범위 — Cox 줄은 3회, ms):

```text
  패턴                 n=20          n=24            n=26
  (a+)+$               0.3~0.4       0.3~0.5         0.3~0.4      ← 메모이제이션 켜짐
  (a+)+$|(b)\2         119~213       1786~2420       6977~9832    ← 상관없는 역참조 하나로 꺼짐
  (?:(a+)+)?$          126~196       2196~2899       8769~11163   ← 반복이 바깥 그룹 안으로 들어가 대상 밖
  Cox: a?ⁿaⁿ 를 aⁿ에    84~119        1000~1259       4234~5725    ← 성공하는 입력인데도 지수 (matches)
```

- 관찰 4 — Java의 방어는 **특정 모양에만 붙은 구현 최적화**다. 명세(Javadoc) 약속이 아니다. Cox 2007의 `a?ⁿaⁿ`는 반복 그룹이 아니라 선택 n개라 메모이제이션 대상도 아니다. 이 실험에서 n=26에 4~6초가 걸렸다.
- 관찰 5 — node에서 V8 실험 플래그 `--enable-experimental-regexp-engine`과 `l` 플래그를 주면 같은 패턴이 n=10⁵에 44~49ms였다(2회). 역참조 `/(a)\1/l`은 `SyntaxError: ... Cannot be executed in linear time`으로 거부됐다. 실험 플래그라 운영 권장은 아니다.

### 실험: 부분집합 구성의 상태 폭발

`(a|b)*a(a|b)^k` = "끝에서 k+1번째 글자가 a"(직접 만든 Thompson + 부분집합 구성, Java 21):

```text
  k   NFA 상태  DFA 상태
  1      9         4
  2     12         8
  3     15        16
  4     18        32
  8     30       512
  12    42      8192
```

- NFA는 k에 비례해 늘고, DFA는 2^(k+1)로 늘었다. DFA는 "지난 k+1글자 중 어디가 a였나"를 전부 기억해야 해서다.
- 그래서 "정규식을 DFA로 미리 다 만든다"도 공짜가 아니다. 지연 DFA를 쓰는 선형 엔진(RE2)은 캐시 크기 상한으로 메모리를 관리한다.

## 쓰이는 자료구조·알고리즘

- **NFA·DFA = 방향 그래프** — 상태가 정점, 글자가 간선 라벨([data-structure/08-graph](../../data-structure/08-graph/2-summary.md)).
- **Thompson 구성** — 정규식을 후위 표기로 바꾼 뒤 스택으로 조각을 합친다([data-structure/03-stack](../../data-structure/03-stack/2-summary.md)). 실험 코드의 `toPostfix`·`compile`이 이 순서다.
- **상태 집합 시뮬레이션** — 현재 상태 집합(해시 집합 또는 비트셋 [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md))과 ε 닫힘(DFS).
- **부분집합 구성** — 집합 상태를 정점으로 삼는 BFS([algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md)).
- **백트래킹** — 갈림길을 하나씩 시도하고 되돌아오기([algorithm/13-backtracking](../../algorithm/13-backtracking/2-summary.md)). 정규식 엔진이 그 대표 사용처다.
- **KMP 실패 함수** — 고정 문자열 하나를 찾는 DFA의 압축판([algorithm/25-string-matching](../../algorithm/25-string-matching/2-summary.md)).
- **키워드 표·트라이** — 식별자와 키워드 구분([data-structure/09-trie](../../data-structure/09-trie/2-summary.md)).

## 적용 — 풀어나가는 법

1. **사용자 입력에 거는 정규식 목록을 만든다.** 검증·라우팅·로그 파싱·WAF·`split`·`replaceAll`.
2. **위험한 모양을 찾는다.**
   - 중첩 수량자 `(a+)+`, `(\w+\s?)*`
   - 겹치는 선택의 반복 `(a|a)*`, `(a|ab)*`
   - `.*`가 여럿 이어진 것 `.*(?:.*=.*)`(Cloudflare 2019 규칙의 끝부분)
   - 역참조(`\1`) — Java의 메모이제이션을 끈다.
3. **고쳐 쓴다.**
   - 중첩을 펴기: `(a+)+` → `a+`(같은 언어).
   - 소유 수량자·원자 그룹: `a++`, `(?>a+)`. Java `Pattern`은 원래 지원한다. Python `re`는 3.11부터다(문서 "Added in version 3.11"). 실험(호스트 Python 3.12.3, n=22, 2회): `(a+)+$` 981~986ms, `(?>a+)+$` 0.02~0.17ms, `(a++)+$` 0.01~0.28ms.
   - 정규식을 버리고 손 파서로.
4. **입력 길이 상한**을 정규식보다 앞에 둔다.
5. **시간 상한**을 둔다. `java.util.regex`에는 타임아웃 API가 없다. 매칭 대상 `CharSequence`가 `charAt`마다 인터럽트를 확인하게 감싸면 끊을 수 있다.

   ```java
   record Interruptible(CharSequence s) implements CharSequence {
       public char charAt(int i) {
           if (Thread.currentThread().isInterrupted()) throw new CancellationException("regex interrupted");
           return s.charAt(i);
       }
       public int length() { return s.length(); }
       public CharSequence subSequence(int a, int b) { return new Interruptible(s.subSequence(a, b)); }
       public String toString() { return s.toString(); }
   }
   // Future<Boolean> f = pool.submit(() -> evil.matcher(new Interruptible(in)).find());
   // f.get(200, MILLISECONDS) 시간 초과 → f.cancel(true)
   ```

   - 실험(JDK 21.0.12): `(a+)+$|(b)\2`에 `a^30!`. 203~204ms에 취소됐다(2회). 100ms 뒤 작업 스레드는 비어 있었다.
6. **선형 엔진**으로 옮긴다. Go `regexp`, RE2 계열. 역참조·전후방 탐색이 필요 없는 검증이라면 손해가 거의 없다.
7. **회귀 테스트**: 바꾼 정규식에 `"a"*n + "!"` 꼴 입력을 n=16·20·24로 넣어 시간이 배로 느는지 본다. 위 실험의 방식이다.

## 장애 시나리오와 대처

### 1. 정규식 하나로 CPU 100% — ReDoS (⚠)

- **현상**: 특정 요청부터 응답이 끝나지 않는다. 그 인스턴스의 코어가 하나씩 100%가 된다. 요청 스레드가 고갈돼 정상 요청도 실패한다.
- **보이는 형태**
  - Java 스레드 덤프가 `java.util.regex.Pattern$GroupHead.match` → `Pattern$Loop.match` → `Pattern$GroupTail.match` → `Pattern$BmpCharPropertyGreedy.match`의 반복이다(실험: JDK 21.0.12에서 `(a+)+$|(b)\2`를 돌리는 스레드의 `getStackTrace()`).
  - 입력에 같은 글자가 길게 이어진다.
  - Cloudflare 2019-07-02(원문): 13:42 UTC에 WAF XSS 규칙을 배포했다. HTTP/HTTPS 처리 CPU가 전 세계에서 거의 100%가 됐고 502를 냈다. 27분 장애였다. Lua WAF가 쓰는 PCRE는 백트래킹 엔진이고 폭주를 막는 장치가 없었다. 문제 정규식 끝부분이 `.*(?:.*=.*)`이다.
- **원인**: 백트래킹 엔진이 실패 입력에서 나눔을 지수(또는 높은 다항)만큼 시도한다. 위 실험에서 Python·node는 한 글자당 약 2배였다.
- **대처**
  - 즉시: 그 규칙·검증을 끄거나 롤백한다. 입력 길이 상한을 건다.
  - 근본: 패턴을 고친다(적용 3). 시간 상한(적용 5)이나 선형 엔진(적용 6)을 둔다. Cloudflare는 후속 조치로 re2나 Rust regex 엔진으로의 전환과 규칙 성능 테스트를 적었다.
  - 다른 실사건과 다항 폭증은 [algorithm/43-alg-incidents](../../algorithm/43-alg-incidents/2-summary.md), 방어 쪽은 [security/28-dos-and-abuse](../../security/28-dos-and-abuse/2-summary.md).

### 2. 긴 입력에서 정규식이 `StackOverflowError`

- **현상**: 짧은 입력은 되는데, 몇 KB짜리 입력에서 검증 함수가 `StackOverflowError`로 죽는다.
- **보이는 형태**: 스택 트레이스에 `Pattern$Branch.match`·`Pattern$GroupHead.match`·`Pattern$Loop.match`·`Pattern$GroupTail.match`·`Pattern$BranchConn.match`가 되풀이된다(실험: JDK 21.0.12, 트레이스는 `MaxJavaStackTraceDepth` 기본값 1,024프레임에서 잘림).
- **원인**: `java.util.regex`의 매칭은 노드끼리 `match`를 재귀 호출한다. `(a|b)*` 같은 그룹 반복은 반복 한 번마다 스택 프레임이 쌓인다. 반면 `[ab]*` 같은 문자 클래스 반복은 `BmpCharPropertyGreedy.match`의 `while` 루프로 처리돼 프레임이 쌓이지 않는다(jdk21u `Pattern.java`). 실험(JDK 21.0.12, 기본 스택): `(a|b)*`에 `abab…` n=1,000은 성공, n=10,000은 `StackOverflowError`였다. 같은 언어인 문자 클래스 `[ab]*`는 n=100,000에서도 성공했다.
- **대처**: 선택 `(a|b)`를 문자 클래스 `[ab]`로 바꾼다. 입력 길이 상한을 둔다. 스택을 키우는 것(`-Xss`)은 상한을 미룰 뿐이다.

### 3. 검증을 통과했는데 이상한 값 — `find()`와 `matches()` 혼동

- **현상**: 숫자만 받는다던 필드에 `12abc`가 저장됐다.
- **보이는 형태**: 검증 코드가 `Pattern.compile("[0-9]+").matcher(s).find()`다.
- **원인**: `find()`는 **어딘가 한 부분**이 맞으면 참이다. `matches()`는 **전체**가 맞아야 참이다. 정규식 자체는 맞고, 오토마타를 "어디서 시작·끝내느냐"가 다르다.
- **대처**: 검증에는 `matches()`(또는 `^…$`와 `\z`)를 쓴다. 단위 테스트에 "앞뒤에 쓰레기가 붙은 입력"을 넣는다.

### 4. 정규식 컴파일 비용이 CPU를 먹음

- **현상**: 프로파일에서 `Pattern.compile`이 상위에 보인다.
- **보이는 형태**: 반복문 안의 `String.matches`·`String.replaceAll`·`String.split(정규식)`. 단 `split`은 `","`처럼 메타 문자가 아닌 한 글자(또는 Java 문자열 `"\\."`처럼 역슬래시 + 영숫자 아닌 글자)면 정규식 없이 빠른 경로로 자른다(jdk21u `String.java`). 그 밖의 패턴만 호출마다 컴파일한다.
- **원인**: `String.matches(regex)`는 `Pattern.matches(regex, s)`와 같고, 호출할 때마다 정규식을 컴파일한다. Java API 문서도 "여러 번 쓸 패턴이면 한 번 컴파일해 재사용하는 편이 효율적"이라고 적는다. 실험(JDK 21.0.12, 100만 회, 3라운드 × 2회): `String.matches` 514~1,835ms, 미리 컴파일한 `Pattern` 132~161ms. 첫 회는 워밍업이 섞였다.
- **대처**: `static final Pattern`으로 한 번만 만든다.

## 핵심 문장

- 렉서는 글자를 토큰으로 자른다. 지금 위치에서 가장 긴 토큰을 고른다(JLS §3.2의 `a--b`).
- 정규식은 연결·선택·반복 세 연산이다. 같은 언어를 유한 오토마타로 실행할 수 있다. 역참조는 이 범위 밖이다.
- 같은 NFA도 백트래킹으로 돌리면 최악 지수, 상태 집합으로 돌리면 입력 길이에 선형이다.
- 이 실험에서 Python·node는 `(a+)+$`에 한 글자당 약 2배 느려졌다. Go와 직접 만든 Thompson 시뮬레이션은 선형이었다.
- Java 21의 메모이제이션은 특정 모양에만 붙은 구현 최적화다. 역참조 하나나 모양 변화로 꺼진다. 입력 길이 상한, 시간 상한, 선형 엔진이 방어선이다.

## 관련 주제·근거

- 선행
  - [01-compile-interpret-jit](../01-compile-interpret-jit/2-summary.md) — 파이프라인에서 렉서의 자리
- 후속·연결
  - [03-parsing-grammars-ast](../03-parsing-grammars-ast/2-summary.md) — 토큰을 받아 트리를 만드는 단계, 정규식이 못 하는 괄호 짝 맞추기
  - [algorithm/13-backtracking](../../algorithm/13-backtracking/2-summary.md) · [algorithm/25-string-matching](../../algorithm/25-string-matching/2-summary.md) · [algorithm/41-computability-and-halting](../../algorithm/41-computability-and-halting/2-summary.md)
  - [algorithm/43-alg-incidents](../../algorithm/43-alg-incidents/2-summary.md) — Stack Overflow 2016·Cloudflare 2019 다항 폭증 재현
  - [security/28-dos-and-abuse](../../security/28-dos-and-abuse/2-summary.md) — ReDoS를 포함한 자원 고갈 방어
  - 문법: [languages/java/syntax/37-regex](../../../languages/java/syntax/37-regex/2-summary.md) — `Pattern` 문법·소유 수량자·Java 메모이제이션 상세
  - 원고 [foundations/compiler-pipeline](../../foundations/compiler-pipeline/README.md) §1 1단계(어휘 분석) · §6(렉서·토큰) · §7(`tokenize` 실습)
- 문서·논문·소스
  - Russ Cox, "Regular Expression Matching Can Be Simple And Fast"(2007-01) — `a?ⁿaⁿ` 비교, Thompson 1968 구성, 역참조와 지수 탐색, DFA 캐시 <https://swtch.com/~rsc/regexp/regexp1.html>
  - JLS SE21 §3.2 Lexical Translations(최장 번역, `a--b`, `>` 예외) <https://docs.oracle.com/javase/specs/jls/se21/html/jls-3.html>
  - Java SE 21 API `Pattern` — 소유 수량자, `Pattern.matches` 재사용 권고 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/regex/Pattern.html>
  - OpenJDK jdk21u `java/util/regex/Pattern.java` — `hasGroupRef`·`topClosureNodes`·`Loop.match`의 `localsPos` 메모이제이션
  - Python 3.12 `re` 문서 — 소유 수량자·원자 그룹 "Added in version 3.11" <https://docs.python.org/3.12/library/re.html>
  - Go 1.23 `go doc regexp` — 선형 시간 보장, RE2 문법
  - Cloudflare, "Details of the Cloudflare outage on July 2, 2019" <https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/>
  - Aho 외 『Compilers』(Dragon Book) 3장 `[?]` · Sipser 『Introduction to the Theory of Computation』 1장 `[?]`
- 실험 목록
  - `(a+)+$` × `a^n!` — Python 3.12.14(`python:3.12-slim`, 3회) · node 22.23.2(`node:22-alpine`, 2회) · Go 1.23.12(`golang:1.23-alpine`, 표준 라이브러리, 2회) · Java 21.0.12(Temurin, 4회). 모두 `--cpus=2 --network none`(집필 + 점검 재실행)
  - Java 21 패턴 변형(`|(b)\2`, `(?:…)?`, Cox `a?ⁿaⁿ`) 4회(Cox 3회) · V8 실험 선형 엔진(`--enable-experimental-regexp-engine`, `/l`)
  - 직접 만든 Thompson NFA + 상태 집합 시뮬레이션 + 부분집합 구성(`Thompson.java`, JDK 21, 2회)
  - 원자 그룹·소유 수량자(호스트 Python 3.12.3) · 인터럽트 가능한 `CharSequence`로 정규식 취소, `(a|b)*` 대 `[ab]*` 스택, `String.matches` 대 미리 컴파일(`Guard.java`, JDK 21) · `a--b` 최장 일치(`Munch.java`)
