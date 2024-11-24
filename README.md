# Distributed Fault Tolerance - Streamlet Consensus Protocol

## Team

- **Rodrigo Craveiro Rodrigues** - nº 64370
- **Denis Ungureanu** - nº 56307
- **Ana Luís** - nº 53563

## Descrição do Projeto
Este projeto implementa o protocolo de consenso Streamlet, projetado para sistemas distribuídos tolerantes a falhas. O protocolo é usado para manter um ledger distribuído, garantindo a ordenação consistente de blocos de transações em presença de falhas de comunicação e de nós. Ele também aborda cenários com forks e garante a convergência para uma única cadeia finalizada de blocos.

### Características Principais
1. **Seleção Determinística de Líderes**: Os líderes de cada época são selecionados de maneira determinística com base no número da época.
2. **Período de Confusão**: Implementa um período que simula forks para testar a robustez do protocolo em situações de atraso ou falhas na rede.
3. **Finalização e Notarização**: Blocos são finalizados após a observação de três blocos consecutivos notarizados.
4. **Transações Distribuídas**: Cada nó pode gerar, transmitir e processar transações de maneira eficiente.
5. **Tolerância a Falhas**: O sistema é robusto contra falhas de nós e atrasos de mensagens.

## Estrutura do Projeto
O código está organizado em múltiplos ficheiros:

- **`main.py`**: Script principal para iniciar a rede de nós distribuídos.
- **`block.py`**: Implementação da classe `Block`, que representa cada bloco da blockchain.
- **`transaction.py`**: Implementação da classe `Transaction`, que representa as transações do sistema.
- **`message.py`**: Define as mensagens usadas na comunicação entre os nós.
- **`node.py`**: Implementação da lógica de cada nó na rede.
- **`node_script.py`**: Script auxiliar para iniciar cada nó como um processo separado.

## Como Executar

### Dependências
- **Python 3.7+**
- Nenhuma dependência externa é necessária.

### Passos
1. Clone este repositório:
   ```bash
   git clone <url-do-repositório>
   cd <nome-do-repositório>
   ```

2. Execute o script principal para iniciar a rede de nós:
   ```bash
   python3 main.py --num_nodes 5 --total_epochs 10 --delta 2 --start_time "00:00" --base_port 5000
   ```
   
   **Parâmetros:**
   - `--num_nodes`: Número de nós na rede.
   - `--total_epochs`: Total de épocas a serem executadas.
   - `--delta`: Duração de uma rodada (em segundos).
   - `--start_time`: Hora de início no formato `HH:MM`.
   - `--base_port`: Porta inicial para os nós.

3. Visualize os logs de cada nó para acompanhar a execução do protocolo.

## Testes e Validação
O código foi cuidadosamente revisado para garantir conformidade com os requisitos do protocolo Streamlet, incluindo:

1. **Tolerância a falhas**:
   - Simulação de falhas de nós e atrasos de mensagens.
   - Testado para convergência após períodos de confusão.

2. **Finalização de Blocos**:
   - Verificado que três blocos consecutivos notarizados resultam na finalização do segundo bloco e de sua cadeia pai.

3. **Convergência**:
   - Testado para garantir que, após forks, todos os nós convergem para uma única cadeia finalizada.

## Estrutura de Dados
- **`Block`**: Representa cada bloco na blockchain.
  - Campos: `epoch`, `previous_hash`, `transactions`, `length`, `hash`
- **`Transaction`**: Representa uma transação.
  - Campos: `tx_id`, `sender`, `receiver`, `amount`
- **`Message`**: Representa as mensagens entre os nós.
  - Campos: `type`, `content`, `sender`

## Limitações Conhecidas
1. Atualmente, as mensagens são limitadas a 4096 bytes.
2. Os nós devem ser executados na mesma máquina ou em redes locais.

---

# Alterações relativamente ao DenisBranch (24/11)

## Seleção de Líderes

Líder determinístico com base na época : o líder para cada época é escolhido deterministicamente com base no número da época, garantindo consistência entre os nós.
Implementação do Período de Confusão : Durante o período de confusão definido, a lógica de seleção do líder é alterada para criar bifurcações intencionalmente. Isso simula partições ou atrasos de rede, permitindo que você demonstre a capacidade do protocolo de lidar com bifurcações e convergência eventual.

## Manipulação do comprimento do bloco

Cada bloco inclui um lengthatributo que representa o comprimento da cadeia até aquele bloco.
Os nós consideram o comprimento do bloco ao decidir se votam em um bloco proposto, votando apenas em blocos que estendem a maior cadeia autenticada que eles já viram até agora.

## Mecanismo de eco (transmissão uniforme e confiável)

Os nós implementam um mecanismo de eco para garantir o Uniform Reliable Broadcast (URB). Ao receber uma mensagem, os nós verificam se já a processaram usando um seen_messagesconjunto.
Se a mensagem for nova, eles a processam e transmitem para todos os outros nós, garantindo que cada mensagem seja entregue de forma confiável a todos os nós exatamente uma vez.

## Geração e tratamento de transações

Os nós geram transações aleatórias e as transmitem para outros nós.
As transações são incluídas nos blocos propostos pelo líder para a época atual.
O código garante que cada transação seja incluída apenas uma vez no blockchain, evitando duplicatas.

## Notarização e Finalização

Um bloco é autenticado quando recebe votos de mais de n/2nós distintos.
A regra de finalização é implementada: se um nó observa três blocos autenticados consecutivos com números de época consecutivos, ele finaliza o segundo bloco e toda a sua cadeia pai.
Os blocos finalizados são adicionados ao blockchain local do nó.

## Manuseio e convergência de garfos

O período de confusão cria bifurcações porque os nós ignoram o processamento de mensagens durante determinados períodos.
Após o período de confusão, os nós retomam a operação normal, e o protocolo garante que o blockchain converge de volta para uma única cadeia por meio da regra de finalização.
Tolerância a falhas :

A implementação foi projetada para lidar com falhas e recuperações de nós.
Ele pode lidar com mensagens atrasadas e nós perdendo épocas, atendendo aos requisitos de tolerância a falhas.

## Conformidade com as especificações do protocolo :

O código segue de perto o protocolo Streamlet, conforme descrito no artigo referenciado, particularmente a versão tolerante a falhas de travamento na Seção 5.
Todas as estruturas de dados, como Transaction, Block, e Message, são implementadas com os campos e funcionalidades necessários.

## Características adicionais :

O código é estruturado para permitir fácil modificação e extensão.
Instruções de registro são incluídas para rastrear o fluxo de execução e observar o comportamento do protocolo durante a operação.
Dadas essas implementações, posso confirmar que o código atende a todos os requisitos especificados e deve funcionar corretamente conforme o algoritmo de consenso do Streamlet. Ele simula efetivamente um livro-razão distribuído tolerante a falhas, demonstra o manuseio de forks e mostra como o blockchain converge de volta para uma única cadeia após interrupções.

---

**Licença**

Este projeto é licenciado sob a MIT License. Consulte o arquivo `LICENSE` para mais informações.
