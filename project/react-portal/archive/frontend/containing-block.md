# Containing Block & Overflow Clipping

> **한 줄**: 요소의 위치(`top/left`)와 % 크기는 **containing block**(기준 상자)으로 계산된다. `overflow: hidden`은 그 기준 상자 체인 안의 자손을 자른다. `position: fixed`는 보통 뷰포트 기준이라 안 잘리지만, **조상에 `transform`이 있으면** 그 조상 기준이 되어 갇힌다.

## containing block은 position마다 다르다

| position | containing block (기준 상자) |
|---|---|
| `static`, `relative` | 가장 가까운 블록 조상의 콘텐츠 영역 |
| `absolute` | 가장 가까운 **위치 지정된**(`static`이 아닌) 조상의 패딩 영역. 없으면 초기 containing block |
| `fixed` | **뷰포트**. 단, 아래 속성을 가진 조상이 있으면 그 조상 |
| `sticky` | 가장 가까운 스크롤 조상 |

### fixed의 기준을 바꾸는 조상 속성
- `transform`, `perspective`, `filter`가 `none`이 아님
- `contain: layout | paint`, `container-type`(일부 브라우저·시점)
- `will-change: transform` 등

## overflow 클리핑과의 관계

`overflow: hidden`은 자기 영역 밖으로 **자손을 그리지 못하게** 자른다. 단, 자손의 containing block 체인이 그 요소를 **거쳐야** 잘린다.

```
.card { overflow: hidden; position: relative; }

  absolute 자식 → 기준 = .card (position 있음)  → 잘림
  fixed 자식    → 기준 = 뷰포트 (.card 밖)       → 안 잘림 ✓

.card { overflow: hidden; position: relative; transform: translateZ(0); }

  fixed 자식    → 기준 = .card (transform 때문)  → 잘림 ✗
```

containing block, 클리핑, stacking context는 **서로 다른 효과**다. transform은 이 셋 모두에 영향을 준다. → [stacking-context.md](stacking-context.md)

## 이 프로젝트에서 (실제로 겪은 것)

- 처음 데모는 카드에 `overflow: hidden`만 있었다. 그런데 모달 오버레이가 `position: fixed`라서 **잘리지 않았다** — "카드에 갇힌다"는 데모가 성립하지 않음.
- 카드에 `transform: translateZ(0)`을 추가(`demo/style.css`) → fixed 오버레이의 기준이 카드가 되어 잘림 → 실무 함정 재현.
- Portal은 DOM을 body로 옮기므로 이 조상 체인 자체에서 벗어난다.

## 흔한 함정

- **"fixed니까 화면 기준이겠지"**: 조상 어딘가의 `transform`(애니메이션, GPU 가속 핵 `translateZ(0)`) 하나로 깨진다.
- **absolute 드롭다운이 스크롤 영역에 잘림**: 기준 상자가 `overflow: auto` 컨테이너 안이라서. 해결은 portal + 좌표 계산.
- **% 크기가 이상함**: 기준 상자가 생각한 조상이 아니다. position이 있는 조상을 확인.
- **React에서는 왜 몰랐나**: UI 라이브러리의 모달·툴팁·드롭다운이 이미 portal로 구현돼 있어서 이 문제를 대신 피해 주고 있었다.
