import torch
from transformers import GPT2Model, GPT2LMHeadModel, GPT2Tokenizer
from dialoguegst.model import DGST
from programmable_chatbot.chatbot_api import Chatbot as PPMDLMChatbot
from dialoguegst.speech_api import ChatSpeechGenerator
import whisper
from mellotron_api import load_tts, load_vocoder, load_arpabet_dict


from typing import List, Dict, Optional


class Chatbot:
    def __int__(
            self,
            self_speaker_id: str = 'AI',
            other_speaker_id: str = 'User',
            asr: Optional[Dict] = None,
            tts: Optional[Dict] = None,
            vocoder: Optional[Dict] = None,
            dgst: Optional[Dict] = None,
            dlm: Optional[Dict] = None
    ):
        # Load neural network models and modules
        # ASR
        if asr is not None and 'whisper' in asr:
            self.whisper = whisper.load_model(asr['whisper'])
        else:
            self.whisper = None
        # TTS
        if tts is not None:
            if 'mellotron' in tts:
                self.mellotron, self.mellotron_stft, self.mellotron_hparams = load_tts(tts['mellotron'])
            else:
                self.mellotron = self.mellotron_stft = self.mellotron_hparams = None
            if 'tacotron2' in tts:
                self.tacotron2, self.tacotron2_stft, self.tacotron2_hparams = load_tts(tts['tacotron2'], model='tacotron2')
            else:
                self.tacotron2 = self.tacotron2_stft = self.tacotron2_hparams = None
            if 'arpabet_dict' in tts:
                self.arpabet_dict = load_arpabet_dict(tts['arpabet_dict'])
            else:
                self.arpabet_dict = None
        else:
            self.mellotron = self.mellotron_stft = self.mellotron_hparams = None
            self.tacotron2 = self.tacotron2_stft = self.tacotron2_hparams = None
            self.arpabet_dict = None
        # Vocoder
        if vocoder is not None and 'waveglow' in vocoder:
            self.waveglow, self.denoiser = load_vocoder(vocoder['waveglow'])
        else:
            self.waveglow = self.denoiser = None
        # Dialogue GST
        if dgst is not None:
            if 'dldlm' in dgst:
                self.therapy_dldlm_tokenizer: GPT2Tokenizer = GPT2Tokenizer.from_pretrained(dgst['dldlm']['tokenizer']).eval()
                self.therapy_dldlm: GPT2Model = GPT2Model.from_pretrained(dgst['dldlm']['model']).eval()
            else:
                self.therapy_dldlm_tokenizer = self.therapy_dldlm = None
            if 'gst_predictor' in dgst and self.therapy_dldlm is not None and self.mellotron is not None:
                self.dgst = DGST(
                    self.therapy_dldlm.config,
                    self.mellotron.gst.stl.attention.num_units,
                    (self.mellotron.gst.stl.attention.num_heads, self.mellotron.gst.stl.embed.size(0))
                )
                self.dgst.load_state_dict(torch.load(dgst['gst_predictor']))
            else:
                self.dgst = None
        else:
            self.dgst = self.therapy_dldlm_tokenizer = self.therapy_dldlm = None
        # LM
        if dlm is not None and 'ppm_dlm' in dlm:
            self.ppm_dlm_tokenizer: GPT2Tokenizer = GPT2Tokenizer.from_pretrained(dlm['ppm_dlm']['tokenizer'])
            self.ppm_dlm: GPT2LMHeadModel = GPT2LMHeadModel.from_pretrained(dlm['ppm_dlm']['model'])
        else:
            self.ppm_dlm_tokenizer = self.ppm_dlm = None
        # Load wrapper for text Chatbot and TTS modules
        # APIs
        if self.ppm_dlm_tokenizer is not None and self.ppm_dlm is not None:
            self.chatbot: PPMDLMChatbot = PPMDLMChatbot(
                self.ppm_dlm, self.ppm_dlm_tokenizer, **dlm.get('module_params', dict())
            )
        else:
            self.chatbot = None
        if self.dgst is not None and self.therapy_dldlm_tokenizer is not None and self.therapy_dldlm:
            self.expressive_speech_generator: ChatSpeechGenerator = ChatSpeechGenerator(
                self.dgst,
                self.therapy_dldlm_tokenizer,
                self.therapy_dldlm,
                mellotron=(self.mellotron, self.mellotron_stft, self.mellotron_hparams),
                tacotron2=(self.tacotron2, self.tacotron2_stft, self.tacotron2_hparams),
                vocoder=(self.waveglow, self.denoiser),
                arpabet_dict=self.arpabet_dict,
                **dgst.get('module_params', dict())
            )
        else:
            self.expressive_speech_generator = None

        # Additional parameters for text and speech generation
        self.self_speaker_id = self_speaker_id
        self.other_speaker_id = other_speaker_id
        if dlm is not None and 'generator_params' in dlm:
            self.task = dlm['generator_params'].get('task')
            self.global_label = dlm['generator_params'].get('global_label')
            self.generate_kwargs = dlm['generator_params'].get('generate_kwargs', dict())
        else:
            self.task = self.global_label = None
            self.generate_kwargs = dict()
        self.prompt = f'{self.self_speaker_id}:' if len(self.self_speaker_id) > 0 else ''
        if dgst is not None and 'generator_params' in dgst:
            self.gst_prediction_approach = dgst['generator_params'].get('gst_prediction_approach')
            self.tts_speaker_id = dgst['generator_params'].get('tts_speaker_id')

    def __call__(self, *args, **kwargs):
        return self.generate_response(*args, **kwargs)

    def generate_response(
            self,
            context: List[Dict[str, str]]
    ) -> str:
        if self.chatbot is not None:
            context = [f"{utterance['speaker']}: {utterance['text']}\n" for utterance in context]
            response = self.chatbot(
                context,
                prompt=self.prompt,
                task_description=self.task,
                global_labels=self.global_label,
                **self.generate_kwargs
            )
        else:
            raise ValueError("Text module is not enabled in the current configuration.")

        return response

    def transcribe_message(self, audio_file_path: str) -> str:
        if self.whisper is not None:
            # Use OpenAI Whisper to generate the transcription
            result = self.whisper.transcribe(audio_file_path)
            return result['text']
        else:
            raise ValueError("Speech recognition module is not enabled in the current configuration.")

    def read_response(
            self,
            audio_file_path: str,
            response: Dict[str, str],
            context: Optional[List[Dict[str, str]]] = None
    ):
        if self.expressive_speech_generator is not None:
            # If Speech generator is available generate response
            self.expressive_speech_generator.generate_speech_response(
                response['text'],
                audio_file_path,
                dialogue=[turn['text'] for turn in context] if context is not None and len(context) > 0 else None,
                gst_prediction=self.gst_prediction_approach,
                speaker_id=self.tts_speaker_id
            )
        else:
            raise ValueError("Speech synthesis module is not enabled in the current configuration.")
