# software-design/12-simple-design-and-yagni — 정답

## 정답

### 1. 4규칙

1. 테스트를 통과한다(Passes the tests)
2. 의도를 드러낸다(Reveals intention)
3. 중복이 없다(No duplication)
4. 요소가 가장 적다(Fewest elements)

- 표현은 Fowler "BeckDesignRules"(2015)의 것이다. 1번이 가장 중요하다.
- Fowler는 2번(의도)과 3번(중복)의 순서를 중요하지 않다고 본다. 둘이 서로를 다듬는다.
- Beck(같은 글 각주): 드물게 충돌하면(그가 떠올린 예는 테스트 코드뿐) "empathy wins" — 읽는 사람을 먼저 생각한다.

### 2. 세 부류와 비용 4종

```text
 필요 없었다            → build + carry
 필요했고 맞게 만들었다 → delay + carry
 필요했지만 틀리게      → repair
```

- 맞았을 때도 delay(그동안 다른 가치를 못 냄)와 carry(쓰이기 전까지 다른 기능 개발을 느리게 함)를 낸다.

### 3. YAGNI가 아닌 것

- (나)·(다)·(라)가 YAGNI 위반이 아니다. (가)만 추정 기능이다.
- (나) 리팩터링, (다) 자체 테스트 코드: 코드를 고치기 쉽게 만드는 노력이라 YAGNI 대상이 아니다. Fowler: YAGNI는 고치기 쉬운 코드를 필요로 한다.
- (라) 조회 테이블: 지금 복잡도를 거의 늘리지 않으면서 나중 비용(번역)을 크게 줄이는 일이다. Fowler는 지금 쉽고 복잡도를 거의 늘리지 않으면서 나중 비용을 크게 줄이는 일은 넣을 만하다고 쓴다(이 예를 직접 든다).

### 4. v1 비용

(실험, JDK 21.0.12 temurin, 2026-10-02)

```text
--- simple-v1
 1 file changed, 5 insertions(+)
--- spec-v1
 7 files changed, 51 insertions(+)
spec-v1: 키 8개, 미사용: discount.rate.percent discount.stackable discount.max.cap discount.plugin.dir discount.currency
```

- SIMPLE 1파일 5줄, SPEC 7파일 51줄. 같은 테스트를 통과한다.
- 설정 키 8개 중 5개를 코드가 읽지 않았다.

### 5. 둘째 요구(VIP)

```text
--- simple-v1 → simple-v2
 2 files changed, 10 insertions(+), 1 deletion(-)
--- spec-v1 → spec-v2
 7 files changed, 20 insertions(+), 8 deletions(-)
```

- SIMPLE 2파일, SPEC 7파일.
- 원인: 미리 만든 `DiscountPolicy.discount(subtotal)`는 금액만 받았다. 실제 요구는 고객 등급이 필요했다. 인터페이스·구현·레지스트리·팩토리·조합 규칙·설정을 다 고쳤다(repair 비용).

### 6. 추측이 맞았는데도

```text
--- spec-v1 → spec-hit
 5 files changed, 18 insertions(+), 6 deletions(-)
```

- 미리 만든 구조는 `discount.type` 하나로 할인 **하나를 고르는** 모양이었다. 실제 요구는 할인 **둘을 차례로** 적용하는 것이었다. 인터페이스 모양은 맞았지만 조합 방식은 추측에 없었다.
- 값어치를 하는 요구(코드 구조로 판단, 실행하지 않음): 할인 금액만 바꾸는 요구는 SPEC에서 `app.properties` 한 줄로, 코드 수정·재컴파일 없이 끝난다(이 실험 구조에서는 재시작은 필요). 운영 중 값 변경이 실제로 필요할 때 만드는 확장점이다.

### 7. 요구 1·2·3

- 요구 1: 직접 구현한다. 확장점 없음.
- 요구 2: 두 사례를 비교해 실제로 달라지는 축(실험: 고객 등급)을 받는 확장점을 만든다.
- 요구 3: 확장점에 끼운다.
- 둘째에서인 이유: 첫 요구만으로는 변하는 축을 추측해야 한다. 둘째가 오면 축이 실제 데이터로 드러난다. 셋째 사례 규칙(11)과 같은 이유다.

### 8. 설정 조합 폭발

- 불리언 20개 → 2^20 = 1,048,576개 조합. 전수 테스트는 불가능하다.
- 찾기: (정의된 키 집합) − (코드가 참조하는 키 집합). 설정 파일 키마다 코드에서 문자열 참조를 grep한다. `@ConfigurationProperties` 바인딩은 문자열 참조가 없으니 필드 사용처를 따로 본다.
- 조치: 안 읽히는 키를 지운다. 남은 키는 유효 조합을 검증 코드로 제한해 잘못된 조합이면 기동을 실패시킨다.

### 9. YAGNI를 핑계로 한 방치

- 몇 달 뒤 작은 요구에도 손대기 무섭다. 변경마다 회귀 버그가 나고, 리팩터링 PR은 "동작이 바뀔까 봐" 거절된다.
- Fowler "Yagni": 리팩터링·SelfTestingCode·지속적 전달은 진화적 설계를 가능하게 하는 습관이고, 이것 없이 YAGNI는 "저주"가 된다. "Yagni requires (and enables) malleable code."
