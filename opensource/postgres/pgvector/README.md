# pgvector - 동작 구조 분석

상위: [PostgreSQL](../README.md)

이 폴더는 pgvector(C)의 동작 구조를 소스 기준으로 정리하는 자리다. PostgreSQL 확장으로 벡터 타입과 거리 연산자, 근사 최근접 검색 인덱스(HNSW, IVFFlat)를 더한다. PostgreSQL의 인덱스 접근 메서드(Index AM) 인터페이스에 새 인덱스가 어떻게 끼워지는지를 보여준다.

## 읽는 기준

- 소스: [pgvector/pgvector](https://github.com/pgvector/pgvector) - 기준 커밋은 [아키텍처 지도](architecture/README.md)에 적는다
- 공식 문서: [pgvector README](https://github.com/pgvector/pgvector#readme)
- PostgreSQL 쪽 인덱스 접근 메서드 흐름과 짝지어 읽는다

## 개념 교차표에서 맡는 칸

- 색인: 벡터 색인(HNSW 그래프, IVFFlat 클러스터)
- 확장 구조: 타입·연산자·인덱스 접근 메서드 등록
