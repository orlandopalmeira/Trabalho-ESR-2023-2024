# Tipos de *Mensagem*

## METRICA
Mensagem enviada pelo **RP** aos **Servidores de Streaming**, para atualizar a informação relativa a cada servidor. As mensagens são utilizadas para medir tempo de resposta e também verificar se houve perda de alguma mensagem pelo caminho, inferindo uma métrica de qualidade para cada servidor.

### Estrutura da mensagem de IDA (RP -> Servidor de Streaming)

```json
{
    "tipo": "METRICA",
    "dados": "",
    "origem": "",
    "timestamp": None,
}
```
### Estrutura da mensagem de VINDA (Servidor de Streaming -> RP)

```json
{
    "tipo": "METRICA",
    "dados": "",
    "origem": "",
    "timestamp": "2020-05-20 16:00:00.000000" // timestamp para medir tempo que a mensagem demorou no sentido (Servidor de Streaming -> RP)
}
```

## CHECK_VIDEO
Mensagem enviada em broadcast para todos os nodos, para encontrar o video requerido no campo **dados**. O nodo que tiver o video, responde com uma mensagem **RESP_CHECK_VIDEO** e não propaga mais a mensagem.

### Estrutura da mensagem
```json
{
    "tipo": "CHECK_VIDEO",
    "dados": "movie.Mjpeg", // nome do vídeo
    "origem": "10.0.0.1", // (OPCIONAL) IP do nodo original que enviou a mensagem (para efeitos de identificação de mensagens repetidas de broadcast)
    "timestamp": None
}
```

## RESP_CHECK_VIDEO
Mensagem enviada para o nodo que enviou a mensagem **CHECK_VIDEO**. Contém o **ip_destino** do nodo que tem o **video**.

### Estrutura da mensagem
```json
{
    "tipo": "RESP_CHECK_VIDEO",
    "dados": True, // True se tem o video
    "origem": "10.0.1.2" // para povoar routing tables no caminho de retorno
    "timestamp": None
}
```

## START_VIDEO
Mensagem enviada para um **ip_destino** que contém o **video**, previamente determinado pela resposta de um **CHECK_VIDEO**.

### Estrutura da mensagem
```json
{
    "tipo": "START_VIDEO",
    "dados": {
        "destino": "10.0.3.3", // IP do nodo com o vídeo
        "video": "movie.Mjpeg" // nome do vídeo
    },
    "origem": "10.0.0.1", // (OPCIONAL) IP do nodo original que enviou a mensagem
    "timestamp": None
}
```

## STOP_VIDEO
Mensagem enviada para um **ip_destino** que lhe está a transmitir o **video**, indicando que para si, já não precisa de enviar mais o vídeo. O nodo que recebe esta mensagem, deve parar de enviar o vídeo para o ip por onde recebeu a mensagem e se não tiver mais nenhum ip para enviar o vídeo, deve recursivamente enviar uma mensagem **STOP_VIDEO** para o ip que lhe está a enviar o vídeo.

### Estrutura da mensagem
```json
{
    "tipo": "STOP_VIDEO",
    "dados": "movie.Mjpeg", // nome do vídeo
    "origem": "",
    "timestamp": None
}
```