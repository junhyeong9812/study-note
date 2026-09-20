# spi

상위: [설정 DSL](../README.md)

설정 DSL 이 기대는 계약 둘이다. 하나는 무언가를 만들고, 하나는 그 만드는 과정에 끼어든다.

```text
 만드는 쪽
   SecurityBuilder<O>    build() 하나. O 를 만들어 돌려준다
                         HttpSecurity 는 SecurityFilterChain 을 만든다

 끼어드는 쪽
   SecurityConfigurer    init 과 configure 두 단계로 빌더에 개입한다
                         DSL 한 줄이 설정자 하나에 대응한다
```

- [SecurityBuilder](SecurityBuilder/README.md)
- [SecurityConfigurer](SecurityConfigurer/README.md)
