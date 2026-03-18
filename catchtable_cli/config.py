from pydantic_settings import BaseSettings


class CatchTableConfig(BaseSettings):
    model_config = {"env_prefix": "CT_"}

    api_base_url: str = "https://ct-api.catchtable.co.kr"
    session_cookie: str = ""  # x-ct-a 쿠키 값 (브라우저 로그인 후 획득)
    use_curl_cffi: bool = True
