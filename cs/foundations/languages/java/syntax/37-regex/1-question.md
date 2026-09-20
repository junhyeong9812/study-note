# java/syntax/37 — 정규식: `Pattern`/`Matcher`·`String` 의 정규식 메서드 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력(예외 메시지 포함)을 맞힐 수 있는지**를 묻는다.
> 수치를 묻는 문항(9·10)은 **절댓값이 아니라 기울기·자릿수**를 맞히는 것이 목표다.
> 선행: [35 `String`](../35-string/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 세 메서드의 아홉 줄 (예측)

```java
Pattern p = Pattern.compile("\\d+");
for (String s : new String[]{"abc123def456", "123", "123abc"}) {
    System.out.println(p.matcher(s).matches());
    System.out.println(p.matcher(s).lookingAt());
    System.out.println(p.matcher(s).find());
}
```

- 아홉 줄의 출력은 각각 무엇인가?
- 셋의 차이를 각각 한 마디로 말할 수 있는가?
- 입력 검증에 `find()` 를 쓰면 무엇이 통과하는가?

### 2. `Matcher` 를 잘못 쓰면 무엇이 나오나 (예측)

```java
Matcher m = Pattern.compile("\\d+").matcher("abc123");
System.out.println(m.group());              // (가)

Matcher n = Pattern.compile("\\d+").matcher("abc");
System.out.println(n.find());
System.out.println(n.group());              // (나)

Matcher k = Pattern.compile("\\d+").matcher("abc123");
System.out.println(k.start());              // (다)
```

- (가)·(나)·(다) 에서 각각 **어떤 예외**가 나는가, **메시지**는 무엇인가?
- 이 중 **JDK 17 과 21 에서 메시지가 다른 것**이 하나 있다 — 어느 것인가?
- `group(5)` 와 `group("없는이름")` 은 각각 어떤 예외인가?

### 3. 탐욕·게으름·소유 (예측)

```java
String html = "<a><b></b></a>";
// <.+>   <.+?>   <.++>   를 각각 find() 하면?
// 입력 "aaa" 에 a*a   a*?a   a*+a   를 각각 find() 하면?
```

- 여섯 결과는 각각 무엇인가(매치 문자열 또는 "매치 없음")?
- 소유 수량자가 매치에 **실패**하는 이유를 한 문장으로 말할 수 있는가?
- 셋의 차이를 "되돌려준다"는 말로 정리할 수 있는가?

### 4. `split` 결과의 길이 일곱 줄 (예측)

```java
"a,b,,c,,".split(",")
"a,b,,c,,".split(",", -1)
"a,b,,c,,".split(",", 2)
",,a".split(",")
"".split(",")
",".split(",")
",".split(",", -1)
```

- 일곱 결과의 **원소와 길이**는 각각 무엇인가?
- 앞쪽 빈 조각과 뒤쪽 빈 조각의 처리가 왜 다른가 — 근거 문장은 어디에 있는가?
- `"".split(",")` 과 `",".split(",")` 의 길이가 갈리는 이유는 무엇인가?
- CSV 를 읽을 때 기본으로 써야 할 형태는 무엇인가?

### 5. 인자가 정규식인 줄 모르면 (예측)

```java
"a.b.c".split(".")
"a.b.c".split("\\.")
"a|b".split("|")
"a.b".replace(".", "#")
"a.b".replaceAll(".", "#")
"price".replaceAll("price", "$9")
```

- 여섯 결과는 각각 무엇인가(예외면 예외 이름과 메시지)?
- `replace` 와 `replaceAll` 의 차이를 한 줄로 말할 수 있는가?
- `Pattern.quote` 와 `Matcher.quoteReplacement` 는 각각 무엇을 막는가?
- `Pattern.quote("a.b|c")` 의 결과 문자열은 무엇인가?

### 6. 문법이 틀린 정규식 (예측)

```java
Pattern.compile("(\\d+")
Pattern.compile("*abc")
Pattern.compile("[a-z")
Pattern.compile("\\p{Nope}")
Pattern.compile("\\1abc")
```

- 다섯 중 예외가 나는 것은 몇 개인가?
- 예외의 **타입**과 **메시지 첫 줄**은 각각 무엇인가?
- 이 예외는 검사 예외인가, 그것이 실무에 주는 함의는 무엇인가?
- 예외가 안 나는 하나는 무엇을 매치하는가?

### 7. 그룹 (경계)

- `(\w+)@(\w+)\.(com|net)` 의 `groupCount()` 는 얼마인가?
- `(?:...)` 는 번호를 차지하는가?
- 패턴 안의 역참조와 치환문의 그룹 참조는 표기가 어떻게 다른가?
- 이름 있는 그룹은 몇 부터인가?

### 8. `Pattern` 과 `Matcher` 중 무엇을 공유해도 되나 (경계)

- javadoc 이 뭐라고 적었는가 — 인용할 수 있는가?
- `Matcher` 를 다른 입력에 다시 쓰는 방법은 무엇인가?
- 여러 스레드가 같은 정규식을 쓸 때 권장 형태는 무엇인가?

### 9. ★ 파국적 백트래킹 — 터뜨릴 수 있는가 (예측)

```java
Pattern.compile("(x+x+)+y").matcher("x".repeat(40)).matches();       // (가)
Pattern.compile("\\1?(x+x+)+y").matcher("x".repeat(26)).matches();   // (나)
```

- (가) 는 JDK 21 에서 몇 ms 쯤 걸리는가?
- (나) 는 몇 ms 쯤 걸리는가 — (가) 보다 입력이 **짧은데도** 그렇다면 왜인가?
- `\1?` 는 매치 결과에 영향을 주는가?
- 이 차이를 만드는 JDK 내부 장치의 이름과, 그것이 꺼지는 조건은 무엇인가?
- 입력이 두 글자 늘 때 시간이 몇 배가 되는가?
- 막는 방법 세 가지를 댈 수 있는가?

### 10. `Pattern` 컴파일 비용 (예측)

- 같은 패턴으로 20만 건을 검사할 때 **매번 `Pattern.compile`** 과 **미리 컴파일**은 몇 배 차이인가?
- `String.matches(regex)` 는 둘 중 어느 쪽과 같은가, 왜인가?
- 1~2 회차가 3 회차보다 느린 이유는 무엇인가?
- 이 수치에서 **재현되는 것**은 무엇이고 재현되지 않는 것은 무엇인가?

### 11. 무엇이 계약이고 무엇이 구현인가 (경계)

- `split` 의 limit 규칙은 계약인가 구현인가?
- 예외 **타입**과 예외 **메시지**는 각각 어느 쪽인가?
- 그리디 루프 메모이제이션은 어느 쪽인가, 그것이 코드 리뷰에서 뜻하는 바는 무엇인가?
- "Java 는 ReDoS 에 안전하다"는 문장을 어떻게 고쳐 써야 하는가?

### 12. 다른 주제와 잇기 (연결)

- 텍스트 블록에 정규식을 적으면 역슬래시가 줄어드는가?
- 정규식으로 하면 안 되는 일 세 가지를 댈 수 있는가?
- `asPredicate` 와 `asMatchPredicate` 는 각각 어느 메서드 기준인가?
- `PatternSyntaxException` 을 기동 시점에 터뜨리려면 어떻게 코드를 배치하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
