# cs/issue/typescript/browser/input-event-model — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
[환경 계층]  OS 입력기 데몬 ── GTK_IM_MODULE ──▶ 웹뷰      불일치 → 조합 자체가 안 됨
                                                        (방안 1: 시작 시 실제 데몬 감지·env 정합)
[이벤트 계층]
  IME 조합   compositionstart ─ input(매 키) ─ ... ─ compositionend(data)
                                   │                       │
                   조합 중 value 덮어쓰기 = preedit 파괴      라이브러리 onData 도 같은 텍스트 → 중복
                   → 조합 끝에서만 절삭·동기화              → 조합 텍스트는 compositionend 1회, onData 비ASCII 폐기

  키 전파    target ─▶ (라이브러리 핸들러: return false = 라이브러리 기본 처리만 막음)
                   ─▶ 버블 ─▶ 상위 컨테이너 keydown   → 같은 키 2회 실행
                   → preventDefault(기본 동작) + stopPropagation(전파) 둘 다, modifier 가드

  포커스      소유자 1명 원칙: 자식 자동 포커스 금지 · 닫을 때 명시 이양 · 새 DOM은 rAF 뒤 focus

  DnD        dragstart ─ dragover(preventDefault 필수) ─ drop
                    └─ Esc·창 밖·다른 타깃 소비 → drop 없이 종료
                    dragleave 는 자식 경계마다 튐 (relatedTarget null 인 엔진도)
             (방안 2: window capture dragend/drop 백스톱 + 지연 클리어 + drop 좌표 재계산)
```

## 핵심 문장

- IME 조합 텍스트는 **여러 경로**(compositionend·input·라이브러리 데이터 이벤트)로 올 수 있다 — 한 경로만 소비한다.
- 조합 중에 value를 프로그램으로 덮으면 조합 버퍼가 깨진다 — 절삭·동기화는 **compositionend**에서.
- 라이브러리의 "처리됨" 반환은 DOM 전파와 **별개**다. `preventDefault`는 기본 동작만, `stopPropagation`은 전파만 막는다.
- `e.key`만 보면 modifier 조합도 같은 키다 — 단축키에는 modifier 가드.
- 키보드 탐색은 **포커스 소유권 하나**에 의존한다 — 빼앗기거나 사라지면 탐색이 끊긴다.
- DnD는 drop 없이 끝날 수 있다 — 로컬 이벤트가 아니라 **창 단위 백스톱**으로 정리한다.
- 추측이 반복 실패하면 이벤트 흐름을 **계측**한다.
