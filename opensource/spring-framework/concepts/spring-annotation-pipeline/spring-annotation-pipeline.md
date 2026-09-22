# 스프링 annotation 파이프라인 — 표식 하나가 프레임워크 기능이 되기까지

> 기준 커밋: upstream `main` 526c706d1c3 (`Merge branch '7.0.x'`).
> 이 문서는 개별 PR이 아니라 **전역 동작**을 다룬다. 개별 주제는 다음 문서가 이미
> 담당하므로 여기서는 재서술하지 않고 링크만 건다:
> [probe(사전 시험 호출)](../../prs/37153-enum-array-annotation-probe/probe-pattern.md) ·
> [JDK vs Spring annotation 처리](../../prs/37153-enum-array-annotation-probe/jdk-vs-spring-annotation-handling.md) ·
> [JLS annotation 멤버 규칙](../jls-annotation-rules/jls-annotation-rules.md) ·
> [격리의 all-or-nothing 계약](../annotation-all-or-nothing-contract/annotation-all-or-nothing-contract.md).

## 0. 한 문장으로

`@RestController` 하나가 빈 등록과 URL 매핑으로 이어지는 과정은 **네 단계의 파이프라인**이다.
JDK가 클래스 파일에서 annotation 객체를 만들고(1), `AnnotationsScanner`가 "어느 요소를 뒤질지"를
정해 원재료를 모으고(2), `AnnotationTypeMappings`가 "이 annotation이 결국 무엇으로 보이는지"를
메타-annotation을 평탄화해 계산하고(3), `MergedAnnotations`/`MergedAnnotation`이 그 결과를
소비자에게 하나의 질의 표면으로 노출한다(4). 검색(2)과 매핑(3)은 서로 직교하는 두 축이며,
스프링의 annotation 코드를 읽을 때 헷갈리는 대부분은 이 두 축을 한 축으로 뭉뚱그린 데서 온다.

## 1. 전체 흐름

파이프라인 전체를 한 장에 놓으면 다음과 같다. 왼쪽 축(검색)은 "요소 계층을 얼마나 넓게
뒤지는가", 오른쪽 축(매핑)은 "찾은 annotation 하나를 얼마나 깊게 풀어내는가"이다.

```
소비자   AnnotatedElementUtils · RequestMappingHandlerMapping · @Conditional 처리기 · ...
           │  질문: "이 요소에 @X 가 있나?" / "@X 의 value 는?"
           ▼
 [4층]  MergedAnnotations  (공개 API)
           ├ from(AnnotatedElement, SearchStrategy, RepeatableContainers, AnnotationFilter)
           ├ search(SearchStrategy)...  (fluent API)
           └ of(Collection<MergedAnnotation<?>>)      ← ASM 경로가 조립해 넣는 입구
           ▼
        TypeMappedAnnotations.scan(criteria, processor)      TypeMappedAnnotations.java:236
           │
           ├─[검색 축]────────────────────────────────────────────────────────────┐
           │   AnnotationsScanner.scan(context, source, strategy, ..., processor) │
           │     · SearchStrategy 에 따라 자기 자신 / 상위클래스 / 인터페이스 /   │
           │       enclosing class 를 순회 — 한 단계마다 aggregateIndex 가 하나씩  │
           │     · 각 단계에서 getDeclaredAnnotations(element)                     │
           │          └ [1층] JDK element.getDeclaredAnnotations()                 │
           │               → AnnotationFilter.PLAIN(java.lang.*) 제외              │
           │               → AttributeMethods.canLoad() probe 통과분만             │
           │               → element 단위 캐시에 적재                              │
           │     ▼                                                                 │
           │   AnnotationsProcessor 구현체가 결과를 소비                           │
           │     (IsPresent / MergedAnnotationFinder / AggregatesCollector)        │
           │                                                                       │
           └─[매핑 축]────────────────────────────────────────────────────────────┤
               AnnotationTypeMappings.forAnnotationType(@X)                        │
                 · @X 의 메타-annotation 을 BFS 로 평탄화 → mappings[0..n]         │
                 · index 0 = @X 자신(distance 0), 이후 distance 1, 2, ...          │
                 · @AliasFor 를 aliasMappings / mirrorSets 로 사전 계산            │
               ▼                                                                   │
               TypeMappedAnnotation = (mapping 한 개) + (실제 값의 출처)  ─────────┘
                 · getValue 시 aliasMapping 이 있으면 root 의 값으로 치환
           ▼
        MergedAnnotation<A>   isPresent() · getString("value") · asMap() · synthesize()
```

두 축의 좌표가 각각 `aggregateIndex`와 `distance`다. 전자는 "요소 계층에서 몇 칸 떨어졌나"
(내 클래스=0, 부모=1, ...), 후자는 "메타 계층에서 몇 칸 떨어졌나"(`@RestController`=0,
`@Controller`=1, `@Component`=2)이다. 결과를 하나 골라야 할 때 스프링은 이 두 좌표를 사전순으로
비교한다 — `AggregatesSpliterator.tryAdvance`는 aggregate를 하나씩 훑으면서 그 안에서
`distance`가 가장 낮은 매핑을 먼저 내보낸다(`TypeMappedAnnotations.java:567`). "가장 가까운
선언이 이긴다"는 스프링의 직관은 이 정렬 규칙의 다른 이름이다.

## 2. 1층 — JDK 리플렉션이 주는 원재료

스프링이 받는 입력은 결국 `AnnotatedElement.getDeclaredAnnotations()` 하나다. 이 호출이
동적 프록시 배열을 돌려주고, 값 해석은 속성 메서드를 호출할 때까지 미뤄진다. 이 지연 계약과
그로 인해 스프링이 떠안는 문제는 [JDK vs Spring 문서](../../prs/37153-enum-array-annotation-probe/jdk-vs-spring-annotation-handling.md)가
다루므로 여기서는 파이프라인 상의 위치만 짚는다. **1층의 출력은 "타입과 값을 아직 신뢰할 수
없는 annotation 객체 배열"이며, 그것을 신뢰 가능한 상태로 바꾸는 것이 2층의 첫 임무다.**

## 3. 2층 — AnnotationsScanner: 어디를 뒤질 것인가

`AnnotationsScanner`는 전략에 따라 요소 계층을 순회하면서, 각 단계마다 그 요소의 선언
annotation을 processor에게 넘긴다. 진입점은 `scan`(`AnnotationsScanner.java:79`)이고, 대상이
`Class`인지 `Method`인지 그 외인지에 따라 세 갈래로 갈린다(`AnnotationsScanner.java:86-97`).

`Class`의 경우 전략별 분기는 `processClass`의 switch가 전부다(`AnnotationsScanner.java:99-108`).

| SearchStrategy | 뒤지는 범위 | 구현 |
|---|---|---|
| `DIRECT` | 선언된 것만 | `processElement` |
| `INHERITED_ANNOTATIONS` | 선언 + `@Inherited`가 붙은 상위클래스 annotation | `processClassInheritedAnnotations` |
| `SUPERCLASS` | 선언 + 상위클래스 전부(`@Inherited` 불필요) | `processClassHierarchy(includeInterfaces=false)` |
| `TYPE_HIERARCHY` | 상위클래스 + 인터페이스 (+ 선택적으로 enclosing class) | `processClassHierarchy(includeInterfaces=true)` |

`INHERITED_ANNOTATIONS`만 구현이 유별난 이유가 있다. `@Inherited` 판정은 JDK가 이미
`getAnnotations()`로 계산해 주므로, 스캐너는 루트의 `getAnnotations()` 결과를 "relevant" 목록으로
잡아 두고 상위클래스를 내려가면서 그 목록에 없는 것을 지워 나간다
(`AnnotationsScanner.java:126-150`). 즉 JDK의 상속 규칙을 재구현하지 않고 결과만 빌려 쓴다.

### 3.1 단일 관문: getDeclaredAnnotations

전략이 무엇이든 실제 원재료 취득은 `getDeclaredAnnotations(source, defensive)` 한 곳을
통과한다(`AnnotationsScanner.java:432-465`). 이 메서드가 하는 일이 2층의 핵심이다.

1. **캐시 조회** — `declaredAnnotationCache`(`AnnotationsScanner.java:55`)에서 element로 찾는다.
2. **정화** — 캐시 미스면 JDK에서 읽어 온 배열을 훑으며 두 종류를 `null`로 지운다.
   `AnnotationFilter.PLAIN`에 걸리는 것(= `java.lang.` / `org.springframework.lang.` 접두어,
   `AnnotationFilter.java:43`)과, `AttributeMethods.forAnnotationType(...).canLoad(...)`가
   실패한 것이다(`AnnotationsScanner.java:445-447`). 후자가 probe이며 상세는
   [probe 문서](../../prs/37153-enum-array-annotation-probe/probe-pattern.md)에 있다.
3. **캐시 적재** — `Class`나 `Member`일 때만 캐시에 넣는다(`AnnotationsScanner.java:454-458`).
   그 외 element(예: 파라미터)는 동일성이 보장되지 않으므로 캐시하지 않는다.
4. **방어 복제** — 캐시에서 나온 배열을 호출자가 훼손할 수 있는 경로에서는 `clone()`을 준다
   (`AnnotationsScanner.java:461-464`). `defensive=true`로 호출하는 곳이 바로 배열 원소를
   `null`로 덮어쓰는 두 지점 — `@Inherited` 필터링(126행)과 bridge 메서드 중복 제거(395행)다.

여기서 얻는 성질 하나: **"로드 불가"로 걸러진 annotation은 캐시에도 걸러진 상태로 남는다.**
따라서 필터링 결과는 파이프라인 전 구간에서 일관되며, 소비자는 그것이 애초에 없었던 것처럼
본다.

### 3.2 조기 종료

스캐너에는 값싼 탈출구가 여럿 있다. `hasPlainJavaAnnotationsOnly`는 이름이 `java.`로 시작하는
타입과 `Ordered`를 통째로 건너뛰고(`AnnotationsScanner.java:498-500`), `isKnownEmpty`는
계층이 없는 요소이면서 선언 annotation이 0개면 스캔 자체를 생략하게 한다
(`AnnotationsScanner.java:471-484`). 후자의 결과가 `TypeMappedAnnotations.from`에서
`NONE`이라는 공유 인스턴스를 돌려주는 근거다(`TypeMappedAnnotations.java:253-256`).
클래스패스 전체를 훑는 프레임워크에서 "아무것도 없다"를 싸게 판정하는 것은 기능이 아니라
생존 조건이다.

## 4. 3층 — AnnotationTypeMappings: 무엇으로 볼 것인가

`AnnotationTypeMappings`는 annotation **타입 하나**를 받아 그 타입이 끌고 오는 메타-annotation
전부를 평탄한 리스트로 만든다. 요소(element)와 무관하게 타입에만 의존하므로 **한 번 계산해
영구 캐시**할 수 있다(`AnnotationTypeMappings.java:226-240`, 캐시는 `AnnotationFilter`별로
분리된 `Cache` 인스턴스).

평탄화는 큐를 쓰는 너비 우선 탐색이다(`AnnotationTypeMappings.java:80-90`). 루트를 큐에 넣고,
꺼낼 때마다 그 타입의 선언 annotation을 다시 큐에 넣는다(`addMetaAnnotationsToQueue`, 92행).
결과 리스트의 index 0은 항상 루트이며, 뒤로 갈수록 `distance`가 커진다.

순환은 두 겹으로 막는다. `isAlreadyMapped`는 지금 만들려는 매핑의 조상 사슬에 같은 타입이
이미 있으면 건너뛰고(`AnnotationTypeMappings.java:141-151`), `visitedAnnotationTypes` 집합은
Java가 아닌 JVM 언어가 허용하는 재귀적 annotation 정의에 대비한다(`AnnotationTypeMapping.java:287-292`).
[JLS 문서](../jls-annotation-rules/jls-annotation-rules.md)가 말하는 "값 구조의 재귀는 유한하다"와 달리 **메타-annotation
그래프는 순환할 수 있고**(그 문서가 드는 실례가 `@Retention`과 `@Documented`의 상호 순환이다),
그래서 값 트리 쪽과 달리 여기서는 명시적 순환 방어가 필요하다.

### 4.1 매핑 하나가 담는 것

`AnnotationTypeMapping`의 생성자가 사전 계산하는 배열들이 이 층의 실체다
(`AnnotationTypeMapping.java:85-102`).

- `attributes` — 이 타입의 속성 메서드 목록(`AttributeMethods`).
- `aliasedBy` — "이 속성을 겨냥한 `@AliasFor`가 어디서 오는가"의 역방향 색인
  (`resolveAliasedForTargets`, 115행). `@AliasFor` 자체의 유효성 검사(자기 참조, 반환 타입 불일치,
  쌍방 선언 누락 등)도 여기서 `AnnotationConfigurationException`으로 즉시 터진다(128-188행).
- `aliasMappings` — 속성 index -> **루트 annotation의 속성 index**. `processAliases`가 별칭
  사슬을 모아(`collectAliases`, 210행) 루트에 대응되는 자리를 찾아 채운다(224-249행).
- `mirrorSets` — 같은 annotation 안에서 서로를 가리키는 별칭 쌍(`@RequestMapping`의
  `value`/`path` 같은)을 한 묶음으로 묶어, 읽을 때 어느 쪽이 실제 값인지 판정하게 한다.
- `synthesizable` — 별칭이나 중첩 annotation 때문에 합성 프록시가 필요한지 여부.

`afterAllMappingsSet`은 모든 매핑이 만들어진 뒤 한 번 돌면서 "겨냥한 대상이 실제로 meta-present
인가"와 "미러 쌍의 기본값이 같은가"를 검증한다(`AnnotationTypeMapping.java:308-346`). 별칭
설정 오류가 런타임 값 조회가 아니라 **매핑 구축 시점에** 예외로 드러나는 이유다.

### 4.2 메타-annotation 매핑 워크: @RestController

실제 스프링 타입으로 걸어 보자. 선언은 다음과 같다 —
`@RestController`는 `@Controller`와 `@ResponseBody`를 달고 있고 `value()`는 `@Controller`의
`value`를 겨냥한다(`RestController.java:48-59`). `@Controller`는 `@Component`를 달고 `value()`는
`@Component`의 `value`를 겨냥한다(`Controller.java:45-52`).

```
@RestController("orders")
class OrderController { }

  (1) 검색 축: AnnotationsScanner 가 OrderController 의 선언 annotation 수집
      → [@RestController]        (@Target/@Retention 등은 PLAIN 필터로 제외)

  (2) 매핑 축: AnnotationTypeMappings.forAnnotationType(RestController.class)

        mappings[0]  @RestController   distance 0   ← root
             │   메타: @Controller, @ResponseBody 를 큐에 적재
             ├── mappings[1]  @Controller      distance 1
             │        │   메타: @Component 를 큐에 적재
             │        └── mappings[3]  @Component   distance 2
             └── mappings[2]  @ResponseBody    distance 1
        (BFS 이므로 리스트 순서는 0, 1, 2, 3 — 깊이가 아니라 너비 순)

  (3) 별칭 사전 계산: mappings[3](@Component) 생성 시 collectAliases 가
      source 사슬을 거슬러 올라가며 별칭 묶음을 모은다

        Component.value ←(@AliasFor)─ Controller.value ←(@AliasFor)─ RestController.value
        묶음 = { Component.value, Controller.value, RestController.value }
        루트에서의 index = 0  →  mappings[3].aliasMappings[value] = 0
                                mappings[1].aliasMappings[value] = 0

  (4) 읽기: MergedAnnotations.from(OrderController.class).get(Component.class)
        → mappings[3] 기반 TypeMappedAnnotation 생성
        → getString("value")
             getValue(0): aliasMapping(0) == 0 이므로 mapping 을 root 로 갈아타고
             root(@RestController) 의 0번 속성에서 실제 값을 꺼낸다
        → "orders"
```

여기서 드러나는 성질이 스프링 annotation 모델의 핵심 계약이다. **`@Component`는 선언된 적이
없지만 "있는 것"으로 보이고, 그 값은 사용자가 `@RestController`에 쓴 값이다.** 값 치환은
`TypeMappedAnnotation.getValue`의 단 몇 줄에서 일어난다 — `useMergedValues`이면
`getAliasMapping`으로 루트 index를 얻어 mapping과 index를 통째로 갈아탄다
(`TypeMappedAnnotation.java:401-413`). 별칭이 없으면 자기 매핑의 값을, 그것도 없으면 속성의
기본값을 쓴다(392-399행, 425-435행).

## 5. 4층 — MergedAnnotations: 소비자가 보는 표면

`MergedAnnotations`는 인터페이스이고, 리플렉션 경로의 구현이 `TypeMappedAnnotations`다.
질의 종류마다 전용 `AnnotationsProcessor`를 만들어 스캐너에 태워 보내는 구조다
(`TypeMappedAnnotations.java:236-246`).

- `isPresent` — `IsPresent` processor. 직접 선언 타입이 일치하면 즉시 true, 아니면 매핑
  전체를 훑어 meta-present를 판정한다(`TypeMappedAnnotations.java:310-343`). 흔한 조합
  네 가지는 공유 인스턴스를 쓴다(287-294행).
- `get` — `MergedAnnotationFinder`. 후보를 만들 때마다 `MergedAnnotationSelector`(기본값
  `nearest()`)에게 "이보다 더 좋은 게 나올 수 있나"를 묻고, distance 0이면 즉시 확정한다
  (`TypeMappedAnnotations.java:414-430`).
- `stream`/`iterator` — `AggregatesCollector`가 aggregate 목록을 만들고, 앞서 본
  `AggregatesSpliterator`가 (aggregate, distance) 순서로 하나씩 흘려보낸다.

`Aggregate` 생성자가 그 단계에서 발견된 annotation마다 `AnnotationTypeMappings`를 미리
확보한다는 점(`TypeMappedAnnotations.java:501-509`)이 두 축이 만나는 지점이다. 검색 축이
"무엇을 찾았는지"를, 매핑 축이 "그것이 무엇으로 보이는지"를 각각 답하고, 스플리터레이터가
둘을 곱해 최종 시퀀스를 만든다.

## 6. 두 개의 입구 — 리플렉션 경로와 ASM 경로

지금까지는 `Class` 객체가 이미 로드돼 있다는 전제였다. 그런데 컴포넌트 스캔은 **클래스를
로드하기 전에** annotation을 읽어야 한다. 후보가 아닌 수천 개의 클래스를 로드하는 비용과,
로드 실패가 기동 실패로 번지는 위험을 피하기 위해서다. 그래서 스프링에는 입구가 둘이다.

```
[리플렉션 경로]                          [ASM 경로]
 Class 객체 (이미 로드됨)                 .class 파일 리소스 (미로드)
      │                                        │
      │                                   ClassReader (spring-core 내장 ASM)
      │                                   SimpleMetadataReader.java:46-52
      │                                        │  SKIP_DEBUG|SKIP_CODE|SKIP_FRAMES
      │                                        ▼
      │                                   SimpleAnnotationMetadataReadingVisitor
      │                                     visitAnnotation → MergedAnnotationReadingVisitor
      │                                     속성을 Map<String,Object> 로 수집
      │                                     MergedAnnotation.of(classLoader, source,
      │                                                         annotationType, attributes)
      │                                        │
      ▼                                        ▼
 MergedAnnotations.from(element, ...)    MergedAnnotations.of(List<MergedAnnotation<?>>)
 TypeMappedAnnotations                   MergedAnnotationsCollection
      │                                        │
      └───────────────┬────────────────────────┘
                      ▼
        같은 AnnotationTypeMappings (매핑 축은 공유)
                      ▼
              MergedAnnotation<A>
```

핵심은 **분기가 검색 축에서만 일어난다**는 것이다. ASM 경로도 메타-annotation 평탄화는
동일한 `AnnotationTypeMappings.forAnnotationType`을 쓴다
(`MergedAnnotationsCollection.java:54-60`, `TypeMappedAnnotation.java:621-629`). 그래서
`@RestController`가 `@Component`로 보이는 성질은 두 경로에서 똑같이 성립한다. 다만 값의 출처가
다르다 — 리플렉션 경로는 JDK annotation 프록시에서 값을 꺼내고(`AnnotationUtils::invokeAnnotationMethod`),
ASM 경로는 바이트코드에서 읽어 만든 `Map`에서 꺼낸다(`TypeMappedAnnotation::extractFromMap`).

ASM 경로도 완전히 "클래스 로딩 없이"는 아니다. **대상 클래스는 로드하지 않지만, annotation
타입 자체와 enum 상수는 로드한다** — `MergedAnnotationReadingVisitor`가 descriptor에서 얻은
이름으로 `ClassUtils.forName`을 호출하고, 실패하면 `TypeNotPresentException`을 던진다
(`MergedAnnotationReadingVisitor.java:102-131`). 여기서도 `AnnotationFilter.PLAIN`에 걸리는
중첩 annotation은 아예 방문하지 않는다(119행).

### 6.1 컴포넌트 스캔이 실제로 쓰는 쪽

`ClassPathScanningCandidateComponentProvider.scanCandidateComponents`는 리소스 패턴으로 찾은
`.class` 파일마다 `MetadataReader`를 얻어 필터를 적용한다
(`ClassPathScanningCandidateComponentProvider.java:446`, 리더 획득은 464행). 기본 include
필터는 `new AnnotationTypeFilter(Component.class)`이고(217행), 그 판정은
`metadata.hasAnnotation(...) || metadata.hasMetaAnnotation(...)`이다
(`AnnotationTypeFilter.java:99-103`). 두 메서드 모두 결국 ASM으로 만든 `MergedAnnotations`에
질의한다(`AnnotationMetadata.java:86-88`, `97-100`).

즉 **컴포넌트 스캔의 후보 판정은 전적으로 ASM 경로**이며, 통과한 클래스는
`ScannedGenericBeanDefinition`으로 감싸져 그 `AnnotationMetadata`(역시 ASM 산물)를 그대로
들고 다닌다(466행). 리플렉션 경로로 넘어가는 것은 그 뒤 실제 빈 인스턴스를 만들 때다.

## 7. 소비자 쪽에서 본 같은 파이프라인

`AnnotatedElementUtils`는 정적 유틸의 얼굴을 하고 있지만 내부는 전부
`MergedAnnotations`다. 이름의 접두어가 곧 전략 선택이다 — `get*` 계열은
`SearchStrategy.INHERITED_ANNOTATIONS`(`AnnotatedElementUtils.java:772-774`), `find*` 계열은
`SearchStrategy.TYPE_HIERARCHY`(799-801행)를 쓴다. 두 계열이 다른 답을 주는 이유는 로직이
달라서가 아니라 **검색 축의 범위만 다르기 때문**이다.

`RequestMappingHandlerMapping`은 두 층을 모두 직접 쓴다. 핸들러 클래스 판정은
`AnnotatedElementUtils.hasAnnotation(beanType, Controller.class)` 한 줄이고
(`RequestMappingHandlerMapping.java:177-179`), 여기서 `@RestController`가 `@Controller`로
보이는 것이 4.2절의 매핑 축 덕분이다. 매핑 정보 생성은 `MergedAnnotations`를 직접 열어
스트림으로 다룬다(265-274행).

```java
MergedAnnotations.from(element, SearchStrategy.TYPE_HIERARCHY, RepeatableContainers.none())
        .stream()
        .filter(MergedAnnotationPredicates.typeIn(RequestMapping.class, HttpExchange.class))
        .filter(MergedAnnotationPredicates.firstRunOf(MergedAnnotation::getAggregateIndex))
        .map(AnnotationDescriptor::new)
```

`firstRunOf(getAggregateIndex)`가 1절에서 본 좌표를 그대로 쓰는 자리다. 스플리터레이터가
aggregate 오름차순으로 흘려보내므로, "가장 가까운 계층의 것만 남기고 뒤는 버린다"가 이 한 줄로
표현된다. `@GetMapping`이 `@RequestMapping`으로 인식되는 것도 매핑 축의 결과이며, 이 코드가
`@GetMapping`을 따로 알 필요는 없다.

## 8. 캐시 지도

파이프라인의 각 층이 자기 캐시를 갖는다. 무엇을 키로 잡는지가 그 층이 무엇에 의존하는지를
말해 준다.

| 캐시 | 키 | 위치 | 무효화 |
|---|---|---|---|
| 선언 annotation | `AnnotatedElement` (Class/Member만) | `AnnotationsScanner.java:55` | `clearCache()` |
| base type 메서드 | `Class<?>` | `AnnotationsScanner.java:58` | `clearCache()` |
| 타입 매핑 | `AnnotationFilter` -> `Class<? extends Annotation>` | `AnnotationTypeMappings.java:56-58` | `clearCache()` |
| 속성 메서드 | annotation 타입 | `AttributeMethods` | — |

매핑 캐시가 요소와 무관하다는 점이 중요하다. `@RestController`가 붙은 클래스가 500개여도
`@RestController`의 메타 그래프는 애플리케이션 전체에서 한 번만 계산된다.

## 9. 코드를 읽을 때의 판별 질문

낯선 annotation 관련 코드를 만났을 때 위치를 특정하는 질문 세 개.

첫째, 이 코드가 **다른 요소**(상위클래스, 인터페이스, 메서드)를 보러 가는가? 그렇다면 검색
축이고, `SearchStrategy`가 동작을 지배한다. 둘째, 이 코드가 **다른 annotation 타입**(메타
annotation, 별칭)을 보러 가는가? 그렇다면 매핑 축이고, `AnnotationTypeMappings`가 이미 계산해
둔 배열을 읽을 뿐이다. 셋째, 대상이 `Class` 객체인가 `MetadataReader`인가? 전자면 리플렉션
경로, 후자면 ASM 경로이며 — 6절대로 — 갈리는 것은 검색 축뿐이다.

## 10. 한 문장 요약

스프링의 annotation 파이프라인은 JDK가 준 신뢰할 수 없는 원재료를 `AnnotationsScanner`가
필터링·캐시하며 요소 계층을 따라 모으고(검색 축), `AnnotationTypeMappings`가 메타-annotation과
`@AliasFor`를 타입 단위로 평탄화해 두며(매핑 축), `MergedAnnotations`가 두 축의 좌표
(aggregateIndex, distance)로 정렬된 결과를 하나의 질의 표면으로 노출하는 구조이고, 컴포넌트
스캔의 ASM 경로는 검색 축만 바꿔 끼운 같은 파이프라인이다.
