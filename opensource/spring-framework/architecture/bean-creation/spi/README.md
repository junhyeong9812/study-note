# spi

상위: [Spring 빈 생성](../README.md)

빈 하나가 만들어지는 동안 사용자 코드와 프레임워크가 끼어드는 자리의 인터페이스다. `BeanPostProcessor` 자체는 [컨테이너 기동](../../container-refresh/spi/BeanPostProcessor/README.md)에 정리했고, 여기에는 빈 생성 단계에서 직접 쓰이는 것들을 모았다.

```text
 doGetBean
   +-- 스코프 분기 ................ Scope
   +-- createBean
   |     +-- resolveBeforeInstantiation ... InstantiationAwareBeanPostProcessor
   |     +-- doCreateBean
   |           +-- createBeanInstance ..... (Smart)InstantiationAware  생성자 선택
   |           +-- 정의 후처리 ............ MergedBeanDefinitionPostProcessor
   |           +-- populateBean ........... InstantiationAware  주입
   |           +-- initializeBean ......... Aware, InitializingBean, BeanPostProcessor
   |           +-- 소멸 등록 .............. DisposableBean, Scope
   +-- getObjectForBeanInstance ... FactoryBean
```

## 하위 인터페이스

- [FactoryBean](FactoryBean/README.md)
- [InstantiationAwareBeanPostProcessor](InstantiationAwareBeanPostProcessor/README.md)
- [MergedBeanDefinitionPostProcessor](MergedBeanDefinitionPostProcessor/README.md)
- [Aware](Aware/README.md)
- [InitializingBean](InitializingBean/README.md)
- [Scope](Scope/README.md)
