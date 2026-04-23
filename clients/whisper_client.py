# -*- coding: utf-8 -*-
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import warnings
warnings.filterwarnings("ignore")

import torch
import numpy as np
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline


class WhisperClient:
    def __init__(self, model_id="openai/whisper-large-v3"):
        self.model_id = model_id
        self.pipe = None
        self._load()

    def _load(self):
        print(f"Whisper yukleniyor: {self.model_id}")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device == "cuda" else torch.float32

        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            self.model_id, torch_dtype=dtype,
            low_cpu_mem_usage=True, use_safetensors=True,
        ).to(device)

        processor = AutoProcessor.from_pretrained(self.model_id)

        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            torch_dtype=dtype,
            device=device,
        )
        print(f"Whisper hazir! ({device})")

    def transcribe(self, audio, language="turkish"):
        result = self.pipe(audio, generate_kwargs={"language": language, "task": "transcribe"})
        return result["text"].strip()
