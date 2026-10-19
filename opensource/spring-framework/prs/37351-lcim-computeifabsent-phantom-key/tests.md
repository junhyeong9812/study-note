# PR #37351 - 테스트 해설 (테스트 하나하나)

배치 전체를 먼저 본다.\
이 결함은 **매핑 함수의 결과가 셋 중 무엇이냐**와 **키가 새 키냐 기존 키냐**의 조합으로 갈린다.\
그래서 새 테스트 다섯이 그 격자의 빈칸을 하나씩 맡는 구도가 된다.\
두 축으로 줄 세우면 이렇다.

> **red 테스트 / 가드 테스트** — red는 수정 전에 반드시 실패해야 하는 테스트, 가드는 수정 전후 모두 통과해야 하는 테스트.\
> 예: red 가 없으면 결함을 겨냥하지 못한 것이고, 가드가 깨지면 기존 동작을 망가뜨린 것이다.

| | 함수가 non-null | 함수가 null | 함수가 예외 |
|---|---|---|---|
| 새 키 | 기존 `computeIfAbsentWithComputedValue` - 가드 / **T5 즉시 축출 - B안 red** | **T1 (A) - red** / **T2 (B) - red** | **T3 (C) - red** |
| 기존 키(값 non-null) | 기존 `computeIfAbsentWithExistingValue` 앞부분 - 가드 | (함수가 불리지 않음) | (함수가 불리지 않음) |
| 기존 키(값 null) | 기존 `computeIfAbsentWithExistingValue` 뒷부분 + **단언 1줄 추가(F4)** - 가드 | **T4 (D) - 가드(F2)** | (테스트 없음 - blind 18번이 덮음) |

같은 배치를 세 버전(수정 전, B안, 최종)의 결과까지 넣은 격자로 보면 각 칸이 무엇을 덮는지가 드러난다.

```text
                                    | 수정 전 |  B 안  |  최종  |  덮는 것
------------------------------------+---------+--------+--------+-------------------------
T1 null 반환 (A)                    |  FAIL   |  PASS  |  PASS  |  팬텀이 남지 않는가
T2 팬텀 표기 누출 (B)               |  FAIL   |  PASS  |  PASS  |  다음 삽입이 오염되지 않는가
T3 예외 (C)                         |  FAIL   |  PASS  |  PASS  |  선등록이 없는가
------------------------------------+---------+--------+--------+-------------------------
T4 기존 null 값 + null 반환 (D)     |  PASS   |  PASS  |  PASS  |  과잉 수정이 없는가
T5 즉시 축출 (E)                    |  PASS   |  FAIL  |  PASS  |  등록 시점이 훅보다 앞인가
------------------------------------+---------+--------+--------+-------------------------
기존 테스트 18 건                   |  PASS   |  PASS  |  PASS  |  무회귀
```

-> T5 한 줄만 모양이 다르다. 수정 전에는 맞고 B안에서 틀리는, **수정이 만든 결함**을 잡는 테스트이기 때문이다.

이 결과는 문서화 단계에서 커밋된 `LinkedCaseInsensitiveMapTests`(23건)를 세 버전 클래스에 대해 JUnit 6.1.2 launcher로 돌려 재확인했다 - "orig: 3 fail (null, casing, exception) / B: 1 fail (`computeIfAbsentWithImmediatelyEvictedEntry`) / final: 0 fail".

## 테스트 코드가 람다를 하드코딩하는 이유

다섯 테스트 모두 매핑 함수를 `key -> null`, `key -> "value"`, `key -> { throw new IllegalStateException(); }`처럼 한 줄로 박아 넣는다.\
이해 게이트 중에 "실제 함수를 넣어야지 왜 널과 벨류 하드코딩 값을 넣냐"는 질문이 나왔고, 그 답이 이 테스트 배치의 설계 원리다.

`computeIfAbsent` 입장에서 매핑 함수는 속을 볼 수 없는 상자다.\
맵은 그 안에서 DB를 조회했는지 파일을 읽었는지 모르고, **결과가 셋 중 무엇인지**에만 반응한다.

| 람다의 결과 | 맵이 해야 할 일 |
|---|---|
| non-null 값 | 저장하고 색인에 등록 |
| null | 아무것도 남기지 않음 |
| 예외 | 예외를 전파하고 아무것도 남기지 않음 |

이 셋이 맵이 받을 수 있는 입력의 전부라서, 각각을 가장 작게 재현한 스텁을 넣으면 빠짐없이 검증된다.

> **스텁(stub)** — 협력자를 대신해 정해진 결과만 돌려주는 가짜 구현.\
> 예: "조회 결과가 없어서 null"이라는 상황을 `key -> null` 한 줄로 만든다.

실제 조회 함수를 넣으면 조회 대상을 테스트 안에 만들어야 하고, 테스트가 깨졌을 때 맵 문제인지 함수 문제인지 구분이 어려워진다.\
기존 테스트도 같은 방식이다(`computeIfAbsent("key", key2 -> "value1")`).

## T1. `computeIfAbsentWithNullComputedValue` - red (A)

```java
@Test
void computeIfAbsentWithNullComputedValue() {
	assertThat(map.computeIfAbsent("Key", key -> null)).isNull();
	assertThat(map).isEmpty();
	assertThat(map.containsKey("key")).isFalse();
}
```
(LinkedCaseInsensitiveMapTests.java:120-125)

- **주장**: 함수가 null을 돌려주면 저장소도 색인도 비어 있어야 한다.
- **수정 전 red인 이유**: 색인에 `"key" -> "Key"`가 선등록된 채로 남아 `containsKey("key")`가 true가 된다.

### 두 단언을 같이 두는 이유

이 테스트에서 가장 중요한 설계는 **`isEmpty()`와 `containsKey()`를 나란히 둔 것**이다.\
두 단언이 서로 다른 맵을 읽기 때문이다.

| 단언 | 읽는 맵 | 수정 전 |
|---|---|---|
| `assertThat(map).isEmpty()` | 저장소 - `isEmpty()`는 `targetMap.isEmpty()`(:153-155) | **통과** |
| `containsKey("key")` -> `isFalse()` | 색인 - `caseInsensitiveKeys.containsKey(...)`(:158-160) | **실패** |

`isEmpty()`만 있었다면 수정 전 버그를 잡지 못한다 - 팬텀은 저장소에 아무것도 남기지 않으니까.\
`containsKey()`만 있었다면 저장소가 비어 있다는 것을 확인하지 못한다.\
**둘을 함께 써야 "두 맵이 모두 비어 있고 서로 일치한다"가 고정된다.**\
이 테스트가 결함을 보는 쪽은 `containsKey`이고, `isEmpty`는 "크기는 0"이라는 반대편을 지키는 가드다.

두 단언이 각각 어느 맵을 덮는지 세로로 그리면 이렇다.

```text
        computeIfAbsent("Key", key -> null) 직후
                        |
         +--------------+--------------+
         |                             |
         v                             v
   targetMap (저장소)            caseInsensitiveKeys (색인)
   수정 전: {}                   수정 전: {"key" -> "Key"}
   수정 후: {}                   수정 후: {}
         |                             |
         v                             v
   isEmpty()  -> 전후 모두 통과   containsKey("key") -> 수정 전 실패
         |                             |
         +--------------+--------------+
                        |
                        v
          둘 다 있어야 "두 맵 일치" 가 고정된다
```

이 질문이 diff 1 이해 게이트의 첫 문항이었다([gates.md](gates.md) G1).

## T2. `computeIfAbsentAfterNullComputedValueUsesGivenKey` - red (B)

```java
@Test
void computeIfAbsentAfterNullComputedValueUsesGivenKey() {
	assertThat(map.computeIfAbsent("Key", key -> null)).isNull();
	assertThat(map.computeIfAbsent("KEY", key -> "value")).isEqualTo("value");
	assertThat(map.keySet()).containsExactly("KEY");
}
```
(LinkedCaseInsensitiveMapTests.java:127-132)

- **주장**: 실패한 호출은 다음 호출의 표기에 영향을 주지 않는다.
- **수정 전 red인 이유**: 두 번째 호출이 팬텀 `"Key"`를 기존 키로 착각해 gh-26868 분기(`key = oldKey`)를 타고, 값을 `"Key"`로 저장한다.\
  실측 red - `keySet()`이 `["Key"]`.

이 테스트는 **두 번의 서로 다른 호출**로 되어 있다는 점이 처음에 헷갈렸다.\
"람다가 value로 바뀌면 저장된다"는 말을 테스트의 주장으로 읽으면 안 된다.\
두 번째 호출은 원래 정상적으로 저장되는 호출이고, 이 테스트가 보는 것은 **어떤 표기로 저장되느냐**다.

| 확인 대상 | 테스트 줄 | 기대 |
|---|---|---|
| 값 | 두 번째 호출의 반환값 `.isEqualTo("value")` | 람다가 만든 `"value"` |
| 키 표기 | `keySet()` `.containsExactly("KEY")` | 호출자가 넘긴 표기 그대로 `"KEY"` |

값 `"value"`는 "값이 하나 들어갔다"는 것을 나타내는 임의의 표식이다.\
게이트 중에 "값을 `KEY` 문자열로 넣는 게 맞지 않냐"는 질문이 나왔고, 메인이 대안으로 `key -> key`(람다가 받은 키를 그대로 값으로 반환)를 제안했다.\
수정 전에는 람다가 바꿔치기된 `"Key"`를 받으므로 표기 오염이 값에서도 드러나는 형태다.\
다만 `keySet().containsExactly("KEY")`가 같은 것을 더 직접적으로 확인하므로, 사용자는 현행 유지를 선택했다.

## T3. `computeIfAbsentWithFailingMappingFunction` - red (C)

```java
@Test
void computeIfAbsentWithFailingMappingFunction() {
	assertThatIllegalStateException().isThrownBy(() ->
			map.computeIfAbsent("Key", key -> { throw new IllegalStateException(); }));
	assertThat(map).isEmpty();
	assertThat(map.containsKey("key")).isFalse();
}
```
(LinkedCaseInsensitiveMapTests.java:134-140)

- **주장**: 함수가 예외를 던지면 예외가 전파되고, 두 맵 모두 비어 있다.
- **수정 전 red인 이유**: T1과 같다 - 선등록이 남아 `containsKey`가 true.

### T1과 결함이 같은데 따로 둔 이유

이 테스트가 T1과 결함이 같으면서도 따로 있어야 하는 이유는 **수정 후 코드에서 두 경우가 막히는 지점이 다르기 때문**이다.\
최종 코드의 새 키 경로로 따라가면 이렇다.

```text
targetMap.computeIfAbsent(key, k -> {
	V value = mappingFunction.apply(k);       <- (가)
	if (value != null) {                      <- (나)
		caseInsensitiveKeys.putIfAbsent(...); <- (다) 등록
	}
	return value;                             <- (라)
});

  null 반환 (T1)                     예외 (T3)
  (가) 정상 통과                      (가) 에서 예외 발생
  (나) 거짓 -> (다) 건너뜀            (나) (다) (라) 실행 안 됨
  (라) null 반환                      람다 -> computeIfAbsent -> 호출자로 전파
  HashMap 이 삽입하지 않음            HashMap 도 삽입하지 않음
```

T1은 (나)의 null 조건이 막아 주는 경로라서, **등록이 함수 실행보다 앞인지 뒤인지**를 검증하지 못한다.\
선등록 + null이면 지우기 같은 구조도 T1은 통과한다.\
T3만이 두 가지를 고정한다 - 함수 실행 전에 색인을 미리 등록하지 않는다는 **순서**, 그리고 try/finally 같은 **정리 코드가 필요 없다**는 점.

이것이 diff 1 게이트 두 번째 문항이었고, 2회차까지 오답이 이어진 문항이다([gates.md](gates.md) G1).

## T4. `computeIfAbsentWithNullComputedValueForExistingNullValue` - 가드 (D, 리뷰 F2)

```java
@Test
void computeIfAbsentWithNullComputedValueForExistingNullValue() {
	assertThat(map.put("Key", null)).isNull();
	assertThat(map.computeIfAbsent("KEY", key -> null)).isNull();
	assertThat(map).hasSize(1);
	assertThat(map.containsKey("key")).isTrue();
	assertThat(map.keySet()).containsExactly("Key");
}
```
(LinkedCaseInsensitiveMapTests.java:142-149)

- **주장**: `put`으로 명시한 null 값 항목은, 이후 함수가 null을 돌려줘도 그대로 남는다.
- **수정 전후 모두 green**: 이 경로는 동작이 바뀌지 않았다.

이 테스트에서 `hasSize(1)`과 `containsKey` true가 **맞는 결과**라는 점이 diff 4 게이트에서 오답으로 나왔다("사이즈가 1이 되면 안되는거 아니야? 0이여야 되는게 맞지않나?").\
핵심은 **null의 두 의미**를 구분하는 것이다.

| 호출 | 의미 | 항목 |
|---|---|---|
| `put("Key", null)` | "Key의 값은 null이다"라고 **명시적으로 저장** | 생긴다(`{Key=null}`), 색인 등록이 맞다 |
| `computeIfAbsent("Key", k -> null)` | "값을 만들어 봤는데 **못 만들었다**" | 안 생긴다, 색인 등록도 안 한다 |

`Map`은 null을 값으로 허용하므로, `put`으로 넣은 null은 "값이 null인 실제 항목"이다.\
그 다음 `computeIfAbsent("KEY", key -> null)`은 **기존 키 경로**를 탄다(`oldKey = "Key"`, 값이 null이라 `targetMap.computeIfAbsent("Key", ...)`).\
JDK `HashMap.computeIfAbsent`는 기존 노드가 있고 함수가 null을 돌려주면 그냥 `return null` 한다 - 기존 노드를 지우지 않는다.\
"null이면 기록하지 않는다"는 **새 매핑을 만들지 않는다**는 뜻이지 기존 항목을 지운다는 뜻이 아니다.

| | T1 (A) | T4 (D) |
|---|---|---|
| 시작 | 빈 맵 | `put("Key", null)`으로 항목 1개 |
| 경로 | 새 키(감싼 람다) | 기존 키(원래 함수) |
| null 반환 결과 | 아무것도 안 생김 -> size 0 | 기존 항목 유지 -> size 1 |

이 테스트가 막는 것은 **과잉 수정**이다.\
만약 수정을 "함수가 null이면 색인에서 지운다"는 식으로 했다면, 이 경우에 저장소에는 `"Key"=null`이 있는데 색인만 사라지는 **반대 방향의 불일치**가 생긴다.\
리뷰 F2가 "명세 §2가 보존을 요구한 동작(기존 null 값 키는 저장된 표기로 계산)에 테스트가 없다"고 지적해 추가됐다.\
blind 워커는 이 칸에 null 반환(17번)과 예외(18번) 둘을 설계했는데, 사용자가 레포에는 null 1건만 넣기로 골랐다.

## T5. `computeIfAbsentWithImmediatelyEvictedEntry` - B안 red (E, 리뷰 F1)

```java
@Test
void computeIfAbsentWithImmediatelyEvictedEntry() {
	LinkedCaseInsensitiveMap<String> evictingMap = new LinkedCaseInsensitiveMap<>() {
		@Override
		protected boolean removeEldestEntry(Map.Entry<String, String> eldest) {
			return true;
		}
	};
	assertThat(evictingMap.computeIfAbsent("Key", key -> "value")).isEqualTo("value");
	assertThat(evictingMap).isEmpty();
	assertThat(evictingMap.containsKey("key")).isFalse();
}
```
(LinkedCaseInsensitiveMapTests.java:151-162)

- **주장**: 삽입하자마자 축출되는 항목은 저장소에서도 색인에서도 사라진다.
- **수정 전**: green - 선등록이 축출 훅보다 앞이라 훅이 함께 지웠다.
- **B안**: red - 등록이 축출 훅보다 뒤라, 이미 축출된 키가 다시 등록된다. `containsKey("key")`가 true.
- **최종**: green - 람다 안 등록이 삽입보다 앞이다.

`removeEldestEntry`가 **항상 true**를 돌려주는 서브클래스는 실전 구성이 아니라, "방금 넣은 항목이 같은 호출 안에서 축출된다"는 상황을 가장 작게 만드는 장치다.\
리뷰어는 실전에서 같은 상황이 나는 예로 "max size 0" 또는 값 기반 술어를 들었다.\
프레임워크 안에 `removeEldestEntry`를 오버라이드하는 이 클래스의 서브클래스는 없다(1회차 Opus 리뷰의 grep, 문서화 워커 재확인).\
그래도 이 메서드는 `protected` 확장점으로 javadoc까지 달려 있어(:341-349) 외부 서브클래스가 쓸 수 있다.

> **확장점(extension point)** — 서브클래스가 오버라이드해 동작을 바꾸도록 일부러 열어 둔 메서드.\
> 예: `protected boolean removeEldestEntry(...)`는 기본값 false지만, 서브클래스가 크기 제한 캐시를 만들 때 오버라이드한다.

지역 변수 이름이 `evictingMap`인 것도 이유가 있다.\
처음 적용은 지역 변수명을 `map`으로 썼는데, 테스트 클래스의 필드 `map`(:35)과 이름이 겹쳐 게이트 후 `evictingMap`으로 정리했다.

이 테스트는 **명세의 원래 테스트 계획에 없었다.**\
명세 §5의 red 테스트는 A·B·C 셋이었고, B안은 그 셋을 전부 통과했다.\
축출이라는 경계는 리뷰어 둘과 blind 워커가 각자 독립적으로 찾았다.

## 기존 테스트에 더한 한 줄 - `computeIfAbsentWithExistingValue` (리뷰 F4)

```java
	assertThat(map.put("null", null)).isNull();
	assertThat(map.putIfAbsent("NULL", "value")).isNull();
	assertThat(map.put("null", null)).isEqualTo("value");
	assertThat(map.computeIfAbsent("NULL", s -> "value")).isEqualTo("value");
	assertThat(map.get("null")).isEqualTo("value");
	assertThat(map.keySet()).containsExactly("Key", "null");   // 추가
```
(LinkedCaseInsensitiveMapTests.java:105-110)

이 부분은 기존 키가 null 값을 가진 상태에서 non-null을 계산하는 경로 - 최종 코드의 `return this.targetMap.computeIfAbsent(oldKey, mappingFunction)`(:232) - 를 탄다.\
리뷰 F4는 이 경로의 **저장 표기**를 단언하는 테스트가 없다고 지적했다.\
기존 마지막 단언 `get("null")`은 색인을 거쳐 조회하므로 저장소의 실제 키 목록을 보지 않는다.

여기에는 정정된 기록이 하나 있다.\
메인은 처음에 "변이 m1(:232의 `oldKey`를 `key`로 바꾼 것)을 새 단언이 잡는다"고 보고했다.\
문서화 단계에서 다시 확인하니 m1을 잡은 것은 **기존 단언 `get("null")`(:109)**이었다.\
새 단언 `keySet().containsExactly("Key", "null")`(:110)은 다른 변이를 혼자 잡는다 - 기존 null 값 경로를 "apply 후 `put`"으로 바꾼 변이 m2에서 `keySet()`이 `["Key","NULL"]`이 되는 것을.

> **변이 테스트(mutation test)** — 코드를 일부러 조금 틀리게 바꿔 보고, 테스트가 그것을 실제로 잡는지 확인하는 방법.\
> 예: `oldKey`를 `key`로 바꿔 돌렸을 때 실패하는 단언이 있어야 그 줄이 테스트로 보호된다고 말할 수 있다.

두 변이와 그것을 잡는 단언을 나란히 놓으면 이렇다.

```text
        변이 m1                                변이 m2
  computeIfAbsent(key, f)               기존 null 값 경로를
  (oldKey 대신 key)                     apply 후 put 으로
+-----------------------------+     +-----------------------------+
| 저장소에 "null" 과 "NULL" 이 |     | keySet = ["Key", "NULL"]    |
| 둘 다 생긴다                |     |                             |
+-----------------------------+     +-----------------------------+
| 잡는 단언:                  |     | 잡는 단언:                  |
|   get("null")  (:109, 기존) |     |   keySet()...  (:110, 신규) |
+-----------------------------+     +-----------------------------+
```

-> 새 단언의 가치는 있지만, 그 가치를 설명한 첫 보고는 틀렸다. 실패한 줄 번호를 확인하지 않은 탓이다.

## 무회귀 가드 - 기존 테스트 18건

새 테스트가 결함 경로를 맡는 동안, 나머지 경로가 그대로임을 고정하는 쪽은 이미 있던 18건이다.\
이 수정과 직접 맞닿는 둘은 이렇다.

| 테스트 | 지키는 것 | 이 수정과의 관계 |
|---|---|---|
| `computeIfAbsentWithExistingValue` (:96-111) | 기존 non-null 값이면 함수 미호출·기존 값 반환, 기존 null 값이면 저장된 표기로 계산 | **기존 키 경로 전체의 가드.** F4 단언으로 표기까지 고정 |
| `computeIfAbsentWithComputedValue` (:113-118) | 새 키는 계산해 저장, 대소문자만 다른 두 번째 호출은 기존 값 반환 | **새 키 non-null 경로의 가드.** 감싼 람다가 등록을 제대로 하는지 |

나머지(`putAndGet`, `putWithOverlappingKeys`, `getOrDefault`, `mapClone`, keySet/values/entrySet 제거 계열 등)는 `computeIfAbsent`를 거치지 않거나 새 키 경로로만 거치므로 동작이 바뀌지 않는다.\
1회차 Opus 리뷰가 "keySet/values/entrySet removal-then-computeIfAbsent tests use a fresh key path and stay valid"로 확인했다.

## blind 테스트 26건 - 레포에 넣지 않은 테스트 설계

stakes를 높음으로 올린 뒤, 구현 diff를 열람하지 않는 계약으로 blind 테스트 워커를 돌렸다.\
워커가 읽은 것은 명세 계약 발췌(`spec-contract.md`)와 upstream 원본 클래스·테스트 두 파일뿐이다.\
26건을 설계했고, 메인이 레포를 건드리지 않고 스크래치에서 세 버전에 대해 돌렸다.

| 버전 | 결과 |
|---|---|
| 수정 전(원본) | 16 fail |
| B안 | **1 fail** - `computeIfAbsentWhenNewEntryIsImmediatelyEvicted` |
| 최종(래핑) | **26/26** |

26건의 묶음은 이렇다.

| 묶음 | 건수 | 대표 |
|---|---|---|
| null 반환 - 기록 없음·색인 일치 | 7 | `getOrDefault`가 기본값을 돌려주는가(수정 전은 null), entrySet·forEach·equals·remove 관측 |
| 예외 - 전파·기록 없음 | 3 | `RuntimeException`이 아닌 `Error`도 흔적을 안 남기는가(RuntimeException만 처리하는 정리 코드를 잡음) |
| 표기 누출 없음 | 4 | 실패 뒤 `putIfAbsent`/`computeIfAbsent`/`put`이 호출자 표기를 쓰는가 |
| 기존 non-null 값 보존 | 1 | 함수 호출 횟수 0 |
| 기존 null 값 보존 | 3 | 저장된 표기로 계산, null 반환·예외에도 기존 항목 유지 |
| 새 키 표기 보존 | 1 | 삽입 순서와 호출자 표기 |
| 확장점과 기타 관측 | 7 | `convertKey` 오버라이드, 터키어 Locale, `removeEldestEntry` 축출, **즉시 축출**, clone, 직렬화 |

레포에 넣은 것은 사용자 선택으로 둘이다 - 즉시 축출 1건(T5)과 F2에 해당하는 기존 null 값 + null 반환 1건(T4).\
26건 전부는 PR로서 너무 많다는 판단이었다.

> **blind 테스트(blind test)** — 구현을 보지 않고 명세만으로 설계한 테스트.\
> 예: 구현자가 생각하지 못한 경계를, 구현을 모르는 쪽이 계약만 보고 찾아낼 수 있다.

## 실측 요약

| 단계 | 실행 | 결과 |
|---|---|---|
| task 01 red | `LinkedCaseInsensitiveMapTests` | **21 tests, 3 failed**(신규 3건 전부 - A·C containsKey true, B keySet ["Key"]), 기존 18 green |
| task 02 (B안) | 같은 클래스 / `:spring-core:test` + checkstyle | 21/0 / 5260 tests 0 failures(스킵 4), checkstyle exit 0 |
| diff 3 (래핑) 병합 후 | 같은 클래스 | 21/0 |
| diff 4 후 | `spring-core` / 사용처 모듈 | 5262/0 · web 88 · messaging 153 · test 80 · jdbc 1026 /0 |
| diff 5 후 | `spring-core` / 변이 | 5262/0, checkstyle · m1(oldKey->key) 1 fail로 포착 · m0 23/0 |
| diff 6 후 | util 테스트 + codex 타깃 재점검 | exit 0 · Findings: none |
| 머지 전 안전선 | `spring-core` / checkstyle / 스모크 | 5262/0 · Main/Test 통과 · U2Smoke·Evict·Reentrant·Trace 정상 |

diff 규모는 2파일, +56/-5다(main +10/-5, 테스트 +46).

## 커밋에 남기지 않은 실행 프로브

테스트로 커밋한 것 외에, 별도 클래스를 만들어 돌리고 결과만 취한 확인이 여럿 있다.\
결함 판정과 수정 검증의 근거이므로 기록해 둔다.

> **프로브(probe)** — 커밋하지 않고 한 번 돌려 사실만 확인하고 버리는 임시 실행 코드.\
> 예: 서브클래스로 축출을 강제해 보는 작은 `main` 하나.

| 프로브 | 무엇을 확인했나 | 결과 |
|---|---|---|
| `U2Smoke.java` | 수정 전 A·B·C 재현, 수정 후 재실행 | 전: A size=0·containsKey=true / B stored [Key] / C 예외 후 containsKey=true. 후: containsKey=false, stored [KEY] |
| `CaseDemo` | 대소문자 변형 `put`/`computeIfAbsent` 동작 | `put(Key,v1)` -> `{Key=v1}`, `computeIfAbsent(key,..)` -> v1 반환·표기 유지, `put(key,v3)` -> `{key=v3}` size 1 |
| `Trace.java` | 경우 1(빈 맵에 "KEY")·경우 2(`put("Key",null)` 뒤 "KEY") 실행 추적 | 경우 1 저장소 `{KEY=value}`, 경우 2 `{Key=null}` -> `{Key=value}` |
| `Evict.java` | 즉시 축출 서브클래스 | B안 size=0·containsKey=true(팬텀), `put`은 정상, 래핑은 containsKey=false |
| `Reentrant.java` | 매핑 함수 안 같은 맵 `put("KEY","x")` | 람다 안 `put`: get(key)=null·remove 후 size=1 / `putIfAbsent`: get(key)=x·remove 후 size=0 |
| `JdkOrder.java` | 일반 `LinkedHashMap`의 호출 순서 | apply -> 삽입 -> `removeEldestEntry`. 기존 null 항목 위 null 반환은 `{Key=null}` 유지 |

`CaseDemo`는 계획 이해 게이트 중 "Key가 있을 때 key를 등록하려고 하면 어떻게 되는거야?"라는 질문에 답하려고 돌린 것이다.\
대소문자만 다른 키는 항상 1개로 취급되고, `put`은 표기를 마지막으로 넣은 것으로 바꾸며, `computeIfAbsent`는 기존 값을 돌려주고 표기를 바꾸지 않는다.

스크래치 재현에서 한 번 함정이 있었다.\
래핑 프로토타입의 첫 `Evict` 실행이 상대경로 classpath 때문에 레포 빌드(당시 B안)를 로드해 "여전히 실패"로 나왔다.\
절대경로로 다시 돌려 정상임을 확인했고, 문서화 단계의 프로브는 각 실행이 로드한 클래스 위치를 출력하게 해 같은 실수를 막았다.
