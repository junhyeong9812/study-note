# REST 디스패치

HTTP 요청 하나가 **어느 핸들러로 가는지 정해지고, 거기 닿기까지**의 길이다. Elasticsearch의 모든 HTTP 요청이 이 한 줄기를 지난다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 핸들러와 인터셉터 계약이다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 AbstractHttpServerTransport.dispatchRequest      L523
   여기서 갈림길이 셋이다
   |
   +-- 이미 잘못된 요청이면       dispatchBadRequest    L527
   +-- 스레드 컨텍스트 채우기 실패 dispatchBadRequest    L533
   |     (보안 플러그인이 여기서 인증한다. 실패하면 이 갈래다)
   |
   +-- 정상
       |
       v
 [01] RestController.dispatchRequest                    L425
      X-elastic-product 헤더를 달고 [02] 로 넘긴다
      |
 [02] RestController.tryAllHandlers                     L702
      후보 핸들러를 하나씩 꺼내 맞는 것을 찾는다
      |
      +-- [03] getAllHandlers          L721  매칭 모드 4종으로 후보를 낸다
      +-- [04] handleNoHandlerFound    L731  후보가 안 맞을 때의 처리
      |
      +-- 찾으면
          |
 [05] RestController.maybeAggregateAndDispatchRequest   L511
      본문을 모아야 하는 핸들러면 다 모은 뒤에 넘긴다
      |
 [06] RestController.dispatchRequest (private 5-arg)    L531
      검사들을 거치고 인터셉터를 태운 뒤 핸들러를 부른다
      |
 [07] BaseRestHandler.handleRequest                     L79
      파라미터를 검증하고 prepareRequest 로 실행할 것을 만든다
      action.accept 에서 TransportAction 으로 넘어간다
```

```text
 이름이 같은 메서드가 셋이다

 AbstractHttpServerTransport.dispatchRequest   L523  3-arg, 셋째가 Throwable
 RestController.dispatchRequest                L425  3-arg, public, 진입점
 RestController.dispatchRequest                L531  5-arg, private, 실제 처리

 [01] 과 [06] 은 같은 클래스 같은 이름이지만 하는 일이 다르다
 [01] 은 예외를 잡는 껍데기이고 [06] 이 검사와 인터셉터를 다 한다
```

```text
 핸들러에 닿지 않고 끝나는 길이 아홉 개다

 [02] L707  error_trace 를 달았는데 상세 오류가 꺼져 있다      400
 [02] L744  메서드를 해석 못 했다                              405
 [02] L749  후보를 다 돌아도 맞는 것이 없다                     400
 [04] L664  OPTIONS 요청이다                                   Allow 헤더
 [04] L672  경로는 있는데 그 메서드로는 등록돼 있지 않다        405
 [06] L548  Content-Type 이 핸들러와 안 맞는다                  406
 [06] L558  서버리스인데 이 API 에 scope 가 없다                ApiNotAvailable
 [06] L615  인터셉터가 실패를 돌려줬다
 [06] L622  서킷브레이커가 걸리는 등 검사 중에 예외가 났다

 그래서 이 흐름의 절반은 "어디서 거절하는가"다
 [01] L431 의 catch 는 위에서 새어 나온 것을 받는 마지막 그물이다
```

```text
 응답을 보내지 않고 끝나는 길도 둘 있다

 [06] L602  인터셉터가 false 를 돌려줬다
            인터셉터가 자기 응답을 이미 보냈다는 뜻이다
            (operator privileges 가 그렇게 쓴다)

 [05] aggregate 의 close()  본문을 다 모으기 전에 연결이 끝났다
            모아 둔 청크만 풀고 끝난다. 이어받을 콜백이 안 불린다
```

## 어디에서 쓰이는가

```text
 [transport action] action.accept 이후가 그 흐름이다
 [구조: 노드 역할] 어느 노드로 보내도 여기까지는 똑같이 온다
 [설정 시점] 핸들러 등록은 기동할 때 끝나 있다. 여기서는 찾기만 한다
```

노드 쪽 조건은 [노드 역할](../../structure/node-roles/README.md)에 있다. 핸들러가 실행을 넘긴 뒤(`action.accept`)는 transport action 흐름이고 아직 그리지 않았다.

## 단계

1. [RestController.dispatchRequest](01_RestController.dispatchRequest/README.md)가 헤더를 달고 예외를 잡는다.
2. [RestController.tryAllHandlers](02_RestController.tryAllHandlers/README.md)가 후보를 돌며 핸들러를 고른다.
3. [RestController.getAllHandlers](03_RestController.getAllHandlers/README.md)가 매칭 모드마다 후보를 하나씩 낸다.
4. [RestController.handleNoHandlerFound](04_RestController.handleNoHandlerFound/README.md)가 안 맞는 후보를 처리한다.
5. [RestController.maybeAggregateAndDispatchRequest](05_RestController.maybeAggregateAndDispatchRequest/README.md)가 본문을 모을지 정한다.
6. [RestController.dispatchRequest (private)](06_RestController.dispatchRequest-private/README.md)가 검사와 인터셉터를 거쳐 핸들러를 부른다.
7. [BaseRestHandler.handleRequest](07_BaseRestHandler.handleRequest/README.md)가 파라미터를 검증하고 실행을 시작한다.

## 결과가 쓰이는 곳

```text
 고른 핸들러
      --> [06] 의 검사들이 이 핸들러에게 물어서 정해진다
          본문을 스트림으로 받는가, 서킷브레이커를 걸 수 있는가,
          시스템 인덱스를 봐도 되는가
      --> deprecated 라우트면 원래 핸들러가 한 겹 싸여 있다
          그래서 물어볼 때 getConcreteRestHandler() 로 벗겨서 묻는다

 MeteringRestChannelDecorator 와 ResourceHandlingHttpChannel
      --> 응답 채널이 두 겹으로 싸인다
      --> 바깥은 핸들러별 메트릭, 안쪽은 서킷브레이커 반환과 중복 응답 방지

 prepareRequest 가 만든 RestChannelConsumer
      --> action.accept(channel) 이 실제 실행이다
      --> 여기서 TransportAction 으로 넘어간다

 스레드
      --> 기본 경로는 여기까지 한 스레드로 온다
      --> 본문이 스트림이거나 인터셉터가 비동기로 갈 때만 끊긴다
```

## 다루지 않는 것

핸들러 등록 경로(`registerHandler` 세 갈래와 `PathTrie` 자료구조), `MethodHandlers` 가 메서드와 API 버전으로 핸들러를 고르는 규칙, REST API 호환성(`RestApiVersion`)의 의미, `SecurityRestFilter` 안의 인증과 감사 로깅, 응답이 나가는 경로(`DefaultRestChannel.sendResponse` 이후), CORS 처리, HTTP 계층(Netty4)과 청크 전송은 같은 뼈대의 곁가지라 요약만 했다. 1차 인증은 이 흐름보다 앞 단계라 여기서 다루지 않는다.

## 하위 메서드

- [01 RestController.dispatchRequest](01_RestController.dispatchRequest/README.md)
- [02 RestController.tryAllHandlers](02_RestController.tryAllHandlers/README.md)
- [03 RestController.getAllHandlers](03_RestController.getAllHandlers/README.md)
- [04 RestController.handleNoHandlerFound](04_RestController.handleNoHandlerFound/README.md)
- [05 RestController.maybeAggregateAndDispatchRequest](05_RestController.maybeAggregateAndDispatchRequest/README.md)
- [06 RestController.dispatchRequest (private 5-arg)](06_RestController.dispatchRequest-private/README.md)
- [07 BaseRestHandler.handleRequest](07_BaseRestHandler.handleRequest/README.md)
- [spi](spi/README.md) — 핸들러 계약, 인터셉터 계약
