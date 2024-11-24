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

## Lidando com falhas de liderança em node.py:

Modificou o runmétodo para incluir um mecanismo de timeout. Os nós esperam por uma proposta do líder pela duração de epoch_duration. Se nenhuma proposta for recebida, o próximo nó na fila atua como um líder de backup.
Ajustou o get_leadermétodo para implementar a lógica do período de confusão conforme os requisitos do projeto, criando bifurcações durante épocas específicas.
Durante o período de confusão, o líder está determinado de forma diferente a criar bifurcações.

## Processamento de mensagens durante o período de confusão:

Garantiu que o processamento de mensagens continuasse durante o período de confusão, mas fosse tratado de uma forma que permitisse a ocorrência de bifurcações.
Ajustou o loop de processamento de mensagens para sempre processar mensagens, mas controlar a seleção do líder para criar a confusão desejada.

## Avanço de Época:

Os nós avançam épocas independentemente com base no for-loop no runmétodo. Isso impede que os nós esperem indefinidamente por mensagens de nós travados.
Ao permitir que os líderes de backup intervenham, os nós podem continuar a processar e finalizar blocos mesmo quando alguns nós falham.

## Lógica de Finalização:

O finalize_blocksmétodo permanece consistente, finalizando um bloco quando ele é seguido por mais dois blocos autenticados na cadeia, independentemente de lacunas de época causadas por nós travados.

---

**Licença**

Este projeto é licenciado sob a MIT License. Consulte o arquivo `LICENSE` para mais informações.
