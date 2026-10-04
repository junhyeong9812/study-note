# engineering-practice/18-engineering-virtues — 게으름·조급함·오만: 원문 대조와 실천 판별 — 정리 (힌트)

## 해결하는 문제

엔지니어링 실천(CI·빌드 캐시·문서·리뷰)은 도구만으로 굴러가지 않는다. **무엇을 참지 말아야 하나**를 정하는 태도가 먼저 있다.

```text
  같은 짜증                           어디로 향하나                   결과
  "이 배포 체크리스트 또 해야 해?"  ─┬─▶ 지금 내 수고 → 건너뛴다          사고
                                    └─▶ 앞으로의 총 수고 → 스크립트로   자동화
  "CI가 20분이나 걸려"             ─┬─▶ 리뷰어·동료 → 재촉·검증 생략    팀 마찰·사고
                                    └─▶ 기계 → 캐시·병렬화             빠른 피드백
```

- Larry Wall은 『Programming Perl』 용어집에서 *게으름(laziness)*·*조급함(impatience)*·*오만(hubris)*을 프로그래머의 세 미덕이라 불렀다. 셋 다 보통은 악덕인 말이다.
- 이 노트는 원본 노트를 이어받는다. 세 미덕의 뜻·견제 관계·실패 모드 표는 [원본 foundations/three-virtues](../../foundations/three-virtues/2-summary.md)에 있다.
- 여기서 보태는 것은 셋이다.
  - 원문을 직접 대조해, 원본의 해석 가운데 원문으로 확인되는 것과 안 되는 것을 가른다.
  - 게으름의 판별 질문("총량을 계산했나")을 실제 계산으로 보인다.
  - 이 영역의 실천(01~17번)과 세 미덕을 잇는다.

쉬운 예: 연기 감지기다.
- 감지기가 울리면 짜증이 난다. 배터리를 빼 버리면 조용해지지만, 진짜 불이 났을 때도 조용하다.
- 감지기를 끄지 않고 **왜 울렸는지**(요리 연기인지, 진짜 불인지)를 읽는다.

똑같은 구조다.\
반복 작업의 짜증, 느린 빌드에 대한 분노, 남이 내 코드를 볼 때의 부끄러움은 끄면 안 되는 감지기다. 원본은 이를 "이미 작동하는 감지 센서"라고 불렀다.

실무 예:
- 매주 손으로 하던 배포 체크리스트를 스크립트로 바꾼다. 아래 계산의 예시 값이면 3주째에 들인 시간을 되찾는다(실측이 아닌 계산).
- "오만이 미덕"이라는 말을 무례한 리뷰의 핑계로 쓰는 사람이 있다. 원문 정의를 보면 그 쓰임은 맞지 않는다.

## 동작·원리

### 1. 원문의 세 정의 — 과녁이 문장 안에 있다

```text
  미덕       원문의 핵심 구절(perlglossary)                         과녁            낳는 것
  게으름     "reduce overall energy expenditure"                    전체 수고        노동 절약 프로그램 + 문서
  조급함     "the anger you feel when the computer is being lazy"   컴퓨터           요구를 예측하는 프로그램
  오만       "programs that other people won't want to say          남의 평가        남이 욕하지 않을 프로그램
             bad things about"                                      (와 유지보수)    (을 쓰고 유지보수)
```

- 정의 원문은 Perl 배포판 문서 perlglossary에 있다. 현재판은 "『Programming Perl』 4판 용어집에서 가져왔다"고 머리에 밝힌다.
- 과녁이 정의 문장 안에 들어 있다.
  - 게으름의 단위는 "overall"(전체)이다. 지금 나의 수고가 아니다.
  - 조급함이 화내는 대상은 "the computer"다. 사람이 아니다.
  - 오만의 기준은 "other people"이다. 자기 만족이 아니다. 그리고 "(and maintain)"이 붙어 있다.
- 게으름 정의에는 "document what you wrote so you don't have to answer so many questions about it"이 들어 있다. 문서화가 게으름에 속한다는 원본의 해석은 이 구절로 확인된다.
    - 흔한 오해: 프로그래밍의 *지연 평가(lazy evaluation)* 와 같은 뜻이다. 지연 평가는 값이 필요할 때까지 계산을 미루는 평가 전략이고, Wall의 게으름은 전체 수고를 줄이려 지금 수고를 들이는 태도다. 이름만 같다.

### 실험: 원문 대조 — 두 판의 perlglossary

원본 노트는 원문을 옮기지 않고 요지만 풀었다. 그래서 원문 자체를 받아 비교했다.
- 옛 판: perl 5.8.8 배포판의 `pod/perlglossary.pod`(끝에 "Based on the Glossary of Programming Perl, Third Edition"이라고 적혀 있다).
- 현재판: perlfaq 배포판 5.20250619의 `lib/perlglossary.pod`(머리에 "4판 용어집에서 가져옴").
- 세 항목만 뽑아 단어 단위로 비교했다. POD 서식 표기(`L<>`·`B<>`·색인용 `X<>`)와 곧은/굽은 따옴표 차이는 추출 단계에서 지웠으므로 비교 대상이 아니다.

```sh
# extract.sh 핵심 — POD에서 =item laziness 같은 항목 본문을 한 줄로 뽑는다
awk -v w="$w" '/^=item /{ on = (tolower($0) ~ "^=item (b<)?" w "(>)?$"); next }
               on && /^=/ { on=0 }  on { printf "%s ", $0 }' "$1"
# 비교
git diff --no-index --word-diff=plain old.txt new.txt
```

(실험, git 2.43.0 · metacpan에서 받은 POD 두 개, 2026-10-05)

```text
== 단어 단위 차이 (old → new)
[laziness] The quality that makes you go to great effort to reduce overall energy expenditure. It makes you write labor-saving programs that other people will find useful, and {+then+} document what you wrote so you don't have to answer so many questions about it. Hence, the first great virtue of a programmer. Also hence, this book. See also impatience and hubris.
[impatience] The anger you feel when the computer is being lazy. This makes you write programs that don't just react to your needs, but actually anticipate them. Or at least that pretend to. Hence, the second great virtue of a programmer. See also laziness and hubris.
[hubris] Excessive pride, the sort of thing {+for which+} Zeus zaps [-you for.-]{+you.+} Also the quality that makes you write (and maintain) programs that other people won't want to say bad things about. Hence, the third great virtue of a programmer. See also laziness and impatience.
```

- 관찰
  - 두 판의 차이는 "then" 한 단어와 "Zeus zaps you for" → "for which Zeus zaps you" 어순뿐이다. 세 정의의 뜻은 판이 바뀌어도 같다.
  - 게으름 항목 끝에 "Also hence, this book."이 있다. 책을 쓴 것 자체가 게으름(같은 질문에 답하지 않으려고 문서를 씀)의 산물이라는 농담이다.
  - 조급함 항목의 "Or at least that pretend to."는 원본 노트의 "(최소한 예측하는 척이라도 하는)"과 맞는다.
- 확인 못 한 것: 세 미덕이 『Programming Perl』 몇 판에 처음 실렸는지. 원본 「더 알면 좋은 것」의 "초판(1991)부터 등장"은 이번에 확인하지 못했다 `[?]`. 웹의 2차 글에는 "첫 줄은 1판, 나머지는 2판"이라는 말도 있으나 1차 출처로 확인하지 못했다.

### 2. 공동체의 미덕 — 원문은 "반대가 아니다"

Wall은 1999년 『Open Sources』(O'Reilly)에 실린 글 "Diligence, Patience, and Humility"에서 이렇게 썼다(oreilly.com 공개본).

```text
  "These are virtues of passion. They are also virtues of an individual.
   They are not, however, virtues of community. The virtues of community
   sound like their opposites: diligence, patience, and humility.
   They're not really opposites, because you can do them all at the same time."
```

```text
  개인의 미덕(열정)        공동체의 미덕
  게으름   ◀─ 반대처럼 들림 ─▶  근면
  조급함   ◀──────────────▶  인내
  오만     ◀──────────────▶  겸손
           ↑ 원문: "반대가 아니다 — 동시에 할 수 있다"
```

- 참고: 원본 「반대 짝」은 결론을 "둘 중 뭐가 맞나가 아니라 언제 어느 쪽을 꺼내 쓰나"로 맺는다. 원문은 한 걸음 더 간다. 둘은 **동시에** 할 수 있다고 쓴다. 예: 빌드 대기에 조급해하면서(기계), 그 빌드를 고치는 동료의 리뷰는 인내심 있게 기다린다(사람). 과녁이 다르면 함께 성립한다.
- 원본 같은 절의 "공동체가 상반된 가치를 동시에 품지 못한다고 생각한다면 Perl을 더 겪어 보라"도 원문에 있다: "If you think a single community can't embrace opposing values, then you should spend more time with Perl." 같은 글은 "There's more than one way to do it. This is true in Perl. It's also true of Perl."이라고도 쓴다.

### 3. 게으름의 판별 — 총량을 실제로 계산한다

원본의 판별 질문은 "지금 아끼는 수고와 나중에 치를 수고를 둘 다 계산했는가?"다. 이를 그대로 계산으로 옮겼다. 실험이라기보다 **계산**이고, 입력 값은 모두 예시다.

```java
// BreakEven.java 핵심 — 수작업 누적 vs (자동화 제작 + 유지 + 남는 수작업) 누적
static int breakEvenWeek(double manualMin, double perWeek, double buildHours,
                         double upkeepHoursPerWeek, double residualMin, int horizon) {
    double manual = 0, auto = buildHours * 60;
    for (int w = 1; w <= horizon; w++) {
        manual += manualMin * perWeek;
        auto += upkeepHoursPerWeek * 60 + residualMin * perWeek;
        if (auto <= manual) return w;
    }
    return -1;   // 기간 안에 이득 없음
}
```

(계산, JDK 21 temurin 21.0.12, `java BreakEven.java`, 2026-10-05 — 입력은 예시)

```text
작업                      수작업  횟수/주  만들기  유지/주  남는수작업 | 손익분기(주, 52주 안)
배포 체크리스트 실행               30분    5.00    6.0h   0.25h        2분 | 3주
분기 1회 보고서 정리              60분    0.08    8.0h   0.00h        5분 | 이득 없음
신규 입사자 환경 설정             240분    0.25   16.0h   0.50h       30분 | 43주
같은 질문 답하기 → 문서            10분    6.00    3.0h   0.10h        1분 | 4주
```

- 관찰
  - 자주 하는 일(배포 체크리스트·같은 질문)은 몇 주 만에 이득이다. "같은 질문 → 문서"는 원문 정의의 "document what you wrote"를 숫자로 본 것이다.
  - 드문 일(분기 보고서)은 1년 안에 본전을 못 찾는다. 원본 실패 모드 표의 "한 번 할 일을 자동화"가 이것이다.
  - 신규 입사자 설정은 43주다. 숫자만 보면 애매하다. 그러나 이 계산에는 실수 방지·대기 시간 같은 효과가 빠져 있다. 계산은 판단의 재료이지 판단 자체가 아니다.

## 쓰이는 자료구조·알고리즘

- **분할 상환(amortization)**: 게으름의 계산은 "한 번 크게 내고 이후 매번 덜 내는" 구조다. 동적 배열이 가끔 큰 복사를 해서 평균 삽입 비용을 O(1)로 맞추는 분할 상환 분석과 같은 모양이다([data-structure/01-dynamic-array](../../data-structure/01-dynamic-array/)). 다른 점: 자동화는 미래 횟수가 불확실하다. 그래서 위 계산처럼 기간(horizon)을 정해 본다.
- **메모이제이션·캐시**: "같은 계산을 두 번 하지 않는다"는 게으름의 알고리즘 판이다. 동적 계획법([algorithm/21-dp-basics](../../algorithm/21-dp-basics/)), 빌드 캐시([07-build-systems-and-reproducibility](../07-build-systems-and-reproducibility/2-summary.md)).
- **피드백 루프 지연**: 조급함의 과녁은 대기 시간이다. 루프 한 바퀴(수정 → 빌드 → 테스트 → 결과)가 짧을수록 같은 시간에 더 많이 배운다. 증분 빌드·병렬 테스트가 이 지연을 줄인다.
- **예측(프리페치)**: 원문의 "anticipate"는 요청 전에 미리 해 두는 것이다. 캐시 워밍·프리페치가 그 예다.

## 적용 — 풀어나가는 법

### 1. 세 미덕을 이 영역의 실천에 잇기

| 미덕 | 과녁 | 이 영역의 실천 | 판별 질문 |
|---|---|---|---|
| 게으름 | 전체 수고 | CI/CD(06)·빌드 캐시(07)·문서(11)·회고 행동 자동화([01](../01-lifecycle-and-agile/2-summary.md)) | 손익분기가 기간 안에 오나? |
| 조급함 | 기계의 대기 | 빌드 시간 줄이기(07)·작은 PR로 리뷰 대기 줄이기(05) | 화내는 대상이 기계인가, 사람인가? |
| 오만 | 남의 평가 + 유지보수 | 리뷰 전 셀프 리뷰(05)·추적 가능한 요구([02](../02-requirements-engineering/2-summary.md))·운영 책임 | 기준이 결과물인가, 나인가? |

- [05-code-review](../05-code-review/2-summary.md) · [11-documentation-practices](../11-documentation-practices/2-summary.md) · [06-ci-cd-pipelines](../06-ci-cd-pipelines/2-summary.md) · [07-build-systems-and-reproducibility](../07-build-systems-and-reproducibility/2-summary.md).

### 2. 조급함을 기계에 겨누는 법 — 대기 시간을 잰다

```java
// 피드백 루프의 각 단계 시간을 재서 가장 긴 대기부터 줄인다
long t0 = System.nanoTime();
runBuild();                       // 예: mvn -q -o package -DskipTests (테스트 실행을 뺀다)
long t1 = System.nanoTime();
runTests();                       // 예: mvn -q -o test
long t2 = System.nanoTime();
System.out.printf("build %.1fs, test %.1fs%n", (t1 - t0) / 1e9, (t2 - t1) / 1e9);
```

- Maven 기본 수명 주기에서 `package`는 앞 단계인 `test`까지 차례로 실행한다(Apache Maven "Introduction to the Build Lifecycle"). 그래서 `-DskipTests` 없이 `package`를 재면 빌드 시간에 테스트가 섞이고, 이어지는 `test`는 테스트를 한 번 더 돌린다.
- 재지 않으면 "원래 느리다"로 굳는다. 숫자가 있으면 가장 긴 단계부터 줄일 수 있다.
- CI에서는 단계별 소요 시간이 이미 로그에 있다. 주간 추이를 본다.

### 3. 오만을 결과물에 겨누는 법

- 리뷰 요청 전에 diff를 처음부터 끝까지 스스로 읽는다. "남이 이 diff를 보고 무엇을 지적할까"를 먼저 찾는다.
- 원문의 "(and maintain)": 배포 뒤에도 내 변경의 지표·알림을 본다. 장애가 나면 내 변경부터 의심한다.
- 지적을 받으면 결과물에 대한 정보로 받는다. 원문의 기준은 "남이 욕하지 않을 프로그램"이므로, 지적은 그 기준에 다가가는 재료다.

## 장애 시나리오와 대처

커리큘럼은 이 주제의 ⚠ 칸을 비워 두었다. 아래는 원본 실패 모드 표를 실천 장면으로 옮긴 것이다.

### 1. 계산 없는 자동화

- 현상: 분기에 한 번 하는 일을 이틀 들여 자동화했다. 스크립트는 다음 분기에 환경이 바뀌어 깨져 있다.
- 보이는 형태: 자동화 스크립트의 마지막 실행 기록이 몇 달 전이다. 유지 비용이 실행 이득보다 크다.
- 원인: 손익분기를 계산하지 않았다(위 계산의 "분기 1회 보고서": 52주 안에 이득 없음).
- 대처: 빈도·수작업 시간·제작·유지 비용을 적고 손익분기를 본다. 드문 일은 체크리스트 문서로 충분할 수 있다.

### 2. 조급함을 사람에게

- 현상: 리뷰를 재촉하고, 리뷰 없이 머지하거나 테스트를 건너뛰고 배포한다.
- 보이는 형태: "LGTM 빨리요" 메시지, 테스트 스킵 플래그가 붙은 배포, 그 뒤 롤백.
- 원인: 대기 시간의 원인(큰 PR·느린 CI)이 아니라 사람과 검증 절차에 화를 냈다. 원문 정의의 과녁("the computer")을 벗어났다.
- 대처: 기다림의 원인을 잰다. PR을 작게 쪼개 리뷰 대기를 줄이고(05), CI 시간을 줄인다(06·07). 검증 단계는 줄이지 않고 빠르게 만든다.

### 3. 오만이 자아를 향함

- 현상: 검증된 라이브러리 대신 직접 만든다(NIH). 리뷰 지적에 방어적으로 답한다.
- 보이는 형태: 같은 기능의 사내 구현이 여러 개다. 리뷰 스레드가 길어지고 결론이 안 난다.
- 원인: 기준이 "남의 평가를 받을 결과물"에서 "나"로 옮겨 갔다.
- 대처: 판별 질문 "기준이 결과물인가, 나인가?"를 쓴다. 직접 만들기 전에 도입 판단([13-build-vs-buy-and-adoption](../13-build-vs-buy-and-adoption/2-summary.md))을 거친다.

### 4. 단어만 떼어 쓰는 문화

- 현상: "오만은 미덕"이 무례함의 핑계가 된다.
- 보이는 형태: 리뷰 말투가 공격적이고, 새 사람이 질문을 안 한다.
- 원인: 정의 없이 단어만 썼다. 이 세 단어를 비판하는 글도 꾸준히 있다(예: Austin Pocus, Hacker Noon 2020 "Larry Wall's 'Three Virtues of a Programmer' are Utter Bullshit" — https://hackernoon.com/larry-walls-three-virtues-of-a-programmer-are-utter-bullshit-35pl3wf5).
- 대처: 세 단어를 쓸 때 과녁을 함께 말한다. 사람과 일할 때는 원문이 말한 공동체의 미덕(근면·인내·겸손)을 함께 든다 — 원문대로 둘은 동시에 할 수 있다.

## 핵심 문장

- 세 미덕의 과녁은 원문 정의 문장 안에 있다: 게으름은 "overall", 조급함은 "the computer", 오만은 "other people"과 "(and maintain)".
- 두 판의 perlglossary를 단어 단위로 비교하면, 정의의 뜻은 판이 바뀌어도 같다(어순·"then" 한 단어 차이).
- 게으름의 판별은 계산으로 할 수 있다. 자주 하는 일의 자동화·문서화는 몇 주 만에 이득이고, 드문 일은 1년 안에 본전을 못 찾을 수 있다.
- Wall은 공동체의 미덕(근면·인내·겸손)이 개인의 미덕과 반대처럼 들리지만, 동시에 할 수 있다고 썼다.
- 세 단어는 정의와 함께 쓸 때만 미덕이다. 단어만 떼면 그냥 악덕의 핑계가 된다.

## 관련 주제·근거

- 원본(기초): [foundations/three-virtues](../../foundations/three-virtues/2-summary.md) — 세 미덕 각각의 시야·실패 모드·견제 관계·비판.
- 선행: [01-lifecycle-and-agile](../01-lifecycle-and-agile/2-summary.md).
- 연결: [05-code-review](../05-code-review/2-summary.md) · [11-documentation-practices](../11-documentation-practices/2-summary.md) · [06-ci-cd-pipelines](../06-ci-cd-pipelines/2-summary.md) · [07-build-systems-and-reproducibility](../07-build-systems-and-reproducibility/2-summary.md) · [13-build-vs-buy-and-adoption](../13-build-vs-buy-and-adoption/2-summary.md) · [12-estimation-and-planning](../12-estimation-and-planning/2-summary.md)(손익분기의 불확실성) · [data-structure/01-dynamic-array](../../data-structure/01-dynamic-array/)(분할 상환).
- 근거
  - perlglossary 현재판(perlfaq 5.20250619, "derived from the Glossary of Programming Perl, Fourth Edition"): https://perldoc.perl.org/perlglossary · 원문 POD: https://fastapi.metacpan.org/v1/pod/perlglossary?content-type=text/x-pod
  - perlglossary 옛 판(perl 5.8.8): https://fastapi.metacpan.org/source/NWCLARK/perl-5.8.8/pod/perlglossary.pod
  - Larry Wall, "Diligence, Patience, and Humility", 『Open Sources: Voices from the Open Source Revolution』(O'Reilly, 1999): https://www.oreilly.com/openbook/opensources/book/larry.html
  - Wall·Christiansen·Orwant, 『Programming Perl』 3판(2000)·4판(2012, Christiansen·foy·Wall·Orwant) 용어집 — 책 본문은 열지 않았고 perlglossary로 대신 확인.
- 실험 목록
  - 원문 대조: `extract.sh`(awk로 세 항목 추출) + `git diff --no-index --word-diff=plain`, 입력 `old.pod`(perl 5.8.8)·`new.pod`(perlfaq 5.20250619), git 2.43.0. 실험 대신 원문 대조로 대신한 주제다(태도 노트).
  - 자동화 손익분기 계산: `BreakEven.java`, `docker run eclipse-temurin:21-jdk java BreakEven.java`, JDK 21.0.12(temurin). 입력은 예시 값.
