# PR #37153 — 리뷰 과정 기록 (듀얼 리뷰가 무엇을 바꿨나)

> 1줄 fix에도 독립 리뷰 2곳 + 감사 1회를 돌렸다. 이 문서는 그 과정에서 나온
> 지적과 채택/기각 판단, 그리고 코드가 실제로 어떻게 바뀌었는지의 기록이다.

## 구성

리뷰는 독립 리뷰어 두 곳과 그 뒤의 종합 감사 한 번으로 짜였다.

- 리뷰어 2곳이 **같은 packet**(spec 원문 + 누적 diff + 검증 실측)만 보고 독립
  리뷰 — 판정 기준은 "그럴듯한가"가 아니라 "spec과 일치하는가".
- 결과: 리뷰어 A는 findings 0(6개 렌즈 전부 verified), 리뷰어 B는 findings 3 +
  open questions 4. 같은 입력에서도 관점이 갈린다는 것 자체가 듀얼 리뷰의 값이다.
- 이후 종합 감사 1회가 메인의 채택/기각 판단 자체를 재검토했고, 실제로 두 건을
  정정했다.

## findings와 처리

### F1. 같은 계산식에 nested annotation 계열도 빠져 있지 않나 (범위 밖 -> 후속 조사)

가장 흥미로운 지적. 이번 fix의 논리("단일 X는 다루는데 X[]가 빠졌다")를 그대로
같은 식에 재적용하면, `type.isAnnotation()` 계열(nested annotation 속성)도 probe
목록에 없다는 사실이 보인다. nested annotation 타입이 classpath에서 사라진 경우
같은 형태의 지연 예외가 날 수 있다면, 이번에 고친 것과 동일한 구멍이 하나 더 있는
셈이다.

처리: JDK 동작이 packet 근거로 확정되지 않았고 spec이 "enum 배열 1줄 한정"이므로
이번 PR에서는 손대지 않는다. 별도 스모크(stale nested annotation v1/v2)로 재현
여부를 확인한 뒤 재현되면 후속 이슈/PR로 분리하기로 했다. **좋은 리뷰는 diff 안의
결함만이 아니라 "이 diff의 논리가 비추는 diff 밖의 그림자"를 본다.**

감사 정정 1: 처음 기각 근거를 "금지영역"이라 적었는데, 해당 파일들은 오히려 허용
영역이다. 올바른 근거는 "enum 배열로 한정된 목표 밖 + JDK 동작 미확정". 기각
사유도 정확해야 ledger가 나중에 쓸모 있다.

### F2. 테스트 4건의 명명 축 불일치 (채택 — 개명 2건)

신규 테스트 4건 중 실패 케이스 2건은 **예외 축**(`...WhenHasEnumConstantNotPresentException...`),
양성 가드 2건은 **속성 축**(`...WhenEnumArrayAttributeDoesNotThrow...`)으로 이름
축이 갈려 있었다. 리뷰어는 속성 축 통일을 제안했지만, 메인 종합에서 **반대로 예외
축으로 통일**했다 — 이 파일의 기존 Class 계열 쌍이 이미 예외 축 관용구
(`isValidWhenHasTypeNotPresentException...` / `isValidWhenDoesNotHaveTypeNotPresentException...`)
를 쓰고 있어, 그 축에 맞추면 기존 4건과 신규 4건이 완전 병렬이 되기 때문이다.

교훈: **리뷰 지적의 채택과 제안의 채택은 별개다.** 문제 인식(축 불일치)은 받아들이되
해법은 파일의 기존 관용구를 근거로 다르게 골랐다. 테스트 이름은 검증하는 계약
(어떤 실패 시나리오인가)을 드러내는 것이 본질이고, 예외 이름이 그 계약의 구체다.

### F3. probe 추가의 비용 (채택 — 코드 무변경, 서술만)

canLoad probe는 리플렉션 실호출 + (배열 속성은) 방어 복제 alloc이 붙는다. enum
배열 속성은 실무에서 드물지 않으므로(`@RequestMapping`의 `RequestMethod[]` 등)
비용 질문은 정당하다. 사실 확인 결과 `AnnotationsScanner`의
`declaredAnnotationCache`가 element 단위로 결과를 캐시해 반복 빈도를 제한하고,
비용의 종류는 이미 통과 중인 `Class[]` probe와 동일 — 정확성을 위한 최소 비용으로
판단, 코드 변경 없이 PR 본문에 한 줄로 선점했다.

감사 정정 2: "캐시 덕에 element당 1회"는 과일반화(캐시 수명·미스마다 재발생).
검증된 표현은 "Class[] probe와 같은 종류의 비용"까지다. **실측하지 않은 정도까지
단정하지 않기.**

## open questions와 처리

findings와 별개로 리뷰어가 던진 확인 질문 네 건은 실파일 확인이나 채택으로 각각 닫혔다.

| 질문 | 처리 |
|---|---|
| 기존에 enum fixture가 있어 중복 아닌가 | 실파일 확인 — 없음(해소) |
| `String[]` 음성 가드가 없다 | **채택** — `canThrowTypeNotPresentExceptionWhenHasNonEnumArrayAttributeReturnsFalse` + `StringArrayValue` fixture 추가. 새 조건의 과확장을 막는 가드레일 |
| `canThrowTypeNotPresentException` javadoc 갱신 필요? | 실파일 확인 — 타입을 열거하지 않는 일반 서술이라 무변경이 맞음(해소) |
| "annotation이 스캔에서 사라지는" 동작 변화를 PR에 밝힐 것 | 채택 — PR 본문 Fix 절에 서술 |

## 수정 후

리뷰 반영을 마친 뒤 재실측과 타깃 재점검으로 종료했다.

- 개명 2건 + 음성 가드 1건 + fixture 1개 반영 -> `AttributeMethodsTests` 21/21
  green 재실측.
- post-fix 타깃 재점검(수정 hunks만 대상, 원 지적을 낸 쪽이 아닌 리뷰어가 수행):
  clean — 수정이 새 결함을 만들지 않았음을 확인하고 종료.

## 이 과정에서 배운 것

1줄 fix에 이만한 리뷰를 돌려서 남은 것은 관점의 독립, 감사의 대상, 범위 규율 셋이다.

1. 독립 리뷰 2곳은 관점이 실제로 갈린다(0건 vs 3건+4문). 한쪽만 믿으면 F1~F3을
   전부 놓쳤거나, 반대로 과잉 수용했을 것이다.
2. 감사는 findings만이 아니라 **메인의 판단 자체**(기각 근거의 정확성, 표현의
   과일반화)를 고친다.
3. 범위 규율: 좋은 지적(F1)이어도 spec 밖이면 이번 diff에 싣지 않고 후속으로
   분리한다 — PR의 리뷰 가능성(1줄 fix라는 명제)이 유지된다.
