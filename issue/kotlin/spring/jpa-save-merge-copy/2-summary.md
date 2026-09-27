# issue/kotlin/spring/jpa-save-merge-copy — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

**한 문장:** `save()`는 "새 것이면 persist, 아니면 merge"다. 이미 영속 상태인 루트에 `save()`를 부르면 merge가 실행되고, merge는 cascade로 딸린 **새 자식의 복사본**을 영속화한다 — 내가 들고 있는 원본 자식은 영속화되지 않아 id가 비어 있다.

```
@Transactional
  root = repo.find(id)                 ← 영속 상태 (영속성 컨텍스트가 관리)
  child = root.addChild(...)           ← 새 객체, 아직 비영속
  repo.saveAndFlush(root)
     │ isNew(root)?  id 있음 → 아니오
     ▼
  em.merge(root)                       ← persist가 아니라 merge
     │ root는 이미 관리 중 → 그대로
     │ cascade MERGE → child는 비영속 → "복사본 child'"를 만들어 영속화
     ▼
  flush: INSERT child'  (id = 101 발급)
  return child.id!!                    ← 원본 child.id == null → NPE

고친 흐름:
  repo.flush()                         ← save 없이 flush만
     │ 변경 감지 + cascade PERSIST: 관리 중인 root의 새 자식 = 원본 child를 persist
     ▼
  INSERT child (id = 101) → child.id == 101
```

핵심은 **merge의 복사 의미론**이다. `persist(x)`는 "x 자체를 관리 대상으로 만든다", `merge(x)`는 "x의 상태를 관리 중인 인스턴스에 복사하고 **그 인스턴스를 돌려준다**"다. 새 객체에 merge가 닿으면 관리 인스턴스를 새로 만들어 복사하므로, 원본은 끝까지 관리 밖에 남는다.

두 번째 요점은 **영속 상태 엔티티에는 `save()`가 필요 없다**는 것이다. 트랜잭션 안에서 불러온 루트는 이미 관리 중이라, 커밋(또는 flush) 때 변경 감지가 UPDATE를 만들고 cascade PERSIST가 새 자식을 INSERT한다. `save()`는 비영속 객체를 처음 넣을 때의 도구다.

## 핵심 문장

- `save()` = isNew면 persist, 아니면 merge. "저장"이라는 이름이 이 분기를 감춘다(누출 추상화).
- persist는 **그 객체**를 관리한다. merge는 **복사본**을 관리하고 그것을 반환한다.
- 영속 루트에 save → merge → 새 자식은 복사본이 INSERT되고 원본 참조는 id가 빈다.
- 이미 관리 중인 애그리거트는 save 없이 flush(또는 커밋)만 — 변경 감지 + cascade PERSIST가 원본을 영속화한다.
- save를 꼭 부르면 **반환값**을 써라. 인자로 넘긴 객체가 영속 인스턴스라는 보장은 없다.
