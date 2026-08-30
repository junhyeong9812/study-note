# issue7 — /api/deploy 중계 + 절대경로 임포트 정책

- 이슈 #12·#14·#15 · PR: #13(중계)·#14(임포트 정책)·#16(Actions)

## 1. /api/deploy 중계 — sync와 완전 동형

배포 요청도 외부(Actions)에서 집 안(ci-cd master)으로 들어와야 하므로 front가 중계한다.
sync 중계에서 확립한 원칙 그대로:

```ts
// features/deploy/lib/relay.ts — 비밀은 저장·검증하지 않고 소유자(master)에게 전달만
const response = await fetch(`${MASTER_URL}/deploy`, {
  headers: { "X-Deploy-Secret": secret, "X-Request-Id": requestId },
  body, signal: AbortSignal.timeout(10_000),
});
```
+ 4KB 본문 상한(413)·requestId 전파·app 라우트는 위임만. **패턴이 두 번째라 리뷰
지적 없이 처음부터 맞게 나왔다** — 첫 구현(sync)에서 리뷰로 배운 게 재사용된 사례.

## 2. 절대경로 임포트 정책 (사용자 확정)

**배경**: features 재편 때 상대 임포트만 3회에 걸쳐 빌드를 깨뜨렸다(issue6). 근본 원인은
개별 실수가 아니라 **정책 부재** — 상대/절대가 섞여 있으면 파일 이동이 임포트를 깨뜨린다.

**결정**: `@/...` 절대경로만 사용. 같은 폴더 안이라도 상대 임포트 금지.

**적용**: 잔존 상대 임포트 7건 전수 제거 + README 정책 명문화. 그리고 함정 하나 —

**상황**: 테스트 파일의 임포트를 `@/`로 바꾸자 vitest만 깨짐.
```
Test Files 2 failed — Cannot find module '@/features/wiki/lib/tree'
```
**원인**: `@` alias는 tsconfig(paths)에 있지만 그건 **Next와 타입체커의 설정**이다.
vitest는 자기 리졸버(vite)를 쓰므로 별도로 알려줘야 한다.
**결론**: `vitest.config.ts`에 `resolve.alias { "@": ./src }` 추가. **원칙**: alias는
"프로젝트 설정"이 아니라 **도구마다의 설정**이다 — 빌드·타입체크·테스트 러너가 각자
리졸버를 가진다.

## 3. 결론

배포 요청 경로 완성(무인증 401 관통 확인) + 임포트 정책 고정. PR: #13·#14·#16
