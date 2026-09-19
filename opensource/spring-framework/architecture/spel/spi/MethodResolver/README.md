# MethodResolver

상위: [Spring 표현식 언어 (SpEL)](../../README.md) / [spi](../README.md)

식에서 `a.b(c)`를 만났을 때 호출할 메서드를 찾는다. 빈 참조를 해석하는 `BeanResolver`와 함께 둔다.

## 실제 코드

`spring-expression` / `org.springframework.expression` / `MethodResolver.java` L39-L57 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-expression/src/main/java/org/springframework/expression/MethodResolver.java#L39-L57))

```java
// MethodResolver.java L39-L57
public interface MethodResolver {

    @Nullable MethodExecutor resolve(EvaluationContext context, Object targetObject, String name,
            List<TypeDescriptor> argumentTypes) throws AccessException;

}
```

`spring-expression` / `org.springframework.expression` / `BeanResolver.java` L29-L41 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-expression/src/main/java/org/springframework/expression/BeanResolver.java#L29-L41))

```java
// BeanResolver.java L29-L41
public interface BeanResolver {

    Object resolve(EvaluationContext context, String beanName) throws AccessException;

}
```

## 흐름에서 불리는 자리

```text
 MethodReference 노드 평가
   문맥의 MethodResolver 들에게 순서대로 질의
   찾은 MethodExecutor 를 노드에 캐시해 재사용
 BeanReference 노드 (@name, &name)
   문맥의 BeanResolver 로 컨테이너에서 빈 조회
```

- [SpelNodeImpl.getValue](../../02_SpelExpression.getValue/01_SpelNodeImpl.getValue/README.md)

## 구현 계층

```text
 MethodResolver
   +-- ReflectiveMethodResolver        리플렉션 (기본)
   +-- DataBindingMethodResolver       데이터 바인딩용 제한 버전

 BeanResolver
   +-- BeanFactoryResolver             ApplicationContext 조회

 주의
   SimpleEvaluationContext 는 둘 다 비활성이거나 제한된다
   식에서 임의 메서드를 부를 수 있다는 것이 SpEL 의 위험 지점이다
```
