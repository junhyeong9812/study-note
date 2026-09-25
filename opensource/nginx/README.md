# Nginx - 동작 구조 분석

이 폴더는 Nginx(C)의 동작 구조를 소스 기준으로 정리하는 자리다. 마스터-워커 프로세스와 워커별 이벤트 루프로 많은 연결을 적은 스레드로 처리하는 구조, 요청을 phase 단위로 나눠 모듈에 넘기는 구조를 볼 수 있다. 리버스 프록시·로드밸런서가 시스템 앞단에서 하는 일의 기준점이 된다.

전체 도구 목록과 진행 순서는 [도구 동작 구조 분석 로드맵](../../docs/tool-analysis-roadmap.md)에 있다.

## 읽는 기준

공식 문서는 지도로 쓰고, 주장은 소스로 확인한다. 공식 문서의 설명을 그대로 옮기지 않고, 흐름을 고르는 출발점과 용어의 기준으로 삼는다.

- 소스: [nginx/nginx](https://github.com/nginx/nginx) - 기준 커밋은 [아키텍처 지도](architecture/README.md)에 적는다
- 공식 문서: [nginx Development guide](https://nginx.org/en/docs/dev/development_guide.html)

## 개념 교차표에서 맡는 칸

로드맵의 개념 교차표 가운데 이 도구가 채우는 축이다.

- 요청 처리 모델: 마스터-워커 프로세스 + 워커별 이벤트 루프(epoll)
- 프록시: upstream 연결과 로드밸런싱
- 설정: 시그널로 무중단 리로드
