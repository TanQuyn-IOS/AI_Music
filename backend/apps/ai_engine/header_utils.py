import re
from urllib.parse import quote


def safe_header_val(val) -> str:
    """
    Đảm bảo giá trị HTTP header luôn an toàn với chuẩn PEP 3333 / WSGI Latin-1.
    Nếu chứa ký tự ngoài phạm vi Latin-1 (như tiếng Việt: Đ, ơ, ư, ễ, ệ...), 
    giá trị sẽ được URL-encode bằng urllib.parse.quote.
    """
    if val is None:
        return ""
    val_str = str(val).strip()
    try:
        val_str.encode("latin-1")
        return val_str
    except UnicodeEncodeError:
        return quote(val_str)


def safe_content_disposition(filename: str, disposition: str = "inline") -> str:
    """
    Tạo Content-Disposition header tuân thủ RFC 5987 và RFC 6266.
    Có fallback filename an toàn ASCII và filename* UTF-8.
    """
    if not filename:
        filename = "audio.mp3"
    # Lọc các ký tự không an toàn cho filename ascii
    ascii_name = re.sub(r'[^\w\.\-]', '_', filename)
    encoded_name = quote(filename)
    return f'{disposition}; filename="{ascii_name}"; filename*=UTF-8\'\'{encoded_name}'
