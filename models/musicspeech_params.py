import numpy as np
from dataclasses import dataclass, field
from typing import List

@dataclass
class MusicSpeech_Params:
    
    sample_rate: float = 22050.0
    
    # pós-processing
    
    min_speech: float = 1.3 
    min_music: float = 3.4 
    max_silence_speech: float = 0.4 
    max_silence_music: float = 0.6 
    audio_clip_length: float = 8.0
    
    # Model
    model_weights_file: str = 'model d-DS.h5'
    
    batch_size: int = 32