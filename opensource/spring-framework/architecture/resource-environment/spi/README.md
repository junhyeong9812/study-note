# spi

상위: [Spring 리소스와 환경](../README.md)

프레임워크 전반이 기대는 두 기초 추상화의 인터페이스다. 무엇을 읽을지(Resource, ResourceLoader)와 어떤 설정값을 쓸지(Environment, PropertySource)를 각각 맡는다.

```text
 getResource ........... ResourceLoader (+ ProtocolResolver)
   결과 ................ Resource
 getResources .......... ResourcePatternResolver
 getProperty ........... Environment (PropertyResolver)
   값의 출처 ........... PropertySource 목록 (앞이 우선)
```

## 하위 인터페이스

- [Resource](Resource/README.md)
- [ResourceLoader](ResourceLoader/README.md)
- [Environment](Environment/README.md)
- [PropertySource](PropertySource/README.md)
