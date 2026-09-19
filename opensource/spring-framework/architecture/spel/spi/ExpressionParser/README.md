# ExpressionParser

상위: [Spring 표현식 언어 (SpEL)](../../README.md) / [spi](../README.md)

문자열을 `Expression`으로 바꾸는 진입점이다. 구현이 SpEL 하나뿐이지만, 인터페이스가 분리돼 있어 다른 식 언어로 교체할 여지를 남긴다.

## 실제 코드

`spring-expression` / `org.springframework.expression` / `ExpressionParser.java` L28-L59 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-expression/src/main/java/org/springframework/expression/ExpressionParser.java#L28-L59))

```java
// ExpressionParser.java L28-L59
public interface ExpressionParser {

    Expression parseExpression(String expressionString) throws ParseException;

    Expression parseExpression(String expressionString, ParserContext context) throws ParseException;

}
```

`spring-expression` / `org.springframework.expression` / `ParserContext.java` L27-L81 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-expression/src/main/java/org/springframework/expression/ParserContext.java#L27-L81))

```java
// ParserContext.java L27-L81
public interface ParserContext {

    boolean isTemplate();

    String getExpressionPrefix();

    String getExpressionSuffix();

    ParserContext TEMPLATE_EXPRESSION = new ParserContext() {

        @Override
        public boolean isTemplate() {
            return true;
        }

        @Override
        public String getExpressionPrefix() {
            return "#{";
        }

        @Override
        public String getExpressionSuffix() {
            return "}";
        }
    };

}
```

## 흐름에서 불리는 자리

```text
 parser.parseExpression(식)               일반 모드
 parser.parseExpression(식, TEMPLATE)      템플릿 모드 (#{...} 구간만 식)
   --> TemplateAwareExpressionParser 가 분기
```

- [parseExpression](../../01_TemplateAwareExpressionParser.parseExpression/README.md)

## 구현 계층

```text
 ExpressionParser
   +-- TemplateAwareExpressionParser      템플릿 분기 공통
         +-- SpelExpressionParser         SpEL

 ParserContext
   접두/접미 문자 지정 (기본 #{ 와 })
   TEMPLATE_EXPRESSION 상수가 가장 흔하다
```
