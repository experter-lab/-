import cv2
print("cv2 version:", cv2.__version__)
print("has wechat_qrcode submodule:", hasattr(cv2, "wechat_qrcode"))
if hasattr(cv2, "wechat_qrcode"):
    print("has WeChatQRCode class:", hasattr(cv2.wechat_qrcode, "WeChatQRCode"))
# Try construct without model files (should fail with informative error if module works)
try:
    detector = cv2.wechat_qrcode.WeChatQRCode()
    print("default constructor OK:", detector)
except Exception as e:
    print("default constructor exception (expected):", repr(e))
