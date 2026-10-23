# issue/cross-cutting/database/catalog-presence-vs-enabled — 정리 (힌트)

## 전체 흐름

```text
[운영자]  ALTER TABLE counter DISABLE TRIGGER touch      → pg_trigger 행은 그대로 · tgenabled = 'D'

[기동 검사 — 문제]
  SELECT count(*) FROM pg_trigger … WHERE tgname = 'touch'   → 1
  "있다" ⇒ 통과 ─────────────────────────────▶ 증분 대조 켜짐
                                                │
  UPDATE counter …  ── 트리거 발화 안 함 ── updated_at 그대로
                                                ▼
  증분 대조: "최근 바뀐 행" 창에 그 행이 안 보임 → 어긋남을 놓침 (오류 없음 — 유실)

[기동 검사 — 교정]
  SELECT tgenabled FROM pg_trigger … WHERE tgname = 'touch'  → ['D']
  있어야 하는 방향:  any(O, A) 아니면 거부 + "ENABLE TRIGGER 로 켜거나 방식을 바꿔라"
  없어야 하는 방향:  행이 있으면 거부 (꺼져 있어도 "있음" — 다시 켜지면 비용이 샌다)

tgenabled:  O = 보통 세션에서 발화 (session_replication_role = origin/local)
            A = 항상 발화
            R = 복제 세션에서만 발화
            D = 꺼짐
```

## 핵심 문장

- 카탈로그 행은 **존재**를 말할 뿐 **효력**을 말하지 않는다 — 트리거는 꺼진 채로 카탈로그에 남는다.
- "있어야 한다" 검사는 **효력**(업무 세션에서 실제로 발화하는 상태 `O`·`A`)으로 판정한다 — `D`만 빼면 `R`(복제 세션 전용)이 통과한다.
- "없어야 한다" 검사는 반대로 **존재**로 판정하는 것이 보수적이다 — 꺼진 것도 언젠가 켜질 수 있다.
- 대상 범위(스키마·테이블)를 좁히는 것과 상태(활성)를 확인하는 것은 별개의 축이다 — 둘 다 해야 한다.
- 이 오판은 오류가 아니라 **유실**로 나타난다 — 검사가 통과시키면 아무도 다시 보지 않는다.
- 거부 메시지에는 관측한 상태와 고치는 문장(`ENABLE TRIGGER …`)을 함께 넣는다.
