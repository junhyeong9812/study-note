# SpelNodeImpl.getValue

상위: [SpelExpression.getValue](../README.md)

구문 트리의 노드 하나를 평가한다. 모든 노드가 같은 계약을 따르고, 실제 동작은 `getValueInternal` 구현이 정한다. 프로퍼티 참조가 가장 흔한 노드다.

## 실제 코드

`spring-expression` / `org.springframework.expression.spel.ast` / `SpelNodeImpl.java` L112-L120 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-expression/src/main/java/org/springframework/expression/spel/ast/SpelNodeImpl.java#L112-L120))

```java
// SpelNodeImpl.java L112-L120
@Override
public final @Nullable Object getValue(ExpressionState expressionState) throws EvaluationException {
    return getValueInternal(expressionState).getValue();
}

@Override
public final TypedValue getTypedValue(ExpressionState expressionState) throws EvaluationException {
    return getValueInternal(expressionState);
}
```

프로퍼티 참조 노드의 평가다.

`spring-expression` / `org.springframework.expression.spel.ast` / `PropertyOrFieldReference.java` L117-L126 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-expression/src/main/java/org/springframework/expression/spel/ast/PropertyOrFieldReference.java#L117-L126))

```java
// PropertyOrFieldReference.java L117-L126
@Override
public TypedValue getValueInternal(ExpressionState state) throws EvaluationException {
    TypedValue tv = getValueInternal(state, state.getActiveContextObject(),
            state.getEvaluationContext(), state.getConfiguration().isAutoGrowNullReferences());
    PropertyAccessor accessorToUse = this.cachedReadAccessor;
    if (accessorToUse instanceof CompilablePropertyAccessor compilablePropertyAccessor) {
        setExitTypeDescriptor(CodeFlow.toDescriptor(compilablePropertyAccessor.getPropertyType()));
    }
    return tv;
}
```

## 동작 흐름

```text
 노드 평가 (공통)
   getValue(state) --> getValueInternal(state).getValue()
   TypedValue 로 감싸 값과 타입 정보를 함께 전달한다
     (다음 노드가 타입을 알아야 접근자를 고를 수 있다)

 PropertyOrFieldReference.getValueInternal
 |
 | L119 현재 활성 객체(앞 노드의 결과)와 평가 문맥으로 readProperty
 |        평가 문맥의 PropertyAccessor 목록을 순회
 |          canRead(context, target, name) 인 첫 접근자로 read
 |          찾은 접근자는 노드에 캐시된다 (같은 타입 반복 평가에 유리)
 |        기본 접근자
 |          ReflectivePropertyAccessor   getter/필드
 |          (컨테이너 환경) BeanExpressionContextAccessor, MapAccessor 등
 |
 | L121 캐시된 접근자가 컴파일 가능하면 반환 타입 기술자를 기록
 |        --> 나중에 바이트코드 생성에 쓰인다
 |
 +-- autoGrowNullReferences 설정이면
        null 인 중간 객체를 자동 생성 (List/Map 등)
```

```text
 다른 노드의 예

 MethodReference    MethodResolver 로 메서드를 찾아 호출 (인자도 각각 평가)
 Indexer            리스트/배열/맵/문자열 인덱싱
 BeanReference      @beanName --> BeanResolver 로 컨테이너 조회
 VariableReference  #var --> 평가 문맥의 변수
 OpPlus 등          피연산자를 평가한 뒤 연산
 Ternary / Elvis    조건에 따라 한쪽만 평가 (단축 평가)
```

## 결과가 쓰이는 곳

```text
 TypedValue
      --> 부모 노드의 입력
      --> 마지막에 SpelExpression.getValue 가 값만 꺼내 반환

 접근자 캐시
      --> 같은 식을 같은 타입에 반복 평가할 때 탐색을 건너뛴다
      --> 타입이 바뀌면 다시 찾는다

 평가 중 예외
      --> SpelEvaluationException (메시지 코드와 위치 포함)
      --> 널 참조, 타입 불일치, 접근 불가 등이 여기로 모인다
```
