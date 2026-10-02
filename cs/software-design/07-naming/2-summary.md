# software-design/07-naming — 이름: 추상화의 첫 표현 — 정리 (힌트)

## 해결하는 문제

이름은 코드를 읽는 사람이 가장 먼저, 가장 자주 보는 문서다.\
이름이 흐리면 읽는 사람이 동작을 **추측**한다. 추측이 틀리면 리뷰를 통과한 버그가 된다.

```text
 processData(list, flag)                  approveRefunds(pendingRefunds, notifyCustomer)
   │                                        │
   ├─ 무엇을 처리하나?      (추측)            ├─ 환불을 승인한다
   ├─ list에는 뭐가 드나?   (추측)            ├─ 대기 중인 환불 목록
   └─ flag가 true면?       (추측)            └─ 고객에게 알릴지  → 읽는 순간 답이 나온다
       → 본문을 열어 봐야 한다                   → 본문을 안 열어도 된다
```

- *이름(identifier)*: 변수·함수·클래스·패키지에 붙인 식별자.
- *추상화(abstraction)*: 세부를 감추고 "무엇인지"만 드러낸 단순한 생각의 틀. 이름은 그 틀의 첫 표현이다.

쉬운 예: 냉장고 반찬통에 "기타"라고 써 붙이면 열어 봐야 안다. "어제 만든 김치찌개(10/1)"라고 쓰면 안 열어도 된다.\
똑같은 구조다.\
실무 예: 주문 모듈은 "고객(customer)", 쿠폰 모듈은 "회원(member)", 결제 모듈은 "사용자(user)"라고 같은 사람을 부른다. "VIP 고객 할인율 변경" 티켓을 받은 개발자가 `customer`로 검색하면 나머지 두 모듈을 놓친다(아래 실험 B).

이 주제는 [06-clean-code](../06-clean-code/2-summary.md)에서 나눴다. 06이 "결과물의 성질"이라면, 이 노트는 그 성질이 코드에서 가장 먼저 드러나는 자리인 이름을 다룬다.

## 동작·원리

### 1. 좋은 이름이 하는 일 — 머릿속 그림을 맞춘다

```text
 작성자 머릿속                 이름                     읽는 사람 머릿속
 "대기 중 환불만,     ──>  pendingRefunds   ──>   "대기 중 환불 목록이구나"
  최대 100건"                (+ 주석: 최대 100건)       (첫 추측이 맞는다)

 작성자 머릿속                 이름                     읽는 사람 머릿속
 "대기 중 환불만"     ──>  data             ──>   "뭐든 될 수 있네" → 본문 읽기
```

- APOSD 14장의 목표: 처음 본 사람의 **첫 추측이 맞게** 한다. 그 장의 절 제목은 "Create an image", "Names should be precise", "Use names consistently"다(2판 목차).
- APOSD의 경고 신호(red flag) 둘(2판 「Summary of Red Flags」):
  - *Vague Name*: 이름이 너무 흐려 쓸모 있는 정보를 거의 전하지 못한다.
  - *Hard to Pick Name*: 정확하고 직관적인 이름을 떠올리기 어렵다. 14장 본문은 이를 이름의 문제가 아니라 그 대상의 설계(정의·목적)가 깔끔하지 않다는 신호로 본다(요약 목록 밖의 이 해석은 독자 노트로만 확인 [?]).

### 2. 이름에 담는 정보 — 다섯 축

| 축 | 나쁜 예 | 나은 예 | 근거 |
|---|---|---|---|
| 의도(무엇·왜) | `data`, `info`, `process()` | `pendingRefunds`, `approveRefunds()` | APOSD 14.3, 커리큘럼 모호어 목록 |
| 도메인 어휘 | `user`·`member`·`customer` 혼용 | 한 개념 = 한 단어 | Evans 유비쿼터스 언어, APOSD 14.4 |
| 범위에 비례한 길이 | 클래스 필드 `q`, 3줄 루프 `currentIndexOfTheLoop` | 필드 `quantity`, 루프 `i` | Gerrand 2014 |
| 단위·경계 | `timeout`, `limit` | `timeoutMillis`, `maxItems`(포함), `end`(미포함) | Boswell–Foucher 2·3장 |
| 참/거짓 | `isNotDisabled`, `flag` | `isEnabled`, `shouldNotify` | Boswell–Foucher 3장 |

- *유비쿼터스 언어(ubiquitous language)*: 개발자와 도메인 전문가가 함께 쓰는 엄밀한 공통 언어. 코드 이름도 이 언어를 쓴다(Fowler bliki "UbiquitousLanguage" 2006, Evans 『Domain-Driven Design』의 용어).
- *범위(scope)*: 이름이 보이는 코드 영역. 선언과 사용이 멀수록 이름이 길어야 한다 — Andrew Gerrand, "What's in a name?"(Go 팀 발표, 2014-10): "The greater the distance between a name's declaration and its uses, the longer the name should be."
- *모호어*: 어떤 클래스에 붙여도 말이 되는 단어. `Manager`·`Processor`·`Data`·`Info`·`Util`. 붙여도 정보가 늘지 않는다.

### 3. 부정 boolean이 버그를 만드는 경로

```text
 isNotDisabled()               조건을 뒤집어야 할 때
   │                              "비활성 사용자는 건너뛴다"
   └─ !isNotDisabled()  ──>     부정 둘 → 사람이 머릿속에서 두 번 뒤집어야 한다
                                한 번만 뒤집으면 조건이 반대가 된다

 isEnabled()
   └─ !isEnabled()      ──>     부정 하나 → "비활성이면"으로 바로 읽힌다
```

- Boswell–Foucher 3장의 권고: boolean에는 `is`·`has`·`can`·`should`를 붙이고, `disable_ssl = false` 대신 `use_ssl = true`처럼 부정어를 이름에 넣지 않는다(책 본문 미열람, 독서 노트로 확인 [?]).

### 실험 A: 도구가 잡는 이름 문제와 못 잡는 이름 문제

PMD 7.28.0 이름 규칙 다섯(LinguisticNaming·BooleanGetMethodName·ShortVariable·LongVariable·ShortMethodName)을 일부러 나쁜 이름을 모은 클래스에 돌렸다.

```java
public class OrderManager {
    private int isPaid;                         // 이름은 boolean인데 타입은 int
    private boolean disabled;
    private int q;
    private String customerShippingAddressLine;
    public boolean getActive() { return !disabled; }
    public void getTotal() { System.out.println(q); }
    public int setStatus(int s) { q = s; return q; }
    public boolean isNotDisabled() { return !disabled; }
    public List<Object> processData(List<Object> list, boolean flag) { return list; }
    ...
}
```

(실험, PMD 7.28.0, JDK 21.0.12 temurin `--cpus=2`, 2026-10-02, `scratchpad/sd/06/e07/run-pmd.sh`)

```text
e07/names/src/OrderManager.java:4:	LinguisticNaming:	Linguistics Antipattern - The field 'isPaid' indicates linguistically it is a boolean, but it is 'int'
e07/names/src/OrderManager.java:6:	ShortVariable:	Avoid variables with short names like q
e07/names/src/OrderManager.java:7:	LongVariable:	Avoid excessively long variable names like customerShippingAddressLine
e07/names/src/OrderManager.java:9:	BooleanGetMethodName:	A getX() method which returns a boolean or Boolean should be named isX()
e07/names/src/OrderManager.java:10:	LinguisticNaming:	Linguistics Antipattern - The getter 'getTotal' should not return void linguistically
e07/names/src/OrderManager.java:11:	LinguisticNaming:	Linguistics Antipattern - The setter 'setStatus' should not return any type except void linguistically
e07/names/src/OrderManager.java:11:	ShortVariable:	Avoid variables with short names like s
[INFO] Found 7 violations.
```

- 잡힌 것 — **형식과 타입의 어긋남**: 이름은 boolean인데 int(`isPaid`), getter인데 void, setter인데 반환값, 길이(짧음: 3자 미만, 긺: 17자 초과 — PMD 7.28.0 규칙 XPath와 기본값 `minimum`).
- 못 잡은 것 — **뜻**: `OrderManager`(모호어), `isNotDisabled`(이중 부정), `processData`·`flag`(무엇을 하는지 모름). 커리큘럼 ⚠ 칸의 세 사례가 모두 도구를 통과했다.
- `customerShippingAddressLine`은 길이 규칙에 걸렸다. 그러나 범위가 넓은 필드라면 이 길이가 맞을 수 있다. 길이 규칙은 범위를 모른다.
- 해석 — 이름 검사 도구는 리뷰의 하한선이다. 뜻을 묻는 질문("이 이름만 보고 동작을 맞힐 수 있나?")은 사람이 한다.
- *LinguisticNaming*: Arnaoudova 외 "Linguistic Antipatterns: What They Are and How Developers Perceive Them"(Empirical Software Engineering, doi 10.1007/s10664-014-9350-8) 연구를 근거로 이름과 타입·반환의 언어적 어긋남을 찾는 PMD 규칙(PMD 문서).

### 실험 B: 한 개념, 세 이름 — 검색이 놓치는 곳

같은 `Customer` 타입을 주문 모듈은 `customer`, 쿠폰 모듈은 `member`, 결제 모듈은 `user`라는 변수명으로 쓴다. 할인율 10%도 세 모듈에 따로 있다.\
요구: "VIP 할인 10% → 15%". 개발자가 티켓 용어(customer, vip)로 검색해 찾은 파일만 고쳤다고 가정했다.\
비교 설계(unified)는 한 단어(`customer`)와 한 정책(`VipPolicy`)만 쓴다.

(실험, 같은 환경, `scratchpad/sd/06/e07/run-drift.sh`)

```text
[drift] 어휘 조사: grep -rhoiE '\b(customer|member|user)\b' src | sort | uniq -c
         8 customer
         2 member
         2 user
[drift] 티켓 용어 'customer'+'vip' 로 찾은 파일: grep -rliE 'customer.*vip|vip.*customer' src
   src/Customer.java
   src/CustomerDiscount.java
[drift] 그중 할인율 상수가 있는 파일만 수정
== [drift] git diff --stat
   src/CustomerDiscount.java | 2 +-
   1 file changed, 1 insertion(+), 1 deletion(-)
  주문 화면 할인액   = 1500
  쿠폰 적용가        = 9000
  결제 최종가        = 9000
== [unified] git diff --stat
   src/VipPolicy.java | 2 +-
   1 file changed, 1 insertion(+), 1 deletion(-)
  주문 화면 할인액   = 1500
  쿠폰 적용가        = 8500
  결제 최종가        = 8500
```

- 관찰 — 같은 VIP 고객에게 주문 화면은 1,500원 할인(15%)을, 쿠폰·결제는 1,000원 할인(10%, 9,000원)을 보여 준다. 오류도 예외도 없다.
- 원인 — `member.vip()`·`user.vip()` 줄에는 검색어 `customer`가 없다. 타입은 같아도 **변수 이름이 다르면 검색이 갈라진다**.
- 해석 — 어휘 조사(첫 명령)는 실험용 진단이다. 한 개념에 이름이 둘 이상 나오면 검색 누락의 후보다. 이 실험은 중복된 할인율(06의 N 위반)과 겹친다. 이름이 하나였다면 중복도 검색 한 번에 드러났을 것이다.

### 4. 이름 길이 — 두 입장

- Gerrand(Go): 지역 변수는 짧게. `index`보다 `i`, `buffer`보다 `b`. 맥락이 이미 주는 정보는 이름에서 뺀다(`RuneCount` 안에서는 `runeCount`보다 `count`).
- Ousterhout(APOSD 2판 14.6 "A different opinion: Go style guide"): 이 Go 관례에 반대 의견을 낸다고 절 제목이 밝힌다(절 본문 미열람 [?]).
- 공통 기준: **선언과 사용의 거리**. 3줄 루프의 `i`와 클래스 필드의 `i`는 같은 이름이라도 비용이 다르다.

## 쓰이는 자료구조·알고리즘

- **심볼 테이블과 스코프 체인**: 컴파일러는 이름을 스코프마다 심볼 테이블에 넣고, 안쪽 스코프부터 바깥으로 찾는다. 범위가 넓은 이름일수록 많은 코드가 같은 테이블 항목을 본다. 그래서 길고 정확해야 한다.
- **식별자 토큰화**: `customerShippingAddress` → `customer`·`shipping`·`address`. camelCase·snake_case 경계로 쪼갠 단어 열이 검색·도구 분석의 단위다. 실험 B의 `\b` 단어 경계 검색은 `MemberCouponService` 안의 `Member`를 별개 단어로 보지 않았다.
- **용어 사전(glossary) = 맵**: 개념 → 정식 단어, 금지 동의어 목록. 린트 규칙이나 리뷰 검사에서 금지어를 찾는 키 집합으로 쓴다.

## 적용 — 풀어나가는 법

### 1. 이름을 고르는 순서

1. **무엇을 담나**를 한 문장으로 말한다. "대기 중인 환불 목록, 최대 100건."
2. 도메인 용어 사전에서 단어를 고른다. 없으면 팀과 정하고 사전에 넣는다.
3. 범위를 본다. 넓으면 단위·경계까지(`timeoutMillis`, `maxItems`). 좁으면 짧게.
4. boolean이면 긍정형 술어(`is`·`has`·`can`·`should`)로.
5. 1번 문장이 "그리고"로 이어지거나 한 단어로 안 줄면, 이름이 아니라 **책임**을 나눈다(Hard to Pick Name).

### 2. 고치기 (Java)

```java
// 전
List<Object> processData(List<Object> list, boolean flag)
boolean isNotDisabled()

// 후 — 동작마다 이름, 긍정형 술어
List<Refund> approveRefunds(List<Refund> pendingRefunds)
List<Refund> approveRefundsAndNotify(List<Refund> pendingRefunds)   // 플래그 대신 두 이름 (08 함수 설계)
boolean isEnabled()
```

- IDE의 Rename(심볼 기반 이름 바꾸기)을 쓴다. 문자열 치환은 주석·문자열·리플렉션 이름을 다르게 다룬다. 공개 API 이름은 deprecate 후 교체한다(parallel change, [51-legacy-change-techniques](../51-legacy-change-techniques/2-summary.md)).

### 3. 진단 명령

```bash
# 한 개념의 동의어가 몇 번 섞였나 (용어 사전의 금지 동의어로 확장)
grep -rhoiE '\b(customer|member|user|client)\b' src | tr 'A-Z' 'a-z' | sort | uniq -c

# 모호어가 붙은 클래스 이름
grep -rhoE 'class [A-Za-z]*(Manager|Processor|Helper|Util|Data|Info)\b' src | sort | uniq -c

# 이름 형식 검사 (PMD 7.x)
pmd check -d src/main/java -R category/java/codestyle.xml/LinguisticNaming,category/java/codestyle.xml/BooleanGetMethodName
```

## 장애 시나리오와 대처

### 1. `processData(list, flag)` → 리뷰어가 동작을 추측하다 버그 통과 (⚠ 커리큘럼)

- 현상: `processData(refunds, true)`가 "승인 + 알림"인 줄 알았는데 "승인 취소"였다. 리뷰를 통과했다.
- 보이는 형태: 테스트는 통과(작성자가 같은 오해로 썼다). 운영에서 고객 문의.
- 원인: 이름과 인자 어디에도 동작이 드러나지 않는다. PMD 이름 규칙도 통과한다(실험 A).
- 대처: 동작마다 이름을 준다(`approveRefunds`·`cancelRefunds`). 플래그 인자는 08에서 다룬다. 리뷰 질문: "이름만 보고 동작을 맞힐 수 있나?"

### 2. `isNotDisabled` 이중 부정 → 조건 반전 버그 (⚠ 커리큘럼)

- 현상: "비활성 사용자 건너뛰기"를 넣었더니 활성 사용자만 건너뛴다.
- 보이는 형태: 발송 수가 거의 0이 된다. 배치 로그에 "skipped" 대량.
- 원인: `if (user.isNotDisabled()) continue;` — 부정 둘을 머릿속에서 한 번만 뒤집었다.
- 대처: `isEnabled()`로 이름을 바꾸고 호출처를 함께 고친다. 부정 boolean 이름은 도구가 못 잡으므로(실험 A) 리뷰 검사표에 넣는다.

### 3. user·member·customer 혼용 → 검색 누락, 한쪽만 수정 (⚠ 커리큘럼)

- 현상: VIP 할인율 변경 후 화면마다 할인액이 다르다.
- 보이는 형태: 실험 B — 주문 화면 1,500원, 쿠폰·결제 9,000원(10%). 에러 없음.
- 원인: 같은 개념이 세 이름으로 불려 티켓 용어 검색이 셋 중 하나만 찾았다. 할인율도 세 곳에 중복이었다.
- 대처: 용어 사전으로 한 단어를 정하고 Rename으로 통일한다. 규칙은 한 곳(`VipPolicy`)으로 모은다(실험 B unified: 1파일 수정으로 세 값이 함께 바뀜).

### 4. 단위·경계 없는 이름 → 단위 혼동

- 현상: `timeout = 30`을 초로 알고 넣었는데 밀리초였다. 호출이 거의 즉시 실패한다.
- 보이는 형태: 타임아웃 에러율 급증, 설정 변경 직후.
- 원인: 이름에 단위가 없다.
- 대처: `timeoutMillis` 또는 `Duration` 타입. 타입으로 강제하는 방법은 [24-types-as-invariants](../24-types-as-invariants/2-summary.md).

## 핵심 문장

- 이름의 목표는 처음 읽는 사람의 첫 추측이 맞게 하는 것이다.
- 정확한 이름이 떠오르지 않으면 이름이 아니라 대상의 책임이 흐린 것이다(APOSD "Hard to Pick Name").
- 한 개념에는 한 단어를 쓴다. 실험에서 같은 고객을 세 이름으로 부르자 검색이 셋 중 하나만 찾았고, 화면마다 할인액이 달랐다.
- 선언과 사용이 멀수록 이름은 길어야 한다.
- PMD 이름 규칙은 형식·타입 어긋남(7건)을 잡았지만 `processData`·`isNotDisabled`·`Manager`는 통과시켰다. 뜻은 사람이 리뷰한다.

## 관련 주제·근거

- 선행
  - [06-clean-code](../06-clean-code/2-summary.md) — 품질 검사표, N(비중복)과 실험 B의 연결
- 후속·연결
  - [08-function-design](../08-function-design/2-summary.md) — 플래그 인자·CQS(이름이 약속한 대로 동작하기)
  - [09-comments-and-conventions](../09-comments-and-conventions/2-summary.md) — 이름이 못 담는 정보는 주석으로
  - [10-code-smells](../10-code-smells/2-summary.md) — Fowler 2판 첫 스멜 "Mysterious Name"
  - [24-types-as-invariants](../24-types-as-invariants/2-summary.md) · [51-legacy-change-techniques](../51-legacy-change-techniques/2-summary.md)(parallel change)
- 글·문서
  - John Ousterhout, 『A Philosophy of Software Design』 2판(2021) 14장 "Choosing Names"(절: 14.1 bad names cause bugs, 14.2 Create an image, 14.3 precise, 14.4 consistently, 14.6 Go style guide), 「Summary of Red Flags」의 Vague Name·Hard to Pick Name — 장·절 제목과 요약 문장은 2판 커뮤니티 번역 사이트의 영문판으로 확인, 절 본문 미열람 <https://yingang.github.io/aposd2e-zh/en/ch14.html>
  - Dustin Boswell·Trevor Foucher, 『The Art of Readable Code』(O'Reilly, 2011) 2장 "Packing Information into Names"·3장 "Names That Can't Be Misconstrued" — 장 제목은 검색 결과 목차, 내용은 독서 노트로만 확인 [?]
  - Felienne Hermans, 『The Programmer's Brain』(Manning) 8장 "How to get better at naming things"(8.4.1 Code with bad names has more bugs, 8.5.1 Name molds) — 목차만 확인 <https://livebook.manning.com/book/the-programmers-brain/chapter-8>
  - Andrew Gerrand, "What's in a name?"(2014-10) <https://go.dev/talks/2014/names.slide>
  - Martin Fowler, "UbiquitousLanguage"(2006-10-31) <https://martinfowler.com/bliki/UbiquitousLanguage.html> · "TwoHardThings"(Phil Karlton 인용) <https://martinfowler.com/bliki/TwoHardThings.html>
  - PMD 7.28.0 codestyle 규칙(LinguisticNaming, BooleanGetMethodName, ShortVariable 3자 미만, LongVariable 17자 초과) <https://docs.pmd-code.org/pmd-doc-7.28.0/pmd_rules_java_codestyle.html>
  - Google eng-practices "What to look for in a code review" — Naming 절 <https://github.com/google/eng-practices/blob/master/review/reviewer/looking-for.md>
- 실험 목록 (코드: scratchpad `sd/06/e07/`, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, PMD 7.28.0, git 2.43.0)
  - A PMD 이름 규칙 5종 — `run-pmd.sh` (7건 보고, 뜻 문제 3종 미보고)
  - B 한 개념 세 이름 + 할인율 변경 — `run-drift.sh` (어휘 조사, 검색 결과, diff --stat, 화면별 금액)
