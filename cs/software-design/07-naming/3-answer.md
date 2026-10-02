# software-design/07-naming — 정답

## 정답

### 1. 추측하게 만드는 이름

- 리뷰어는 무엇을 처리하는지, list에 무엇이 드는지, flag가 true면 무엇이 달라지는지를 본문을 열어 확인해야 한다.
- APOSD 14장의 기준: 처음 본 사람의 **첫 추측이 맞는** 이름. `processData`는 어떤 추측도 가능해서 기준을 못 넘는다.
- 추측이 틀린 채 승인되면 리뷰를 통과한 버그가 된다.

### 2. Hard to Pick Name

- APOSD 「Summary of Red Flags」: 정확하고 직관적인 이름을 떠올리기 어렵다는 것. 대상의 설계가 깔끔하지 않다는 신호로 읽는다.
- 할 일: "이것은 ○○을 한다"를 한 문장으로 말해 본다. "그리고"가 붙으면 책임을 나눈다. 이름만 고쳐서 끝내지 않는다.

### 3. 도구가 잡는 것

(실험 A, PMD 7.28.0, 2026-10-02)

```text
[INFO] Found 7 violations.
```

- 7건: `isPaid`(int인데 boolean 이름), `q`·`s`(짧음), `customerShippingAddressLine`(긺), `getActive`(boolean인데 get), `getTotal`(void getter), `setStatus`(반환하는 setter).
- ⚠ 칸 세 사례는 **0개** 잡혔다. `processData`·`flag`·`isNotDisabled`·`OrderManager`는 모두 보고되지 않았다. 도구는 형식과 타입의 어긋남을 보고, 뜻은 보지 않는다.

### 4. 세 이름의 결과

(실험 B, 2026-10-02)

```text
== [drift]
  주문 화면 할인액   = 1500
  쿠폰 적용가        = 9000
  결제 최종가        = 9000
== [unified]
  주문 화면 할인액   = 1500
  쿠폰 적용가        = 8500
  결제 최종가        = 8500
```

- drift: 주문 화면만 15%(1,500원). 쿠폰·결제는 10%가 남아 9,000원. `member.vip()`·`user.vip()` 줄에 검색어가 없어 놓쳤다.
- unified: `VipPolicy` 1파일 수정으로 세 값이 함께 15%가 됐다(8,500원).

### 5. 이름 길이

- Gerrand(2014): "The greater the distance between a name's declaration and its uses, the longer the name should be."
- 괜찮은 `i`: 3줄짜리 for 루프 인덱스. 나쁜 `i`: 클래스 필드나 50줄 떨어져 쓰이는 지역 변수.
- PMD `ShortVariable`(3자 미만)·`LongVariable`(17자 초과)은 글자 수만 본다. 범위(거리)를 모른다. 단 `ShortVariable`은 for 루프·catch·람다 매개변수를 제외한다(PMD 문서의 XPath).

### 6. 이중 부정 버그

- 원인: `if (user.isNotDisabled()) continue;` — "비활성이면 건너뛴다"를 쓰려다 부정을 한 번만 뒤집었다. 활성 사용자를 건너뛴다.
- 대처: `isEnabled()`로 이름을 바꾸고 조건을 `if (!user.isEnabled()) continue;`로 다시 쓴다. 이 이름은 PMD가 잡지 않으므로(3번) 리뷰 검사표에 "부정 boolean 이름"을 넣는다.

### 7. 유비쿼터스 언어

- 개발자와 도메인 전문가가 함께 쓰는 엄밀한 공통 언어(Evans DDD, Fowler bliki 2006-10-31). 코드 이름도 그 단어를 쓴다.
- 이름이 하나면 같은 지식의 사본이 검색 한 번에 모두 나온다. 이름이 갈라지면 사본(N 위반)이 검색에서 숨는다. 실험 B는 이름 혼용과 할인율 중복이 겹쳐 생긴 장애다.

### 8. 단위 없는 이름

- 장애: 초와 밀리초 혼동. `timeout = 30`이 30ms로 해석돼 호출이 거의 즉시 타임아웃.
- 이름으로 막기: `timeoutMillis`.
- 이름 말고: `Duration` 같은 단위를 가진 타입을 쓴다. 타입으로 불변식을 강제하는 방법은 24 types-as-invariants.
