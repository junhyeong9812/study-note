# Spring 표현식 언어 (SpEL)

`#{...}` 식 하나가 문자열에서 구문 트리로 바뀌고, 평가 문맥 위에서 값으로 계산되기까지의 흐름을 위에서 아래로 따라간다. `@Value`, `@Cacheable(condition)`, `@PreAuthorize` 같은 애노테이션 속성이 모두 이 경로를 지난다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 파서와 평가 문맥의 확장 인터페이스다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 parser.parseExpression("user.name") 또는 "#{user.name}" (템플릿)
 |
 +-- [01] TemplateAwareExpressionParser.parseExpression
        템플릿이면 --> 리터럴과 식을 잘라 CompositeStringExpression
        아니면     --> doParseExpression
        |
        +-- [01-01] InternalSpelExpressionParser.doParseExpression
               길이 제한 검사
               Tokenizer 로 토큰 분해
               재귀 하강 파서가 AST 구성 (eatExpression 이하)
               --> SpelExpression(식 문자열, AST, 설정)

 expression.getValue(context, rootObject)
 |
 +-- [02] SpelExpression.getValue
        컴파일된 버전이 있으면 그것으로 실행 (실패 시 모드에 따라 해석 모드로 복귀)
        없으면 ExpressionState 를 만들어 AST 평가
        평가 후 checkCompile -- 임계치를 넘으면 바이트코드로 컴파일
        |
        +-- [02-01] SpelNodeImpl.getValue
               노드마다 getValueInternal 구현
               PropertyOrFieldReference --> PropertyAccessor 로 프로퍼티 읽기
               MethodReference          --> MethodResolver 로 메서드 찾기
               BeanReference (@bean)    --> BeanResolver 로 빈 조회
```

## 어디에서 쓰이는가

```text
 @Value("${...}") 의 ${} 는 플레이스홀더이고, #{} 가 SpEL 이다
   --> StandardBeanExpressionResolver 가 컨테이너에서 평가
       (prepareBeanFactory 가 등록한다)

 @Cacheable(condition/unless/key)      CacheOperationExpressionEvaluator
 @Transactional 의 일부 속성
 @EventListener(condition)             EventExpressionEvaluator
 @PreAuthorize (Spring Security)
 XML/애노테이션 설정의 동적 값
```

## 단계

1. [TemplateAwareExpressionParser.parseExpression](01_TemplateAwareExpressionParser.parseExpression/README.md)이 문자열을 `Expression`으로 바꾼다.
2. [SpelExpression.getValue](02_SpelExpression.getValue/README.md)가 평가 문맥 위에서 값을 계산한다.

## 결과가 쓰이는 곳

```text
 파싱 결과(Expression)
      --> 보통 캐시된다 (같은 식을 여러 번 평가하므로)
          예: @Cacheable 의 key 식은 메서드마다 한 번만 파싱
      --> 파싱 비용보다 평가 비용이 반복적으로 든다

 평가 결과
      --> 주입 값, 캐시 키, 조건 판정 결과 등
      --> 기대 타입이 주어지면 TypeConverter 로 변환된다

 컴파일
      --> 같은 식이 반복 평가되면 바이트코드로 컴파일해 속도를 올린다
      --> 기본 모드는 OFF. 켜면 MIXED/IMMEDIATE 로 동작한다
```

## 다루지 않는 것

토크나이저와 재귀 하강 파서의 문법 규칙 하나하나, 컴파일러가 생성하는 바이트코드는 범위 밖이다. 이 지도는 "문자열이 어떻게 값이 되는가"의 골격만 따라간다.

## 하위 메서드

- [01 TemplateAwareExpressionParser.parseExpression](01_TemplateAwareExpressionParser.parseExpression/README.md)
- [02 SpelExpression.getValue](02_SpelExpression.getValue/README.md)
- [spi](spi/README.md) — 파서, 표현식, 평가 문맥, 접근자
