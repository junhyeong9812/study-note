# python/python-web/02 — Django Views (뷰 처리) — 정리 (힌트)

> 출처 — study-site 항목 `python/django-views`(항목 데이터 `data/python/web-frameworks.json`) · 정답 코드 study-practice `python/python-web/reference/django-views.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `django` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**Django 뷰는 「식당 주방의 요리사」다.**
손님의 주문서(요청)가 들어오면 안내 데스크(URLconf)가 주문서를 맡을 요리사에게 넘긴다.
요리사는 재료(DB)를 꺼내 요리(템플릿 렌더링 · JSON)를 담아 접시(응답)로 내보낸다.
혼자 처음부터 끝까지 조리하는 요리사도 있고, 표준 레시피를 물려받아 몇 군데만 바꾸는 요리사도 있다.
Django 의 뷰도 똑같은 구조다.

> **뷰(view)** — 요청 객체를 받아 응답 객체를 돌려주는 콜러블이다.\
> 예: `def post_list(request): ... return render(...)`.

| 비유 | 실체 |
|---|---|
| 주문서 | `request` 객체 |
| 안내 데스크 | `urlpatterns` 의 `path(...)` |
| 혼자 다 하는 요리사 | FBV (함수 기반 뷰) |
| 표준 레시피를 물려받은 요리사 | CBV · Generic View (`ListView` · `CreateView` …) |
| 입구의 「회원만 입장」 직원 | `@login_required` · `LoginRequiredMixin` |
| 「그런 메뉴 없습니다」 | `get_object_or_404` 가 내는 404 |
| 접시 | `HttpResponse` · `JsonResponse` · `redirect(...)` |

```text
브라우저 ──요청──▶ urlpatterns ──고른다──▶ 뷰(FBV 함수 / CBV.as_view())
                                              │
                                     DB 조회 · 폼 검증 · 권한 확인
                                              │
브라우저 ◀──────────── 응답 (HTML · JSON · 302 리다이렉트 · 404)
```

## 이 주제가 답하려는 질문

1. 요청은 어떻게 뷰에 닿고, 뷰는 무엇을 돌려주나?
2. 같은 일을 FBV 와 CBV 는 어떻게 다르게 표현하나?
3. 없는 글 · 비공개 글 · 미로그인 · 남의 글 같은 예외 상황은 어디서 걸러지나?
4. 쿼리와 URL 은 언제 만들어야 안전한가 — N+1 과 `reverse_lazy` 는 무엇을 막나?

## 동작 방식

### (1) 요청 → URLconf → 뷰 → 응답

**언제 쓰나** — 모든 뷰의 공통 바탕이다.
주소 하나에 뷰 하나를 잇는 것부터 시작한다.

```text
GET /posts/7/
   │
   ▼
path('posts/<int:pk>/', PostDetailView.as_view(), name='post-detail')
   │  '7' 을 int 로 바꿔 pk=7 로 넘긴다
   ▼
뷰(request, pk=7) ──▶ render(...) ──▶ HTML 응답
```

- `urlpatterns` 의 `path` 가 주소 모양과 뷰를 짝짓는다.
- `<int:pk>` 는 그 자리의 글자를 정수로 바꿔 `pk` 라는 인자로 뷰에 넘긴다.
- `int` 로 바꿀 수 없는 글자(예: `create`)면 그 패턴은 맞지 않고 다음 패턴으로 넘어간다.
- CBV 는 클래스라서 그대로는 뷰가 아니다 — `.as_view()` 를 불러 콜러블로 바꿔 등록한다.
- `name='post-detail'` 은 주소에 붙인 이름이다. `redirect` · `reverse_lazy` 가 이 이름으로 주소를 거꾸로 만든다.

> **URLconf** — 주소 모양과 뷰를 짝지은 목록(`urlpatterns`)이다.\
> 예: `path('posts/', PostListView.as_view(), name='post-list')`.

> **컨버터(converter)** — 주소의 한 조각을 잡아 타입을 바꿔 넘기는 표시다.\
> 예: `<int:pk>` 는 `/posts/7/` 의 `7` 을 `pk=7` 로 넘긴다.

### (2) FBV — 함수 하나가 처음부터 끝까지

**언제 쓰나** — 흐름이 짧고 한눈에 읽혀야 하는 뷰.
목록 · 상세 · JSON 응답처럼 단순한 일.

```text
post_list(request)
  1. Post.objects.filter(status='PB').select_related('author','category')
  2. Paginator(posts, 10)                     ← 페이지당 10개
  3. request.GET.get('page', 1)               ← ?page= 없으면 1
  4. paginator.get_page(번호)                  ← 잘못된 번호도 안전하게
  5. render(request, 'blog/post_list.html', {'page_obj':…, 'total_count': paginator.count})
```

1. 공개 글(`status='PB'`)만 고르고, 작성자 · 분류를 JOIN 으로 미리 가져온다.
2. `Paginator` 가 목록을 10개씩 자른다.
3. 쿼리 문자열의 `page` 값을 읽는다.
4. `get_page` 는 숫자가 아니거나 범위를 벗어난 번호에도 예외를 던지지 않고 페이지를 돌려준다.
5. `render` 가 템플릿과 컨텍스트 딕셔너리로 HTML 응답을 만든다.

`post_detail` 은 `get_object_or_404(Post, pk=pk, status='PB')` 로 글 하나를 꺼낸다.
조건에 맞는 글이 없으면 — 번호가 없든, 번호는 있는데 공개가 아니든 — 그 자리에서 404 응답이 된다.
찾았으면 `view_count` 를 1 올리고 `save(update_fields=['view_count'])` 로 그 컬럼만 갱신한다.

`api_posts` 는 `.values('id', 'title', 'created_at')` 로 딕셔너리 꼴 QuerySet 을 만들고 `list(...)` 로 바꿔 `JsonResponse` 에 넘긴다.
`JsonResponse` 는 기본으로 딕셔너리만 받으므로 리스트를 넘길 때는 `safe=False` 를 준다.

> **QuerySet** — DB 질의를 나타내는 객체다. 실제로 값을 꺼낼 때 질의가 나간다.\
> 예: `Post.objects.filter(status='PB')`.

> **컨텍스트(context)** — 템플릿에 넘기는 이름 → 값 딕셔너리다.\
> 예: `{'post': post}` 를 넘기면 템플릿에서 `post` 로 쓴다.

### (3) FBV 의 폼 처리와 PRG

**언제 쓰나** — 같은 주소가 GET 이면 빈 폼을, POST 면 저장을 하는 작성 화면.

```text
@login_required                       ← 바깥 껍질
@require_http_methods(['GET','POST'])  ← 안쪽 껍질
def post_create(request): …

요청 ─▶ [login_required] ─미로그인─▶ 로그인 페이지로
            │ 로그인됨
            ▼
        [require_http_methods] ─GET/POST 아님─▶ 거절
            │
            ▼
        post_create
          POST & is_valid()  ─▶ save(commit=False) → author 채움 → save() → save_m2m()
                                 → redirect('post-detail', pk=post.pk)   (PRG)
          POST & 검증 실패    ─▶ 맨 아래 render(form)  ← 오류가 담긴 폼을 다시 보여 준다
          GET                ─▶ form = PostForm() → render(form)
```

- `@login_required` 는 로그인하지 않은 사용자를 로그인 페이지로 보낸다.
- `@require_http_methods(['GET', 'POST'])` 는 허용 메서드 화이트리스트다.
- `form.save(commit=False)` 는 모델 객체만 만들고 DB 에 쓰지 않는다 — 작성자처럼 폼에 없는 필드를 채울 틈을 준다.
- `commit=False` 로 저장을 미뤘으면 다대다(태그) 관계는 `form.save_m2m()` 으로 따로 저장해야 한다.
- 저장에 성공하면 HTML 을 바로 그리지 않고 `redirect` 로 상세 페이지로 보낸다 — 이것이 PRG(POST-Redirect-GET) 패턴이다.
- 검증에 실패하면 `if form.is_valid()` 안으로 들어가지 않으므로 맨 아래 `render` 에 오류가 담긴 폼이 넘어간다.

> **PRG 패턴** — POST 처리 뒤 리다이렉트로 GET 페이지를 보여 주는 방식이다.\
> 예: 글 저장 후 `redirect('post-detail', pk=post.pk)`.

> **데코레이터** — 함수를 감싸 앞뒤에 기능을 덧붙이는 문법(`@이름`)이다.\
> 예: `@login_required` 를 붙이면 미로그인 요청이 함수 본문에 닿지 않는다.

### (4) 제네릭 CBV — 갈아 끼울 자리만 덮어쓴다

**언제 쓰나** — 목록 · 상세 · 작성 · 수정 · 삭제(CRUD)처럼 모양이 정해진 일.

```text
class PostListView(ListView)
   model = Post                  ─┐
   template_name = …             ─┤ 클래스 속성으로 설정
   context_object_name = 'posts' ─┤ (안 주면 object_list)
   paginate_by = 10              ─┘ 페이지네이션 자동
   def get_queryset(self):       ← 「어떤 글을 보여 줄까」 한 군데만 덮어쓴다
       super() 결과 → status='PB' → ?q= 있으면 title__icontains → select_related
```

| 클래스 | 하는 일 | 원본이 덮어쓴 자리 |
|---|---|---|
| `TemplateView` | 템플릿 하나 렌더링 | `get_context_data` — `latest_posts` 5개 추가 |
| `ListView` | 목록 + 자동 페이지네이션 | `get_queryset` — 공개 글 · 제목 검색 |
| `DetailView` | 객체 하나 상세 | `get_queryset` — 공개 글만 |
| `CreateView` | 폼 표시 + 저장 | `form_valid` — 작성자 주입 / `get_success_url` |
| `UpdateView` | 기존 객체 수정 폼 | `get_queryset` — 자기 글만 |
| `DeleteView` | 삭제 확인 + 삭제 | `success_url = reverse_lazy('post-list')` |

1. 클래스 속성(`model` · `template_name` · `fields` …)으로 기본 동작을 설정한다.
2. 바꿀 단계만 메서드로 덮어쓰고, 나머지는 `super()` 로 부모에게 맡긴다.
3. `get_context_data` 는 `super()` 가 만든 컨텍스트에 값을 더해 돌려준다.
4. `form_valid` 는 검증을 통과했을 때 불리며, 저장 직전에 `form.instance.author` 를 채운 뒤 `super().form_valid(form)` 으로 저장을 맡긴다.
5. `get_success_url` 은 저장 뒤 보낼 주소를 돌려준다 — 저장된 객체는 `self.object` 에 있다.

> **제네릭 뷰(generic view)** — 흔한 패턴(CRUD)을 미리 구현해 둔 CBV 다.\
> 예: `ListView` 는 `model` 만 주면 목록을 그린다.

### (5) 권한 거르기 — Mixin 과 get_queryset

**언제 쓰나** — 로그인한 사람만, 또는 자기 글만 다루게 할 때.

```text
class PostUpdateView(LoginRequiredMixin, UpdateView)
            │                    │
            │ 먼저 검사           │ 그다음 수정 로직
            ▼                    ▼
   미로그인 → 로그인 페이지     get_queryset() = 내 글만
                                  │
                       pk 가 남의 글 → 이 QuerySet 에 없다 → 404
```

- `LoginRequiredMixin` 은 CBV 에서 `@login_required` 를 대신한다.
- 다중 상속에서 왼쪽 클래스가 먼저 적용되므로 Mixin 은 **맨 왼쪽**에 둔다.
- `login_url` 은 미로그인일 때 보낼 주소다.
- `UpdateView` 는 주소의 `pk` 로 객체를 찾을 때 `get_queryset()` 안에서 찾는다.
- 그래서 `get_queryset` 을 「내 글만」으로 좁히면, 남의 글 `pk` 는 찾지 못해 404 가 된다 — 이것이 객체 수준 권한이다.

> **Mixin** — 단독으로 쓰지 않고 다른 클래스와 섞어 기능 하나를 보태는 클래스다.\
> 예: `class PostCreateView(LoginRequiredMixin, CreateView)`.

### (6) View 직접 상속 — 메서드 이름으로 나눈다

**언제 쓰나** — 제네릭 뷰의 틀이 맞지 않는 API 같은 뷰.

```text
PostAPIView.as_view()
   요청 GET  ──▶ self.get(request)  ──▶ JsonResponse(list, safe=False)
   요청 POST ──▶ self.post(request) ──▶ json.loads(request.body) → JsonResponse({...}, status=201)
```

- `View` 를 상속하고 HTTP 메서드 이름(`get` · `post`)과 같은 메서드를 정의한다.
- 요청의 메서드에 따라 같은 이름의 메서드가 불린다 — FBV 의 `if request.method == 'POST'` 분기를 메서드로 나눈 꼴이다.
- `request.body` 는 원본 바이트 본문이라 `json.loads` 로 풀어 쓴다.
- `JsonResponse(..., status=201)` 처럼 상태 코드를 직접 줄 수 있다.

### (7) 에러 핸들러

**언제 쓰나** — 404 · 500 화면을 사이트 모양으로 바꿀 때.

```text
handler404 = 'blog.views.custom_404'  ─▶ custom_404(request, exception) → render(..., status=404)
handler500 = 'blog.views.custom_500'  ─▶ custom_500(request)            → render(..., status=500)
```

- `handler404` · `handler500` 은 urls.py 에 문자열 경로로 등록하는 전역 핸들러다.
- 404 핸들러는 `exception` 인자를 하나 더 받고, 500 핸들러는 `request` 만 받는다.
- `render(..., status=404)` 처럼 상태 코드를 직접 적어야 한다 — 빼면 기본 상태 코드로 나간다.
- `Http404` 는 뷰 안에서 404 를 명시적으로 일으킬 때 던지는 예외다(원본은 import 만 한다).

### (8) URL 이름과 reverse_lazy

**언제 쓰나** — 주소를 하드코딩하지 않고 이름으로 만들 때.

```text
클래스 정의 시점  ─ success_url = reverse_lazy('post-list')   ← 지금은 「나중에 계산할 약속」만 저장
                     (이때 URLconf 가 아직 준비되지 않았을 수 있다)
요청 처리 시점   ─ 약속을 풀어 '/posts/' 로 계산
```

- `redirect('post-detail', pk=post.pk)` 는 URL 이름과 인자로 주소를 만들어 리다이렉트한다(HTTP 302).
- 클래스 속성은 모듈을 읽을 때 바로 계산되는데, 그때는 URLconf 가 아직 준비되지 않았을 수 있다.
- `reverse_lazy` 는 주소 계산을 실제로 쓰일 때까지 미룬다.

> **N+1 문제** — 목록 1번 질의 뒤 항목마다 관련 객체를 1번씩 더 질의하는 일이다.\
> 예: 글 10개를 보여 주며 작성자 이름을 찍으면 질의가 1 + 10 번 나간다.

`select_related('author', 'category')` 는 JOIN 으로 관련 객체를 처음 질의에 함께 가져와 이 문제를 막는다.
팁은 `prefetch_related` 도 같은 목적의 도구로 든다.

## 문법 — 형태와 규칙

같은 「공개 글 상세」를 FBV 와 CBV 로 쓴 최소 예제다.

```python
from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView
from django.urls import path

def note_detail(request, pk):                      # FBV
    note = get_object_or_404(Note, pk=pk, public=True)
    return render(request, 'note.html', {'note': note})

class NoteDetailView(DetailView):                  # CBV
    model = Note
    template_name = 'note.html'
    context_object_name = 'note'
    def get_queryset(self):
        return super().get_queryset().filter(public=True)

urlpatterns = [
    path('a/<int:pk>/', note_detail, name='note-a'),
    path('b/<int:pk>/', NoteDetailView.as_view(), name='note-b'),
]
```

- FBV 는 `def 이름(request, URL인자...)` 꼴이고 응답 객체를 `return` 한다.
- CBV 는 `path` 에 `.as_view()` 로 넣는다. FBV 는 함수를 그대로 넣는다.
- 제네릭 뷰는 클래스 속성으로 설정하고, 바꿀 단계만 메서드로 덮어쓴 뒤 `super()` 를 부른다.
- `context_object_name` 을 주지 않으면 `ListView` 의 목록은 템플릿에서 `object_list` 다.
- FBV 에 기능을 더할 때는 데코레이터, CBV 에 더할 때는 Mixin 을 왼쪽에 상속한다.
- 상태 코드를 바꿀 때는 `render(..., status=404)` · `JsonResponse(..., status=201)` 처럼 인자로 준다.

| 도구 | 하는 일 |
|---|---|
| `render(request, 템플릿, 컨텍스트)` | 템플릿 렌더링 응답 |
| `get_object_or_404(모델, 조건...)` | 없으면 404 |
| `redirect(URL이름, 인자...)` | HTTP 302 리다이렉트 |
| `JsonResponse(데이터, safe=False)` | JSON 응답, 리스트도 허용 |
| `Paginator(목록, 개수).get_page(번호)` | 페이지 자르기 |
| `reverse_lazy(URL이름)` | URL 계산을 미룬다 |
| `@require_http_methods([...])` | 허용 메서드 제한 |

## 어디서 틀리나

### 1. FBV 와 CBV 고르기
팁: FBV 는 간단한 뷰에, CBV 는 CRUD 패턴에 맞는다.
간단한 일을 CBV 로 쓰면 어느 메서드가 언제 불리는지 찾아다녀야 하고, CRUD 를 FBV 로 쓰면 같은 분기를 매번 다시 쓴다.

### 2. `.get()` 대신 `get_object_or_404`
팁: `get_object_or_404` 는 `DoesNotExist` 예외 대신 404 를 돌려준다.
`Post.objects.get(pk=pk)` 를 그냥 쓰면 없는 번호에서 예외가 터져 500 오류가 된다.
조건(`status='PB'`)을 같이 주면 「비공개 글」도 같은 404 로 걸러진다.

### 3. N+1 질의
팁: `select_related` · `prefetch_related` 로 N+1 질의 문제를 막는다.
목록 뷰에서 관련 객체(작성자 · 분류)를 템플릿이 하나씩 읽으면 질의가 항목 수만큼 늘어난다.
원본은 FBV(`post_list`)와 CBV(`PostListView.get_queryset`) 양쪽에 `select_related('author', 'category')` 를 붙였다.

### 4. CBV 에 `@login_required` 를 그대로 붙이기
팁: CBV 에서는 `@login_required` 대신 `LoginRequiredMixin` 을 쓴다.
그리고 Mixin 은 맨 왼쪽에 둔다 — `class X(CreateView, LoginRequiredMixin)` 처럼 오른쪽에 두면 인증 검사가 먼저 돌지 않을 수 있다.

### 5. `commit=False` 뒤 `save_m2m()` 빠뜨리기
`form.save(commit=False)` 로 저장을 미루면 다대다 관계(태그)는 저장되지 않은 채 남는다.
`post.save()` 뒤에 `form.save_m2m()` 을 불러야 태그까지 저장된다.

### 6. 리스트를 `JsonResponse` 에 넘기며 `safe=False` 빠뜨리기
`JsonResponse` 는 기본으로 딕셔너리만 받는다.
`list(posts)` 를 넘기려면 `safe=False` 가 필요하다.

### 7. 클래스 속성에 `reverse` 쓰기
`success_url = reverse('post-list')` 처럼 즉시 계산하면 URLconf 가 준비되기 전에 계산될 수 있다.
클래스 속성에는 `reverse_lazy` 를 쓴다.

### 8. POST 뒤 바로 HTML 을 그리기
저장 성공 뒤 `render` 로 페이지를 그리면 새로고침이 POST 를 다시 보내 같은 글이 또 저장될 수 있다.
원본은 `redirect` 로 GET 페이지에 보내는 PRG 패턴을 쓴다.

### 9. 원본 주석 「데코레이터 스택: 위에서부터 적용」
원본의 주장 → 데코레이터는 위에서부터 적용된다.
왜 의심스러운가 → 파이썬에서 데코레이터가 함수를 **감싸는** 순서는 아래(함수에 가까운 쪽)부터다.
`require_http_methods` 가 먼저 `post_create` 를 감싸고, 그 결과를 `login_required` 가 다시 감싼다.
다만 요청이 들어왔을 때 **검사가 실행되는** 순서는 바깥 껍질인 위쪽(`login_required`)부터다.
「위에서부터」는 실행 순서로 읽어야 맞고, 감싸는 순서로 읽으면 틀린다.

### 10. 원본 주석 「Django는 WSGI 기반」
원본의 주장 → Django 는 WSGI 기반이고, 뷰는 request 를 받아 HttpResponse 를 돌려주는 콜러블이다.
왜 의심스러운가 → 뒷부분(뷰 = 콜러블)은 맞지만, 최근 Django 는 ASGI 로도 돌릴 수 있어 「WSGI 기반」으로만 말하기는 좁다 (확인 필요).

### 11. 에러 핸들러의 시그니처
404 핸들러는 `(request, exception)`, 500 핸들러는 `(request)` 다.
둘을 같은 꼴로 쓰면 인자 수가 맞지 않는다.
상태 코드도 `status=404` 로 직접 적어야 한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 데코레이터는 아래부터 감싸고, 요청 때는 바깥(위)부터 실행된다 | 파이썬 언어 (데코레이터 문법) |
| 다중 상속에서 왼쪽 클래스의 메서드가 먼저 찾아진다 | 파이썬 언어 (MRO) |
| `get_object_or_404` 는 없으면 404 를 낸다 | Django API |
| `redirect` 는 HTTP 302 를 보낸다 | Django API (원본 주석 기준) |
| `ListView` 의 기본 컨텍스트 이름은 `object_list` | Django API |
| `JsonResponse` 는 `safe=False` 없이 리스트를 받지 않는다 | Django API |
| `select_related` 는 JOIN 으로 가져온다 | Django ORM 구현 |
| Django 는 WSGI 기반이다 | 원본 주석의 주장 — ASGI 도 있다 (확인 필요) |
| `status='PB'` 가 「공개」를 뜻한다 | 이 프로젝트의 `Post` 모델 정의 (Django 와 무관) |
| `request.user.author_profile` | 이 프로젝트가 만든 관계 이름 (Django 와 무관) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 흐름이 짧은 단순 뷰 | FBV | 메서드를 여럿 덮어써야 하는 CBV |
| 목록 · 상세 · 작성 · 수정 · 삭제 | `ListView` · `DetailView` · `CreateView` · `UpdateView` · `DeleteView` | 같은 분기를 반복하는 FBV |
| 템플릿 하나만 그리기 | `TemplateView` | 빈 함수를 매번 쓰기 |
| 메서드별로 다른 API | `View` 상속 + `get` · `post` | 제네릭 뷰에 억지로 끼우기 |
| 객체 하나 찾기 | `get_object_or_404` | 예외 처리 없는 `.get()` |
| 로그인 필수 | FBV 는 `@login_required`, CBV 는 `LoginRequiredMixin`(왼쪽) | CBV 클래스에 데코레이터 직접 |
| 자기 글만 수정 | `get_queryset` 을 작성자로 좁히기 | 템플릿에서 버튼만 숨기기 |
| 클래스 속성의 URL | `reverse_lazy` | `reverse` |
| POST 저장 성공 후 | `redirect` (PRG) | 그 자리에서 `render` |
| 목록에서 관련 객체 쓰기 | `select_related` · `prefetch_related` | 그냥 반복하며 접근 |

## 핵심 문장

1. **뷰는 요청을 받아 응답을 돌려주는 콜러블이다** — FBV 는 함수, CBV 는 `.as_view()` 가 만든 콜러블이다.
2. **제네릭 CBV 는 클래스 속성으로 설정하고 바꿀 단계만 덮어쓴다** — `get_queryset` · `get_context_data` · `form_valid` · `get_success_url`.
3. **거르기는 앞에서 한다** — 인증은 데코레이터 · 맨 왼쪽 Mixin, 없는 글과 남의 글은 `get_object_or_404` 와 좁힌 `get_queryset` 이 404 로 막는다.
4. **POST 성공 뒤에는 리다이렉트한다** — PRG 로 새로고침 중복 저장을 막는다.
5. **질의와 URL 은 시점을 따진다** — 관련 객체는 `select_related` 로 미리, 클래스 속성의 URL 은 `reverse_lazy` 로 나중에.

## 관련 자료

- [django-models](../01-django-models/2-summary.md)
- `django-orm` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [django-forms](../04-django-forms/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/web-frameworks.json` 의 `django-views`

## 용어 풀이

- **뷰(view)** — 요청을 받아 응답을 돌려주는 콜러블.
- **콜러블(callable)** — `()` 로 부를 수 있는 것(함수 · `__call__` 이 있는 객체).
- **FBV** — 함수로 쓴 뷰(Function-Based View).
- **CBV** — 클래스로 쓰고 `.as_view()` 로 등록하는 뷰(Class-Based View).
- **제네릭 뷰** — CRUD 같은 흔한 패턴을 미리 구현한 CBV.
- **Mixin** — 다른 클래스와 섞어 기능 하나를 보태는 클래스.
- **MRO** — 다중 상속에서 메서드를 찾는 클래스 순서.
- **데코레이터** — 함수를 감싸 기능을 덧붙이는 `@` 문법.
- **URLconf** — 주소 모양과 뷰를 짝지은 `urlpatterns` 목록.
- **컨버터** — `<int:pk>` 처럼 주소 조각의 타입을 바꿔 넘기는 표시.
- **QuerySet** — DB 질의를 나타내는 Django 객체.
- **컨텍스트** — 템플릿에 넘기는 이름 → 값 딕셔너리.
- **페이지네이션** — 긴 목록을 페이지 단위로 자르는 일.
- **N+1 문제** — 목록 질의 1번 뒤 항목마다 질의가 1번씩 더 나가는 일.
- **`select_related`** — 관련 객체를 JOIN 으로 함께 가져오는 QuerySet 메서드.
- **`prefetch_related`** — 관련 객체를 미리 가져와 N+1 을 막는 QuerySet 메서드.
- **PRG 패턴** — POST 처리 뒤 리다이렉트로 GET 페이지를 보이는 방식.
- **`reverse_lazy`** — URL 이름으로 주소를 만들되 계산을 쓰일 때로 미루는 함수.
- **객체 수준 권한** — 객체마다(내 글인가) 접근을 가르는 권한.
- **에러 핸들러** — 404 · 500 응답을 그리는 전역 뷰(`handler404` · `handler500`).

## 더 들어가면

- `Paginator.get_page` 는 숫자가 아닌 번호에는 첫 페이지를, 범위를 넘는 번호에는 마지막 페이지를 돌려준다 (확인 필요).
- `select_related` 는 외래키 · 일대일 관계에 쓰고, 다대다 · 역방향 관계에는 별도 질의를 날려 파이썬에서 합치는 `prefetch_related` 를 쓴다 (확인 필요).
- `handler404` · `handler500` 은 루트 URLconf 에 둬야 효과가 있고, `DEBUG = True` 일 때는 Django 의 디버그 화면이 대신 나온다 (확인 필요).
- `get_success_url` 은 요청을 처리하는 중에 불리므로 그 안에서는 `reverse` 를 써도 된다 — 원본처럼 `reverse_lazy` 를 써도 동작은 한다 (확인 필요).
- `@require_http_methods` 에 걸린 요청은 405 응답을 받는다 (확인 필요).
- `View` 를 상속한 CBV 에 정의하지 않은 메서드(예: `PUT`)로 요청하면 405 응답이 된다 (확인 필요).
- `post.view_count += 1` 은 읽고 더하고 쓰는 세 단계라 동시 요청에서 증가가 빠질 수 있고, `F('view_count') + 1` 식이 이를 피한다 (확인 필요).
- CBV 의 `post` 메서드로 JSON 을 받는 API 는 CSRF 검사에 걸릴 수 있다 (확인 필요).
- 원본은 `HttpResponse` · `Http404` 를 import 만 하고 쓰지 않는다.
