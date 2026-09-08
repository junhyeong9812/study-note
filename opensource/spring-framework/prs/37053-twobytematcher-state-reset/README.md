# PR #37053 — Reset TwoByteMatcher partial match on mismatching byte

## 0. 정향

이 PR은 `DataBufferUtils` 안의 두 바이트 구분자 매처가 부분 일치 상태를 풀지 않아, 떨어져 있는 두 바이트를 하나의 구분자로 오인하던 버그를 고친다. 결과적으로 WebFlux의 `StringDecoder`가 줄 안에 홀로 놓인 `\r`을 만나면 그 줄의 마지막 글자를 조용히 삼켰다. 수정은 `TwoByteMatcher.match(byte)`를 오버라이드해, 기대하지 않은 바이트가 오면 카운터를 0으로 되돌리는 8줄이다. PR은 2026-08-05에 Brian Clozel이 머지했고, 커밋은 `7f1966f5f57`이다.

## 1. 배경 — matcher는 무엇이고 어디서 쓰이나

`DataBufferUtils.matcher(byte[]...)`는 여러 개로 쪼개져 도착하는 `DataBuffer` 스트림에서 구분자의 위치를 찾아 주는 도구다. 공개 계약은 `DataBufferUtils.Matcher` 인터페이스 하나로 요약된다.

```java
public interface Matcher {

	/**
	 * Find the first matching delimiter and return the index of the last
	 * byte of the delimiter, or {@code -1} if not found.
	 */
	int match(DataBuffer dataBuffer);

	/**
	 * Return the delimiter from the last invocation of {@link #match(DataBuffer)}.
	 */
	byte[] delimiter();

	/**
	 * Reset the state of this matcher.
	 */
	void reset();
}
```

핵심은 매처가 **상태를 가진다**는 점이다. 스트리밍에서는 구분자가 버퍼 경계에 걸쳐 쪼개져 도착할 수 있다. `\r`이 첫 버퍼 끝에, `\n`이 다음 버퍼 앞에 오는 경우다. 그래서 매처는 "지금까지 구분자의 몇 바이트를 맞췄는지"를 호출 사이에 기억해야 하고, 이 기억이 이번 버그의 무대가 된다.

구분자 길이에 따라 구현체가 갈린다. `createMatcher`는 1바이트면 `SingleByteMatcher`, 2바이트면 `TwoByteMatcher`, 그보다 길면 `KnuthMorrisPrattMatcher`를 만든다. 이 분기 자체가 2020년 Rossen Stoyanchev의 리팩토링(`fb4363e4e04`, gh-25915)에서 성능을 위해 도입됐다. 그 전에는 매처마다 버퍼 전체를 따로 훑어서, 구분자가 많은 큰 버퍼에서 성능이 크게 나빠졌다. 리팩토링 이후에는 인덱스 하나를 공유하며 모든 매처를 한 바이트씩 함께 전진시킨다.

소비자는 두 갈래다. 하나는 `spring-core`의 `AbstractCharSequenceDecoder`이고, 여기서 `StringDecoder`와 `CharBufferDecoder`가 파생된다. 즉 WebFlux에서 텍스트나 `String` 본문을 디코딩하면 반드시 이 매처를 지나간다. 다른 하나는 `spring-web`의 멀티파트 파서 두 종류(`http/codec/multipart/MultipartParser`, `http/converter/multipart/MultipartParser`)로, boundary와 `\r\n\r\n` 헤더 종료를 찾는 데 쓴다.

`StringDecoder`의 기본 구분자는 `AbstractCharSequenceDecoder`에 상수로 박혀 있다.

```java
/** The default delimiter strings to use, i.e. {@code \r\n} and {@code \n}. */
public static final List<String> DEFAULT_DELIMITERS = List.of("\r\n", "\n");
```

구분자가 둘이므로 `matcher(byte[]...)`는 `CompositeMatcher`를 만들고, 그 안에는 `\r\n`용 `TwoByteMatcher`와 `\n`용 `SingleByteMatcher`가 나란히 들어간다.

## 2. 수정 전 동작 방식 — 상태 기계

상태 기계의 본체는 `AbstractNestedMatcher`다. 필드는 `matches` 하나이고, 지금까지 맞춘 구분자 바이트 수를 센다.

```java
@Override
public boolean match(byte b) {
	if (b == this.delimiter[this.matches]) {
		this.matches++;
		return (this.matches == delimiter().length);
	}
	return false;
}
```

이 기본 구현은 **불일치에 대한 처리가 없다**는 점이 결정적이다. 기대한 바이트가 오면 카운터를 올리고, 다 채웠으면 `true`를 돌려준다. 기대하지 않은 바이트가 오면 그냥 `false`를 돌려줄 뿐, 카운터는 건드리지 않는다. 이는 의도된 설계였다. 불일치 시 어디로 되돌아갈지는 구분자의 모양에 따라 다르므로, 하위 클래스가 각자 정하도록 남겨 둔 것이다.

실제로 형제 구현들은 각자 답을 갖고 있었다. `SingleByteMatcher`는 아예 `AbstractNestedMatcher`를 상속하지 않고 상태 없이 `this.delimiter[0] == b`만 비교한다. `KnuthMorrisPrattMatcher`는 접미사-접두사 테이블로 되돌아갈 지점을 계산해 오버라이드한다.

```java
@Override
public boolean match(byte b) {
	while (getMatches() > 0 && b != delimiter()[getMatches()]) {
		setMatches(this.table[getMatches() - 1]);
	}
	return super.match(b);
}
```

수정 전 `TwoByteMatcher`는 이 자리가 비어 있었다. 클래스 전체가 생성자와 길이 검증뿐이었다.

```java
private static class TwoByteMatcher extends AbstractNestedMatcher {

	protected TwoByteMatcher(byte[] delimiter) {
		super(delimiter);
		Assert.isTrue(delimiter.length == 2, "Expected a 2-byte delimiter");
	}
}
```

주석이 밝히듯 두 바이트 구분자는 Knuth-Morris-Pratt 테이블에서 얻을 이득이 없다. 그래서 KMP를 쓰지 않는 결정은 옳았지만, KMP가 테이블로 수행하던 **되감기 자체**가 함께 사라진 것이 문제였다.

여러 매처를 묶는 `CompositeMatcher`는 위치마다 모든 매처에게 같은 바이트를 먹이고, 맞은 것 중 **가장 긴 구분자**를 고른다.

```java
for (NestedMatcher matcher : this.matchers) {
	if (matcher.match(b) && matcher.delimiter().length > this.longestDelimiter.length) {
		this.longestDelimiter = matcher.delimiter();
	}
}
```

이 "가장 긴 것 우선" 규칙은 정상 입력에서는 필수다. `\r\n` 앞에서 `\n` 매처도 함께 맞으므로, 더 긴 `\r\n`을 골라야 `\r`이 줄 내용에 남지 않는다. 하지만 뒤에서 보듯, 이 규칙이 잘못된 매치를 증폭시키는 통로가 된다.

## 3. 무엇이 문제였나 — 떨어진 두 바이트가 하나의 구분자가 된다

증상부터 말하면, 줄 안에 홀로 있는 `\r`이 있으면 그 줄의 마지막 글자가 사라진다. 입력 `"a\rXY\nb"`를 기본 설정 `StringDecoder`로 디코딩할 때의 값 비교는 다음과 같다.

| | 첫 줄 |
|---|---|
| 기대 | `a\rXY` |
| 수정 전 실제 | `a\rX` |

바이트 단위로 따라가면 원인이 드러난다. `TwoByteMatcher`의 구분자는 `\r\n`이고, `matches`는 0에서 시작한다.

- `a` — `delimiter[0]`인 `\r`이 아니다. `matches`는 0 그대로. 정상이다.
- `\r` — `delimiter[0]`과 같다. `matches`가 1이 된다. 부분 일치 상태다.
- `X` — `delimiter[1]`인 `\n`이 아니다. `false`를 반환하지만 **`matches`는 1로 남는다**. 여기가 결함 지점이다.
- `Y` — 마찬가지로 `matches`는 1로 남는다.
- `\n` — `delimiter[1]`과 같다. `matches`가 2가 되어 `true`. 두 바이트짜리 `\r\n`이 맞았다고 보고한다.

실제 입력에서 `\r`과 `\n` 사이에는 `X`와 `Y`가 끼어 있었는데도 매처는 연속된 `\r\n`을 본 것처럼 행동한다. 잘못된 상태가 몇 바이트든 유지되므로, `\r`과 다음 `\n` 사이 거리가 얼마든 같은 일이 벌어진다.

여기서 `CompositeMatcher`의 "가장 긴 것 우선"이 피해를 확정한다. 같은 위치에서 진짜 `\n`(길이 1)도 맞지만, 거짓 `\r\n`(길이 2)이 더 길므로 후자가 선택된다. 그리고 `AbstractCharSequenceDecoder.processDataBuffer`는 선택된 구분자의 길이만큼 뒤에서 잘라낸다.

```java
int delimiterLength = matcher.delimiter().length;
if (chunks.isEmpty()) {
	if (this.stripDelimiter) {
		split.writePosition(split.writePosition() - delimiterLength);
	}
	result.add(split);
}
```

`split`은 `a\rXY\n` 5바이트인데 `delimiterLength`가 2로 보고되었으므로 뒤에서 2바이트를 떼어 `a\rX`가 남는다. `\n`은 진짜 구분자이니 사라지는 게 맞지만, 그 앞의 `Y`는 본문이었는데도 함께 잘린다. 예외도 로그도 없이 한 글자가 사라지는 조용한 데이터 손실이다.

상태가 버퍼 경계를 넘어 유지되기 때문에, `\r`과 `\n`이 서로 다른 버퍼에 있어도 같은 결과가 나온다. `"a\r"`과 `"Xb\n"` 두 버퍼로 나눠 보내면 `a\rXb`가 아니라 `a\rX`가 나온다.

영향 범위는 WebFlux의 텍스트 디코딩 경로 전부다. `\r`이 홀로 등장하는 입력은 드물지 않다. 사용자가 붙여 넣은 텍스트, 옛 macOS 계열 개행, 바이너리에 가까운 페이로드를 텍스트로 읽는 경우 등이다.

## 4. 수정 해설 — 빠져 있던 되감기를 채운다

수정은 `TwoByteMatcher`에 형제들이 갖고 있던 불일치 처리를 되돌려 준다.

```java
@Override
public boolean match(byte b) {
	if (getMatches() > 0 && b != delimiter()[getMatches()]) {
		setMatches(0);
	}
	return super.match(b);
}
```

구조는 `KnuthMorrisPrattMatcher`를 그대로 따라간다. 부분 일치 상태에서 기대하지 않은 바이트가 오면 카운터를 되감고, 그 다음 `super.match(b)`에 위임한다. 다른 점은 `while`이 `if`로, 테이블 조회가 상수 `0`으로 줄어든 것뿐이다. 두 바이트 구분자에서는 부분 일치 상태가 `matches == 1` 하나뿐이고, 그때 KMP 테이블의 값은 항상 `table[0] == 0`이므로 되감기는 한 번에 끝난다. 즉 `if` + `setMatches(0)`은 KMP 루프를 이 경우에 맞게 접은 것이며, 축약이 아니라 등가다.

`super.match(b)`에 위임하는 순서가 중요하다. 카운터를 0으로 되돌린 뒤 곧바로 기본 구현이 같은 바이트를 `delimiter[0]`과 다시 비교하므로, 되감은 그 바이트가 새로운 구분자의 시작일 수 있는 경우를 놓치지 않는다. `"a\r\rX\nb"`처럼 `\r`이 연달아 오는 입력이 이에 해당한다. 두 번째 `\r`에서 카운터가 0으로 풀린 직후 다시 1이 되어, 그 다음에 `\n`이 바로 오면 정상적으로 매치된다.

연속된 진짜 구분자는 영향을 받지 않는다. 기대한 바이트가 온 경우에는 `getMatches() > 0 && b != delimiter()[getMatches()]` 조건이 거짓이라 되감기를 건너뛰고, 기존과 똑같이 `super.match(b)`가 매치를 완성한다. 그래서 이 수정은 거짓 양성만 제거하고 참 양성은 건드리지 않는다.

`AbstractNestedMatcher.match(DataBuffer)`는 `forEachByte(start, end - start, b -> !this.match(b))` 형태로 바이트 단위 `match`를 호출한다. 이 호출이 가상 디스패치이므로, 버퍼 단위 진입 경로와 `CompositeMatcher` 경로 모두에서 오버라이드가 자동으로 적용된다. 별도의 연결 작업이 필요 없었던 이유다.

## 5. 검증 — 테스트가 고정하는 것

테스트는 두 층에 걸쳐 있다. 매처 자체의 계약을 고정하는 층과, 사용자가 실제로 겪는 증상을 고정하는 층이다.

`DataBufferUtilsTests`에는 세 개의 파라미터화 테스트가 추가됐다. 첫째는 떨어진 두 바이트가 매치되지 않음을 못 박는다.

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

둘째 `matcherMatchesContiguousTwoByteDelimiter`는 `"a\r\nb"`에서 여전히 인덱스 `2`를 반환함을 확인한다. 회귀 방지가 아니라 **수정이 과하지 않았음**을 고정하는 테스트다. 셋째 `matcherDoesNotMatchAfterRepeatedFirstDelimiterByte`는 `"a\r\rX\nb"`에 대해 `-1`을 요구하여, 되감기 직후의 재시도 경로가 거짓 매치를 만들지 않는지 본다.

`StringDecoderTests`에는 증상 층 테스트 두 개가 붙었다. 하나는 단일 버퍼, 하나는 버퍼 경계를 넘는 경우다.

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

이 테스트가 고정하는 것은 매처의 내부 상태가 아니라 "홀로 있는 `\n` 앞 글자는 보존된다"는 관찰 가능한 계약이다. 두 번째 테스트 `decodePreservesCharacterAcrossBuffersAfterCarriageReturn`은 `"a\r"`과 `"Xb\n"` 두 버퍼로 나눠 넣어 `"a\rXb"`를 기대한다. 부분 일치 상태가 버퍼 호출을 넘어 유지된다는 이 매처의 본질적 성질까지 검증 범위에 넣은 것이다.

전체 변경은 본문 8줄, 테스트 66줄로 3개 파일 74줄 추가였다.

## 6. 상태와 교훈

PR은 2026-08-05에 머지됐다(`7f1966f5f57`, 리뷰 코멘트 없이 Brian Clozel이 병합). 기여자 코멘트에서 밝혔듯 변경 위치는 `spring-core`지만 실제 피해자는 웹 스택이며, 결함은 2020년 gh-25915 리팩토링까지 거슬러 올라간다.

첫 번째 교훈은 **추상 클래스가 하위 클래스에 남겨 둔 빈칸은 문서화되지 않은 의무**라는 점이다. `AbstractNestedMatcher.match(byte)`는 불일치 처리를 일부러 비워 두었고, `SingleByteMatcher`와 `KnuthMorrisPrattMatcher`는 각자 채웠지만 `TwoByteMatcher`만 채우지 않았다. 컴파일러도 테스트도 이 누락을 잡을 수 없었다. 형제 구현들을 나란히 읽고 "이 클래스만 없는 것은 무엇인가"를 묻는 것이 이런 결함을 찾는 실질적인 방법이다.

두 번째 교훈은 **최적화로 코드 경로를 분기할 때 원래 경로가 수행하던 책임을 함께 옮겨야 한다**는 것이다. 두 바이트 구분자에 KMP 테이블이 불필요하다는 판단은 맞았지만, 테이블이 수행하던 되감기라는 기능까지 같이 버려졌다. 성능을 위한 특수 케이스는 일반 케이스와 동작이 같아야 하며, 이번 수정처럼 "일반 구현을 이 경우에 맞게 접은 형태"로 쓰면 그 등가성이 코드에서 읽힌다.

---

연관 ko-docs (모듈 지도): `spring-core/07-유틸리티와-부가-인프라.md`
