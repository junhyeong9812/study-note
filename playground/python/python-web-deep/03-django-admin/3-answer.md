# python/python-web-deep/03 — Django Admin 커스터마이징 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 「Django 마스터: 3개」 한 줄만 찍힌다

**출력**

```text
필터: 재고 부족
  Django 마스터: 3개
```

**왜 그런가**
재고가 50 · 3 · 0 · 15 인 네 상품 중 `0 < p.stock < 10` 을 만족하는 것은 재고 3 인 「Django 마스터」뿐이다.
재고 0 인 「USB 키보드」는 `0 < 0` 이 거짓이라 빠진다.
`"\n필터: 재고 부족"` 의 `\n` 때문에 실제 출력에서는 이 줄 앞에 빈 줄이 하나 있다.
근거: 2-summary 「동작 방식 (8)」.

### 2. 「1개 상품 비활성화됨」이 찍히지만 재고는 그대로 0 이다

**출력**

```text
액션: 품절 상품 비활성화
  1개 상품 비활성화됨
```

**왜 그런가**
재고 0 인 상품은 「USB 키보드」 하나라 `len(out_of_stock)` 이 1 이다.
이 코드는 개수를 세어 출력만 하고 어떤 객체의 값도 바꾸지 않는다.
그래서 「USB 키보드」의 `stock` 은 그대로 0 이다.
근거: 2-summary 「어디서 틀리나 5」.

### 3. 「2개 주문이 취소됨」

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
메시지는 `2개 주문이 취소됨` 이 된다.

**왜 그런가**
`queryset.filter(status='pending')` 이 고른 다섯 중 `pending` 인 둘만 남긴다.
`update(status='cancelled')` 는 바뀐 행의 수 2 를 돌려주고, 그 수가 `updated` 에 들어가 메시지에 찍힌다.
`shipped` 인 셋은 거르기에서 빠져 취소되지 않는다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 2」.

### 4. 계산 결과는 DB 필드가 아니라 정렬 기준을 따로 알려야 한다

`stock_status` 는 행마다 메서드가 계산해 돌려주는 값이고, 데이터베이스에 그런 필드는 없다.
그래서 이 컬럼 머리글로 정렬하려면 「실제로는 `stock` 필드로 정렬하라」고 `ordering='stock'` 으로 알려 준다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1」.

### 5. 폭은 글자 수로 세는데 한글은 화면에서 더 넓다

`:<16` 같은 폭은 글자 수 기준이다.
한글 한 글자는 화면에서 영문 두 칸쯤을 차지하므로, 한글이 많은 머리글 줄(`이름` · `카테고리` 등)이 데이터 줄과 다르게 밀려 보인다.
글자 수로 세는 것은 파이썬 서식 규칙이고, 칸 수는 터미널 · 글꼴이 정한다.
근거: 2-summary 「어디서 틀리나 6」 · 「구현 세부사항 대 언어 보장」.

### 6. 범위 · 복합 조건 필터는 못 만든다 — `SimpleListFilter` 를 쓴다

필드 이름 문자열은 그 필드의 값으로 거르는 필터만 만든다.
「재고 0 초과 10 미만」처럼 조건을 직접 정한 선택지는 `SimpleListFilter` 를 상속해 `lookups` 와 `queryset` 을 채워 만든다.
만든 클래스는 `list_filter` 에 필드 이름과 섞어 넣는다.
근거: 2-summary 「동작 방식 (7)」 · 「어디서 틀리나 3」.

### 7. DB 를 고치지 않고 CSV 파일 응답을 돌려줄 수도 있다

`export_csv` 는 `HttpResponse(content_type='text/csv')` 를 만들고 `Content-Disposition` 을 `attachment; filename="orders.csv"` 로 준 뒤 선택된 주문을 한 행씩 써서 그 응답을 돌려준다.
즉 액션은 DB 갱신만이 아니라 선택된 행으로 파일을 내려받게 하는 일도 한다.
근거: 2-summary 「동작 방식 (4)」.

### 8. 고칠 수 없고, 「메타」 구역은 접을 수 있다

`created_at` 은 `readonly_fields` 에 있으므로 보이기만 하고 고칠 수 없다.
「메타」 구역에는 `'classes': ('collapse',)` 가 있어 접을 수 있는 구역으로 보인다.
근거: 2-summary 「동작 방식 (6)」.

### 9. 주문 하나에 품목 여럿이 달린 부모-자식 관계

`OrderItemInline` 은 주문(부모) 상세 페이지 안에서 그 주문에 딸린 품목(자식)들을 표 형식으로 함께 편집하게 한다.
`min_num=1` · `max_num=20` 이 「주문 하나에 품목 1~20개」라는 범위를 화면에 건다.
`item_count` 가 `obj.items.count()` 로 주문의 품목 수를 세는 것도 같은 관계를 쓴 것이다.
자식이 부모를 가리키는 외래 키로 이어져 있다는 점은 코드에서 읽은 추론이다 (원본에 근거 없음 — 추론).
근거: 2-summary 「동작 방식 (5)」.

### 10. `'low'` 분기의 `stock__gt=0, stock__lt=10` 과 맞물린다

`StockRangeFilter.queryset` 에서 `self.value() == 'low'` 일 때 `queryset.filter(stock__gt=0, stock__lt=10)` 을 돌려준다.
`__gt` 는 「보다 크다」, `__lt` 는 「보다 작다」라서 「0 초과 10 미만」이고, 시뮬레이션의 연쇄 비교 `0 < p.stock < 10` 과 같은 조건이다.
근거: 2-summary 「동작 방식 (7)」 · 「동작 방식 (8)」.

## 실습 정답

### 실습 1. Django Admin 커스터마이징 패턴 정리 스크립트

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 두 등록 방식 | 섹션 1 문자열의 `admin.site.register(Product)` · `@admin.register(Product)` |
| 2. 목록 옵션 · 계산 컬럼 | 섹션 2 문자열의 `list_display` ~ `date_hierarchy`, `@admin.display(...)` `stock_status` |
| 3. 액션 세 개 | 섹션 3 문자열의 `actions`, `mark_as_shipped` · `mark_as_cancelled` · `export_csv` |
| 4. 인라인 둘 · `item_count` | 섹션 4 문자열의 `OrderItemInline` · `OrderNoteInline` · `inlines` · `item_count.short_description` |
| 5. fieldsets | 섹션 5 문자열의 `fieldsets` · `'classes': ('collapse',)` · `readonly_fields` · `autocomplete_fields` |
| 6. 커스텀 필터 | 섹션 6 문자열의 `StockRangeFilter` · `lookups` · `queryset` · `list_filter = [StockRangeFilter, ...]` |
| 7. 시뮬레이션 모델 | `class Product` 의 `__init__` |
| 8. 재고 상태 | `Product.stock_status` |
| 9. 표 출력 | `for p in products:` 의 f-string (`{p.price:>8,}`) |
| 10. 재고 부족 필터 | `low_stock = [p for p in products if 0 < p.stock < 10]` |
| 11. 품절 액션 | `out_of_stock` · `len(out_of_stock)` |
| 12. 핵심 정리 | 마지막 `print` 네 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web-deep/reference/django-admin.py`

```python
# [웹 프레임워크 심화] Django Admin 커스터마이징
# 설명: ModelAdmin 커스터마이징, list_display, filter, action, inline
# 팁: Django Admin은 ModelAdmin을 상속하여 커스터마이징한다. list_display로 목록 컬럼, list_filter로 필터, actions로 일괄 작업, inlines로 관련 모델 편집을 추가한다. @admin.display 데코레이터로 계산된 컬럼을 만들고, SimpleListFilter로 커스텀 필터를 정의한다.

"""Django Admin 커스터마이징: ModelAdmin, filter, action"""
# 날짜 계산용 (예: 최근 가입자 필터)
from datetime import datetime, timedelta
# 타입 힌트
from typing import List

# === Django Admin 시뮬레이션 ===
# 실제 Django Admin 코드 패턴을 보여주는 데모

# === 1. 기본 ModelAdmin ===
print("=== 1. 기본 ModelAdmin ===")
# 가장 단순한 등록 방식 두 가지 (admin.site.register vs @admin.register)
print("""
from django.contrib import admin
from .models import Product, Order, Customer

# 가장 기본적인 등록
admin.site.register(Product)

# 또는 데코레이터 방식 (권장)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass
""")

# === 2. list_display와 list_filter ===
print("=== 2. list_display, list_filter ===")
# ModelAdmin 핵심 옵션 모음 (목록 페이지 커스터마이징)
print("""
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # 목록에 표시할 필드
    list_display = ['name', 'price', 'category', 'stock', 'is_available', 'created_at']

    # 필터 사이드바
    list_filter = ['category', 'is_available', 'created_at']

    # 검색 필드 (icontains 사용)
    search_fields = ['name', 'description', 'category__name']

    # 정렬
    ordering = ['-created_at']

    # 목록에서 바로 수정
    list_editable = ['price', 'stock', 'is_available']

    # 페이지당 항목 수
    list_per_page = 25

    # 날짜 기반 네비게이션
    date_hierarchy = 'created_at'

    # 커스텀 컬럼 (계산된 값)
    @admin.display(description='재고 상태', ordering='stock')
    def stock_status(self, obj):
        if obj.stock == 0:
            return '품절'
        elif obj.stock < 10:
            return f'부족 ({obj.stock})'
        return f'충분 ({obj.stock})'
""")

# === 3. 커스텀 Action ===
print("=== 3. 커스텀 Action ===")
# Action: 목록에서 선택한 항목들에 대한 일괄 작업 (트랜잭션 단위)
print("""
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'total', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    actions = ['mark_as_shipped', 'mark_as_cancelled', 'export_csv']

    @admin.action(description='선택된 주문을 배송 처리')
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'{updated}개 주문이 배송 처리됨')

    @admin.action(description='선택된 주문을 취소')
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='cancelled')
        self.message_user(request, f'{updated}개 주문이 취소됨')

    @admin.action(description='CSV로 내보내기')
    def export_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', '고객', '총액', '상태', '날짜'])
        for order in queryset:
            writer.writerow([
                order.id, order.customer, order.total,
                order.status, order.created_at
            ])
        return response
""")

# === 4. Inline (관련 모델 편집) ===
print("=== 4. Inline ===")
# Inline: 부모 폼에서 자식 모델을 함께 편집 (TabularInline=표 형식, StackedInline=세로 스택)
print("""
class OrderItemInline(admin.TabularInline):  # 또는 StackedInline
    model = OrderItem
    extra = 1          # 빈 폼 수
    min_num = 1        # 최소 항목
    max_num = 20       # 최대 항목
    readonly_fields = ['subtotal']
    autocomplete_fields = ['product']  # 자동완성 검색

class OrderNoteInline(admin.StackedInline):
    model = OrderNote
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline, OrderNoteInline]
    list_display = ['id', 'customer', 'item_count', 'total', 'status']

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = '상품 수'
""")

# === 5. fieldsets (상세 페이지 레이아웃) ===
print("=== 5. fieldsets ===")
# fieldsets: 상세 페이지의 입력 필드를 그룹화 (collapse 옵션으로 접기 가능)
print("""
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    fieldsets = [
        ('기본 정보', {
            'fields': ('name', 'email', 'phone'),
        }),
        ('주소', {
            'fields': ('address', 'city', 'zip_code'),
            'classes': ('collapse',),  # 접을 수 있음
        }),
        ('메타', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',),
        }),
    ]

    readonly_fields = ['created_at', 'updated_at']

    # 자동완성 검색
    autocomplete_fields = ['referred_by']
""")

# === 6. 커스텀 필터 ===
print("=== 6. 커스텀 필터 ===")
# SimpleListFilter: 단순 옵션 외에 임의 쿼리 조건을 사이드바 필터로 노출
print("""
class StockRangeFilter(admin.SimpleListFilter):
    title = '재고 상태'
    parameter_name = 'stock_range'

    def lookups(self, request, model_admin):
        return [
            ('out', '품절'),
            ('low', '부족 (10 미만)'),
            ('ok', '충분 (10 이상)'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'out':
            return queryset.filter(stock=0)
        elif self.value() == 'low':
            return queryset.filter(stock__gt=0, stock__lt=10)
        elif self.value() == 'ok':
            return queryset.filter(stock__gte=10)
        return queryset

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_filter = [StockRangeFilter, 'category', 'is_available']
""")

# === 7. 실행 가능한 데모 ===
print("=== 7. Admin 패턴 데모 ===")

# Product 클래스: ModelAdmin 패턴을 시뮬레이션하기 위한 단순 모델
class Product:
    # 생성자: name/price/stock/category 받음
    def __init__(self, name, price, stock, category):
        self.name = name
        self.price = price
        self.stock = stock
        self.category = category

    # 계산된 컬럼: @admin.display 메서드를 시뮬레이션
    def stock_status(self):
        if self.stock == 0:
            return '품절'
        elif self.stock < 10:
            return f'부족 ({self.stock})'
        return f'충분 ({self.stock})'

# 목록 표시 시뮬레이션 — 4개 샘플 데이터
products = [
    Product("Python 기초", 25000, 50, "도서"),
    Product("Django 마스터", 35000, 3, "도서"),
    Product("USB 키보드", 15000, 0, "전자기기"),
    Product("모니터 암", 45000, 15, "전자기기"),
]

# list_display처럼 표 형식 출력
print(f"{'이름':<16} {'가격':>8} {'재고':>6} {'카테고리':<8} {'상태':<10}")
print("-" * 56)
for p in products:
    print(f"{p.name:<16} {p.price:>8,} {p.stock:>6} {p.category:<8} {p.stock_status():<10}")

# 필터 시뮬레이션 — 재고 부족 항목만 추출
print("\n필터: 재고 부족")
low_stock = [p for p in products if 0 < p.stock < 10]
for p in low_stock:
    print(f"  {p.name}: {p.stock}개")

# Action 시뮬레이션 — 품절 상품 처리
print("\n액션: 품절 상품 비활성화")
out_of_stock = [p for p in products if p.stock == 0]
print(f"  {len(out_of_stock)}개 상품 비활성화됨")

print("\n=== 핵심 정리 ===")
print("list_display: 목록 컬럼 / list_filter: 필터 사이드바")
print("search_fields: 검색 / list_editable: 목록에서 수정")
print("actions: 일괄 작업 / inlines: 관련 모델 편집")
print("fieldsets: 상세 페이지 레이아웃 / SimpleListFilter: 커스텀 필터")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 1. 기본 ModelAdmin ===

from django.contrib import admin
from .models import Product, Order, Customer

# 가장 기본적인 등록
admin.site.register(Product)

# 또는 데코레이터 방식 (권장)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass

=== 2. list_display, list_filter ===

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # 목록에 표시할 필드
    list_display = ['name', 'price', 'category', 'stock', 'is_available', 'created_at']

    # 필터 사이드바
    list_filter = ['category', 'is_available', 'created_at']

    # 검색 필드 (icontains 사용)
    search_fields = ['name', 'description', 'category__name']

    # 정렬
    ordering = ['-created_at']

    # 목록에서 바로 수정
    list_editable = ['price', 'stock', 'is_available']

    # 페이지당 항목 수
    list_per_page = 25

    # 날짜 기반 네비게이션
    date_hierarchy = 'created_at'

    # 커스텀 컬럼 (계산된 값)
    @admin.display(description='재고 상태', ordering='stock')
    def stock_status(self, obj):
        if obj.stock == 0:
            return '품절'
        elif obj.stock < 10:
            return f'부족 ({obj.stock})'
        return f'충분 ({obj.stock})'

=== 3. 커스텀 Action ===

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'total', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    actions = ['mark_as_shipped', 'mark_as_cancelled', 'export_csv']

    @admin.action(description='선택된 주문을 배송 처리')
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'{updated}개 주문이 배송 처리됨')

    @admin.action(description='선택된 주문을 취소')
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='cancelled')
        self.message_user(request, f'{updated}개 주문이 취소됨')

    @admin.action(description='CSV로 내보내기')
    def export_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', '고객', '총액', '상태', '날짜'])
        for order in queryset:
            writer.writerow([
                order.id, order.customer, order.total,
                order.status, order.created_at
            ])
        return response

=== 4. Inline ===

class OrderItemInline(admin.TabularInline):  # 또는 StackedInline
    model = OrderItem
    extra = 1          # 빈 폼 수
    min_num = 1        # 최소 항목
    max_num = 20       # 최대 항목
    readonly_fields = ['subtotal']
    autocomplete_fields = ['product']  # 자동완성 검색

class OrderNoteInline(admin.StackedInline):
    model = OrderNote
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline, OrderNoteInline]
    list_display = ['id', 'customer', 'item_count', 'total', 'status']

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = '상품 수'

=== 5. fieldsets ===

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    fieldsets = [
        ('기본 정보', {
            'fields': ('name', 'email', 'phone'),
        }),
        ('주소', {
            'fields': ('address', 'city', 'zip_code'),
            'classes': ('collapse',),  # 접을 수 있음
        }),
        ('메타', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',),
        }),
    ]

    readonly_fields = ['created_at', 'updated_at']

    # 자동완성 검색
    autocomplete_fields = ['referred_by']

=== 6. 커스텀 필터 ===

class StockRangeFilter(admin.SimpleListFilter):
    title = '재고 상태'
    parameter_name = 'stock_range'

    def lookups(self, request, model_admin):
        return [
            ('out', '품절'),
            ('low', '부족 (10 미만)'),
            ('ok', '충분 (10 이상)'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'out':
            return queryset.filter(stock=0)
        elif self.value() == 'low':
            return queryset.filter(stock__gt=0, stock__lt=10)
        elif self.value() == 'ok':
            return queryset.filter(stock__gte=10)
        return queryset

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_filter = [StockRangeFilter, 'category', 'is_available']

=== 7. Admin 패턴 데모 ===
이름                     가격     재고 카테고리     상태        
--------------------------------------------------------
Python 기초          25,000     50 도서       충분 (50)   
Django 마스터         35,000      3 도서       부족 (3)    
USB 키보드            15,000      0 전자기기     품절        
모니터 암              45,000     15 전자기기     충분 (15)   

필터: 재고 부족
  Django 마스터: 3개

액션: 품절 상품 비활성화
  1개 상품 비활성화됨

=== 핵심 정리 ===
list_display: 목록 컬럼 / list_filter: 필터 사이드바
search_fields: 검색 / list_editable: 목록에서 수정
actions: 일괄 작업 / inlines: 관련 모델 편집
fieldsets: 상세 페이지 레이아웃 / SimpleListFilter: 커스텀 필터
````

**풀이 요점**

- 섹션 1~6 은 실행이 아니라 출력이다 — Django 코드를 삼중 따옴표 문자열 그대로 찍는다.
- 계산 컬럼은 `@admin.display(ordering='stock')` 로 정렬 기준까지 준다.
- 취소 액션은 `filter(status='pending')` 으로 한 번 더 거른 뒤 `update` 하고, 그 반환값(바뀐 수)을 메시지에 쓴다.
- `StockRangeFilter.queryset` 은 고른 값이 없을 때 받은 queryset 을 그대로 돌려줘야 한다.
- 시뮬레이션의 비교식 `0 < p.stock < 10` 은 `stock__gt=0, stock__lt=10` 과 같은 조건이고, 액션 흉내는 개수만 센다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
