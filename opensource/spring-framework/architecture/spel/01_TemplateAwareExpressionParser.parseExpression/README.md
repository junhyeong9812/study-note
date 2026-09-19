# TemplateAwareExpressionParser.parseExpression

상위: [Spring 표현식 언어 (SpEL)](../README.md)

식 문자열을 `Expression` 객체로 바꾼다. 템플릿 모드면 `#{...}` 구간만 골라 파싱하고 나머지는 리터럴로 둔다.

## 실제 코드

`spring-expression` / `org.springframework.expression.common` / `TemplateAwareExpressionParser.java` L55-L65 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-expression/src/main/java/org/springframework/expression/common/TemplateAwareExpressionParser.java#L55-L65))

```java
// TemplateAwareExpressionParser.java L55-L65
@Override
public Expression parseExpression(String expressionString, @Nullable ParserContext context) throws ParseException {
    if (context != null && context.isTemplate()) {
        Assert.notNull(expressionString, "'expressionString' must not be null");
        return parseTemplate(expressionString, context);
    }
    else {
        Assert.hasText(expressionString, "'expressionString' must not be null or blank");
        return doParseExpression(expressionString, context);
    }
}
```

`spring-expression` / `org.springframework.expression.common` / `TemplateAwareExpressionParser.java` L68-L80 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-expression/src/main/java/org/springframework/expression/common/TemplateAwareExpressionParser.java#L68-L80))

```java
// TemplateAwareExpressionParser.java L68-L80
private Expression parseTemplate(String expressionString, ParserContext context) throws ParseException {
    if (expressionString.isEmpty()) {
        return new LiteralExpression("");
    }

    Expression[] expressions = parseExpressions(expressionString, context);
    if (expressions.length == 1) {
        return expressions[0];
    }
    else {
        return new CompositeStringExpression(expressionString, expressions);
    }
}
```

## 동작 흐름

```text
 parseExpression(expressionString, context)
 |
 +-- context.isTemplate() 인 경우 (ParserContext.TEMPLATE_EXPRESSION 등)
 |     parseTemplate
 |       "안녕 #{user.name} 님" 을 조각으로 나눈다
 |         리터럴 "안녕 "        --> LiteralExpression
 |         식 "user.name"        --> doParseExpression
 |         리터럴 " 님"          --> LiteralExpression
 |       조각이 하나면 그대로, 여럿이면 CompositeStringExpression
 |       = 평가하면 각 조각을 이어 붙인 문자열이 된다
 |
 +-- 템플릿이 아니면 (기본)
       doParseExpression(expressionString, context)
```

1. 실제 파싱은 [InternalSpelExpressionParser.doParseExpression](01_InternalSpelExpressionParser.doParseExpression/README.md)이 한다.

## 결과가 쓰이는 곳

```text
 반환된 Expression
      --> getValue(...) 로 반복 평가
      --> 스레드 안전하므로 캐시해 두고 재사용하는 것이 표준 사용법

 템플릿 모드의 쓰임
      --> @Value("#{...}") 도 템플릿 모드로 파싱된다. StandardBeanExpressionResolver 가
          isTemplate()=true 인 ParserContext(접두 "#{", 접미 "}")를 넘기고,
          #{} 를 잘라 내는 일은 parseExpressions 가 한다
      --> 템플릿 모드는 문자열 안에 여러 식이 섞인 경우에 쓴다

 ParserContext
      --> 접두/접미 문자를 바꿀 수 있다 (기본은 #{ 와 })
```
