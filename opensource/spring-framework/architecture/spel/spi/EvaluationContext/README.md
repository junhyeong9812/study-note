# EvaluationContext

상위: [Spring 표현식 언어 (SpEL)](../../README.md) / [spi](../README.md)

평가에 필요한 모든 것을 담는다. 루트 객체, 변수, 접근자 목록, 타입 변환기, 빈 조회기가 여기 있다. **평가 범위를 제한하는 지점**이기도 하다.

## 실제 코드

`spring-expression` / `org.springframework.expression` / `EvaluationContext.java` L66-L140 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-expression/src/main/java/org/springframework/expression/EvaluationContext.java#L66-L140))

```java
// EvaluationContext.java L66-L140
public interface EvaluationContext {

    TypedValue getRootObject();

    default List<PropertyAccessor> getPropertyAccessors() {
        return Collections.emptyList();
    }

    default List<IndexAccessor> getIndexAccessors() {
        return Collections.emptyList();
    }

    default List<ConstructorResolver> getConstructorResolvers() {
        return Collections.emptyList();
    }

    default List<MethodResolver> getMethodResolvers() {
        return Collections.emptyList();
    }

    @Nullable BeanResolver getBeanResolver();

    TypeLocator getTypeLocator();

    TypeConverter getTypeConverter();

    TypeComparator getTypeComparator();

    OperatorOverloader getOperatorOverloader();

```

## 흐름에서 불리는 자리

```text
 SpelExpression.getValue(context)
   ExpressionState 가 이 문맥을 감싼다
 노드 평가
   PropertyOrFieldReference --> context.getPropertyAccessors()
   MethodReference          --> context.getMethodResolvers()
   BeanReference            --> context.getBeanResolver()
```

- [SpelExpression.getValue](../../02_SpelExpression.getValue/README.md)
- [SpelNodeImpl.getValue](../../02_SpelExpression.getValue/01_SpelNodeImpl.getValue/README.md)

## 구현 계층

```text
 EvaluationContext
   +-- StandardEvaluationContext      모든 기능 (리플렉션 접근 전부)
   +-- SimpleEvaluationContext        제한된 기능 (데이터 바인딩용)
         forReadOnlyDataBinding / forReadWriteDataBinding
         메서드 호출, 타입 참조, 빈 참조를 막는다

 보안
   사용자 입력을 평가해야 한다면 SimpleEvaluationContext 를 쓴다
   StandardEvaluationContext 는 T(java.lang.Runtime) 같은 접근을 허용한다
```
