# InternalSpelExpressionParser.doParseExpression

상위: [TemplateAwareExpressionParser.parseExpression](../README.md)

식 문자열을 토큰으로 나누고, 재귀 하강 방식으로 구문 트리(AST)를 만든다. 결과는 `SpelExpression` 하나로, 그 안에 루트 노드가 들어 있다.

## 실제 코드

`spring-expression` / `org.springframework.expression.spel.standard` / `InternalSpelExpressionParser.java` L131-L157 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-expression/src/main/java/org/springframework/expression/spel/standard/InternalSpelExpressionParser.java#L131-L157))

```java
// InternalSpelExpressionParser.java L131-L157
@Override
protected SpelExpression doParseExpression(String expressionString, @Nullable ParserContext context)
        throws ParseException {

    checkExpressionLength(expressionString);

    try {
        this.expressionString = expressionString;
        Tokenizer tokenizer = new Tokenizer(expressionString);
        this.tokenStream = tokenizer.process();
        this.tokenStreamLength = this.tokenStream.size();
        this.tokenStreamPointer = 0;
        this.constructedNodes.clear();
        SpelNodeImpl ast = eatExpression();
        if (ast == null) {
            throw new SpelParseException(this.expressionString, 0, SpelMessage.OOD);
        }
        Token t = peekToken();
        if (t != null) {
            throw new SpelParseException(this.expressionString, t.startPos, SpelMessage.MORE_INPUT, toString(nextToken()));
        }
        return new SpelExpression(expressionString, ast, this.configuration);
    }
    catch (InternalParseException ex) {
        throw ex.getCause();
    }
}
```

`spring-expression` / `org.springframework.expression.spel.standard` / `InternalSpelExpressionParser.java` L159-L164 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-expression/src/main/java/org/springframework/expression/spel/standard/InternalSpelExpressionParser.java#L159-L164))

```java
// InternalSpelExpressionParser.java L159-L164
private void checkExpressionLength(String string) {
    int maxLength = this.configuration.getMaximumExpressionLength();
    if (string.length() > maxLength) {
        throw new SpelEvaluationException(SpelMessage.MAX_EXPRESSION_LENGTH_EXCEEDED, maxLength);
    }
}
```

## 동작 흐름

```text
 doParseExpression(expressionString, context)
 |
 | L135 checkExpressionLength
 |        설정된 최대 길이(기본 10,000자)를 넘으면 평가 전에 거부
 |        = 외부 입력을 식으로 넘길 때의 1차 방어선
 |
 | L139 Tokenizer(expressionString).process()
 |        문자열을 토큰 열로 (식별자, 리터럴, 연산자, 괄호 등)
 |
 | L144 eatExpression()
 |        재귀 하강 파서. 우선순위가 낮은 규칙부터 내려간다
 |        삼항 --> 논리합 --> 논리곱 --> 관계 --> 덧셈 --> 곱셈 --> 단항 --> 주요항
 |        주요항에서 프로퍼티 참조, 메서드 호출, 인덱서, 투영/선택, 빈 참조 등을 만든다
 |        --> SpelNodeImpl 트리
 |
 | L148 남은 토큰이 있으면 MORE_INPUT 오류 (예: "1 + 2 )" )
 |
 +-- L152 new SpelExpression(문자열, AST, 설정)
```

```text
 만들어지는 노드의 예 (user.orders[0].total > 100)

 OpGT
   +-- CompoundExpression
   |     +-- PropertyOrFieldReference "user"
   |     +-- PropertyOrFieldReference "orders"
   |     +-- Indexer [0]
   |     +-- PropertyOrFieldReference "total"
   +-- IntLiteral 100
```

## 결과가 쓰이는 곳

```text
 SpelExpression
      --> getValue / setValue 의 진입점
      --> AST 는 불변이므로 여러 스레드가 같은 식을 평가해도 안전하다

 파싱 오류
      --> SpelParseException (위치 정보 포함)
      --> 평가 시점이 아니라 파싱 시점에 드러나므로
          설정 로딩 중 잘못된 식이 조기에 발견된다

 최대 길이 제한
      --> SpelParserConfiguration 으로 조정
      --> 사용자 입력을 식으로 평가하는 구조 자체를 피하는 편이 안전하다
```
