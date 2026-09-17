# spi

상위: [Spring 컨테이너 기동](../README.md)

컨테이너 기동 중간에 사용자 코드가 끼어드는 자리의 인터페이스다. 어느 인터페이스가 `refresh()`의 몇 번째 단계에서 불리는지 알면, 확장 코드가 "왜 이 시점에 이 상태인지"를 설명할 수 있다.

```text
 refresh
   [04] invokeBeanFactoryPostProcessors ... BeanFactoryPostProcessor (정의 단계)
          ConfigurationClassParser ........ ImportSelector / ImportBeanDefinitionRegistrar
   [05] registerBeanPostProcessors ........ BeanPostProcessor (등록만, 호출은 빈 생성 때)
   [08] registerListeners ................. ApplicationListener
   [09] preInstantiateSingletons .......... SmartInitializingSingleton (싱글톤 전부 생성 후)
   [10] finishRefresh ..................... SmartLifecycle (phase 순서로 start)
```

## 하위 인터페이스

- [BeanFactoryPostProcessor](BeanFactoryPostProcessor/README.md)
- [BeanPostProcessor](BeanPostProcessor/README.md)
- [ImportSelector](ImportSelector/README.md)
- [ApplicationListener](ApplicationListener/README.md)
- [SmartInitializingSingleton](SmartInitializingSingleton/README.md)
- [SmartLifecycle](SmartLifecycle/README.md)
