# cs/issue/gui-platform/coordinate-space-consistency — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **screenX = 소스 문서의 논리(CSS) px, bounds = (이 셸 API에서는) OS 물리 px.**\
   창 bounds의 단위는 셸·OS API마다 다르다 — 물리 px로 주는 API도, 논리 px로 주는 API도 있으니 문서로 확인한다.\
   논리 px는 각 모니터의 배율로 나눈 값이라, 모니터마다 원점과 배율이 다르다.\
   배율 1.0 모니터의 논리 좌표와 2.0 모니터의 논리 좌표는 같은 축 위에 놓이지 않는다 — 하나의 전역 좌표계가 아니다.\
   (Windows처럼 OS 전역 좌표가 물리 px인 플랫폼 기준. macOS는 OS 전역 좌표 자체가 point(논리) 단위라 사정이 다르다 — 어느 단위가 "전역"인지는 플랫폼이 정한다.)
   > **논리 px vs 물리 px** — 물리 px는 실제 화면 픽셀, 논리(CSS) px는 배율(DPI scale)로 나눈 값. scale 2.0이면 논리 1px = 물리 2px.

2. **다른 배율 모니터 위의 드롭 지점이 엉뚱한 곳으로 계산된다.**\
   소스 창의 scale은 소스 모니터에만 맞는다.\
   드롭 지점이 배율이 다른 모니터에 있으면 곱한 결과가 실제 물리 위치와 달라, 탭이 바탕화면이나 다른 창으로 라우팅됐다.

3. **"소스 scale" 가정을 그대로 두었기 때문이다. 최종은 물리 px 통일 + OS 전역 커서 위치.**\
   bounds를 나눠 논리로 비교해도 나눗셈에 쓰는 scale이 소스 기준이라 같은 오류가 남는다.\
   최종: 모든 hit-test를 물리 px 한 공간에서 하고(bounds의 `/scale` 제거), 드롭 시점에 OS가 주는 전역 커서 위치(물리)를 질의한다.\
   `screenX × scale`은 그 질의가 실패했을 때만 쓰는 fallback이다.

4. **창 생성 API가 논리 좌표를 받기 때문이다.**\
   판정(어느 창 위인가)은 전역에서 일관된 물리 px로, 새 창 *배치*는 그 API의 단위(논리)에 맞춰 `물리 ÷ scale`로 환산한다.\
   원칙: 내부 계산은 한 공간, 변환은 외부 API 경계에서 한 번.\
   경계 부근의 배치 오차는 겉보기 문제로만 남는다.

5. **winding·법선·UV·가시영역·라벨 투영 전부.**\
   x 부호가 뒤집히면 삼각형 정점 순서(winding)가 뒤집혀 법선이 구 안쪽을 향하고, 앞면만 그리면(FrontSide) 정면이 안 보인다.\
   가시영역 계산 `atan2(camDir.z, -camDir.x)`도 같은 반전을 전제해 반대편 타일을 로드했다.\
   양면 렌더(DoubleSide)에선 우연히 작동해 문제가 가려져 있었다.

6. **각 지점이 반전을 따로 "보상"하고 있어서, 한 곳을 바로잡으면 그 보상에 기대던 다른 곳이 깨진다.**\
   winding 반전·UV 반전·x 부호 제거·내부 차폐구·BackSide 다섯 가지 모두 실패했다 — 부호 제거는 연동된 계산을 무너뜨렸다.\
   같은 결함을 여러 번 부분 수정해도 계속 깨지면 토대가 틀린 것이다.\
   채택한 수: 타일 시스템을 제거하고 표준 구면 기하 + 단일 고해상도 텍스처로 구조를 교체했다(줌 해상도 한계는 미해결로 수용).

## 문제 구조 (추상화 코드)

### 변형 A — 논리 px와 물리 px 혼용
① 문제 코드
```ts
onDragEnd(e) {
  const p = { x: e.screenX * sourceScale, y: e.screenY * sourceScale }; // 소스 모니터 기준
  const target = pickWindow(windowBounds(), p);   // bounds는 물리 px
  route(target, p);
}
```
② 고친 코드
```ts
async onDragEnd(e) {
  try {
    const p = await os.cursorPosition();                 // OS 전역 물리 좌표
    if (Number.isFinite(p.x) && Number.isFinite(p.y)) return dropAt(p);
  } catch { /* fallback */ }
  return dropAt({ x: e.screenX * sourceScale, y: e.screenY * sourceScale });
}
function dropAt(pPhys) {
  const target = pickWindow(windowBoundsPhysical(), pPhys);  // 판정은 물리 한 공간
  if (!target) createWindowAt(toLogical(pPhys, sourceScale)); // 배치만 논리로 환산(소스 scale — 경계 부근 오차 잔존)
  // ...
}
```
깨진 것: 모니터마다 다른 논리 좌표를 전역 좌표처럼 써서 경계를 넘는 드롭이 엉뚱한 곳으로 갔다.

### 변형 B — 좌표 부호 반전이 곳곳의 보상과 얽힘
① 문제 코드
```ts
function tileVertex(r, phi, theta) {
  return { x: -r * sin(phi) * cos(theta), y: r * cos(phi), z: r * sin(phi) * sin(theta) };
}
const visibleLon = atan2(camDir.z, -camDir.x);   // 반전을 따로 보상
material.side = DoubleSide;                       // 뒤집힌 법선을 가림
```
② 고친 코드
```ts
// 부분 보정 대신 토대 교체: 표준 구면 + 단일 텍스처
const globe = new Mesh(new SphereGeometry(r /* ... */), new Material({ map: fullTexture }));
// 타일 가시영역 계산 제거
```
깨진 것: 한 좌표 규약의 부호 반전을 여러 지점이 각자 보상해, 어느 한 곳의 수정도 다른 곳을 깼다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
