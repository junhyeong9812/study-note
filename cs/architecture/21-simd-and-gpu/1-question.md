# architecture/21-simd-and-gpu — 질문

## 질문

1. (그림) AVX2의 `ymm` 레지스터 하나에 `int`·`float`·`double`이 각각 몇 개 들어가나? `vpaddd ymm0, ymm1, ymm2`가 하는 일을 레인 그림으로 그려라.
2. (경계) 컴파일러가 자동 벡터화하기 쉬운 루프와 어려운 루프의 조건을 각각 셋 이상 대라. GCC 13.3에서 `-O2`와 `-O3`의 벡터화는 무엇이 다른가?
3. (예측) L1에 들어가는 int 배열 덧셈과 64MiB int 배열 덧셈을 `-O2 -fno-tree-vectorize`에서 `-O3 -march=native`로 바꾸면 각각 몇 배쯤 빨라질까? 왜 다른가? (`simd.c`)
4. (예측) `float` 합 루프는 `-O3 -march=native`에서 빨라질까? `-ffast-math`를 더하면? 결과 값은 어떻게 되나? `objdump`에서 무엇을 보면 구분되나?
5. (예측) Java 21에서 `-XX:-UseSuperWord`로 끄면 `int[]` 덧셈, `int` 합, `float` 합은 각각 어떻게 될까? `float` 합만 다른 이유를 JLS로 설명하라. (`SimdJava.java`)
6. (그림) `if (x > 0) A else B`를 8칸 SIMD로 처리하는 과정을 마스크로 그려라. 비용은 데이터에 따라 어떻게 되나?
7. (예측) 양쪽 갈래가 모두 무거운 분기를 입력 "전부 양수"와 "부호 무작위"로 돌리면 스칼라 판과 벡터 판의 시간은 각각 어떻게 변할까? (`diverge.c`)
8. (연결) CUDA의 워프와 warp divergence를 CPU SIMD의 마스크와 연결해 설명하라. GPU 전역 메모리 coalescing이 깨지면 메모리 사용 효율이 최악 몇 %까지 떨어지나?
9. (장애 진단) `-march=native`로 빌드한 바이너리가 일부 서버에서 `Illegal instruction`으로 죽는다. 원인과 대처는?
10. (장애 진단) 분기가 많은 규칙 엔진을 GPU로 옮겼더니 기대보다 느리다. 원인과 코드·데이터 쪽 대처는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
