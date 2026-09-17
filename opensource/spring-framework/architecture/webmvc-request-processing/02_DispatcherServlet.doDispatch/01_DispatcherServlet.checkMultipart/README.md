# DispatcherServlet.checkMultipart

상위: [DispatcherServlet.doDispatch](../README.md)

요청이 multipart(파일 업로드)면 `MultipartResolver`로 파싱해 `MultipartHttpServletRequest`로 감싼 요청을 돌려준다. 아니면 원래 요청을 그대로 돌려준다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet` / `DispatcherServlet.java` L1089-L1117 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/DispatcherServlet.java#L1089-L1117))

```java
// DispatcherServlet.java L1089-L1117
protected HttpServletRequest checkMultipart(HttpServletRequest request) throws MultipartException {
    if (this.multipartResolver != null && this.multipartResolver.isMultipart(request)) {
        if (WebUtils.getNativeRequest(request, MultipartHttpServletRequest.class) != null) {
            if (DispatcherType.REQUEST.equals(request.getDispatcherType())) {
                logger.trace("Request already resolved to MultipartHttpServletRequest, for example, by MultipartFilter");
            }
        }
        else if (hasMultipartException(request)) {
            logger.debug("Multipart resolution previously failed for current request - " +
                    "skipping re-resolution for undisturbed error rendering");
        }
        else {
            try {
                return this.multipartResolver.resolveMultipart(request);
            }
            catch (MultipartException ex) {
                if (request.getAttribute(WebUtils.ERROR_EXCEPTION_ATTRIBUTE) != null) {
                    logger.debug("Multipart resolution failed for error dispatch", ex);
                    // Keep processing error dispatch with regular request handle below
                }
                else {
                    throw ex;
                }
            }
        }
    }
    // If not returned before: return original request.
    return request;
}
```

## 동작 흐름

```text
 checkMultipart(request)
 |
 +-- multipartResolver 없음, 또는 isMultipart(request) == false
 |       --> return request                          (대부분의 요청)
 |
 +-- 이미 MultipartHttpServletRequest로 감싸져 있음   (MultipartFilter가 먼저 처리)
 |       --> 로그만, return request
 |
 +-- 이전 시도에서 MultipartException이 났던 오류 디스패치
 |       --> 다시 파싱하지 않음, return request      (오류 페이지 렌더링을 방해하지 않기 위해)
 |
 +-- 그 밖
         --> multipartResolver.resolveMultipart(request)
               성공 --> return 감싼 요청
               실패 --> 오류 디스패치 중이면 삼키고 원래 요청
                        아니면 MultipartException 던짐 --> doDispatch의 dispatchException
```

## 결과가 쓰이는 곳

```text
 반환값 processedRequest
      |
      +-- doDispatch L948  processedRequest != request 이면 multipartRequestParsed = true
      |                      --> finally에서 cleanupMultipart()로 임시 파일 삭제
      |
      +-- 이후 모든 단계의 요청 객체
              --> @RequestParam MultipartFile / @RequestPart 인자 해석이
                  MultipartHttpServletRequest.getFile()로 파일을 꺼냄
```
