import urllib.request
import os

def download_piper_model():
    base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/tr/tr_TR/dfki/medium"
    files = ["tr_TR-dfki-medium.onnx", "tr_TR-dfki-medium.onnx.json"]
    target_dir = r"E:\Project"

    for file in files:
        url = f"{base}/{file}"
        dest = os.path.join(target_dir, file)
        print(f"Indiriliyor: {file}...")
        urllib.request.urlretrieve(url, dest)
        size = os.path.getsize(dest) / 1024 / 1024
        print(f"Tamamlandi: {size:.1f} MB")

if __name__ == "__main__":
    download_piper_model()


