# python/python-web/02 — Django Views (뷰 처리) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 404 응답을 받고, 조회수는 그대로다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`get_object_or_404(Post, pk=7, status='PB')` 는 번호와 공개 조건을 함께 만족하는 글을 찾는다.
pk=7 인 글은 공개가 아니라 조건에 맞지 않으므로 그 자리에서 404 응답이 된다.
그 아래 `view_count += 1` · `save(...)` 줄에는 닿지 않으므로 조회수는 바뀌지 않는다.

**왜 그런가**
`get_object_or_404` 는 `DoesNotExist` 예외 대신 404 를 돌려주고, 추가 조건 불일치도 「없음」과 같이 다룬다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 2」.

### 2. 맨 아래 `render` 에 닿아 오류가 담긴 작성 폼이 다시 보인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`request.method == 'POST'` 이므로 `form = PostForm(request.POST)` 를 만든다.
`form.is_valid()` 가 `False` 라 `redirect` 가 있는 블록에 들어가지 않는다.
`else` 는 GET 일 때만이므로 건너뛰고, 맨 아래 `return render(request, 'blog/post_form.html', {'form': form})` 에 닿는다.
사용자는 리다이렉트 없이 같은 작성 화면을, 입력값과 검증 오류가 담긴 폼으로 다시 본다.

**왜 그런가**
검증 실패 경로는 따로 `return` 이 없고, 받은 폼을 그대로 맨 아래 `render` 에 넘기는 구조다.
근거: 2-summary 「동작 방식 (3)」 그림의 「POST & 검증 실패」 줄.

### 3. `object_list`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
템플릿에서 목록을 `posts` 로 부를 수 없게 되고 `object_list` 로 꺼내야 한다.

**왜 그런가**
원본 주석이 `context_object_name = 'posts'  # 기본: object_list` 라고 적어 두었다 — 이 속성은 기본 이름을 바꾸는 설정일 뿐이다.
근거: 2-summary 「동작 방식 (4)」 · 「문법 — 형태와 규칙」.

### 4. `@login_required` 의 거절 — 로그인 페이지로 보내진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
미로그인 `PUT` 요청은 메서드 검사에 닿기 전에 로그인 페이지로 리다이렉트된다.

**왜 그런가**
파이썬은 데코레이터를 아래부터 감싼다 — `require_http_methods` 가 먼저 `post_create` 를 감싸고, 그 결과를 `login_required` 가 다시 감싼다.
요청이 들어오면 가장 바깥 껍질인 `login_required` 가 먼저 돌아 미로그인을 걸러 내므로 안쪽의 메서드 검사는 실행되지 않는다.
원본 주석 「위에서부터 적용」은 이 실행 순서로 읽으면 맞는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 9」 (원본에 근거 없음 — 추론).

### 5. PRG — 새로고침이 POST 를 다시 보내 중복 저장되는 것을 막는다

저장 성공 뒤 그 자리에서 `render` 로 그리면 브라우저의 마지막 요청은 POST 로 남는다.
사용자가 새로고침하면 같은 POST 가 다시 가서 같은 글이 또 저장될 수 있다.
`redirect` 로 상세 주소(GET)로 보내면 마지막 요청이 GET 이 되어 새로고침해도 다시 읽기만 한다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 8」.

### 6. 클래스를 정의할 때는 URLconf 가 아직 준비되지 않았을 수 있어서

`success_url` 은 클래스 속성이라 모듈을 읽는 순간 값이 계산된다.
그 시점에는 URLconf 가 아직 준비되지 않았을 수 있어 이름으로 주소를 만드는 즉시 계산이 실패할 수 있다.
`reverse_lazy` 는 「나중에 계산할 약속」만 저장해 두고 실제로 쓰일 때(요청 처리 중) 주소를 계산한다.
근거: 2-summary 「동작 방식 (8)」 · 「어디서 틀리나 7」.

### 7. `get_queryset` 이 자기 글만 남겨, 남의 글은 찾지 못해 404 가 된다

A 는 로그인했으므로 `LoginRequiredMixin` 은 통과한다.
`PostUpdateView.get_queryset` 은 `author=self.request.user.author_profile` 로 A 의 글만 남긴다.
주소의 `pk` 로 수정할 글을 이 좁힌 QuerySet 에서 찾으므로 B 의 글은 보이지 않고 404 가 된다.
「403 금지」가 아니라 「그런 글 없음」으로 응답하는 셈이다.
근거: 2-summary 「동작 방식 (5)」 (원본은 「자신의 글만 수정 가능 (객체 수준 권한)」까지만 적었고, 404 라는 결과는 원본에 근거 없음 — 추론).

### 8. `create` 는 `int` 로 바뀌지 않아 상세 패턴에 맞지 않는다 / `/posts/abc/` 는 어느 패턴에도 맞지 않는다

`<int:pk>` 는 그 자리의 글자를 정수로 바꿀 수 있을 때만 맞는다.
`create` 는 정수가 아니라 `posts/<int:pk>/` 가 맞지 않고, 다음 패턴들로 넘어가 `posts/create/` 에 맞는다.
그래서 적힌 순서와 관계없이 두 주소가 부딪치지 않는다.
`/posts/abc/` 도 정수가 아니므로 상세 · 수정 · 삭제 패턴에 맞지 않고, 글자 그대로의 `posts/create/` 와도 다르다.
맞는 패턴이 없으니 404 가 되고, 전역 404 핸들러(`custom_404`)가 그 화면을 그린다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (7)」 (`/posts/abc/` 가 `custom_404` 로 가는 부분은 원본에 근거 없음 — 추론).

### 9. FBV 는 데코레이터(함수를 감싸기), CBV 는 다중 상속(Mixin 을 맨 왼쪽에)

`@login_required` 는 함수 위에 붙는 데코레이터로, 함수를 감싸 미로그인 요청이 본문에 닿지 못하게 한다.
`LoginRequiredMixin` 은 클래스를 다중 상속에 섞어 넣는 방식이며, 왼쪽 클래스가 먼저 적용되므로 맨 왼쪽에 둔다.
팁이 말하듯 CBV 에서는 `@login_required` 대신 Mixin 을 쓴다 — 같은 「인증 필수」를 함수 세계와 클래스 세계의 조합 도구로 각각 푼 것이다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (5)」 · 「어디서 틀리나 4」.

### 10. 목록 질의 1번 + 글마다 작성자 질의 1번씩 — N+1 이 된다

`select_related` 가 없으면 목록 질의는 글만 가져온다.
템플릿이 글마다 작성자를 읽을 때 그 글의 작성자를 따로 질의하므로, 한 페이지 10개면 1 + 10 번이 된다.
`select_related('author', 'category')` 는 처음 질의에서 JOIN 으로 함께 가져와 이를 막는다.
팁은 같은 목적으로 `prefetch_related` 도 든다.
근거: 2-summary 「동작 방식 (8)」 아래 N+1 설명 · 「어디서 틀리나 3」.

## 실습 정답

### 실습 1. 블로그 뷰 한 벌 — FBV · 제네릭 CBV · API · 에러 핸들러 · URLconf

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 공개 글 + JOIN | `post_list` 의 `Post.objects.filter(status='PB').select_related('author', 'category')` |
| 2. 페이지네이션 · 컨텍스트 | `Paginator(posts, 10)` · `request.GET.get('page', 1)` · `paginator.get_page(...)` · `'page_obj'` · `'total_count': paginator.count` |
| 3. 없으면 404 | `post_detail` 의 `get_object_or_404(Post, pk=pk, status='PB')` |
| 4. 조회수 갱신 | `post.view_count += 1` · `post.save(update_fields=['view_count'])` |
| 5. 로그인 · 메서드 제한 | `@login_required` · `@require_http_methods(['GET', 'POST'])` |
| 6. 저장 · 리다이렉트 | `form.save(commit=False)` · `post.author = request.user.author_profile` · `post.save()` · `form.save_m2m()` · `redirect('post-detail', pk=post.pk)` |
| 7. 빈 폼 / 실패 폼 렌더 | `else: form = PostForm()` · 맨 아래 `render(request, 'blog/post_form.html', {'form': form})` |
| 8. JSON 목록 | `api_posts` 의 `.values('id', 'title', 'created_at')` · `JsonResponse(list(posts), safe=False)` |
| 9. 홈 + 최신 5개 | `HomeView.get_context_data` 의 `context['latest_posts'] = ...[:5]` |
| 10. 목록 이름 · 페이지 | `PostListView` 의 `context_object_name = 'posts'` · `paginate_by = 10` |
| 11. 검색 · JOIN | `PostListView.get_queryset` 의 `filter(status='PB')` · `self.request.GET.get('q')` · `title__icontains` · `select_related(...)` |
| 12. 상세 CBV | `PostDetailView` 의 `context_object_name = 'post'` · `get_queryset` |
| 13. 작성 CBV 인증 | `class PostCreateView(LoginRequiredMixin, CreateView)` · `fields = [...]` · `login_url = '/accounts/login/'` |
| 14. 작성자 주입 · 이동 | `form_valid` 의 `form.instance.author = ...` · `get_success_url` 의 `reverse_lazy('post-detail', kwargs={'pk': self.object.pk})` |
| 15. 자기 글만 수정 | `PostUpdateView.get_queryset` 의 `filter(author=self.request.user.author_profile)` |
| 16. 삭제 후 이동 | `PostDeleteView` 의 `success_url = reverse_lazy('post-list')` |
| 17. API GET | `PostAPIView.get` 의 `.values('id', 'title')` · `JsonResponse(..., safe=False)` |
| 18. API POST | `PostAPIView.post` 의 `json.loads(request.body)` · `JsonResponse({'status': 'created'}, status=201)` |
| 19. 핸들러 등록 | `handler404 = 'blog.views.custom_404'` · `handler500 = 'blog.views.custom_500'` |
| 20. 핸들러 함수 | `custom_404(request, exception)` · `custom_500(request)` · `render(..., status=...)` |
| 21. URLconf | `urlpatterns` 의 일곱 `path(...)` · `<int:pk>` · `.as_view()` · `name=...` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web/reference/django-views.py`

```python
# [웹 프레임워크] Django Views (뷰 처리)
# 설명: FBV(함수 기반), CBV(클래스 기반), generic views, 리다이렉트, 에러 처리
# 팁: FBV는 간단한 뷰에, CBV는 CRUD 패턴에 적합하다. get_object_or_404는 DoesNotExist 예외 대신 404를 반환한다. select_related/prefetch_related로 N+1 쿼리 문제를 방지한다. LoginRequiredMixin은 CBV에서 @login_required 대신 사용한다.

# Django Views - FBV, CBV, Generic Views

# === 1. FBV (함수 기반 뷰) ===
# render: 템플릿 렌더링 헬퍼 / get_object_or_404: 없으면 404 / redirect: HTTP 302
from django.shortcuts import render, get_object_or_404, redirect
# HTTP 응답 객체들 / Http404: 명시적 404 예외
from django.http import HttpResponse, JsonResponse, Http404
# login_required: 미인증 시 로그인 페이지로 리다이렉트하는 데코레이터
from django.contrib.auth.decorators import login_required
# require_http_methods: 허용 메서드 화이트리스트
from django.views.decorators.http import require_http_methods
# Paginator: 페이지네이션 유틸 클래스
from django.core.paginator import Paginator


# Django는 WSGI 기반 - request 객체를 받아 HttpResponse를 반환하는 콜러블이 뷰
def post_list(request):
    """게시글 목록 - 기본 FBV"""
    # select_related로 JOIN 미리 수행 (N+1 방지)
    posts = Post.objects.filter(status='PB').select_related('author', 'category')

    # 페이지네이션
    # Paginator(객체리스트, 페이지당개수)
    paginator = Paginator(posts, 10)  # 페이지당 10개
    # GET 쿼리 파라미터에서 page 번호 읽기
    page_number = request.GET.get('page', 1)
    # get_page: 잘못된 번호도 안전하게 처리
    page_obj = paginator.get_page(page_number)

    # render(request, 템플릿경로, 컨텍스트딕셔너리)
    return render(request, 'blog/post_list.html', {
        'page_obj': page_obj,
        'total_count': paginator.count,
    })


def post_detail(request, pk):
    """게시글 상세 - get_object_or_404 사용"""
    # 추가 조건과 함께 객체 조회 (조건 불일치도 404)
    post = get_object_or_404(Post, pk=pk, status='PB')
    post.view_count += 1
    # update_fields로 view_count 컬럼만 갱신
    post.save(update_fields=['view_count'])
    return render(request, 'blog/post_detail.html', {'post': post})


# 데코레이터 스택: 위에서부터 적용
@login_required                          # 로그인 필수 데코레이터
@require_http_methods(['GET', 'POST'])   # 허용 메서드 제한
def post_create(request):
    """게시글 작성 - POST 처리"""
    if request.method == 'POST':
        # POST 데이터로 폼 인스턴스 생성
        form = PostForm(request.POST)
        if form.is_valid():
            # commit=False: DB 저장 전에 추가 필드 설정
            post = form.save(commit=False)
            post.author = request.user.author_profile
            post.save()
            # M2M은 commit=False 시 별도 저장 필요
            form.save_m2m()  # ManyToMany 저장
            # PRG 패턴 (POST-Redirect-GET)
            return redirect('post-detail', pk=post.pk)  # 리다이렉트
    else:
        form = PostForm()
    return render(request, 'blog/post_form.html', {'form': form})


def api_posts(request):
    """JSON 응답 뷰"""
    # values(): dict 형태 QuerySet
    posts = Post.objects.filter(status='PB').values('id', 'title', 'created_at')
    # JsonResponse: JSON 직렬화 응답 (safe=False는 list 직렬화 허용)
    return JsonResponse(list(posts), safe=False)


# === 2. CBV (클래스 기반 뷰) ===
# View: CBV의 베이스 클래스
from django.views import View
# Generic Views: 공통 패턴(CRUD)을 추상화한 클래스들
from django.views.generic import (
    TemplateView, ListView, DetailView,
    CreateView, UpdateView, DeleteView
)
# Mixin: 다중 상속으로 기능 조합 (LoginRequiredMixin = 인증 필수)
from django.contrib.auth.mixins import LoginRequiredMixin
# reverse_lazy: URL을 지연 평가 (클래스 정의 시점엔 URL conf 미준비)
from django.urls import reverse_lazy


# TemplateView: 단순 템플릿 렌더링 전용
class HomeView(TemplateView):
    """단순 템플릿 렌더링"""
    template_name = 'blog/home.html'

    # get_context_data: 템플릿에 추가 컨텍스트 주입
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_posts'] = Post.objects.filter(status='PB')[:5]
        return context


# ListView: 목록 표시 + 페이지네이션 자동
class PostListView(ListView):
    """게시글 목록 - ListView"""
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'       # 기본: object_list
    # 페이지당 개수 - 자동 페이지네이션
    paginate_by = 10

    # get_queryset 오버라이드로 동적 필터링
    def get_queryset(self):
        qs = super().get_queryset().filter(status='PB')
        # 검색 기능
        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(title__icontains=search)
        return qs.select_related('author', 'category')


# DetailView: 단일 객체 상세
class PostDetailView(DetailView):
    """게시글 상세 - DetailView"""
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return super().get_queryset().filter(status='PB')


# CreateView: 폼 표시 + 저장
# Mixin은 왼쪽부터 우선 적용 (LoginRequiredMixin이 먼저)
class PostCreateView(LoginRequiredMixin, CreateView):
    """게시글 작성 - CreateView"""
    model = Post
    fields = ['title', 'content', 'category', 'tags', 'status']
    template_name = 'blog/post_form.html'
    login_url = '/accounts/login/'       # 미로그인 시 이동 URL

    # form_valid: 검증 통과 시 호출, 저장 직전 추가 처리
    def form_valid(self, form):
        # 작성자 자동 주입
        form.instance.author = self.request.user.author_profile
        return super().form_valid(form)

    # 저장 후 이동할 URL
    def get_success_url(self):
        return reverse_lazy('post-detail', kwargs={'pk': self.object.pk})


# UpdateView: 기존 객체 수정 폼
class PostUpdateView(LoginRequiredMixin, UpdateView):
    """게시글 수정 - UpdateView"""
    model = Post
    fields = ['title', 'content', 'category', 'tags', 'status']
    template_name = 'blog/post_form.html'

    def get_queryset(self):
        # 자신의 글만 수정 가능 (객체 수준 권한)
        return super().get_queryset().filter(
            author=self.request.user.author_profile
        )


# DeleteView: 삭제 확인 페이지 + 삭제
class PostDeleteView(LoginRequiredMixin, DeleteView):
    """게시글 삭제 - DeleteView"""
    model = Post
    template_name = 'blog/post_confirm_delete.html'
    # 삭제 후 이동할 URL (lazy로 정의)
    success_url = reverse_lazy('post-list')


# === 3. 커스텀 CBV ===
# View 직접 상속 후 HTTP 메서드 이름의 메서드 정의
class PostAPIView(View):
    """직접 구현하는 CBV API"""
    # GET 처리
    def get(self, request):
        posts = Post.objects.filter(status='PB').values('id', 'title')
        return JsonResponse(list(posts), safe=False)

    # POST 처리
    def post(self, request):
        import json
        # request.body: 원본 바이트 본문
        data = json.loads(request.body)
        # 처리 로직...
        return JsonResponse({'status': 'created'}, status=201)


# === 4. 에러 핸들링 뷰 ===
# urls.py에 등록 (전역 핸들러)
handler404 = 'blog.views.custom_404'
handler500 = 'blog.views.custom_500'

# 404 핸들러는 exception 인자를 추가로 받음
def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)

def custom_500(request):
    return render(request, 'errors/500.html', status=500)


# === 5. urls.py ===
# path: URL 패턴과 뷰 매핑
from django.urls import path

urlpatterns = [
    # CBV는 .as_view()로 콜러블로 변환
    path('', HomeView.as_view(), name='home'),
    path('posts/', PostListView.as_view(), name='post-list'),
    # <int:pk>: int 컨버터로 캡처된 값을 뷰 인자로 전달
    path('posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('posts/create/', PostCreateView.as_view(), name='post-create'),
    path('posts/<int:pk>/edit/', PostUpdateView.as_view(), name='post-update'),
    path('posts/<int:pk>/delete/', PostDeleteView.as_view(), name='post-delete'),
    path('api/posts/', PostAPIView.as_view(), name='api-posts'),
]

print("Django Views 핵심 정리")
print("="*50)
print("FBV: 단순, 명시적, 데코레이터로 기능 추가")
print("CBV: 재사용성, 상속, Mixin으로 기능 조합")
print("Generic Views: ListView, DetailView, CreateView 등")
print("LoginRequiredMixin / @login_required: 인증 필수")
print("get_object_or_404: 없으면 자동 404 응답")
print("redirect(): URL이름 또는 경로로 리다이렉트")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `django` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**
- FBV 는 함수 하나에 흐름을 다 적고, 기능은 데코레이터로 덧붙인다 — 인증이 바깥 껍질이 되도록 `@login_required` 를 위에 둔다.
- `commit=False` 로 저장을 미뤘으면 `save()` 뒤 `save_m2m()` 까지 불러야 태그가 저장된다.
- 제네릭 CBV 는 클래스 속성으로 설정하고 `get_queryset` · `get_context_data` · `form_valid` · `get_success_url` 만 덮어쓴 뒤 `super()` 에 맡긴다.
- `LoginRequiredMixin` 은 맨 왼쪽, 클래스 속성의 URL 은 `reverse_lazy`.
- 「자기 글만」 권한은 `get_queryset` 을 좁혀 남의 글을 아예 찾지 못하게 만드는 방식이다.
- 404 핸들러만 `exception` 인자를 받고, 핸들러는 상태 코드를 직접 적는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `django` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
