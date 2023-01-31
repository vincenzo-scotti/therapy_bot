# Models

This directory is used to host the pre-trained models (TTS and vocoder).
All credits to the original authors and contributors that trained the models (see links below).

- Speech recognition:
  - [Whisper](https://arxiv.org/abs/2212.04356)
- Speech synthesis:
  - Spectrogram generation:
    - [Mellotron](https://doi.org/10.1109/ICASSP40776.2020.9054556):
      - Trained on [LibriTTS](https://openslr.org/60/) ([weights checkpoint](https://drive.google.com/open?id=1ZesPPyRRKloltRIuRnGZ2LIUEuMSVjkI))
    - [Tacotron 2](https://doi.org/10.1109/ICASSP.2018.8461368) ([weights checkpoint](https://drive.google.com/file/d/1c5ZTuT7J08wLUoVZ2KkUs_VdZuJ86ZqA/view?usp=sharing))
  - Vocoder:
    - [WaveGlow](https://doi.org/10.1109/ICASSP.2019.8683143) ([weights checkpoint](https://drive.google.com/open?id=1okuUstGoBe_qZ4qUEF8CcwEugHP7GM_b))
  - GST Prediction:
    - [DGST]():
      - Using Therapy-DLDLM response embeddings computed from context ([weights checkpoint](https://polimi365-my.sharepoint.com/:u:/g/personal/10451445_polimi_it/EYvTr-aD0glErLSBhKf1J18BgetFIAhC_MO1iugkFHwrhg?e=2ReQdb))
- Dialogue Language models:
  - [Therapy-DLDLM](): ([weights and configs checkpoint](https://polimi365-my.sharepoint.com/:u:/g/personal/10451445_polimi_it/EQ7PspwlveNPnXsB4Bl7T2wBxpa6SGVS3hTaBAEvFatTWA?e=qC8CxS))
  - [PPM-DLM](): ([weights and configs checkpoint](https://polimi365-my.sharepoint.com/:u:/g/personal/10451445_polimi_it/Efr1JtJNCARPuLRZXzDz04MBzl-hghON_FFwahi-lxEZBA?e=K1JoNi))
  
Please refer to the original repositories for further details:
- [Whisper](https://github.com/openai/whisper) (by [OpenAI](https://openai.com))
- [Mellotorn](https://github.com/NVIDIA/mellotron) (by [NVIDIA](https://www.nvidia.com));
- [Waveglow](https://github.com/NVIDIA/waveglow) (by [NVIDIA](https://www.nvidia.com));
- [Tacotron 2](https://github.com/NVIDIA/tacotron2) (by [NVIDIA](https://www.nvidia.com));
- [DGST](https://github.com/vincenzo-scotti/dialoguegst) (by [Vincenzo Scotti](https://www.linkedin.com/in/vincenzoscotti95));
- [Therapy-DLDLM](https://github.com/vincenzo-scotti/dldlm) (by [Vincenzo Scotti](https://www.linkedin.com/in/vincenzoscotti95));
- [PPM-DLM](https://github.com/vincenzo-scotti/programmable_chatbot) (by [Vincenzo Scotti](https://www.linkedin.com/in/vincenzoscotti95)).

For simplicity, we provide a separate zip file with all the model checkpoints ([link]()).

Directory structure:
```
 |- models/
    |- tts/
      |- mellotron/
        |- mellotron_libritts.pt
      |- tacotron_2/
        |- tacotron2_statedict.pt
    |- dgst/
      |- dgst_therapy_dldlm_from_ctx.pt
    |- vocoder/
      |- waveglow/
        |- waveglow_256channels_universal_v4.pt
    |- lm/
      |- therapy_dldlm/
        |- added_tokens.json
        |- config.json
        |- merges.txt
        |- pytorch_model.bin
        |- special_tokens_map.json
        |- tokenizer_config.json
        |- vocab.json
      |- ppm_dlm/
        |- config.json
        |- pytorch_model.bin
```