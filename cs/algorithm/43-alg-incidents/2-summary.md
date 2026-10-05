# algorithm/43-alg-incidents — 실사건: JDK 이진 탐색 오버플로(Bloch 2006) · Stack Overflow 정규식 장애(2016-07-20) · Cloudflare WAF 정규식 백트래킹(2019-07-02) — 알고리즘 관점 — 정리 (힌트)

## 해결하는 문제

세 사건은 모두 **증명되거나 오래 쓰인 코드**가 입력이 커지거나 모양이 바뀌자 무너진 경우다.

```text
  Bloch 2006       교과서·JDK의 이진 탐색  ── 배열 원소가 약 10억(2^30)을 넘자 ──▶ (low + high) 오버플로 → 음수 인덱스
  Stack Overflow   공백 자르기 정규식 \s+$ 꼴 ── 공백 약 2만 개가 든 글 하나 ──────▶ O(n²) 백트래킹 → 홈페이지 느려짐 → 헬스 체크 실패 → 34분 전체 장애
  Cloudflare 2019  WAF 규칙의 .*(?:.*=.*)    ── 전역 배포된 규칙 하나 ──────────▶ 과도한 백트래킹 → HTTP 처리 CPU 거의 100% → 27분
```

쉬운 예: 다리의 설계 하중이다.\
10톤 트럭까지 버티게 계산한 다리는 수십 년 동안 문제없다. 어느 날 20톤 트럭이 지나가면 계산은 틀린 적이 없는데 다리는 무너진다.\
계산의 **가정**(트럭은 10톤 이하)이 깨진 것이다.

똑같은 구조다.\
이진 탐색의 정확성 증명은 "정수는 넘치지 않는다"를 가정했다. 정규식 매칭은 "입력이 짧다"를 암묵적으로 가정했다.\
가정이 맞는 동안 코드는 옳았고, 테스트도 통과했다.

실무 예:
- 사용자가 올린 글·요청 본문·로그 한 줄처럼 **길이를 남이 정하는 입력**에 정규식을 거는 코드는 흔하다.
- 배열 크기·오프셋·타임스탬프처럼 `int`로 시작한 값이 시간이 지나 커지는 일도 흔하다.

  - *1차 출처*: 당사자가 직접 쓴 문서 — Bloch의 블로그 글, JDK 버그 보고, Stack Exchange의 사후 보고서, Cloudflare의 사후 보고서. 이 노트는 시각·수치를 원문 그대로 옮기고, 원문에 없는 연결은 "해석"이라고 표시한다.
  - *백트래킹 정규식 엔진*: 패턴의 선택지(몇 글자를 먹을지)를 하나 골라 진행하다 실패하면 되돌아가 다른 선택지를 시도하는 엔진. Java `java.util.regex`, PCRE, Perl이 이 방식이다([13-backtracking](../13-backtracking/2-summary.md)).

## 동작·원리

### 사건 1 — JDK `Arrays.binarySearch` 중간값 오버플로 (보고 2004 · 수정 JDK 6 · Bloch 글 2006-06-02)

출처
- Joshua Bloch, "Extra, Extra - Read All About It: Nearly All Binary Searches and Mergesorts are Broken", Google Research 블로그, 2006-06-02 <https://research.google/blog/extra-extra-read-all-about-it-nearly-all-binary-searches-and-mergesorts-are-broken/>(2026-10-05 열람).
- JDK-5045582 "(coll) binarySearch() fails for size larger than 1<<30", 2004-05-11 등록, Fix Version 6(6 b83), 2006-04-29 해결(bugs.java.com 표시. 2026-10-05에 bugs.openjdk.org는 오류 페이지라 Internet Archive 사본으로 읽었다) <https://bugs.openjdk.org/browse/JDK-5045582>.
- JDK-6412541 "Arrays.binarySearch does not work for arrays larger than 1<<30", 2006-04-12 등록, Duplicate로 종료 — Bloch 글이 링크한 버그 <https://bugs.openjdk.org/browse/JDK-6412541>.
- Jon Bentley, 『Programming Pearls』(1986, 2판 2000) 5장 — Bloch 글이 인용.

#### 사실 (원문)

- Bloch 글: Bentley가 『Programming Pearls』 5장에서 증명하고 테스트한 이진 탐색에 버그가 있었다. Bloch가 JDK `java.util.Arrays`에 쓴 판도 같은 버그를 가졌고, 누군가의 프로그램을 망가뜨려 Sun에 보고됐다. "after lying in wait for nine years or so."
- 버그 줄: `int mid = (low + high) / 2;` — `low + high`가 `int` 최댓값(2^31 - 1)을 넘으면 음수로 넘치고, 2로 나눠도 음수다. Java에서는 `ArrayIndexOutOfBoundsException`, C에서는 예측할 수 없는 배열 범위 밖 접근.
- 원문: "This bug can manifest itself for arrays whose length (in elements) is 2^30 or greater (roughly a billion elements)."
- 고친 식(원문): `int mid = low + ((high - low) / 2);` 또는 `int mid = (low + high) >>> 1;`. C·C++은 `((unsigned int)low + (unsigned int)high) >> 1` 꼴(원문 게시글에는 닫는 괄호가 하나 더 있는 오타가 있다. 2008-02-17 갱신: 원래 제안한 C 수정이 C99에서 부호 있는 덧셈 오버플로가 정의되지 않은 동작이라 보장되지 않는다는 지적을 반영).
- Bloch: 같은 버그가 병합 정렬과 다른 분할 정복 알고리즘에도 있다. "fix it now before it blows up."
- JDK 버그 보고(JDK-5045582, JDK 1.5.0-beta에서 보고): JDK 코드의 실제 줄은 `int mid = (low + high) >> 1;`(부호 있는 시프트)이었고, 부호 없는 시프트(`>>>`)를 제안했다. 블로그의 `/ 2`와 표기만 다르고 같은 결함이다.

#### 원리 — 어디서부터 넘치나

```text
  int 범위:  -2^31 ........ 0 ........ 2^31 - 1 (= 2,147,483,647)

  루프 안에서는 0 <= low <= high <= n - 1 이므로   low + high <= 2n - 2
  넘치려면  low + high >= 2^31   →   2n - 2 >= 2^31   →   n >= 2^30 + 1

  n = 2^30 + 1 에서 끝 원소를 찾으면 low = high = 2^30 인 순간이 온다
     low + high = 2^31  →  -2^31 (넘침)  →  >> 1  →  -2^30 = -1,073,741,824
```

- 해석(계산): 원문은 "2^30 or greater (roughly)"라고 쓴다. 위 부등식으로는 정확히 2^30개면 아직 넘치지 않고 2^30 + 1개부터 넘칠 수 있다. 아래 실험이 같은 경계를 보인다. "약 10억 개부터"라는 요지는 같다.
- `(low + high) >>> 1`이 맞는 이유: 두 수는 0 이상 2^31 - 1 이하라 합은 0 이상 2^32 - 2 이하다. 32비트 부호 없는 수로는 정확한 값이고, 부호 없는 오른쪽 시프트는 그 값을 2로 나눈다.

#### 실험 D: 가상 배열로 경계 재현 (`MidOverflow.java`)

길이 10억 이상의 실제 배열은 메모리 상한(1GB)을 넘는다. 그래서 `a[i] = i`인 **가상 정렬 배열**을 `get(i)`로 흉내 냈다. `get`은 범위 밖이면 JVM과 같은 문구의 `ArrayIndexOutOfBoundsException`을 직접 던진다. 실제 배열이 아니다.

```java
static long get(int i) {                       // 배열 접근 흉내: 범위 밖이면 JVM 과 같은 예외
    if (i < 0 || i >= n) throw new ArrayIndexOutOfBoundsException("Index " + i + " out of bounds for length " + n);
    return i;
}
static int buggy(long key) {                   // JDK 6 이전 Arrays.binarySearch 와 같은 꼴
    int low = 0, high = (int) n - 1;
    while (low <= high) {
        int mid = (low + high) >> 1;           // JDK-5045582 의 원래 줄
        long v = get(mid);
        if (v < key) low = mid + 1; else if (v > key) high = mid - 1; else return mid;
    }
    return -(low + 1);
}
// fixed(): 같은 코드에서 mid = (low + high) >>> 1
// 크기 2^29, 2^30 - 1, 2^30, 2^30 + 1, Integer.MAX_VALUE 에서 맨 끝 원소(n - 1)를 찾는다
```

(실험, eclipse-temurin:21-jdk = OpenJDK 21.0.12, docker `--network none --cpus=2`, 2026-10-05 — 결정적, 실행마다 같다)

```text
n=536,870,912  buggy -> found@536870911
              fixed -> found@536870911
n=1,073,741,823  buggy -> found@1073741822
              fixed -> found@1073741822
n=1,073,741,824  buggy -> found@1073741823
              fixed -> found@1073741823
n=1,073,741,825  buggy -> AIOOBE: Index -1073741824 out of bounds for length 1073741825
              fixed -> found@1073741824
n=2,147,483,647  buggy -> AIOOBE: Index -536870913 out of bounds for length 2147483647
              fixed -> found@2147483646
lo=1073741824 hi=2147483646  (lo+hi)=-1073741826  (lo+hi)/2=-536870913  (lo+hi)>>>1=1610612735  lo+(hi-lo)/2=1610612735
```

- 관찰: n = 2^30(1,073,741,824)까지는 버그 판도 끝 원소를 찾았다. n = 2^30 + 1에서 처음 `Index -1073741824`가 났다. 위 부등식과 같다.
- 관찰: 마지막 줄처럼 `(lo + hi) / 2`는 음수, `>>> 1`과 `lo + (hi - lo) / 2`는 같은 양수(1,610,612,735)다.
- 관찰: 수정 판은 시험한 다섯 크기 모두에서 끝 원소를 찾았다.
- 해석: 원소 수가 2^30보다 작은 테스트는 이 결함을 원리적으로 못 잡는다. 배열 없이 `lo`·`hi`를 직접 받는 탐색 함수라면 `lo = 10억, hi = 20억` 같은 경계값을 바로 넣어 시험할 수 있다([06-binary-search](../06-binary-search/2-summary.md) 장애 1).

### 사건 2 — Stack Overflow: 공백 자르기 정규식이 홈페이지를 멈춤 (2016-07-20)

출처
- Stack Exchange Network Status, "Outage Postmortem - July 20, 2016" <https://stackstatus.tumblr.com/post/147710624694/outage-postmortem-july-20-2016>. 원 페이지는 브라우저 검사 때문에 스크립트 없이 열리지 않아, Internet Archive 사본(2016년 수집, `stackstatus.net` 주소)의 본문을 읽었다(2026-10-05).

#### 사실 — 타임라인과 원인 (원문)

| 항목 | 원문 |
|---|---|
| 장애 | 2016-07-20, 14:44 UTC부터 34분 |
| 원인 파악 | 10분 |
| 수정 코드 작성 | 14분 |
| 수정 배포(사이트가 다시 열릴 때까지) | 10분 |
| 직접 원인 | 형식이 이상한 글(malformed post) 하나 때문에 정규식 하나가 웹 서버 CPU를 많이 씀 |
| 증폭 | 그 글이 홈페이지 목록에 있어 홈페이지를 볼 때마다 정규식이 실행됨 → 홈페이지가 충분히 빨리 응답하지 못함 → 로드 밸런서의 헬스 체크가 홈페이지라 서버들이 순환에서 빠짐 → 사이트 전체 불가 |

- 정규식: `^[\s\u200c]+|[\s\u200c]+$` — 줄의 앞뒤 유니코드 공백을 자르려는 것. 같은 문제를 보이는 단순한 형태로 원문은 `\s+$`를 든다.
- 입력: 주석 줄(`-- play happy sound for player to enjoy`로 시작) 안의 약 20,000개 연속 공백. 공백 뒤에 다른 문자가 있어 줄 끝이 아니었다.
- 원문의 계산: 엔진은 첫 공백부터 2만 개를 확인하고 실패한 뒤, 두 번째 공백에서 다시 19,999개를 확인하는 식으로 되돌아간다. 원문은 이 확인 횟수를 "20,000+19,999+19,998+…+3+2+1 = 199,990,000"으로 적었다. 같은 합을 계산하면 200,010,000이다(실험 E의 마지막 줄) — 원문의 수치가 조금 어긋나지만 규모(약 2억)는 같다.
- 원문: "This is not classic catastrophic backtracking … (performance is O(n²), not exponential, in length), but it was enough."
- 후속 조치(원문): 정규식을 substring 함수로 교체. 정규식과 글 검증 흐름 감사. 로드 밸런서에 헬스 체크를 끌 수 있는 장치 추가(홈페이지 말고는 접근 가능했을 것이라고 봄). 장애 대응 체크리스트 작성(상태 트위터 알림이 늦었음).

#### 원리 — 실패한 시작 위치마다 끝까지 다시 본다

```text
  입력:  ␣␣␣␣ ... ␣␣␣ x        (공백 n개 뒤에 x — 줄 끝이 아님)
  패턴:  \s+$

  시작 1: ␣␣␣...␣ 를 n개 먹음 → x 는 $ 가 아님 → 되돌아가며 n-1, n-2, ... 개로 줄여 봐도 실패
  시작 2: n-1개 ...                                                     실패
  ...
  시작 n: 1개                                                           실패
  확인 횟수 ≈ n + (n-1) + ... + 1 = n(n+1)/2  →  O(n²)
```

- 한 시작 위치 안에서 "몇 개를 먹을지"를 줄여 가는 시도도 있지만, 공백 다음 글자가 `$`에 맞지 않으므로 각 시도가 바로 실패한다. 비용의 대부분은 시작 위치 n개 × 공백 훑기 n번이다(해석 — 엔진 구현마다 최적화가 다를 수 있다).
- 뒤에서부터 공백을 세는 함수는 끝의 공백 수만큼만 본다. 정규식을 substring 함수로 바꾼 원문의 처방이 이것이다.

#### 실험 E: `\s+$`의 시간 — n 두 배에 약 4배 (`SoRegex.java`)

원문의 엔진(Stack Overflow 쪽)이 아니라 Java `java.util.regex`로 같은 패턴을 재현했다. 입력은 `"-- play happy sound" + 공백 n개 + "x"`, `find()` 한 번의 경과 시간이다.

```java
Pattern simple = Pattern.compile("\\s+$");
Pattern orig = Pattern.compile("^[\\s\\u200c]+|[\\s\\u200c]+$");
for (int n : new int[]{5_000, 10_000, 20_000, 40_000}) {
    String s = "-- play happy sound" + " ".repeat(n) + "x";   // 공백 뒤에 다른 문자: $ 에 못 닿음
    long t0 = System.nanoTime(); boolean m1 = simple.matcher(s).find(); long t1 = System.nanoTime();
    boolean m2 = orig.matcher(s).find(); long t2 = System.nanoTime();
    int end = s.length(); while (end > 0 && Character.isWhitespace(s.charAt(end - 1))) end--;   // 정규식 없이 끝 공백 자르기
    long t3 = System.nanoTime();
    // 출력: 각 단계의 마이크로초
}
```

(실험, eclipse-temurin:21-jdk = OpenJDK 21.0.12, docker `--network none --cpus=2`, 2026-10-05 — 두 번 실행. 시간은 실행마다 다르다. 출력의 "round1"은 각 실행 안의 회차 표시다)

```text
round1 n= 5,000  \s+$  222,832 us (match=false)  원래패턴  284,088 us (match=false)  뒤에서 훑기 190 us
round1 n=10,000  \s+$ 1,029,097 us (match=false)  원래패턴 1,436,887 us (match=false)  뒤에서 훑기 20 us
round1 n=20,000  \s+$ 4,494,743 us (match=false)  원래패턴 3,797,567 us (match=false)  뒤에서 훑기 20 us
round1 n=40,000  \s+$ 15,650,093 us (match=false)  원래패턴 15,370,440 us (match=false)  뒤에서 훑기 15 us
1+2+...+20000 = 200,010,000
round1 n= 5,000  \s+$  190,472 us (match=false)  원래패턴  235,829 us (match=false)  뒤에서 훑기 146 us
round1 n=10,000  \s+$  863,077 us (match=false)  원래패턴 1,003,281 us (match=false)  뒤에서 훑기 13 us
round1 n=20,000  \s+$ 3,928,202 us (match=false)  원래패턴 3,973,558 us (match=false)  뒤에서 훑기 17 us
round1 n=40,000  \s+$ 15,342,571 us (match=false)  원래패턴 15,172,162 us (match=false)  뒤에서 훑기 14 us
```

- 관찰
  - 원문과 같은 공백 2만 개에서 `find()` 한 번이 약 3.7~4.5초였다(`--cpus=2`, 사실 점검 재실행 3.68초 포함).
  - 1만 → 2만 → 4만에서 시간이 약 4배씩(`\s+$`: 1.03 → 4.49 → 15.65초, 두 번째 0.86 → 3.93 → 15.34초) 늘었다. O(n²)의 "두 배에 네 배"다. 사실 점검 재실행(한 번)은 0.21 → 0.77 → 3.68 → 14.52초(두 배마다 3.7·4.8·3.9배)였다. 작은 n 쪽 비율은 실행마다 3.7~4.8배로 흔들렸다(측정 잡음·JIT로 보임).
  - 원래 패턴(`^[\s\u200c]+|[\s\u200c]+$`)도 같은 규모였다. 앞쪽 대안 `^…`은 줄 맨 앞에서만 맞을 수 있어 비용 대부분은 뒤쪽 대안에서 나온다(해석).
  - 결과는 모두 `match=false`(줄 끝 공백이 없음)로 **정답**이다. 결과만 보는 테스트는 통과한다.
  - "뒤에서 훑기"는 끝 글자가 공백이 아니라 즉시 멈췄다(수십~수백 µs). 이 입력에서는 할 일이 거의 없으므로 공정한 속도 비교가 아니다. 요지는 정규식 없이 같은 일을 끝 공백 수에 비례하는 비용으로 할 수 있다는 것이다.
- 해석: 홈페이지를 볼 때마다 4초짜리 일이 생기면, 몇 개의 동시 요청만으로 웹 서버 워커가 다 찬다. 그 결과 **헬스 체크까지** 느려져 로드 밸런서가 정상 서버를 빼냈다. 알고리즘 결함 하나가 운영 설계(무거운 경로를 헬스 체크로 씀)를 만나 전체 장애가 됐다.

### 사건 3 — Cloudflare WAF: `.*(?:.*=.*)`의 과도한 백트래킹 (2019-07-02)

출처
- John Graham-Cumming, "Details of the Cloudflare outage on July 2, 2019", Cloudflare 블로그, 2019-07-12 <https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/>(2026-10-05 열람) — 본문과 부록 "About Regular Expression Backtracking".
- 배포 절차·타임라인·11가지 취약점은 [engineering-practice/20-practice-incidents](../../engineering-practice/20-practice-incidents/2-summary.md) 사건 2가 정본이다. 이 노트는 정규식 알고리즘만 다룬다.

#### 사실 (원문)

- 영향: WAF 관리 규칙에 새 규칙 하나를 배포하자 전 세계 Cloudflare 네트워크에서 HTTP/HTTPS를 처리하는 모든 CPU 코어가 소진됐다. 원문은 서비스 중단을 27분이라고 쓴다.
- 원인으로 지목된 정규식(원문 그대로):

```text
(?:(?:\"|'|\]|\}|\\|\d|(?:nan|infinity|true|false|null|undefined|symbol|math)|\`|\-|\+)+[)]*;?((?:\s|-|~|!|{}|\|\||\+)*.*(?:.*=.*)))
```

- 원문: 핵심 부분은 `.*(?:.*=.*)`다. `(?:`…`)`는 캡처하지 않는 그룹이므로 설명을 위해 `.*.*=.*`로 줄여 볼 수 있다.
- 엔진(원문): Lua로 쓴 WAF가 내부에서 PCRE를 쓰고, PCRE는 백트래킹으로 매칭하며 폭주하는 식을 막는 장치가 없었다.
- 부록의 단계 수(원문. 원문은 단계를 Perl `Regexp::Debugger` 영상으로 보여 준다)

| 패턴 | 입력 | 단계 수 |
|---|---|---|
| `.*.*=.*` | `x=x` | 23 |
| `.*.*=.*` | `x=xx` | 33 |
| `.*.*=.*` | `x=xxx` | 45 |
| `.*.*=.*` | `x=` + x 20개 | 555 |
| `.*.*=.*` | x 20개(`x=` 없음 — 매칭 실패) | 4,067 |
| `.*.*=.*;` | `x=x` | 90 |
| `.*.*=.*;` | `x=` + x 20개 | 5,353 |

- 원문: 해법은 1968년 Ken Thompson의 논문 "Programming Techniques: Regular expression search algorithm"부터 알려져 있다 — 정규식을 NFA로 바꾸고 상태 전이를 따라가 입력 길이에 선형인 시간에 매칭한다.
- 후속 조치(원문, 정규식 관련): 제거됐던 정규식 CPU 보호 장치 복구, WAF 관리 규칙 3,868개 수동 점검, 테스트 묶음에 규칙별 성능 프로파일링, "re2 or Rust regex engine which both have run-time guarantees"로 전환(ETA 7월 31일).

#### 원리 — 겹치는 `.*`가 분할 방법을 전부 시도한다

```text
  패턴 .*.*=.*  ,  입력 xxxxxxxx (= 없음, 길이 n)

  find() 는 시작 위치 s = 0, 1, ..., n 마다 시도한다
    첫 .*  : 남은 글자 m 개 중 몇 개를 먹나       m+1 가지 (욕심: 많이부터)
    둘째 .* : 그 나머지 중 몇 개를 먹나            최대 m+1 가지
    = : 매번 실패 → 되돌아감
  한 시작 위치의 시도 ≈ m²/2,  전체 ≈ Σ m²/2 ≈ n³/6   →  O(n³)
```

- 해석: 위는 단순화한 셈이다. 실제 엔진의 최적화에 따라 상수와 차수가 달라질 수 있다. 원문의 표에서도 매칭 실패 입력(4,067단계)이 매칭 성공 입력(555단계)보다 훨씬 비싸다 — 실패하면 모든 분할을 다 시도하고서야 끝나기 때문이다.
- `.*.*=.*;`처럼 끝에 글자 하나를 더 요구하면, 매칭이 될 듯하다가 마지막에 실패하는 경우가 늘어 단계가 더 는다(원문 90 대 23, 5,353 대 555).
- Thompson 방식(RE2·RE2J·Rust regex)은 "지금 가능한 NFA 상태의 집합"을 한 글자씩 옮긴다. 상태 수는 패턴 크기로 정해지므로 시간은 입력 길이 × 패턴 크기에 비례한다. 대신 역참조(`\1`)와 전후방 탐색(`(?=…)`)을 지원하지 않는다(RE2 문법 문서 "NOT SUPPORTED").

#### 측정 — Java로 같은 패턴 (다른 노트의 실험)

이 노트에서 새로 돌리지 않았다. [engineering-practice/20-practice-incidents](../../engineering-practice/20-practice-incidents/2-summary.md) 실험 B(OpenJDK 21.0.12 + RE2J 1.8, `--cpus=1`, 2026-10-05)의 값을 옮긴다. 입력은 모두 매칭 실패.

| 패턴 / 입력 | n=1,000 | n=2,000 | 두 배에 |
|---|---|---|---|
| `.*.*=.*` / `x`…(n+1자) — java.util.regex | 2.66초 (재실행 2.37·2.49초) | 19.5초 (재실행 19.2·19.1초) | 약 7~8배 |
| 원본 정규식 / 숫자 `1`을 n+1개 — java.util.regex | 3.50초 (재실행 6.11초) | 27.97초 (재실행 48.79초) | 약 8배 |
| 위 모든 입력 — RE2J | 3.5 ms 이하 | 3.5 ms 이하 | 거의 그대로 |

- 해석: 두 배에 약 8배는 위 그림의 O(n³)과 맞는다. 같은 원본 정규식도 입력 모양에 따라 수십 ms(`"x…`)와 수십 초(`1…`)로 갈렸다 — 원본 패턴의 첫 그룹(`\d` 등)에 걸리는 시작 위치가 많을수록 시도가 늘기 때문으로 보인다(그 노트의 해석).

### 세 사건을 나란히 (해석)

| | Bloch 2006 | Stack Overflow 2016 | Cloudflare 2019 |
|---|---|---|---|
| 알고리즘 | 이진 탐색 | 백트래킹 정규식 `\s+$` | 백트래킹 정규식 `.*(?:.*=.*)` |
| 깨진 가정 | `low + high`가 `int`에 들어간다 | 공백 구간이 짧다 | 규칙이 입력 길이에 무난한 시간에 끝난다 |
| 차수·경계 | n ≥ 2^30 + 1에서 넘침 | O(n²) (원문) | 다항, 두 배에 약 8배(측정) |
| 결과 | 예외(Java)·정의되지 않은 동작(C) | 결과는 정답, 시간만 폭증 | 결과는 정답, 시간만 폭증 |
| 왜 테스트가 못 잡았나 | 그 크기의 배열을 만들지 않음 | 결과만 확인, 긴 공백 입력 없음 | 원문: 과다 CPU를 식별할 방법이 테스트에 없었음 |
| 증폭 | 라이브러리 → 모든 호출자 | 홈페이지 목록 → 헬스 체크 → 전체 이탈 | 전역 즉시 배포 → 전 세계 PoP |
| 처방 | `>>> 1`, `lo + (hi - lo)/2` | substring 함수 | 보호 장치 복구, 성능 프로파일링, 선형 엔진 |

- 세 사건 모두 **입력의 크기·모양이 가정 밖으로 나갈 때만** 터졌다. 평소의 테스트와 운영 입력은 가정 안에 있었다.
- 정규식 두 사건은 결과가 맞았다. 정확성 테스트는 통과하고 시간만 폭증한다. [42-alg-symptom-index](../42-alg-symptom-index/2-summary.md) 4절이 "시간을 재야 보인다"고 적는 이유다.
- 정규식 두 사건 모두 증폭 경로가 있었다. Stack Overflow는 헬스 체크, Cloudflare는 전역 배포다. 알고리즘 결함의 크기보다 **노출 범위**가 피해를 정했다(운영 관점은 [engineering-practice/20](../../engineering-practice/20-practice-incidents/2-summary.md)).

## 쓰이는 자료구조·알고리즘

- **이진 탐색과 불변식**: `0 <= low <= high <= n - 1`이 중간값 계산의 범위를 정한다 — [06-binary-search](../06-binary-search/2-summary.md). 같은 계산이 병합 정렬의 중간점에도 있다([02-merge-sort](../02-merge-sort/2-summary.md) 장애 3).
- **2의 보수 정수와 시프트**: `>>`(산술, 부호 유지)와 `>>>`(논리, 0 채움) — [29-bit-manipulation](../29-bit-manipulation/2-summary.md).
- **백트래킹**: 선택지를 하나씩 시도하고 실패하면 되돌아가는 전수 탐색 — [13-backtracking](../13-backtracking/2-summary.md). 정규식 엔진의 최악은 분할 방법 수만큼 시도한다.
- **NFA 시뮬레이션(Thompson 1968)**: 상태 집합을 한 글자씩 옮기는 선형 시간 매칭. 유한 오토마톤 위의 BFS와 같은 모양이다 — [26-aho-corasick](../26-aho-corasick/2-summary.md)(여러 패턴 오토마톤), [25-string-matching](../25-string-matching/2-summary.md)(KMP 실패 함수).
- **쓰이는 곳(🔧)**: 표준 라이브러리의 탐색·정렬(`Arrays.binarySearch`), 입력 정규화(공백 자르기), WAF·로그 파서·입력 검증의 정규식 규칙.

## 적용 — 풀어나가는 법

### 1. 내 코드로 옮길 점검 목록

| 점검 질문 | 사건 근거 | 처방 | leaf |
|---|---|---|---|
| 두 인덱스·오프셋의 합을 `int`로 계산하는 곳이 있나? 값이 2^30 근처까지 갈 수 있나? | Bloch 2006 | `(lo + hi) >>> 1`, `lo + (hi - lo) / 2`, `Math.addExact`로 넘침을 예외로 | [06-binary-search](../06-binary-search/2-summary.md) |
| 정규식이 외부 입력(글·본문·헤더·로그)에 걸리나? 입력 길이에 상한이 있나? | Stack Overflow 2016 | 길이 상한, 문자열 함수로 대체 | [13-backtracking](../13-backtracking/2-summary.md) |
| 패턴에 `.*`가 이어지거나 중첩 수량자(`(a+)+`)·겹치는 대안이 있나? | Cloudflare 2019 · ReDoS | 패턴 재작성, 선형 엔진 | [42-alg-symptom-index](../42-alg-symptom-index/2-summary.md) 4절 |
| 정규식 규칙 테스트가 결과뿐 아니라 **시간**도 보나? | Cloudflare 원문(테스트에 CPU 식별 수단 없음) | 적대적 입력 + 시간 예산 | [engineering-practice/20](../../engineering-practice/20-practice-incidents/2-summary.md) 실험 C |
| 헬스 체크가 무거운 경로(홈페이지·DB 질의)를 타나? | Stack Overflow 2016 | 가벼운 전용 헬스 엔드포인트 | [reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md) |

### 2. 정규식 위험 진단 — 길이를 두 배씩

```bash
# 의심 입력을 로그에서 꺼낸 뒤, 그 모양을 유지한 채 길이만 두 배씩 늘려 시간을 잰다
for n in 1000 2000 4000 8000; do
  python3 -c "print('-- c' + ' '*$n + 'x')" > in.$n.txt
done
# 앱과 같은 엔진(java.util.regex 등)으로 find() 시간을 재고 비율을 본다:
#   약 2배 = 선형, 약 4배 = O(n²), 약 8배 = O(n³), 한 글자에 2배 = 지수
```

- 위 셸은 입력 파일만 만든다. 시간은 앱과 **같은 엔진**으로 재야 한다. 엔진마다 최적화가 달라 같은 패턴도 차수가 다를 수 있다.
- 처방 순서: ① 정규식이 꼭 필요한가(공백 자르기·접두사 확인은 `String.strip`·`startsWith`) ② 입력 길이 상한 ③ 패턴을 겹치지 않게(`.*` 대신 `[^=]*`처럼 다음 글자를 배제 — 차수는 줄지만 `find()`에서는 여전히 선형이 아닐 수 있다, 실험 F) ④ 선형 엔진 ⑤ 매칭 시간 예산.

### 3. 코드 — Java 21

```java
import java.util.regex.*;

final class Safe {
    // 사건 1: 중간값
    static int mid(int lo, int hi) { return (lo + hi) >>> 1; }            // lo, hi >= 0 일 때
    static long midLong(long lo, long hi) { return lo + (hi - lo) / 2; }  // 음수도 되지만 hi - lo가 long 안에 들 때만 (MIN_VALUE~MAX_VALUE면 넘친다)

    // 사건 2: 끝 공백 자르기는 정규식 없이 (Java 11+)
    static String trimUnicode(String s) { return s.strip(); }             // Character.isWhitespace 기준

    // 사건 3: "어딘가에 = 가 있나"가 의도라면 정규식이 필요 없다
    static final Pattern RISKY = Pattern.compile(".*.*=.*");               // 실패 입력에서 약 O(n³)
    static final Pattern LESS  = Pattern.compile("[^=]*=");                // 겹침 제거: 약 O(n²) (실험 F)
    static boolean hasEquals(String in) { return in.indexOf('=') >= 0; }   // 선형

    // 외부 입력에 쓰기 전 길이 상한 (값은 예시)
    static boolean matchesBounded(Pattern p, String in) {
        if (in.length() > 8_192) throw new IllegalArgumentException("input too long: " + in.length());
        return p.matcher(in).find();
    }
}
```

- `String.strip()`은 `Character.isWhitespace` 기준이다. 원래 패턴은 `\s`와 별도로 `\u200c`(zero-width non-joiner)를 넣었다. Java에서는 그 문자가 공백으로 분류되지 않는다. OpenJDK 21.0.12에서 확인(`Ws.java`): `Character.isWhitespace(0x200C) = false`, `"\u200c".strip().length() = 1`, `Pattern.matches("\\s", "\u200c") = false`. 그것까지 잘라야 하면 직접 루프에서 함께 검사한다. 공백 집합도 다르다. .NET 정규식의 `\s`는 유니코드 구분자(`\p{Z}`)를 포함해 U+00A0(줄 바꿈 없는 공백)도 공백으로 본다(Microsoft .NET 문서 "Character classes in regular expressions" — 원래 서비스가 .NET 엔진을 썼다는 것은 사후 보고에 직접 없다 [?]). Java의 `Character.isWhitespace`는 U+00A0·U+2007·U+202F를 빼므로(Javadoc) `strip()`이 이들을 남긴다(같은 21.0.12 확인: 세 문자 모두 `isWhitespace = false`, `strip()` 길이 1). 원래 동작과 똑같이 하려면 이 차이도 루프에서 처리한다.
- `LESS`는 `RISKY`와 의미가 같지 않을 수 있다. 바꿀 때는 기존 규칙의 정상·공격 입력 모음으로 결과가 같은지 확인한다.
- 겹침을 없애도 `find()`는 시작 위치마다 다시 시도한다. `[^=]*=`는 시작 위치마다 남은 글자를 다 먹고 `=`를 못 찾아 되돌아가므로, `=`가 없는 입력에서 전체가 약 O(n²)이다(아래 실험 F). 차수를 줄인 것이지 선형 보장이 아니다.

#### 실험 F: 겹침을 없앤 패턴과 정규식 없는 판정 (`Safer.java`)

입력은 `x`를 n+1개(`=` 없음, 매칭 실패). `.*.*=.*`는 n ≤ 2,000에서만 돌렸다.

(실험, eclipse-temurin:21-jdk = OpenJDK 21.0.12, docker `--network none --cpus=2`, 2026-10-05 — 두 번 실행. 첫 실행)

```text
n= 1,000  .*.*=.*  2,741,559 us  [^=]*=   151,513 us (false)  indexOf    40 us (false)
n= 2,000  .*.*=.* 20,220,919 us  [^=]*=    26,041 us (false)  indexOf     3 us (false)
n= 4,000  .*.*=.*    (생략)      [^=]*=   104,396 us (false)  indexOf     2 us (false)
n= 8,000  .*.*=.*    (생략)      [^=]*=   399,593 us (false)  indexOf    15 us (false)
n=16,000  .*.*=.*    (생략)      [^=]*= 1,589,230 us (false)  indexOf    18 us (false)
```

두 번째 실행: `.*.*=.*` 2,611,211 → 18,654,405 us, `[^=]*=` 144,602 · 24,507 · 90,852 · 392,237 · 1,491,028 us, `indexOf` 1~17 us.

- 관찰: `.*.*=.*`는 1,000 → 2,000에 약 7배(2.6~2.7초 → 18.7~20.2초). `[^=]*=`는 2,000 → 4,000 → 8,000 → 16,000에서 두 배마다 약 3.7~4.3배로, 제곱에 가깝게 늘었다. `indexOf`는 16,000자에서도 수십 µs 이하였다.
- 관찰: `[^=]*=`의 n=1,000 값(145~152 ms)이 n=2,000(25~26 ms)보다 큰 것은 첫 호출의 JIT 워밍업으로 보인다(해석). 비율은 2,000 이후로 본다.
- 해석: 패턴을 고치면 차수가 내려가지만, 백트래킹 엔진 + `find()` 조합에서 선형을 보장받으려면 정규식을 쓰지 않거나 선형 엔진을 쓴다.
- 길이 상한 8,192는 예시 값이다.

## 장애 시나리오와 대처

### 1. 오래된 `int` 계산이 데이터 성장으로 넘친다 — Bloch형

- **현상**: 수년 잘 돌던 탐색·정렬·페이지 계산이 데이터가 커진 뒤 특정 요청에서만 예외를 낸다.
- **보이는 형태**: 음수 인덱스의 `ArrayIndexOutOfBoundsException`(실험 D: `Index -1073741824 out of bounds for length 1073741825`). C·C++이면 크래시 또는 조용히 틀린 값.
- **원인**: 두 `int`의 합(`lo + hi`, `offset + length`)이 2^31 - 1을 넘었다. 테스트 데이터가 그 크기에 닿지 않았다.
- **대처**: `>>> 1`·`lo + (hi - lo) / 2`·`long`·`Math.addExact`. 배열 없이 경계값을 넣어 보는 테스트를 둔다. 표준 라이브러리(`Arrays.binarySearch`, JDK 6부터 수정)를 쓴다.

### 2. 사용자 입력 + 백트래킹 정규식 — 다항 폭주

- **현상**: 특정 글·요청 하나가 들어온 뒤 웹 서버 CPU가 오르고 응답이 느려진다. 그 글을 지우면 회복한다.
- **보이는 형태**: 덤프 맨 위가 `java.util.regex.Pattern$…`(Java) 또는 엔진 함수. 그 입력에 긴 반복 구간(공백 2만 개)이 있다. 결과는 매칭 실패로 정상이다.
- **원인**: 실패한 시작 위치마다 반복 구간을 다시 훑는 패턴(`\s+$`) — O(n²). 원문 표현대로 "catastrophic"(지수)이 아니어도 충분히 멈춘다.
- **대처**: 정규식을 문자열 함수로 바꾸거나, 입력 길이 상한을 둔다. 저장 시점에 입력을 정규화해(긴 공백 축약) 읽을 때마다 무거운 일을 하지 않게 한다.

### 3. 무거운 경로를 헬스 체크로 씀 — 부분 장애가 전체 장애로

- **현상**: 페이지 하나가 느려졌는데 사이트 전체가 접속 불가가 된다.
- **보이는 형태**: 로드 밸런서 로그에 백엔드 서버들이 연달아 unhealthy로 빠진다. 서버 프로세스는 살아 있고, 다른 경로는 직접 요청하면 응답한다.
- **원인**: 헬스 체크가 홈페이지처럼 무거운 경로를 탔다. 그 경로만 느려져도 서버들이 "죽음"으로 판정됐다(Stack Overflow 원문의 판단: 헬스 체크가 아니었다면 홈페이지 외에는 접근 가능했을 것).
- **대처**: 헬스 체크는 프로세스 생존과 핵심 의존성만 보는 가벼운 엔드포인트로. 모든 백엔드가 동시에 실패하면 이탈시키지 않는 등 헬스 체크 자체의 실패 모드를 설계한다(운영 쪽 정본: [reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md)).

### 4. 선형 엔진으로 바꿨더니 일부 규칙이 컴파일되지 않는다

- **현상**: 백트래킹 폭주를 막으려 RE2 계열로 바꾸자 일부 패턴이 오류를 내거나 결과가 달라진다.
- **보이는 형태**: 패턴 컴파일 오류(역참조 `\1`, 전방 탐색 `(?=…)` 등). 또는 같은 입력에서 매칭 위치가 다르다.
- **원인**: 선형 시간 보장을 위해 RE2는 역참조·전후방 탐색을 지원하지 않는다(문법 문서 "NOT SUPPORTED"). 엔진마다 문법·의미 차이가 있다.
- **대처**: 전환 전에 기존 규칙 전부를 새 엔진으로 컴파일해 보고, 정상·공격 입력 모음으로 결과를 대조한다. 지원 안 되는 패턴은 재작성하거나 별도 경로(시간 예산을 건 백트래킹 엔진)로 둔다.

### 5. 정답만 보는 테스트 — 시간을 재지 않음

- **현상**: 규칙 변경이 리뷰·CI를 다 통과하고 배포된 직후 CPU가 치솟는다.
- **보이는 형태**: CI 로그에 실패 없음. 테스트 실행 시간도 이전과 비슷하다(Cloudflare 원문: 이전 빌드 로그에서도 테스트 실행 시간 증가가 관찰되지 않았다).
- **원인**: 테스트 입력이 짧아 다항 폭주가 보이지 않았고, 테스트가 매칭 결과만 확인했다.
- **대처**: 규칙마다 적대적 입력(긴 반복, 매칭 실패, 구분자 없음)으로 시간 예산을 검사한다. 길이를 두 배로 늘린 입력에서 비율도 본다(적용 2).

## 핵심 문장

- Bloch(2006): 증명된 이진 탐색도 `int mid = (low + high) / 2`가 2^31을 넘으면 깨진다. JDK의 같은 결함은 2004년에 보고돼 JDK 6에서 고쳐졌고, 실험에서 n = 2^30 + 1부터 음수 인덱스가 났다.
- Stack Overflow(2016-07-20): 공백 약 2만 개가 든 글 하나에 `\s+$` 꼴 정규식이 O(n²)으로 돌았고, 그 페이지가 헬스 체크라 34분 전체 장애가 됐다. Java로 재현하면 공백 2만 개에 약 4초, 두 배에 약 4배였다.
- Cloudflare(2019-07-02): `.*(?:.*=.*)`의 겹치는 `.*`가 분할 방법을 전부 시도해 PCRE 백트래킹이 폭주했다. 원문의 단계 수는 x 20개짜리 실패 입력에 4,067이었고, Java 측정은 두 배에 약 8배였다.
- 정규식 두 사건은 결과가 맞았다. 정확성 테스트로는 안 보이고 시간을 재야 보인다.
- 세 사건 모두 입력의 크기·모양이 가정 밖으로 나갈 때만 터졌다. 경계 너머 입력을 테스트에 일부러 넣고, 피해 범위는 노출 범위(헬스 체크, 전역 배포)가 정했다.

## 관련 주제·근거

- 선행: [42-alg-symptom-index](../42-alg-symptom-index/2-summary.md) 4·5절 · [06-binary-search](../06-binary-search/2-summary.md) 장애 1·2 · [13-backtracking](../13-backtracking/2-summary.md) 장애 1 · [02-merge-sort](../02-merge-sort/2-summary.md) 장애 3
- 같은 사건의 다른 관점: [engineering-practice/20-practice-incidents](../../engineering-practice/20-practice-incidents/2-summary.md)(Cloudflare 배포 절차·11가지 취약점·RE2J 측정·CI 시간 예산 실험)
- 자료구조 실사건: [data-structure/44-ds-incidents](../../data-structure/44-ds-incidents/2-summary.md)(HashDoS — 같은 "입력이 평균 가정을 깬다" 모양)
- 운영: [reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md) · [reliability/35-timeout-design-worksheet](../../reliability/35-timeout-design-worksheet/2-summary.md)
- 1차 출처
  - Joshua Bloch, "Extra, Extra - Read All About It: Nearly All Binary Searches and Mergesorts are Broken", 2006-06-02(2008-02-17 갱신) <https://research.google/blog/extra-extra-read-all-about-it-nearly-all-binary-searches-and-mergesorts-are-broken/>
  - JDK-5045582 <https://bugs.openjdk.org/browse/JDK-5045582> · JDK-6412541 <https://bugs.openjdk.org/browse/JDK-6412541>
  - Stack Exchange Network Status, "Outage Postmortem - July 20, 2016" <https://stackstatus.tumblr.com/post/147710624694/outage-postmortem-july-20-2016> (Internet Archive 사본으로 열람)
  - John Graham-Cumming, "Details of the Cloudflare outage on July 2, 2019", 2019-07-12 <https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/>
  - Ken Thompson, "Programming Techniques: Regular expression search algorithm", Communications of the ACM, 1968 — Cloudflare 원문이 인용한 범위만 확인
  - RE2 문법 문서 <https://github.com/google/re2/wiki/Syntax>
- 실험 목록
  - D. 이진 탐색 중간값 오버플로(가상 배열): `scratchpad/dsa/syn/e1/MidOverflow.java`, `docker run --rm --pull never --network none --cpus=2 -u $(id -u):$(id -g) -e HOME=/tmp -v <dir>:/w -w /w eclipse-temurin:21-jdk java MidOverflow.java`(OpenJDK 21.0.12). 결정적 출력. 실제 10억 원소 배열이 아니라 범위 검사를 흉내 낸 `get(i)`다.
  - E. `\s+$`·원래 패턴의 시간: `scratchpad/dsa/syn/e1/SoRegex.java`, 같은 명령(`timeout 90`) 두 번. 시간은 실행마다 다르다. Stack Overflow가 쓴 엔진이 아니라 Java `java.util.regex`다.
  - F. 겹침 제거 패턴·`indexOf` 비교: `scratchpad/dsa/syn/e4/Safer.java`, 같은 명령(`timeout 120`) 두 번. 시간은 실행마다 다르다.
  - `\u200c` 공백 판정: `scratchpad/dsa/syn/e4/Ws.java`, 같은 이미지 `--cpus=1`. 결정적.
  - Cloudflare 정규식의 Java·RE2J 시간은 [engineering-practice/20](../../engineering-practice/20-practice-incidents/2-summary.md) 실험 B에서 옮겼다(새로 돌리지 않음).
