import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clients.ollama_client import OllamaClient


def test_ollama_available():
    client = OllamaClient()
    assert client.is_available(), "Ollama calismiyor!"

def test_ollama_chat():
    client = OllamaClient()
    if not client.is_available():
        print("Ollama mevcut degil, test atlandi.")
        return
    response = client.chat([
        {"role": "user", "content": "Merhaba, sadece 'Merhaba!' diye cevap ver."}
    ])
    assert response is not None
    assert len(response) > 0
    print(f"Ollama yaniti: {response}")

if __name__ == "__main__":
    test_ollama_available()
    test_ollama_chat()
    print("Tum testler gecti!")
