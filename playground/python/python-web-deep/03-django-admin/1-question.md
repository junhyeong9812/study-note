# python/python-web-deep/03 — Django Admin 커스터마이징 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 재고 부족 필터 흉내의 출력 (예측)

```python
# 질문용 발췌
products = [
    Product("Python 기초", 25000, 50, "도서"),
    Product("Django 마스터", 35000, 3, "도서"),
    Product("USB 키보드", 15000, 0, "전자기기"),
    Product("모니터 암", 45000, 15, "전자기기"),
]
print("\n필터: 재고 부족")
low_stock = [p for p in products if 0 < p.stock < 10]
for p in low_stock:
    print(f"  {p.name}: {p.stock}개")
```

- 「필터: 재고 부족」 아래에 몇 줄이, 어떤 내용으로 찍히나?

### 2. 품절 상품 액션 흉내 (예측)

```python
# 질문용 발췌 (products 는 1번과 같다)
print("\n액션: 품절 상품 비활성화")
out_of_stock = [p for p in products if p.stock == 0]
print(f"  {len(out_of_stock)}개 상품 비활성화됨")
```

- 무엇이 찍히나?
- 이 코드를 돌린 뒤 「USB 키보드」 객체의 `stock` 값은 무엇인가?

### 3. 주문 다섯 개를 골라 취소 액션을 돌리면 (예측)

```python
# 질문용 발췌
@admin.action(description='선택된 주문을 취소')
def mark_as_cancelled(self, request, queryset):
    updated = queryset.filter(status='pending').update(status='cancelled')
    self.message_user(request, f'{updated}개 주문이 취소됨')
```

- 고른 다섯 주문 중 `pending` 이 둘, `shipped` 가 셋이면 화면에 뜨는 메시지는 무엇인가?

### 4. 계산 컬럼에 `ordering='stock'` 을 주는 까닭 (왜)

- `@admin.display` 에 `ordering` 을 따로 적어야 하는 까닭은 무엇인가?

### 5. 시뮬레이션 표의 머리글 줄이 데이터 줄과 어긋나 보이는 까닭 (왜)

- `f"{'이름':<16}"` 처럼 폭을 맞췄는데도 줄이 어긋나 보이는 까닭은 무엇인가?

### 6. 필드 이름 문자열 `list_filter` 의 한계 (경계)

- `list_filter = ['category', 'is_available']` 만으로 만들 수 없는 필터는 어떤 것이고, 그때 무엇을 쓰나?

### 7. 액션이 할 수 있는 일의 범위 (경계)

- 액션은 선택된 행을 DB 에서 고치는 일만 하나, 원본의 `export_csv` 는 무엇을 돌려주나?

### 8. 상세 페이지에서 고칠 수 없는 필드 (경계)

- `CustomerAdmin` 의 상세 페이지에서 `created_at` 을 고칠 수 있나, 그리고 「메타」 구역은 어떻게 보이나?

### 9. 인라인이 화면에 옮긴 것 (연결)

- `OrderAdmin.inlines` 의 `OrderItemInline` 은 주문과 품목 사이의 어떤 관계를 한 화면에 모은 것인가?

### 10. 시뮬레이션 비교식과 Django 조회식의 대응 (연결)

- 시뮬레이션의 `0 < p.stock < 10` 은 `StockRangeFilter` 의 어느 분기 · 어떤 조회식과 맞물리나?

## 실습

### 실습 1. Django Admin 커스터마이징 패턴 정리 스크립트

**만들 것** — Django Admin 커스터마이징 코드 여섯 가지를 문자열로 찍어 보여 주고, 마지막에 상품 목록 · 필터 · 액션을 순수 파이썬으로 흉내 내는 스크립트.

**준비물** — Django 설치는 필요 없다. 섹션 1~6 은 Django 코드를 문자열로 출력만 하고, 섹션 7 은 Django 를 흉내 낸 순수 파이썬이다.

**요구 조건**

1단계 — 코드 패턴 출력(섹션 1~6). 섹션마다 `=== N. … ===` 제목 줄을 찍은 뒤 삼중 따옴표 문자열로 Django 코드를 찍는다.

1. 섹션 1: `admin.site.register(Product)` 방식과 `@admin.register(Product)` 데코레이터 방식(몸통 `pass`)을 함께 보인다.
2. 섹션 2: `ProductAdmin` 에 `list_display` · `list_filter` · `search_fields`(`category__name` 포함) · `ordering`(내림차순) · `list_editable` · `list_per_page` · `date_hierarchy` 를 적고, `@admin.display(description=..., ordering='stock')` 로 재고 상태 계산 컬럼 `stock_status` 를 만든다.
3. 섹션 3: `OrderAdmin` 에 액션 세 개 — 전부 배송 처리(`update` 결과 수를 `message_user` 로 알림), `pending` 만 골라 취소, CSV 응답을 만들어 돌려주는 내보내기 — 를 `@admin.action` 으로 만든다.
4. 섹션 4: `TabularInline` 품목 인라인(`extra` · `min_num` · `max_num` · `readonly_fields` · `autocomplete_fields`)과 `StackedInline` 메모 인라인을 `OrderAdmin.inlines` 에 넣고, `short_description` 속성으로 머리글을 단 `item_count` 컬럼을 보인다.
5. 섹션 5: `CustomerAdmin` 에 구역 셋(기본 정보 · 주소 · 메타)의 `fieldsets` 를 적고 뒤 두 구역은 접을 수 있게 하며, `readonly_fields` · `autocomplete_fields` 를 둔다.
6. 섹션 6: `SimpleListFilter` 를 상속한 `StockRangeFilter`(품절 · 부족 · 충분 세 선택지, 고른 값마다 다른 조회식, 아무것도 안 골랐으면 그대로 돌려줌)를 만들어 `list_filter` 에 필드 이름과 함께 넣는다.

2단계 — 시뮬레이션 모델(섹션 7).

7. `Product` 클래스는 이름 · 가격 · 재고 · 분류를 받아 저장한다.
8. `stock_status()` 는 재고 0 이면 `'품절'`, 10 미만이면 `'부족 (재고)'`, 그 밖이면 `'충분 (재고)'` 을 돌려준다.

3단계 — 목록 · 필터 · 액션 흉내.

9. 상품 네 개를 표로 찍는다. 각 행에 이름 · 가격(천 단위 쉼표) · 재고 · 분류 · `stock_status()` 를 머리글과 같은 폭으로 놓는다.
10. 재고가 0 보다 크고 10 보다 작은 상품만 골라 `  이름: 재고개` 꼴로 찍는다.
11. 재고 0 인 상품의 개수를 세어 `  N개 상품 비활성화됨` 으로 찍는다.
12. 마지막에 핵심 정리 네 줄을 찍는다.

**시작 코드**

```python
"""Django Admin 커스터마이징: ModelAdmin, filter, action"""
from datetime import datetime, timedelta
from typing import List

print("=== 1. 기본 ModelAdmin ===")
print("""
from django.contrib import admin
from .models import Product, Order, Customer

# TODO: 기본 등록 한 줄
# TODO: 데코레이터 방식 등록 (몸통 pass)
""")

print("=== 2. list_display, list_filter ===")
print("""
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # TODO: 목록 옵션 일곱 개
    # TODO: @admin.display 계산 컬럼 stock_status
""")

print("=== 3. 커스텀 Action ===")
print("""
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'total', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    # TODO: actions 목록과 액션 메서드 세 개
""")

print("=== 4. Inline ===")
print("""
# TODO: OrderItemInline(TabularInline), OrderNoteInline(StackedInline)
# TODO: OrderAdmin.inlines 와 item_count 컬럼
""")

print("=== 5. fieldsets ===")
print("""
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    # TODO: fieldsets 세 구역, readonly_fields, autocomplete_fields
""")

print("=== 6. 커스텀 필터 ===")
print("""
# TODO: StockRangeFilter(SimpleListFilter) 와 list_filter 등록
""")

print("=== 7. Admin 패턴 데모 ===")

class Product:
    def __init__(self, name, price, stock, category):
        pass  # TODO: 네 값을 저장

    def stock_status(self):
        pass  # TODO: 품절 / 부족 (n) / 충분 (n)

products = [
    Product("Python 기초", 25000, 50, "도서"),
    Product("Django 마스터", 35000, 3, "도서"),
    Product("USB 키보드", 15000, 0, "전자기기"),
    Product("모니터 암", 45000, 15, "전자기기"),
]

print(f"{'이름':<16} {'가격':>8} {'재고':>6} {'카테고리':<8} {'상태':<10}")
print("-" * 56)
# TODO: 상품마다 한 행 (머리글과 같은 폭, 가격은 천 단위 쉼표)

print("\n필터: 재고 부족")
# TODO: 0 < 재고 < 10 인 상품만

print("\n액션: 품절 상품 비활성화")
# TODO: 재고 0 인 상품 개수

print("\n=== 핵심 정리 ===")
print("list_display: 목록 컬럼 / list_filter: 필터 사이드바")
print("search_fields: 검색 / list_editable: 목록에서 수정")
print("actions: 일괄 작업 / inlines: 관련 모델 편집")
print("fieldsets: 상세 페이지 레이아웃 / SimpleListFilter: 커스텀 필터")
```

**확인 방법** — `python django-admin.py` 로 돌려, 섹션 7 의 표에 상태가 `충분 (50)` · `부족 (3)` · `품절` · `충분 (15)` 로 나오고, 필터 아래에 「Django 마스터」 한 줄, 액션 아래에 `1개 상품 비활성화됨` 이 나오는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
