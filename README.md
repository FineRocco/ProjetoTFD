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

**Licença**

Este projeto é licenciado sob a MIT License. Consulte o arquivo `LICENSE` para mais informações.
