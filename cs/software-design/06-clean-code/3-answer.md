# software-design/06-clean-code — 정답

## 정답

### 1. 감각 리뷰의 한계

- 결합과 중복은 diff 밖에 있다. 바뀐 규칙의 다른 사본, 바뀐 시그니처의 호출처는 리뷰 화면에 나오지 않는다.
- 클래스 하나로 답할 수 없는 둘: **L**(이걸 바꾸면 무엇이 따라 바뀌나)과 **N**(이 지식은 또 어디 있나).
- C·E·A는 그 클래스를 열어 보면 답할 수 있다.

### 2. Ask vs Tell

(실험 A, JDK 21.0.12, 2026-10-02)

```text
== [ask] git diff --stat
   4 files changed, 10 insertions(+), 3 deletions(-)
  approve      = false
  refund       = false
  earnPoints   = true
== [tell] git diff --stat
   2 files changed, 7 insertions(+), 2 deletions(-)
  approve      = false
  refund       = false
  earnPoints   = false
```

- Ask: 4파일. grep(`getStatus() == CardStatus.ACTIVE`)이 승인·환불만 찾았다. 모양이 다른 `PointService`가 빠져 잠긴 카드에도 포인트를 준다.
- Tell: 2파일(Card·픽스처). 판단이 Card 한 곳에 있어 세 서비스가 함께 바뀌었다.

### 3. diff 크기는 같았다

- 두 설계 모두 `1 file changed, 1 insertion(+), 1 deletion(-)`.
- 합친 설계는 정산 수수료가 같은 상수를 써서 따라 바뀌었다: `FAIL settlementFee(1000) = 30 (기대 25)`.
- diff 줄 수가 아니라 영향 범위가 비용이다. 카드사 계약과 가맹점 약관은 함께 바뀌지 않는 다른 지식이었다.

### 4. CPD의 한계

- 셋 중 **둘**(Approval·Refund, 3줄 27토큰)을 잡았다. `PointService`는 같은 지식을 다른 모양으로 써서 잡히지 않았다.
- 도구가 못 하는 두 경우:
  - 같은 지식이 다른 글자로 적힌 경우(놓침).
  - 다른 지식이 같은 글자로 적힌 경우(합치라고 잘못 권할 수 있음 — 실험 B의 두 상수).

### 5. 긴장과 공통 질문

- N ↔ L: 공유하면 중복은 사라지지만 함께 묶인다.
- C ↔ N: 함께 변하는 것을 묶으면 다른 곳과 겹칠 수 있다.
- E ↔ 편의성: 캡슐화하면 메서드를 매번 만들어야 한다.
- A ↔ 계층 분리: DB가 필요한 판단은 도메인 객체 안에 못 넣는다.
- 공통 질문: **이 둘은 함께 바뀌나?** 함께면 모으고, 따로면 떨어뜨린다.

### 6. DRY의 단위

- "Every piece of knowledge must have a single, unambiguous, authoritative representation within a system." 단위는 **지식**이다.
- 같은 절 "Not All Code Duplication is Knowledge Duplication": 주문 수량과 나이 검증이 같은 코드여도 "That's a coincidence, not a duplication."

### 7. Tell, Don't Ask의 오독

- getter를 전부 없애면 화면 표시·직렬화처럼 값 자체가 목적인 곳까지 막힌다.
- Fowler(2013-09-05)는 원칙을 소개하면서도 "personally, I don't use tell-dont-ask"라고 쓰고, 데이터와 행동을 함께 두는 것(co-locate)을 본다고 한다.
- 안전한 읽기: **판단을 데이터 곁에 둔다.** getter는 판단 재료로만 쓰일 때 의심한다.

### 8. 포인트만 쌓이는 장애

- 의심: "쓸 수 있는 카드" 판단식이 여러 곳에 있고 그중 하나가 갱신되지 않았다(A·N 동시 위반).
- 순서:
  1. 이번 배포가 고친 조건식을 찾는다.
  2. 같은 판단 재료(`getStatus()`·`getExpiry()`·`isBlocked()`)의 사용처를 전수 검색한다. 글자 일치 grep은 모양이 다른 사본을 놓친다(실험 A).
  3. 갱신되지 않은 사본을 찾으면 판단을 객체 하나(`isUsable`)로 모으고, 세 서비스가 같은 결과를 내는 테스트를 둔다.

### 9. CLEAN의 출처

- 확인된 출처: David Scott Bernstein 『Beyond Legacy Code』(Pragmatic Bookshelf, 2015) Practice 5 「Create CLEAN Code」(pragprog 목차).
- 원본은 "제프 랭어의 저술 … (확인 필요)"라고 적었다. 이 출처는 확인되지 않았다. 커리큘럼의 Shalloway–Trott 출처와 Assertive의 최초 제안자도 확인하지 못했다 [?].
- 구성 개념(응집·결합·정보 은닉·DRY)은 두문자어보다 오래됐다.
