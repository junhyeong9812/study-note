# PR #37053 — 테스트 해설 (테스트 하나하나)

> PR #37053 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR의 테스트 다섯 건은 두 층으로 나뉜다. `DataBufferUtilsTests`의 세 건은 매처 자체의
계약을 보고, `StringDecoderTests`의 두 건은 사용자가 실제로 겪는 증상을 본다. 결론부터
말하면 fix 전 결과 기준으로 **red 4건, 항상 green인 가드 1건**이다. 층을 기준으로 보면
"매처 층 3건 + 증상 층 2건"이고, 역할을 기준으로 보면 "결함 재현 4건 + 과잉수정 방지
가드 1건"이다. 두 분류가 겹치지 않으므로 아래에서 테스트마다 둘 다 밝힌다. red/green
판별은 실행 결과가 아니라 diff 논리 — 수정 전 `TwoByteMatcher`에 불일치 처리가 없어
`matches`가 1로 남는다는 사실 — 에서 유도했다.

## 0. 두 층이 보는 것이 왜 다른가

매처 층과 증상 층은 같은 결함을 서로 다른 배선으로 본다. 차이의 핵심은
`CompositeMatcher`의 개입 여부다.

`DataBufferUtils.matcher(delims)`에 2바이트 구분자 하나만 넘기면 `createMatcher`가
`TwoByteMatcher`를 **직접** 만든다. `CompositeMatcher`는 구분자가 둘 이상일 때만
등장한다. 그래서 매처 층 테스트 세 건은 "가장 긴 구분자 우선" 규칙이 끼어들지 않은
상태에서 `TwoByteMatcher`의 상태 기계만 홀로 관찰한다. 반환값 `-1`은 "구분자를 못
찾았다"는 뜻이고, 그것이 이 층의 계약 전부다.

반면 `StringDecoderTests`는 `StringDecoder.allMimeTypes()`를 쓰므로 기본 구분자
`\r\n`과 `\n` 두 개가 걸리고, 따라서 `CompositeMatcher` 안에 `TwoByteMatcher`와
`SingleByteMatcher`가 나란히 들어간다. 거짓 `\r\n` 매치가 진짜 `\n` 매치를 길이로
이겨서 앞 글자까지 잘라 먹는 증폭 경로가 이 층에서만 재현된다. 매처 층만 있으면
"매처가 -1을 안 준다"까지만 알 수 있고, 그것이 왜 한 글자 유실로 이어지는지는
증상 층이 맡는다.

## 1. 떨어진 두 바이트 — red (매처 층, 결함 재현)

첫 테스트는 결함의 최소 형태, 곧 `\r`과 `\n` 사이에 다른 바이트가 끼어 있는 입력을 매처에 직접 먹인다.

```java
@ParameterizedDataBufferAllocatingTest
void matcherDoesNotMatchAcrossNonContiguousDelimiterBytes(DataBufferFactory bufferFactory) {
	super.bufferFactory = bufferFactory;

	DataBuffer buffer = stringBuffer("a\rXY\nb");

	byte[] delims = "\r\n".getBytes(StandardCharsets.UTF_8);
	DataBufferUtils.Matcher matcher = DataBufferUtils.matcher(delims);
	int result = matcher.match(buffer);
	assertThat(result).isEqualTo(-1);

	release(buffer);
}
```

- **주장**: `\r`과 `\n` 사이에 다른 바이트가 끼어 있으면 `\r\n` 구분자는 매치되지
  않는다(`-1`).
- **fixture가 흉내 내는 것**: `stringBuffer("a\rXY\nb")`는 줄 안에 홀로 놓인 캐리지
  리턴이 있는 텍스트다. 사용자가 붙여 넣은 문자열, 옛 macOS 계열 개행, 텍스트로 읽히는
  준-바이너리 페이로드처럼 실제로 드물지 않은 입력을 6바이트로 압축했다.
- **fix 전 결과와 이유**: `a`에서 `matches`는 0, `\r`에서 1이 되고, `X`와 `Y`는
  기본 구현이 불일치를 처리하지 않으므로 `matches`를 1로 남긴다. 그 뒤 `\n`이
  `delimiter[1]`과 같아 `matches`가 2가 되고 매치가 성립한다. `match(DataBuffer)`는
  구분자 마지막 바이트의 인덱스, 곧 `\n`의 위치인 4를 반환한다. `-1`이 아니므로
  단언 실패, red다.
- **fix 후**: `X`에서 `getMatches() > 0 && b != delimiter()[1]`이 참이라 `setMatches(0)`,
  이후 `\n`을 만나도 `matches`는 0이라 `delimiter[0]`인 `\r`과 비교되어 불일치.
  버퍼 끝까지 매치가 없어 `-1`.
- **역할**: 이 결함의 최소 재현. mock도 스트림도 없이 매처 하나에 바이트열 하나만
  먹여 "떨어진 두 바이트는 구분자가 아니다"만 본다.

## 2. 붙어 있는 진짜 구분자 — 항상 green (매처 층, 과잉수정 가드)

둘째 테스트는 같은 매처에 연속된 진짜 구분자를 먹여 참 양성이 그대로 남는지를 본다.

```java
@ParameterizedDataBufferAllocatingTest
void matcherMatchesContiguousTwoByteDelimiter(DataBufferFactory bufferFactory) {
	super.bufferFactory = bufferFactory;

	DataBuffer buffer = stringBuffer("a\r\nb");

	byte[] delims = "\r\n".getBytes(StandardCharsets.UTF_8);
	DataBufferUtils.Matcher matcher = DataBufferUtils.matcher(delims);
	int result = matcher.match(buffer);
	assertThat(result).isEqualTo(2);

	release(buffer);
}
```

- **주장**: 연속된 `\r\n`은 여전히 매치되고, 반환 인덱스는 구분자 마지막 바이트의
  위치인 2다.
- **fix 전 green인 이유**: `\r`에서 `matches`가 1, 곧바로 `\n`이 와서 2가 되고 매치.
  되감기가 없어도 이 경로에는 아무 영향이 없다. 즉 이 테스트는 수정 전에도 통과한다.
- **존재 이유는 fix 후에 있다**: 새 오버라이드가 참 양성까지 죽이지 않았음을 고정한다.
  기대 바이트가 온 경우에는 `b != delimiter()[getMatches()]` 조건이 거짓이라 되감기를
  건너뛴다는 것이 코드의 주장인데, 그 주장을 코드가 아니라 관찰 가능한 반환값으로
  못박는다. 이 테스트가 없으면 "불일치든 아니든 무조건 `setMatches(0)`" 같은 잘못된
  수정이 침묵으로 통과한다.
- **분류**: 무회귀 질문("멀쩡한 구분자를 안 깨뜨린다는 확신은?")에 대한 직접적인
  답. ../37153/guard-tests.md의 용어로는 양성 가드에 해당한다.

## 3. 첫 바이트 반복 — red (매처 층, 되감기 재시도 경로)

셋째 테스트는 구분자 첫 바이트가 연달아 오는 입력으로 되감기 직후의 재시도 경로를 밟는다.

```java
@ParameterizedDataBufferAllocatingTest
void matcherDoesNotMatchAfterRepeatedFirstDelimiterByte(DataBufferFactory bufferFactory) {
	super.bufferFactory = bufferFactory;

	DataBuffer buffer = stringBuffer("a\r\rX\nb");

	byte[] delims = "\r\n".getBytes(StandardCharsets.UTF_8);
	DataBufferUtils.Matcher matcher = DataBufferUtils.matcher(delims);
	int result = matcher.match(buffer);
	assertThat(result).isEqualTo(-1);

	release(buffer);
}
```

- **주장**: `\r`이 연달아 온 뒤에 다른 바이트를 거쳐 `\n`이 와도 매치되지 않는다.
- **fix 전 결과와 이유**: 이 테스트도 red다. `\r`에서 `matches`가 1이 된 뒤 두 번째
  `\r`은 `delimiter[1]`인 `\n`이 아니므로 `false`를 반환하지만 `matches`는 1로 남고,
  `X`도 마찬가지다. 이어서 `\n`이 와 `matches`가 2가 되어 인덱스 4를 반환한다.
  1번과 같은 이유로 실패한다.
- **fix 후 왜 통과하나**: 두 번째 `\r`에서 `setMatches(0)`으로 되감은 다음 곧바로
  `super.match(b)`가 **같은 바이트를** `delimiter[0]`과 다시 비교한다. `\r`이므로
  `matches`가 다시 1이 된다. 그 다음 `X`에서 또 0으로 풀리고, `\n`은 `matches`가 0인
  상태에서 `\r`과 비교되어 불일치. 최종 `-1`이다.
- **1번과 다른 역할**: 같은 red이지만 겨냥하는 코드 줄이 다르다. 1번은 되감기의
  **존재**를 요구하고, 이 테스트는 되감기 직후 `super.match(b)`에 위임하는 **순서**가
  살아 있는지를 본다. 되감은 그 바이트가 새 구분자의 시작일 수 있다는 성질을 실제로
  밟는 유일한 입력이다.
- **판별 근거 부족 지점**: 다만 이 테스트가 "위임을 뺀 잘못된 수정"까지 잡아내지는
  못한다. `setMatches(0); return false;`처럼 위임 없이 되감기만 하는 구현으로도
  `"a\r\rX\nb"`는 `-1`이 나온다. 위임 누락을 실제로 드러내려면 `"a\r\r\nb"`처럼
  되감은 바이트가 진짜 구분자의 시작이 되는 입력이 필요한데, 이 PR에는 그 입력이
  없다. 이 테스트는 되감기 후 상태가 오염되지 않았음을 보장할 뿐, 위임 순서 자체를
  단독으로 고정하지는 않는다.

## 4. 한 버퍼 안의 증상 — red (증상 층)

넷째 테스트는 매처가 아니라 디코더를 통해, 사용자가 실제로 보는 문자열이 무엇인지를 고정한다.

```java
@Test
void decodePreservesCharacterBeforeLoneNewlineAfterCarriageReturn() {
	Flux<DataBuffer> input = Flux.just(stringBuffer("a\rXY\nb"));

	testDecode(input, String.class, step -> step
			.expectNext("a\rXY")
			.expectNext("b")
			.expectComplete()
			.verify());
}
```

- **주장**: 홀로 있는 `\n` 앞의 글자는 본문이므로 보존된다. 첫 줄은 `a\rXY`이고,
  구분자 없이 남은 꼬리 `b`가 두 번째 값으로 나온 뒤 스트림이 완료된다.
- **fixture가 흉내 내는 것**: `Flux.just(stringBuffer(...))`는 WebFlux가 네트워크에서
  받아 넘기는 `DataBuffer` 스트림이다. `testDecode`는 `AbstractDecoderTests`가 제공하는
  헬퍼로, 디코더에 그 스트림을 먹이고 결과를 `StepVerifier`로 검사한다.
  `expectNext`/`expectComplete`/`verify` 체인이 리액티브 스트림의 발행 순서와 종료를
  한 줄씩 단언하는 방식이다.
- **fix 전 결과와 이유**: 1번과 같은 상태 오염이 일어나되, 여기서는
  `CompositeMatcher`가 개입한다. `\n` 위치에서 진짜 `\n`(길이 1)과 거짓 `\r\n`(길이 2)이
  모두 매치되고 "가장 긴 것 우선" 규칙이 후자를 고른다. 그러면
  `AbstractCharSequenceDecoder.processDataBuffer`가 구분자 길이 2만큼 뒤에서 잘라내
  `a\rXY\n` 5바이트에서 `a\rX`가 남는다. 첫 `expectNext("a\rXY")`가 실패해 red다.
  본문이던 `Y`가 예외도 로그도 없이 사라지는 것이 이 결함의 사용자 관점 증상이다.
- **매처 층과 중복이 아닌 이유**: 매처 층은 `-1`이라는 내부 반환값을, 이 층은
  "디코딩된 문자열"이라는 공개 관찰값을 고정한다. 매처가 고쳐져도 디코더 쪽 잘라내기
  계산이 다르게 틀어지면 이 테스트만 깨진다.

## 5. 버퍼 경계를 넘는 증상 — red (증상 층)

다섯째 테스트는 같은 페이로드를 두 버퍼로 쪼개, 부분 일치 상태가 호출 경계를 넘을 때도 결과가 같은지를 본다.

```java
@Test
void decodePreservesCharacterAcrossBuffersAfterCarriageReturn() {
	Flux<DataBuffer> input = Flux.just(
			stringBuffer("a\r"),
			stringBuffer("Xb\n")
	);

	testDecode(input, String.class, step -> step
			.expectNext("a\rXb")
			.expectComplete()
			.verify());
}
```

- **주장**: `\r`이 한 버퍼의 끝에, 그 뒤 내용이 다음 버퍼에 있어도 결과는 같다 —
  `a\rXb` 한 줄이 나오고 끝난다.
- **fixture가 흉내 내는 것**: 같은 페이로드가 네트워크 사정에 따라 두 조각으로 쪼개져
  도착하는 실제 스트리밍 상황이다. 두 번째 버퍼가 `\n`으로 끝나므로 꼬리 값이 없고,
  그래서 `expectNext`가 하나뿐이다.
- **fix 전 결과와 이유**: 실제 내용은 `a\rXb\n`이고, 첫 버퍼에서 세워진
  `matches == 1` 상태가 **다음 `match(DataBuffer)` 호출까지 살아남는다**. 두 번째
  버퍼의 `X`, `b`가 상태를 풀지 못하고 `\n`에서 거짓 `\r\n`이 완성되어 뒤 2바이트가
  잘린다. 결과는 `a\rX`이므로 단언 실패, red다.
- **4번과 다른 역할**: 4번은 되감기가 **한 호출 안에서** 작동하는지를 보고, 이
  테스트는 되감기가 **호출 경계를 넘어** 작동하는지를 본다. 매처가 상태를 호출 사이에
  유지한다는 것은 이 클래스의 본질적 성질이므로, 그 성질과 새 되감기가 함께 놓였을 때도
  옳은지를 따로 고정할 값어치가 있다. 앞의 네 테스트는 전부 단일 호출이라 이 축을
  덮지 못한다.

## fixture

이 PR은 새 fixture 타입을 만들지 않았다. 다섯 테스트가 쓰는 재료는 전부 기존
테스트 기반 클래스의 것이다.

매처 층은 `AbstractDataBufferAllocatingTests`를 상속한 `DataBufferUtilsTests`에 붙었다.

```java
protected DataBuffer stringBuffer(String value) {
	return byteBuffer(value.getBytes(StandardCharsets.UTF_8));
}

protected void release(DataBuffer... buffers) {
	Arrays.stream(buffers).forEach(DataBufferUtils::release);
}
```

`stringBuffer`는 문자열을 UTF-8 바이트로 만들어 현재 팩토리가 할당한 버퍼에 쓴다.
테스트 입력이 문자열로 읽히면서도 실제로는 바이트열로 매처에 들어간다는 뜻이다.
`release`는 풀링 버퍼의 참조 카운트를 되돌려 누수를 막는 정리 호출이며, 단언이 아니다.

`@ParameterizedDataBufferAllocatingTest`는 이 파일의 관용구다.

```java
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
@ParameterizedTest
@MethodSource("org.springframework.core.testfixture.io.buffer.AbstractDataBufferAllocatingTests#dataBufferFactories()")
public @interface ParameterizedDataBufferAllocatingTest {
}
```

`dataBufferFactories()`가 Netty 4의 풀/비풀 × 힙/오프힙 네 가지와 기본 팩토리 두 가지,
합계 여섯 조합을 흘려보낸다. 즉 매처 층 테스트 세 건은 실제로는 열여덟 번 실행된다.
버퍼 구현마다 `forEachByte` 순회 방식이 다를 수 있으므로, 상태 기계 수정이 특정 할당기에만
맞는 것이 아님을 부수적으로 덮어 준다. 첫 줄 `super.bufferFactory = bufferFactory;`가
주입된 팩토리를 기반 클래스에 꽂아 `stringBuffer`가 그 팩토리를 쓰게 만든다.

증상 층은 `AbstractDecoderTests<StringDecoder>`를 상속한 `StringDecoderTests`에 붙었고,
디코더는 생성자에서 고정된다.

```java
StringDecoderTests() {
	super(StringDecoder.allMimeTypes());
}
```

`allMimeTypes()`가 기본 구분자 `\r\n`, `\n`을 쓰므로 `CompositeMatcher` 경로가 자동으로
켜진다. 두 증상 테스트가 별도 설정 없이 "가장 긴 것 우선" 규칙까지 포함해 재현되는
이유다.

## 분류와 역할 요약

다섯 테스트를 fix 전 결과와 층으로 정리하면 다음과 같다. 판별 근거는 diff 논리이며
실행으로 측정한 값이 아니다.

| 테스트 | 층 | fix 전 | 고정하는 것 |
|---|---|---|---|
| `matcherDoesNotMatchAcrossNonContiguousDelimiterBytes` | 매처 | red | 되감기의 존재 |
| `matcherMatchesContiguousTwoByteDelimiter` | 매처 | green | 참 양성 보존 |
| `matcherDoesNotMatchAfterRepeatedFirstDelimiterByte` | 매처 | red | 되감기 후 상태 무오염 |
| `decodePreservesCharacterBeforeLoneNewlineAfterCarriageReturn` | 증상 | red | 한 버퍼 안에서 글자 보존 |
| `decodePreservesCharacterAcrossBuffersAfterCarriageReturn` | 증상 | red | 호출 경계를 넘는 글자 보존 |

정리하면 red 4건, 항상 green인 가드 1건이다. 가드가 하나뿐인 것은 이 수정이 좁기
때문이다. 바꾼 것은 거짓 양성을 만드는 상태 잔류 하나이고, 그 상태 잔류에 의존하는
정상 동작은 존재하지 않는다. 그래서 보존해야 할 축도 하나 — "붙어 있는 진짜 구분자는
여전히 매치된다" — 뿐이고, 2번이 그것을 단독으로 맡는다.

red 4건이 서로 중복이 아닌 이유는 각자 다른 축을 밟기 때문이다. 1번은 결함의 최소 형태,
3번은 되감기 이후의 상태, 4번은 `CompositeMatcher`를 거친 사용자 관찰값, 5번은 호출
경계를 넘는 상태 유지다. 어느 하나를 지워도 남은 테스트로는 덮이지 않는 구멍이 생긴다.
