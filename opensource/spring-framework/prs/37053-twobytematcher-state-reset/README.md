# PR #37053 — Reset TwoByteMatcher partial match on mismatching byte

## 0. 정향

이 PR은 `DataBufferUtils` 안의 두 바이트 구분자 매처가 부분 일치 상태를 풀지 않아, 떨어져 있는 두 바이트를 하나의 구분자로 오인하던 버그를 고친다.\
결과적으로 WebFlux의 `StringDecoder`가 줄 안에 홀로 놓인 `\r`을 만나면 그 줄의 마지막 글자를 조용히 삼켰다.\
수정은 `TwoByteMatcher.match(byte)`를 오버라이드해, 기대하지 않은 바이트가 오면 카운터를 0으로 되돌리는 8줄이다.\
PR은 2026-08-05에 Brian Clozel이 머지했고, 커밋은 `7f1966f5f57`이다.

> **구분자(delimiter)** — 바이트 스트림을 논리적 조각으로 끊어 주는 약속된 바이트열.\
> 예: 텍스트 한 줄의 끝을 알리는 `\r\n` 두 바이트가 구분자다.

> **WebFlux** — 요청 본문을 한 덩어리로 받지 않고 조각조각 흘려보내며 처리하는 Spring의 리액티브 웹 스택.\
> 예: `String` 본문을 읽으면 `StringDecoder`가 그 조각들을 줄 단위로 잘라 문자열로 만든다.

## 1. 배경 — matcher는 무엇이고 어디서 쓰이나

`DataBufferUtils.matcher(byte[]...)`는 여러 개로 쪼개져 도착하는 `DataBuffer` 스트림에서 구분자의 위치를 찾아 주는 도구다.\
공개 계약은 `DataBufferUtils.Matcher` 인터페이스 하나로 요약된다.

> **DataBuffer** — Spring이 바이트 묶음 하나를 감싼 추상 타입. 읽는 위치와 쓰는 위치를 따로 들고 있다.\
> 예: 네트워크에서 `"a\rXY\nb"` 6바이트가 도착하면 그 내용을 담은 `DataBuffer` 하나가 디코더로 넘어온다.

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

핵심은 매처가 **상태를 가진다**는 점이다.\
스트리밍에서는 구분자가 버퍼 경계에 걸쳐 쪼개져 도착할 수 있다.\
`\r`이 첫 버퍼 끝에, `\n`이 다음 버퍼 앞에 오는 경우다.\
그래서 매처는 "지금까지 구분자의 몇 바이트를 맞췄는지"를 호출 사이에 기억해야 하고, 이 기억이 이번 버그의 무대가 된다.

> **부분 일치 상태(partial match state)** — 구분자의 앞부분까지만 맞은 채로 다음 바이트를 기다리는 중간 상태.\
> 예: `\r\n`을 찾는 중에 `\r`까지 봤다면 "1바이트 맞춤" 상태로 `\n`을 기다린다.

구분자 길이에 따라 구현체가 갈린다.\
`createMatcher`는 1바이트면 `SingleByteMatcher`, 2바이트면 `TwoByteMatcher`, 그보다 길면 `KnuthMorrisPrattMatcher`를 만든다.\
이 분기 자체가 2020년 Rossen Stoyanchev의 리팩토링(`fb4363e4e04`, gh-25915)에서 성능을 위해 도입됐다.\
그 전에는 매처마다 버퍼 전체를 따로 훑어서, 구분자가 많은 큰 버퍼에서 성능이 크게 나빠졌다.\
리팩토링 이후에는 인덱스 하나를 공유하며 모든 매처를 한 바이트씩 함께 전진시킨다.

> **Knuth-Morris-Pratt(KMP)** — 부분 일치가 깨졌을 때 처음으로 돌아가지 않고, 미리 만든 표를 보고 되돌아갈 지점을 계산하는 문자열 탐색 알고리즘.\
> 예: `aab`를 찾다가 세 번째 글자에서 틀리면 처음이 아니라 "이미 맞은 `a` 한 글자" 자리로 점프한다.

소비자는 두 갈래다.\
하나는 `spring-core`의 `AbstractCharSequenceDecoder`이고, 여기서 `StringDecoder`와 `CharBufferDecoder`가 파생된다.\
즉 WebFlux에서 텍스트나 `String` 본문을 디코딩하면 반드시 이 매처를 지나간다.\
다른 하나는 `spring-web`의 멀티파트 파서 두 종류(`http/codec/multipart/MultipartParser`, `http/converter/multipart/MultipartParser`)로, boundary와 `\r\n\r\n` 헤더 종료를 찾는 데 쓴다.

> **멀티파트(multipart)** — 파일 업로드처럼 한 요청 본문에 여러 조각을 담고, 각 조각을 boundary 문자열로 갈라 놓는 형식.\
> 예: `--boundary`로 시작하는 줄이 나올 때마다 새 조각이 시작된다.

`StringDecoder`의 기본 구분자는 `AbstractCharSequenceDecoder`에 상수로 박혀 있다.

```java
/** The default delimiter strings to use, i.e. {@code \r\n} and {@code \n}. */
public static final List<String> DEFAULT_DELIMITERS = List.of("\r\n", "\n");
```

구분자가 둘이므로 `matcher(byte[]...)`는 `CompositeMatcher`를 만들고, 그 안에는 `\r\n`용 `TwoByteMatcher`와 `\n`용 `SingleByteMatcher`가 나란히 들어간다.

## 2. 수정 전 동작 방식 — 상태 기계

상태 기계의 본체는 `AbstractNestedMatcher`다.\
필드는 `matches` 하나이고, 지금까지 맞춘 구분자 바이트 수를 센다.

> **상태 기계(state machine)** — 지금까지 본 입력을 "상태" 하나로 요약해 들고, 입력이 올 때마다 그 상태를 옮기는 계산 모형.\
> 예: 여기서 상태는 `matches` 하나이며 값은 0 또는 1이고, 2가 되는 순간 "구분자 완성"으로 끝난다.

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

이 기본 구현은 **불일치에 대한 처리가 없다**는 점이 결정적이다.\
기대한 바이트가 오면 카운터를 올리고, 다 채웠으면 `true`를 돌려준다.\
기대하지 않은 바이트가 오면 그냥 `false`를 돌려줄 뿐, 카운터는 건드리지 않는다.\
이는 의도된 설계였다.\
불일치 시 어디로 되돌아갈지는 구분자의 모양에 따라 다르므로, 하위 클래스가 각자 정하도록 남겨 둔 것이다.

기본 설정 `StringDecoder`에서 바이트 하나가 이 자리까지 내려오는 경로는 이렇다 — 값이 갈라지는 자리는 마지막 세 칸이다.

```text
StringDecoder.decode(input, ...)        스트림 하나당 matcher 를 한 벌만 만든다
        |
        v
DataBufferUtils.matcher({13,10},{10})   구분자가 둘이므로 CompositeMatcher
        |
        +--> TwoByteMatcher({13,10})       <- createMatcher case 2 (결함이 살던 갈래)
        +--> SingleByteMatcher({10})       <- createMatcher case 1
        |
        v
processDataBuffer(buffer, matcher, ...)  버퍼 하나에서 구분자를 반복 탐색
        |
        v
matcher.match(buffer)                    위치 0,1,2,... 마다 모든 자식에게 같은 바이트를 먹인다
        |
        +--> SingleByteMatcher.match(b)    delimiter[0] == b 순수 비교 (상태 없음)
        +--> TwoByteMatcher.match(b)       상속받은 AbstractNestedMatcher.match(byte)
        |         |
        |         v
        |    b == delimiter[matches] ?     예 -> matches++ / 아니오 -> false 만 반환
        |                                  ^ 아니오 갈래에서 matches 를 건드리지 않는다
        v
맞은 것 중 가장 긴 구분자를 longestDelimiter 로 채택
        |
        v
delimiterLength = matcher.delimiter().length   이 길이만큼 본문 뒤에서 잘라낸다
```

네 칸을 지나는 동안 상태를 들고 가는 것은 `TwoByteMatcher` 하나뿐이고, 그 하나가 불일치를 만났을 때 상태를 풀지 않는 것이 이 그림의 유일한 빈칸이다.

실제로 형제 구현들은 각자 답을 갖고 있었다.\
`SingleByteMatcher`는 아예 `AbstractNestedMatcher`를 상속하지 않고 상태 없이 `this.delimiter[0] == b`만 비교한다.\
`KnuthMorrisPrattMatcher`는 접미사-접두사 테이블로 되돌아갈 지점을 계산해 오버라이드한다.

> **접미사-접두사 테이블(longest suffix-prefix table)** — 구분자의 각 위치까지 봤을 때 "앞부분이자 동시에 뒷부분인 가장 긴 조각"의 길이를 미리 적어 둔 배열.\
> 예: `aab`의 표는 `[0, 1, 0]`이고, 두 번째 글자에서 깨지면 1로 되감으라는 뜻이다.

```java
@Override
public boolean match(byte b) {
	while (getMatches() > 0 && b != delimiter()[getMatches()]) {
		setMatches(this.table[getMatches() - 1]);
	}
	return super.match(b);
}
```

수정 전 `TwoByteMatcher`는 이 자리가 비어 있었다.\
클래스 전체가 생성자와 길이 검증뿐이었다.

```java
private static class TwoByteMatcher extends AbstractNestedMatcher {

	protected TwoByteMatcher(byte[] delimiter) {
		super(delimiter);
		Assert.isTrue(delimiter.length == 2, "Expected a 2-byte delimiter");
	}
}
```

주석이 밝히듯 두 바이트 구분자는 Knuth-Morris-Pratt 테이블에서 얻을 이득이 없다.\
그래서 KMP를 쓰지 않는 결정은 옳았지만, KMP가 테이블로 수행하던 **되감기 자체**가 함께 사라진 것이 문제였다.

> **되감기(rewind / backtrack)** — 부분 일치가 깨졌을 때 지금까지 세어 둔 카운터를 뒤로 되돌리는 일.\
> 예: `\r`까지 맞춰 `matches = 1`이 됐는데 다음 바이트가 `X`이면, `matches`를 0으로 되돌려야 한다.

여러 매처를 묶는 `CompositeMatcher`는 위치마다 모든 매처에게 같은 바이트를 먹이고, 맞은 것 중 **가장 긴 구분자**를 고른다.

```java
for (NestedMatcher matcher : this.matchers) {
	if (matcher.match(b) && matcher.delimiter().length > this.longestDelimiter.length) {
		this.longestDelimiter = matcher.delimiter();
	}
}
```

이 "가장 긴 것 우선" 규칙은 정상 입력에서는 필수다.\
`\r\n` 앞에서 `\n` 매처도 함께 맞으므로, 더 긴 `\r\n`을 골라야 `\r`이 줄 내용에 남지 않는다.\
하지만 뒤에서 보듯, 이 규칙이 잘못된 매치를 증폭시키는 통로가 된다.

## 3. 무엇이 문제였나 — 떨어진 두 바이트가 하나의 구분자가 된다

증상부터 말하면, 줄 안에 홀로 있는 `\r`이 있으면 그 줄의 마지막 글자가 사라진다.\
입력 `"a\rXY\nb"`를 기본 설정 `StringDecoder`로 디코딩할 때의 값 비교는 다음과 같다.

| | 첫 줄 |
|---|---|
| 기대 | `a\rXY` |
| 수정 전 실제 | `a\rX` |

바이트 단위로 따라가면 원인이 드러난다.\
`TwoByteMatcher`의 구분자는 `\r\n`이고, `matches`는 0에서 시작한다.

- `a` — `delimiter[0]`인 `\r`이 아니다. `matches`는 0 그대로. 정상이다.
- `\r` — `delimiter[0]`과 같다. `matches`가 1이 된다. 부분 일치 상태다.
- `X` — `delimiter[1]`인 `\n`이 아니다. `false`를 반환하지만 **`matches`는 1로 남는다**. 여기가 결함 지점이다.
- `Y` — 마찬가지로 `matches`는 1로 남는다.
- `\n` — `delimiter[1]`과 같다. `matches`가 2가 되어 `true`. 두 바이트짜리 `\r\n`이 맞았다고 보고한다.

같은 걸음을 카운터만 남겨 세로로 그리면 잔류가 어디서 시작되는지가 한눈에 보인다.

```text
입력      a      \r      X       Y      \n      b
위치      0      1       2       3      4       5
                                          
matches   0  ->  1  ->   1   ->  1  ->   2
                 ^       ^       ^       ^
                 |       |       |       +-- 2 == length -> true (거짓 매치)
                 |       +-------+---------- 불일치인데 되감지 않아 1 로 잔류
                 +---------------------------- delimiter[0] 과 일치해 1 로 상승
```

`X`와 `Y` 자리에서 카운터가 1에 얼어붙은 것이, 네 칸 뒤 `\n`에서 구분자가 완성됐다는 거짓 보고로 이어진다.

실제 입력에서 `\r`과 `\n` 사이에는 `X`와 `Y`가 끼어 있었는데도 매처는 연속된 `\r\n`을 본 것처럼 행동한다.\
잘못된 상태가 몇 바이트든 유지되므로, `\r`과 다음 `\n` 사이 거리가 얼마든 같은 일이 벌어진다.

여기서 `CompositeMatcher`의 "가장 긴 것 우선"이 피해를 확정한다.\
같은 위치에서 진짜 `\n`(길이 1)도 맞지만, 거짓 `\r\n`(길이 2)이 더 길므로 후자가 선택된다.\
그리고 `AbstractCharSequenceDecoder.processDataBuffer`는 선택된 구분자의 길이만큼 뒤에서 잘라낸다.

```java
int delimiterLength = matcher.delimiter().length;
if (chunks.isEmpty()) {
	if (this.stripDelimiter) {
		split.writePosition(split.writePosition() - delimiterLength);
	}
	result.add(split);
}
```

`split`은 `a\rXY\n` 5바이트인데 `delimiterLength`가 2로 보고되었으므로 뒤에서 2바이트를 떼어 `a\rX`가 남는다.\
`\n`은 진짜 구분자이니 사라지는 게 맞지만, 그 앞의 `Y`는 본문이었는데도 함께 잘린다.\
예외도 로그도 없이 한 글자가 사라지는 조용한 데이터 손실이다.

> **무음 실패(silent failure)** — 실패했는데 예외도 로그도 없이 조용히 넘어가, 결과가 틀린 채로 계속 진행되는 실패.\
> 예: `Y` 한 글자가 잘려 나가도 디코딩은 정상 종료하고 아무 신호도 남지 않는다.

같은 입력이 수정 전후로 어떻게 갈리는지를 같은 눈높이에 놓으면 이렇다.

```text
수정 전 (되감기 없음)                  수정 후 (불일치에서 0 으로 되감기)
+------------------------------+      +------------------------------+
| 입력  "a\rXY\nb"             |      | 입력  "a\rXY\nb"             |
| \n 위치에서 맞은 매처        |      | \n 위치에서 맞은 매처        |
|   TwoByteMatcher   {13,10}   |      |   SingleByteMatcher {10}     |
|   SingleByteMatcher {10}     |      |   (TwoByteMatcher 는 안 맞음)|
| 최장 우선 채택 -> 길이 2     |      | 후보가 하나 -> 길이 1        |
| split = "a\rXY\n" (5바이트)  |      | split = "a\rXY\n" (5바이트)  |
| 뒤에서 2바이트 절단          |      | 뒤에서 1바이트 절단          |
+------------------------------+      +------------------------------+
  -> "a\rX"   (본문 Y 유실)             -> "a\rXY" (본문 보존)
```

같은 위치, 같은 `split`인데 보고된 구분자 길이 하나가 달라 본문 한 글자의 운명이 갈린다.

상태가 버퍼 경계를 넘어 유지되기 때문에, `\r`과 `\n`이 서로 다른 버퍼에 있어도 같은 결과가 나온다.\
`"a\r"`과 `"Xb\n"` 두 버퍼로 나눠 보내면 `a\rXb`가 아니라 `a\rX`가 나온다.

영향 범위는 WebFlux의 텍스트 디코딩 경로 전부다.\
`\r`이 홀로 등장하는 입력은 드물지 않다.\
사용자가 붙여 넣은 텍스트, 옛 macOS 계열 개행, 바이너리에 가까운 페이로드를 텍스트로 읽는 경우 등이다.

> **캐리지 리턴(carriage return, `\r`)** — 커서를 줄 맨 앞으로 되돌리라는 제어 문자(바이트 값 13).\
> 예: 윈도우 계열 개행은 `\r\n` 두 글자지만, 옛 macOS 계열은 `\r` 하나만 쓴다.

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

구조는 `KnuthMorrisPrattMatcher`를 그대로 따라간다.\
부분 일치 상태에서 기대하지 않은 바이트가 오면 카운터를 되감고, 그 다음 `super.match(b)`에 위임한다.\
다른 점은 `while`이 `if`로, 테이블 조회가 상수 `0`으로 줄어든 것뿐이다.\
두 바이트 구분자에서는 부분 일치 상태가 `matches == 1` 하나뿐이고, 그때 KMP 테이블의 값은 항상 `table[0] == 0`이므로 되감기는 한 번에 끝난다.\
즉 `if` + `setMatches(0)`은 KMP 루프를 이 경우에 맞게 접은 것이며, 축약이 아니라 등가다.

두 구현을 나란히 놓으면 접힌 자리가 보인다.

```text
KnuthMorrisPrattMatcher (길이 3+)      TwoByteMatcher (길이 2)
+------------------------------+      +------------------------------+
| while (matches > 0           |      | if (matches > 0              |
|        && b != delim[m])     |      |     && b != delim[m])        |
|   matches = table[m - 1]     |      |   matches = 0                |
| return super.match(b)        |      | return super.match(b)        |
+------------------------------+      +------------------------------+
  되감을 곳이 여러 번일 수 있다          m 은 1 뿐, table[0] 은 늘 0
  -> 루프로 표를 따라 내려간다           -> 한 번에 0, 루프가 if 로 접힌다
```

왼쪽의 `while`과 표 조회가 오른쪽에서 `if`와 상수 0으로 줄어든 것이 전부이고, 위임하는 마지막 줄은 글자 그대로 같다.

`super.match(b)`에 위임하는 순서가 중요하다.\
카운터를 0으로 되돌린 뒤 곧바로 기본 구현이 같은 바이트를 `delimiter[0]`과 다시 비교하므로, 되감은 그 바이트가 새로운 구분자의 시작일 수 있는 경우를 놓치지 않는다.\
`"a\r\rX\nb"`처럼 `\r`이 연달아 오는 입력이 이에 해당한다.\
두 번째 `\r`에서 카운터가 0으로 풀린 직후 다시 1이 되어, 그 다음에 `\n`이 바로 오면 정상적으로 매치된다.

```text
입력 "a\r\rX\nb" 에서 되감은 바이트를 다시 평가하는 걸음 (수정 후)

  \r (위치 1)   matches 0 -> 조건 거짓 -> super: 13 == delim[0] -> matches 1
  \r (위치 2)   matches 1 -> 조건 참   -> setMatches(0)
                              그 직후 super: 13 == delim[0] -> matches 1  (새 시작으로 인정)
  X  (위치 3)   matches 1 -> 조건 참   -> setMatches(0)
                              그 직후 super: X != 13        -> matches 0
  \n (위치 4)   matches 0 -> 조건 거짓 -> super: 10 != delim[0](13) -> false
```

되감기와 재평가가 한 호출 안에서 이어지므로, 두 번째 `\r`은 버려지지 않고 새 부분 일치의 출발점이 된다.

연속된 진짜 구분자는 영향을 받지 않는다.\
기대한 바이트가 온 경우에는 `getMatches() > 0 && b != delimiter()[getMatches()]` 조건이 거짓이라 되감기를 건너뛰고, 기존과 똑같이 `super.match(b)`가 매치를 완성한다.\
그래서 이 수정은 거짓 양성만 제거하고 참 양성은 건드리지 않는다.

> **거짓 양성(false positive)** — 사실이 아닌데 "맞다"고 보고하는 오류.\
> 예: `\r`과 `\n` 사이에 `XY`가 끼었는데도 `\r\n` 구분자를 찾았다고 보고하는 것.

`AbstractNestedMatcher.match(DataBuffer)`는 `forEachByte(start, end - start, b -> !this.match(b))` 형태로 바이트 단위 `match`를 호출한다.\
이 호출이 가상 디스패치이므로, 버퍼 단위 진입 경로와 `CompositeMatcher` 경로 모두에서 오버라이드가 자동으로 적용된다.\
별도의 연결 작업이 필요 없었던 이유다.

> **가상 디스패치(virtual dispatch)** — 어느 메서드를 실행할지 컴파일 시점의 선언 타입이 아니라 실행 시점의 실제 객체 타입으로 정하는 것.\
> 예: 부모 클래스 안의 `this.match(b)`가 실제로는 `TwoByteMatcher`의 오버라이드를 부른다.

## 5. 검증 — 테스트가 고정하는 것

테스트는 두 층에 걸쳐 있다.\
매처 자체의 계약을 고정하는 층과, 사용자가 실제로 겪는 증상을 고정하는 층이다.

`DataBufferUtilsTests`에는 세 개의 파라미터화 테스트가 추가됐다.\
첫째는 떨어진 두 바이트가 매치되지 않음을 못 박는다.

> **파라미터화 테스트(parameterized test)** — 같은 테스트 본문을 입력만 바꿔 가며 여러 번 돌리는 JUnit 기능.\
> 예: 버퍼 팩터리 여섯 종류를 차례로 주입해 테스트 하나를 여섯 번 실행한다.

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

둘째 `matcherMatchesContiguousTwoByteDelimiter`는 `"a\r\nb"`에서 여전히 인덱스 `2`를 반환함을 확인한다.\
회귀 방지가 아니라 **수정이 과하지 않았음**을 고정하는 테스트다.\
셋째 `matcherDoesNotMatchAfterRepeatedFirstDelimiterByte`는 `"a\r\rX\nb"`에 대해 `-1`을 요구하여, 되감기 직후의 재시도 경로가 거짓 매치를 만들지 않는지 본다.

`StringDecoderTests`에는 증상 층 테스트 두 개가 붙었다.\
하나는 단일 버퍼, 하나는 버퍼 경계를 넘는 경우다.

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

이 테스트가 고정하는 것은 매처의 내부 상태가 아니라 "홀로 있는 `\n` 앞 글자는 보존된다"는 관찰 가능한 계약이다.\
두 번째 테스트 `decodePreservesCharacterAcrossBuffersAfterCarriageReturn`은 `"a\r"`과 `"Xb\n"` 두 버퍼로 나눠 넣어 `"a\rXb"`를 기대한다.\
부분 일치 상태가 버퍼 호출을 넘어 유지된다는 이 매처의 본질적 성질까지 검증 범위에 넣은 것이다.

전체 변경은 본문 8줄, 테스트 66줄로 3개 파일 74줄 추가였다.

## 6. 상태와 교훈

PR은 2026-08-05에 머지됐다(`7f1966f5f57`, 리뷰 코멘트 없이 Brian Clozel이 병합).\
기여자 코멘트에서 밝혔듯 변경 위치는 `spring-core`지만 실제 피해자는 웹 스택이며, 결함은 2020년 gh-25915 리팩토링까지 거슬러 올라간다.

첫 번째 교훈은 **추상 클래스가 하위 클래스에 남겨 둔 빈칸은 문서화되지 않은 의무**라는 점이다.\
`AbstractNestedMatcher.match(byte)`는 불일치 처리를 일부러 비워 두었고, `SingleByteMatcher`와 `KnuthMorrisPrattMatcher`는 각자 채웠지만 `TwoByteMatcher`만 채우지 않았다.\
컴파일러도 테스트도 이 누락을 잡을 수 없었다.\
형제 구현들을 나란히 읽고 "이 클래스만 없는 것은 무엇인가"를 묻는 것이 이런 결함을 찾는 실질적인 방법이다.

두 번째 교훈은 **최적화로 코드 경로를 분기할 때 원래 경로가 수행하던 책임을 함께 옮겨야 한다**는 것이다.\
두 바이트 구분자에 KMP 테이블이 불필요하다는 판단은 맞았지만, 테이블이 수행하던 되감기라는 기능까지 같이 버려졌다.\
성능을 위한 특수 케이스는 일반 케이스와 동작이 같아야 하며, 이번 수정처럼 "일반 구현을 이 경우에 맞게 접은 형태"로 쓰면 그 등가성이 코드에서 읽힌다.

---

연관 ko-docs (모듈 지도): `spring-core/07-유틸리티와-부가-인프라.md`
