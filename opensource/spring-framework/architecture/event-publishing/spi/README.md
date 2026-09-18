# spi

상위: [Spring 이벤트 발행](../README.md)

이벤트가 오가는 네 자리의 인터페이스다. 발행하는 쪽, 받는 쪽, 둘 사이에서 나눠 주는 쪽, 그리고 애노테이션 메서드를 리스너로 바꿔 주는 공장이다.

```text
 publishEvent .......... ApplicationEventPublisher   (= ApplicationContext)
   multicastEvent ...... ApplicationEventMulticaster
     선별 .............. ApplicationListener 의 타입 판정
     호출 .............. ApplicationListener.onApplicationEvent
                           @EventListener 는 EventListenerFactory 가 만든 어댑터
```

## 하위 인터페이스

- [ApplicationEventPublisher](ApplicationEventPublisher/README.md)
- [ApplicationListener](ApplicationListener/README.md)
- [ApplicationEventMulticaster](ApplicationEventMulticaster/README.md)
- [EventListenerFactory](EventListenerFactory/README.md)
