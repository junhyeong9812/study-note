# 트랜스포트 액션

액션 하나가 **실제로 실행되기까지 거치는 공통 골격**이다. 검증하고, 참조 수를 올리고, 필터 체인을 태우고, 필요하면 스레드를 갈아타고 나서야 `doExecute` 가 불린다. [REST 디스패치](../rest-dispatch/README.md)의 `action.accept` 뒤가 여기다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 필터와 체인 계약이다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 앞단 (클라이언트 경로)

 AbstractClient.execute                            L154
   +-- doExecute(...)                              L160  구현에 따라 갈린다
   +-- catch (Exception)                           L161
         assert false 후 listener.onFailure        L162-163

 NodeClient.doExecute                              L77
   +-- executeAndReturnTask                        L84
   |     +-- transportAction(action)               L113  ActionType -> TransportAction
   |     +-- taskManager.registerAndExecute        L111
   +-- catch 3종만 잡아 리스너로 보낸다             L85-91
         TaskCancelled / IllegalArgument / IllegalState

 TaskManager.registerAndExecute                    L195
   +-- register(...)                               L212  태스크를 만든다
   +-- action.execute(task, request, 래핑 리스너)  L217  -> [01]

       |
       v
 [01] TransportAction.execute                      L58
      executor 를 보고 포크할지 정한다
      |
 [02] TransportAction.handleExecution              L67
      검증하고 참조 수를 올리고 체인을 만든다
      |
 [03] RequestFilterChain.proceed                   L128
      필터를 하나씩 태우고 마지막에 실행한다
      |
      +-- 포크하는 경우
          |
 [04] TransportAction.doExecuteForking             L99
      ~~> 다른 스레드에서
      |
 doExecute (abstract)                              L103
      여기서부터 액션마다 다른 구현이다
```

```text
 진입점이 둘이다

 execute       L58  클라이언트가 부른다. 포크할 수 있다
 executeDirect L54  전송 계층이 부른다. 언제나 doExecute 다

 executeDirect 가 포크하지 않는 이유는
 전송 핸들러를 등록할 때 이미 executor 를 줬기 때문이다
 (HandledTransportAction L45-52)
 즉 그 스레드에 도착한 시점에 이미 제 스레드풀 위에 있다

 둘 다 handleExecution 으로 모인다. 다른 것은 handler 인자뿐이다
```

```text
 진입 경로는 그보다 많다

 (1) 다른 액션이 execute 를 직접 부른다
   TransportSingleItemBulkWriteAction L49  단건 쓰기를 bulk 로 감싸 넘긴다
   TransportSubmitAsyncSearchAction   L101
   TransportEsqlAsyncStopAction       L108
   TaskManager 등록을 새로 하지 않고 호출한 쪽의 task 를 물려준다
   즉 한 액션의 doExecute 안에서 다른 액션의 필터 체인이 새로 돈다

 (2) 클라이언트가 NodeClient.doExecute 를 건너뛴다
   RestCancellableNodeClient 는 FilterClient 를 상속해
   doExecute 를 오버라이드하고 곧장 executeAndReturnTask 를 부른다 (L75-82)
   그래서 NodeClient L85 의 catch 가 아니라
   AbstractClient L161 의 catch 가 안전망이 된다
   executeAndReturnTask 를 직접 부르는 곳이 비테스트 7곳 있다

 (3) executeDirect 를 직접 등록한다
   HandledTransportAction 만 등록하는 것이 아니다
   자기 생성자에서 직접 등록하는 클래스가 비테스트 25곳 있다

 (4) 필터 체인을 아예 건너뛰는 길도 있다
   TransportSingleShardAction 은 핸들러를 둘 등록한다 (L99-107)
     TransportHandler      L330  executeDirect 를 부른다. 체인을 탄다
     ShardTransportHandler L341  asyncShardOperation 을 바로 부른다
                                 체인도 검증도 거치지 않는다
```

```text
 doExecute 에 닿지 않고 끝나는 길

 [02] L79-80  validate() 가 예외를 던졌다
 [02] L83-84  validate() 가 검증 오류를 돌려줬다
 [03] L138    proceed 가 필터 수보다 많이 불렸다
 [03] L142    필터나 doExecute 가 동기로 예외를 던졌다
 [04]         executor 가 큐를 거부했다. 호출한 스레드에서 끝난다
 [04]         포크한 스레드에서 doExecute 가 동기로 던졌다
 필터가 chain.proceed 를 안 부르고 리스너를 완료시켰다

 L77 의 assert 가 켜져 있으면 검증 예외는 L79 까지 못 간다
 AssertionError 로 위로 던져진다

 앞단에서 끊기는 것도 있다
 NodeClient L90     액션을 못 찾았거나 태스크 등록이 막혔다
 TaskManager L213   부모 태스크가 이미 취소됐다 (실제 발생은 L265)
 TaskManager L150   태스크 헤더가 최대 크기를 넘었다
```

## 어디에서 쓰이는가

```text
 [REST 디스패치] BaseRestHandler 의 action.accept 뒤가 이 흐름이다
 [구조: 노드 역할] 다른 노드에서 온 요청은 executeDirect 로 들어온다
 [보안] 인증과 인가가 필터 하나로 이 체인에 끼어든다
```

앞 흐름은 [REST 디스패치](../rest-dispatch/README.md)에 있다. `doExecute` 안쪽은 액션마다 달라 별도 흐름에서 다룬다.

## 단계

1. [TransportAction.execute](01_TransportAction.execute/README.md)가 포크 여부를 정한다.
2. [TransportAction.handleExecution](02_TransportAction.handleExecution/README.md)이 검증하고 체인을 만든다.
3. [RequestFilterChain.proceed](03_RequestFilterChain.proceed/README.md)가 필터를 태우고 실행으로 넘긴다.
4. [TransportAction.doExecuteForking](04_TransportAction.doExecuteForking/README.md)이 스레드를 갈아탄다.

## 결과가 쓰이는 곳

```text
 태스크
      --> _tasks API 가 보여 주는 것이 이것이다
      --> 취소도 이 태스크를 통해 전달된다
      --> getShouldStoreResult 인 요청은 결과가 인덱스에 저장된다

 요청 참조 수
      --> handleExecution 이 올리고 (L93)
      --> 체인 끝(L134)이나 리스너 완료(L96) 중 먼저 오는 쪽이 내린다
      --> 포크하면 제출 직후에 내려간다. doExecute 완료 시점이 아니다

 필터 체인
      --> 보안이 여기 끼어들어 인증과 인가를 한다
      --> 필터가 요청을 바꾸거나 응답을 가로챌 수 있다

 스레드
      --> executeDirect 는 이미 제 스레드 위다
      --> execute 는 executor 가 DIRECT 가 아니면 여기서 갈아탄다
```

## 다루지 않는 것

`doExecute` 구현들(액션마다 다르다), `TaskManager` 의 태스크 등록·취소·결과 저장 내부, `_tasks` API 와 태스크 취소 전파, `SecurityActionFilter` 안의 인증과 인가, 스레드풀 종류와 큐 정책, `ActionModule` 이 액션과 필터를 조립하는 기동 경로, 전송 계층의 직렬화와 노드 간 통신은 같은 뼈대의 곁가지라 요약만 했다.

## 하위 메서드

- [01 TransportAction.execute](01_TransportAction.execute/README.md)
- [02 TransportAction.handleExecution](02_TransportAction.handleExecution/README.md)
- [03 RequestFilterChain.proceed](03_RequestFilterChain.proceed/README.md)
- [04 TransportAction.doExecuteForking](04_TransportAction.doExecuteForking/README.md)
- [spi](spi/README.md) — 필터 계약, 체인 계약
