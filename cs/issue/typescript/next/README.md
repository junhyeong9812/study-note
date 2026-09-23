# typescript/next — BFF·라우팅·모듈 해석

Next.js의 BFF·라우팅·SSR·모듈 해석에서 나오는 패턴이다.\
공통 원리: **같은 사실·같은 검증을 한 곳에서만 만든다** — 소비처마다 흩어진 판정은 반드시 어긋난다.

## 공통 원리

```
  백엔드 응답 ──▶ BFF (단일 창구: 봉투 검증·형태 변환)
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
        페이지 A   페이지 B   페이지 C   ← 각자 검사하면 누락이 생긴다
```

## 패턴 카드

- [absolute-imports-and-per-tool-resolver](absolute-imports-and-per-tool-resolver/) — 상대 경로·모듈 해석은 파일 위치·도구(번들러·테스트 러너·로더)마다 기준이 달라 이동·도구 교체에 깨진다 — 절대 경로 정책과 도구별 리졸버 설정을 맞춘다.
- [bff-envelope-single-gate](bff-envelope-single-gate/) — 응답 봉투·래핑 검사를 소비처마다 하면 누락돼 오류가 정상 데이터(빈 배열)로 렌더된다 — 형태 변환·검증 책임을 한 계층(BFF)으로 모은다.
- [single-source-of-truth-routing](single-source-of-truth-routing/) — 같은 사실(판정식·파이프라인·상태·변환 코드)을 두 곳에서 따로 관리·계산하면 반드시 어긋난다 — 단일 출처에서 파생시킨다.
- [ssr-hydration-parity](ssr-hydration-parity/) — 하이드레이션 첫 렌더는 서버 HTML과 같아야 한다 — 브라우저 전용 값·HTML 파서가 재구성하는 중첩 위반은 불일치를 만든다.

> 이 폴더의 메타 태그: `silent-failure`(1) · `single-source-of-truth`(1) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../../README.md#태그-역인덱스).
