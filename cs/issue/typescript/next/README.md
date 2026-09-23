# next — Next.js(BFF·라우팅·모듈 해석) 패턴

Next.js를 **BFF(유일한 외부 노출 지점) + SSR 위키**로 쓰며 겪은, 프레임워크 경계에서 터진 패턴.

| 패턴 | 한 줄 | 사례 이슈 |
|------|-------|-----------|
| [bff-envelope-single-gate](bff-envelope-single-gate/) | 봉투(`{success,data\|error}`) 검사를 페이지마다 하면 잊어 오류를 정상 데이터로 렌더 → BFF 단일창구에서 정규화(검증 DRY). 가장 위험한 가정 먼저 실증 | front1 |
| [absolute-imports-and-per-tool-resolver](absolute-imports-and-per-tool-resolver/) | 상대·절대 임포트 혼용 → 파일이동에 깨짐(절대경로 정책). alias는 `tsconfig`만으론 부족 — vitest는 자기 리졸버라 못 찾음(도구마다 별도) | front6 · front7 |
| [single-source-of-truth-routing](single-source-of-truth-routing/) | 노드 종류를 URL·백엔드 두 곳에서 관리하면 어긋남 → `is_subject` 단일 소스, 캐치올 라우팅. 상대링크는 렌더 시점에 해석 | front2 |
