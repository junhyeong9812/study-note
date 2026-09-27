# gui-platform — 좌표계·웹뷰 엔진

데스크톱 GUI·웹뷰 위에서 나오는 플랫폼 패턴이다.\
공통 원리: **브라우저가 보장하던 동작과 좌표계는 대상 플랫폼에서 다시 확인해야 한다** — 한 가지 기준(좌표계·엔진)으로 통일하고 실기에서 검증한다.

## 공통 원리

```
  UI 코드 ──▶ 웹뷰 엔진 (OS마다 다름) ──▶ 네이티브 창
    │              │
    │              └─ DnD·PDF·z-order: 크롬에선 됐지만 여기선?
    └─ 논리 px ↔ 물리 px ↔ 축 부호 혼용
                   ▼
       한 지점 보정이 다른 지점의 보상과 충돌
```

## 패턴 카드

- [coordinate-space-consistency](coordinate-space-consistency/) — 좌표계(논리 px vs 물리 px, 좌표축 부호)를 섞으면 한 지점 보정이 다른 지점의 보상 오류와 충돌한다 — 하나의 좌표계로 통일한 뒤 변환한다.
- [webview-engine-platform-gaps](webview-engine-platform-gaps/) — 데스크톱 웹뷰 엔진·OS는 크롬이 보장하던 동작(DnD·PDF 뷰어·z-order API·문서 간 드래그)을 보장하지 않는다 — 대상 엔진에서 실측한다.
