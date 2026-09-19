# PropertyAccessor

상위: [Spring 표현식 언어 (SpEL)](../../README.md) / [spi](../README.md)

식에서 `a.b`를 만났을 때 실제로 값을 읽는 전략이다. 대상 타입마다 다른 접근자가 쓰일 수 있다.

## 실제 코드

`spring-expression` / `org.springframework.expression` / `PropertyAccessor.java` L49-L99 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-expression/src/main/java/org/springframework/expression/PropertyAccessor.java#L49-L99))

```java
// PropertyAccessor.java L49-L99
public interface PropertyAccessor extends TargetedAccessor {

    boolean canRead(EvaluationContext context, @Nullable Object target, String name) throws AccessException;

    TypedValue read(EvaluationContext context, @Nullable Object target, String name) throws AccessException;

    boolean canWrite(EvaluationContext context, @Nullable Object target, String name) throws AccessException;

    void write(EvaluationContext context, @Nullable Object target, String name, @Nullable Object newValue)
            throws AccessException;

}
```

## 흐름에서 불리는 자리

```text
 PropertyOrFieldReference.getValueInternal
   문맥의 접근자 목록을 순회
   canRead 인 첫 접근자로 read
   선택된 접근자를 노드에 캐시
```

- [SpelNodeImpl.getValue](../../02_SpelExpression.getValue/01_SpelNodeImpl.getValue/README.md)

## 구현 계층

```text
 PropertyAccessor
   +-- ReflectivePropertyAccessor          getter/필드 (기본)
   |     +-- (CompilablePropertyAccessor 를 구현해 컴파일 지원)
   +-- MapAccessor                         Map 을 프로퍼티처럼
   +-- BeanFactoryAccessor / BeanExpressionContextAccessor
   +-- EnvironmentAccessor
   +-- (Spring Data, Security 등이 자체 접근자를 등록)

 등록
   StandardEvaluationContext.addPropertyAccessor(...)
   순서가 우선순위
```
