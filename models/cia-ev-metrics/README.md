# ECAD - CIA-EV - METRICS

###Run Locally
uvicorn main:app --reload --port 3003

O CIA-EV Metrics tem por objetivo avaliar o desempenho do CIA-EV através de uma comparação 
entre as marcações manuais auditadas e as obtidas com o sistema automático.
```
IMPORTANTE: 

Obs 1: somente devem ser utilizados na comparação, segmentos de hypothesis com 
códigos de obras diferentes “0”. O segmentador apresenta uma lista de segmentos 
composta por obras identificadas e “0” quando não há música identificada. 

Obs 2: Os tempos de cada segmento da referência e hipótese são relativos ao início do 
arquivo de áudio.
```

As medidas fornecidas são:

1) TP -- número de matches por segmento de referência. Pode haver mais de um match dentro do segmento de uma anotação de referência;

2) FN -- número de vezes que o sistema não identifica uma anotação. 

3) FP -- número de vezes que o sistema identifica uma música quando não há anotações de referência no segmento. 
   
5) DAP (Detected annotation percentage) -- número de matches dividido pelo nr de anotações de referência. Só pode haver um match por segmento de anotação de referência. A diferença entre TP e DAP é que aquele conta todos os matches dentro de um segmento da anotação e este conta um match por segmento.

6) DLP (Detected Length Percentage) -- razão entre o tempo do match e o tempo da anotação.

![dlp_eq](images/dlp_eq.png)

7) Purity: é uma medida dual da DLP, indica a pureza de um segmento da hipótese em relação a referência.

![purity_eq](images/purity_eq.png)

onde |r| (respectivamente |h|) é a duração do segmento de referência específico (resp. hipótese) 
e |r ∩ h| é a duração de sua interseção.

- A API do CIA-EV-Metrics é baseada em Flask e Docker. Ele faz parte do repositório do CIA-EV. 
  E utiliza o docker-compose geral do projeto.
  
- A estrutura do projecto está descrita na arvore de pastas em baixo.

```
    ├── Pasta/
    │   ├── CIA-EV/  #Repositorio de algoritmos (CIA-EV)
    │       ├── CIA-EV-Metrics/         
    │       │   ├── Dockerfile   
    │       │   ├── app.py
    │       │   ├── requirements.txt
    │       │   ├── requirements-dev.txt
    │       │   ├── README.md    
    │       │   ├── src/       
    │       │   ├── scripts-dev/     
    │   ├── CIA-EV_API/ 
    │       │   ├── docker-compose.yml        
```

Para a requsição deve-se utilizar a estrutura json abaixo:

```
{   "tolerance": 5.0,
    "filesizetask": 0.0,
    "com_contexto": 1,
    "universe":["work_id0", "work_id1","..."],
    "reference":{"nome": "",
                "marcacoes": [{
                "obra": "<work_id>",
                "inicio":0.0,
                "fim":0.0
                },
                {
                "obra": "<work_id>",
                "inicio": 0.0,
                "fim": 0.0,
                }]},
    "hypothesis":{"nome":"",
                "marcacoes": [{
                    "obra": "work_id",
                    "inicio": 0.0,
                    "fim": 0.0
                 },
                 {
                    "obra": "<work_id>",
                    "inicio": 0.0,
                    "fim": 0.0
                 }]}
}   
```

onde:

1) tolerance (float): valor de extrapolação de borda do segmento de referência permitido para cada extremidade. (default = 5.0 segundos)
2) filesizetask (float) (Opcional): tempo em segundos do tamanho o áudio da tarefa
3) com_contexto ({0,1}): indica a intenção de se fazer as medidas considerendo-se somente os códigos das obras que estão no universo de músicas. (default = 0)
4) universe (lista strings) (Opcional): códigos das obras que estão no universo identificável. será utilizado somente se com_contexto=1
5) reference (dicionário): 
   - "nome" (string) -- nome atribuído ao arquivo de referência
   - "marcações" (lista de dicionários): contém os tempos dos segmentos e codigos de obras de referência
      - "obra": código de obra
      - "inicio": tempo em segundos
      - "fim": tempo em segundos
6) hypothesis (dicionário): 
   - "nome" (string) -- nome atribuído ao arquivo de tarefa
   - "marcações" (lista de dicionários): contém os tempos dos segmentos e codigos de obras identificadas pelo sistema
      - "obra": código de obra
      - "inicio": tempo em segundos
      - "fim": tempo em segundos: 

O resultado do request é dado no formato json com os seguintes campos:

```
{'counts': {'missed detection': 3,
            'false alarm': 1,
            'correct tp': 2,
            'correct dap': 2,
            'total': 5
           },
 'dap': 0.4,
 'errors': {'pyannote': 'Annotation',
            'content': [   { 'segment': {'start': 0, 'end': 10},
                             'track': 'missed detection0',
                             'label': ('missed detection', 'A', '-')
                           },
                           {'segment': {'start': 6, 'end': 15},
                            'track': 'correct dap0',
                            'label': ('correct dap', 'B', 'B')
                           },
                        ],
             'uri': ('file_ref', 'file2')
            }
  "dlp": 0.8 
  "purity": 0.6
  "F": 0.6
}
```

onde:

1) counts (dicionário): contagem dos erros
2) dap (float): Detected annotation percentage
3) errors (lista de dicionários): detalhes por segmento dos erros encontrados
  - content (list): lista de segmentos com os erros
  - uri (tupla de str): nomes atribuído à referência e tarefa
4) dlp (float): Detected Length Percentage
5) purity (float): Pureza é o dual do dlp, indica como os segmentos de hipóteses são puros, ou seja estão dentro da referência.
6) F (float): é a média harmônica entre o dlp e purity. É uma medida que resume a avaliação de erros de segmentação.


![F_eq](images/F_eq.png)
