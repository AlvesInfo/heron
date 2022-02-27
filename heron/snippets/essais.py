from django.utils.encoding import force_text, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

for_uid = force_bytes(urlsafe_base64_encode(b"9d59795e-8d86-4c74-9ac1-7ac72acf0daa"))
print(for_uid)

uid = force_text(urlsafe_base64_decode(force_text(for_uid)))
print(uid)

