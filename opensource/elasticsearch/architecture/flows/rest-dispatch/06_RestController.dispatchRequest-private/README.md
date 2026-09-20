# RestController.dispatchRequest (private 5-arg)

상위: [REST 디스패치](../README.md)

검사들을 차례로 통과시킨 뒤 인터셉터를 태우고 핸들러를 부른다. [공개 3-arg 진입점](../01_RestController.dispatchRequest/README.md)과 이름이 같지만 하는 일이 다르다. 이 흐름에서 거절하는 길 넷이 여기서 나간다.

## 위치

`server` / `org.elasticsearch.rest` / `RestController.java` L531-L624 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/rest/RestController.java#L531-L624))

## 실제 코드

본문을 어떻게 다룰지 정하고, 안 맞으면 여기서 끝낸다.

`server` / `org.elasticsearch.rest` / `RestController.java` L539-L561 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/rest/RestController.java#L539-L561))

```java
// RestController.java L539-L561
        if (request.hasContent()) {
            final boolean isBrowserSafelistedContentType = isBrowserSafelistedContentType(request);
            consumeFormEncodedBodyParameters = isBrowserSafelistedContentType
                && request.method() == RestRequest.Method.POST
                && handler.supportsReadOnlyFormEncodedPostBody()
                && isFormEncodedBody(request)
                && interceptor.allowsBrowserSafelistedContentType(request);
            if ((isBrowserSafelistedContentType && consumeFormEncodedBodyParameters == false)
                || (consumeFormEncodedBodyParameters == false && handler.mediaTypesValid(request) == false)) {
                sendContentTypeErrorMessage(request.getAllHeaderValues("Content-Type"), channel);
                return;
            }
        } else {
            consumeFormEncodedBodyParameters = false;
        }
        RestChannel responseChannel = channel;
        if (apiProtections.isEnabled()) {
            Scope scope = handler.getServerlessScope();
            if (scope == null) {
                handleServerlessRequestToProtectedResource(request.uri(), request.method(), responseChannel);
                return;
            }
        }
```

스트리밍 본문은 크기를 모르니 0 으로 잡는다.

`server` / `org.elasticsearch.rest` / `RestController.java` L562-L562 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/rest/RestController.java#L562-L562))

```java
// RestController.java L562-L562
        final int contentLength = request.isFullContent() ? request.contentLength() : 0;
```

서킷브레이커를 예약하고 응답 채널을 한 겹 더 감싼다.

`server` / `org.elasticsearch.rest` / `RestController.java` L564-L570 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/rest/RestController.java#L564-L570))

```java
// RestController.java L564-L570
            if (handler.canTripCircuitBreaker()) {
                inFlightRequestsBreaker(circuitBreakerService).addEstimateBytesAndMaybeBreak(contentLength, "<http_request>");
            } else {
                inFlightRequestsBreaker(circuitBreakerService).addWithoutBreaking(contentLength);
            }
            // iff we could reserve bytes for the request we need to send the response also over this channel
            responseChannel = new ResourceHandlingHttpChannel(channel, circuitBreakerService, contentLength, methodHandlers);
```

인터셉터를 태우고 핸들러를 부른다. 이 블록 전체가 L563 에서 열린 try 안에 있고, 그 catch 가 L621-623 이다.

`server` / `org.elasticsearch.rest` / `RestController.java` L598-L620 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/rest/RestController.java#L598-L620))

```java
// RestController.java L598-L620
            final var finalChannel = responseChannel;
            this.interceptor.intercept(request, responseChannel, handler.getConcreteRestHandler(), new ActionListener<>() {
                @Override
                public void onResponse(Boolean processRequest) {
                    if (processRequest) {
                        try {
                            validateRequest(request, handler, client);
                            handler.handleRequest(request, finalChannel, client);
                        } catch (Exception e) {
                            onFailure(e);
                        }
                    }
                }

                @Override
                public void onFailure(Exception e) {
                    try {
                        sendFailure(finalChannel, e);
                    } catch (IOException ex) {
                        logger.info("Failed to send error [{}] to HTTP client", ex.toString());
                    }
                }
            });
```

## 동작 흐름

```text
 L539  본문이 있는가
       |
       +-- L541  폼 인코딩 본문을 파라미터로 읽어도 되는가를 정한다
       |         브라우저 안전 타입 + POST + 핸들러가 허용 + 실제로 폼 인코딩
       |         + 인터셉터가 허용 (L545)   <- 인터셉터 1회차
       |
       +-- L546  브라우저 안전 타입인데 폼으로 안 읽거나
       |         미디어 타입이 핸들러와 안 맞으면
       |     +-- L548  sendContentTypeErrorMessage   406, 여기서 끝
       |
       +-- L551  본문이 없으면 폼 파라미터도 없다

 L555  서버리스 보호가 켜져 있는가                    (apiProtections 1회차)
       +-- L557  이 핸들러에 scope 가 없으면
             +-- L558  handleServerlessRequestToProtectedResource   여기서 끝

 L562  contentLength = isFullContent() ? contentLength() : 0
         스트리밍 본문은 0 으로 잡는다. 아직 크기를 모른다

 L564  핸들러가 서킷브레이커 대상인가
       +-- true   L565  addEstimateBytesAndMaybeBreak   넘치면 예외
       +-- false  L567  addWithoutBreaking              세기만 한다

 L570  new ResourceHandlingHttpChannel(...)
         응답 채널 두 겹째. 응답이 나갈 때 예약한 바이트를 돌려준다

 L572  시스템 인덱스 접근 헤더를 정한다 (세 갈래)
         핸들러가 기본 허용이면            L584  TRUE
         아니고 Elastic 제품 헤더가 있으면 L578  TRUE + 출처
         아니면                            L581  FALSE

 L587  서버리스 보호가 켜져 있는가                    (apiProtections 2회차)
       +-- L590  요청에 서버리스 표시를 남긴다

 L594  L541 에서 정한 값이 참이면
       +-- L595  폼 인코딩 본문을 파라미터로 읽어 소비한다

 L599  interceptor.intercept(request, responseChannel, 벗긴 핸들러, 리스너)
       |
       +-- L601  onResponse(processRequest)
       |     +-- L602  true
       |     |     +-- L604  validateRequest        서버 구현은 빈 메서드 (L630)
       |     |     +-- L605  handler.handleRequest  핸들러로 넘어간다
       |     |     +-- L606  여기서 던지면 onFailure 로 합류
       |     |
       |     +-- false  아무 것도 하지 않는다
       |                인터셉터가 자기 응답을 이미 보냈다는 뜻이다
       |
       +-- L613  onFailure
             +-- L615  sendFailure

 L621  catch (Exception e)
       +-- L622  sendFailure(responseChannel, e)
                 서킷브레이커 트립, 인터셉터의 동기 throw 등을 받는다
```

```text
 인터셉터는 대개 동기다

 구현은 SecurityRestFilter 하나뿐이고
 보안 플러그인이 없으면 생성자가 람다를 꽂는다 (L137-139)

 동기로 끝나는 경우
   인터셉터 없음           L138                 즉시 TRUE
   보안이 꺼져 있음        SecurityRestFilter   즉시 TRUE
   OPTIONS                 SecurityRestFilter   즉시 실패
   보안 켜짐, 일반 요청    같은 스레드로 재진입

 비동기가 되는 경우는 둘
   본문이 스트림이고 감사 로그가 본문을 포함한다
   secondary authentication 헤더가 붙어 있다

 그래서 리스너를 받는다고 해서 사슬이 끊기는 것은 아니다
```

```text
 인터셉터가 흐름에 두 번 나온다

 L545  allowsBrowserSafelistedContentType   폼 본문을 읽어도 되는지
 L599  intercept                             요청을 진행해도 되는지

 앞엣것은 값을 돌려주는 동기 질의이고
 뒤엣것만 리스너를 받는다
```

```text
 응답 채널이 두 겹이다

 L736  MeteringRestChannelDecorator   바깥. 핸들러 이름으로 메트릭을 남긴다
 L570  ResourceHandlingHttpChannel     안쪽. 예약한 바이트를 돌려주고
                                       중복 응답을 막는다

 L570 이전에 나가는 응답(406, 서버리스 거절)은 바깥 것만 거친다
 예약을 아직 안 했으니 돌려줄 것도 없다
```

## 결과가 쓰이는 곳

```text
 핸들러에게 물어 정해진 것들
      --> supportsReadOnlyFormEncodedPostBody  폼 본문 허용 (L543)
      --> mediaTypesValid                      미디어 타입 (L547)
      --> getServerlessScope                   서버리스 노출 (L556)
      --> canTripCircuitBreaker                서킷브레이커 (L564)
      --> allowSystemIndexAccessByDefault      시스템 인덱스 (L572)
      --> 이 다섯 가지가 핸들러마다 다른 정책이 된다

 스레드 컨텍스트 헤더
      --> 시스템 인덱스 접근 여부가 여기 실린다
      --> 아래 TransportAction 들이 이 헤더를 읽는다

 getConcreteRestHandler()
      --> 인터셉터에게는 벗긴 핸들러를 준다 (L599)
      --> deprecated 래퍼가 아니라 진짜 핸들러를 보고 판단하게 한다

 processRequest 가 false 인 경우
      --> 응답이 여기서 나가지 않는다
      --> operator privileges 검사가 그렇게 쓴다. 자기가 응답을 보내고 false 를 준다
```

## 다루지 않는 것

`SecurityRestFilter` 안의 인증과 감사 로깅, operator privileges 검사, 서킷브레이커(`inFlightRequestsBreaker`)의 임계치와 예약 반환 시점, `ResourceHandlingHttpChannel` 의 중복 응답 방지와 chunked 응답 처리, 시스템 인덱스 접근 제어 헤더를 읽는 쪽, 서버리스 `Scope` 의 의미, 폼 인코딩 본문을 파라미터로 바꾸는 파싱은 같은 뼈대의 곁가지라 요약만 했다.
