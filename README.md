# Projeto de Tolerância a Faltas Distribuída - Protocolo Streamlet

**Faculdade de Ciências da Universidade de Lisboa**
**Departamento de Informática**  
**Mestrado em Engenharia Informática** 

**Autores**:  
- Rodrigo Craveiro Rodrigues (Nº 64370)  
- Denis Ungureanu (Nº 56307)  
- Ana Luís (Nº 53563)  

**Professor**: Doutor Alysson Bessani  
**1º Semestre Letivo 2024/2025** 

---

## How to run

1. Make sure all blockchain.json files are deleted

2. Configure the network_info.json file with the desired values (num_node [int]; total_epochs[int]; delta[int]; start_time[hh:mm]; ports[List<int>]; confusion_start[int], confusion_duration[int])

3. Open the terminals and run in each one: 
```
python3 node_script.py [node_id] [port number] [Rejoin flag] network_info.json`
```
- NOTE: Make sure to set start_time with a minimum 2 minutes delay from current time.

4. Wait for the epochs to complete to see the displayed blockchain or you can observe the blockchain_[i].json during the process

---

## Commands

### Script to delete all Json Files:
```
python3 delete_blockchain_files.py
```

### Start each individual node with the node_id, port, rejoin flag and config file location:
```
python3 node_script.py 1 5001 False network_info.json
```

### Command for crashed node with flag rejoin activated:
```
python3 node_script.py 1 5001 True network_info.json
```

--- 

## Introdução
Este projeto explora a implementação do protocolo de consenso Streamlet em um sistema distribuído, com foco na tolerância a falhas. Na segunda fase, a ênfase foi colocada em enfrentar desafios práticos, como nós atrasados, perda de épocas, crash-recovery e forks na blockchain, garantindo convergência para uma cadeia consistente.

---

## Objetivos
### Primeira Fase
1. Implementar o protocolo Streamlet, incluindo:
   - Proposta, votação, notarização e finalização de blocos.
2. Criar um ambiente distribuído com múltiplos nós.
3. Garantir tolerância a falhas de crash.
4. Gerar e processar transações consistentemente.

### Segunda Fase
1. Lidar com nós atrasados e perda de épocas.
2. Implementar capacidades de crash-recovery.
3. Gerir forks na blockchain.
4. Periodos de Confusão.

---

## Fundamentação Teórica
### Protocolo Streamlet
- **Funcionamento**:
  - Divisão em épocas com líder rotativo.
  - Propostas, votos, notarizações e finalizações de blocos.
- **Propriedades**:
  - Simplicidade e eficiência.
  - Tolerância a falhas de paragem com até t falhas (n ≥ 2t + 1).

### Adaptações para a Fase 2
- **Crash-Recovery**:
  - Detecção de reingresso e recuperação de blocos em falta.
- **Gestão de Forks**:
  - Seleção da cadeia mais longa.
- **Períodos de Confusão**:
  - Teste de resiliência com múltiplos líderes simultâneos.

---

## Estrutura do Projeto
### Organização
- **block.py**: Define blocos da blockchain com funções de hash e serialização.
- **transaction.py**: Implementa transações com atributos como remetente e destinatário.
- **message.py**: Gerencia mensagens (propostas, votos, transações, etc.).
- **node.py**: Representa nós com lógica de consenso, recuperação e gestão de forks.
- **node_script.py**: Inicia e gerencia nós em processos separados.
- **network_info.json**: Configurações da rede.
- **blockchain_[i].json**: Armazena o estado local dos nós.
- **delete_blockchain_files.py**: Limpa dados persistidos.

### Tecnologias e Ferramentas
- **Python3**: Linguagem principal.
- **Bibliotecas**:
  - `threading` e `socket` para concorrência e comunicação.
  - `pickle` e `json` para serialização.
  - `hashlib` para hashes seguros.

### Features

- **Fault Tolerance**: Handles network partitions, crash faults, and ensures blockchain persistence across nodes.
- **Leader Rotation**: Rotates leader roles each epoch, enabling fair participation in proposing blocks.
- **Consensus Mechanism**: Ensures nodes reach agreement on the blockchain state through voting and notarization.
- **Blockchain Persistence**: Nodes can save and recover the blockchain state, preserving transaction history.
- **Forks Management**: Nodes select the longest chain between the forks abd merge
- **Confusion Period**: It simulates a confusion in the network with multiple leaders in the same epoch and creates new forks for testing the robustness of the blockchain

### Code Overview

#### `Node.py`
- **Block Proposal**: The leader node for each epoch proposes a block containing the list of pending transactions.
- **Voting and Notarization**: Nodes vote on blocks based on chain length and notarize blocks that receive a majority.
- **Finalization**: Finalizes a block if three consecutive blocks are notarized, appending it to the local blockchain.
- **Transaction Management**: Clears pending transactions across nodes after a proposal.

#### `Message.py`
- **Serialization**: Manages serialization and deserialization of messages between nodes, including block proposals, votes, and transactions.
- **Message Types**: Defines `MessageType` constants for organized communication (`PROPOSE`, `VOTE`, `ECHO_TRANSACTION`, `QUERY_MISSING_BLOCKS`, `RESPONSE_MISSING_BLOCKS`).

#### `node_script.py`
- **Node Initialization**: Initializes an individual node, loads configuration parameters
- **Message Handling**: Processes different message types received by the node.
  - **PROPOSE**: Receives and votes on proposed blocks from other nodes.
  - **VOTE**: Tracks votes for blocks, updates notarizations, and ensures no duplicate votes from the same node.
  - **ECHO_TRANSACTION**: Adds echoed transactions to ensure consistent transaction state across nodes.
  - **QUERY_MISSING_BLOCKS**: Requests the missing blocks by sending the last saved epoch when flag rejoin activated.
  - **RESPONSE_MISSING_BLOCKS**: Responds to the rejoin request by calculating the missing blocks and sending them.
- **Error Handling**: Logs and handles potential exceptions during message processing to maintain robustness.

---

## Testes e Validação
### Metodologia
1. **Execução com diferentes números de nós**: Testes com 3, 5 e 7 nós.
2. **Simulação de falhas**: Crash de nós para validar robustez.
3. **Crash-Recovery**: Verificação de recuperação de nós falhados.
4. **Forks e períodos de confusão**: Teste de convergência para uma cadeia única.

### Resultados
- Consistência garantida em todos os testes.
- Robustez frente a falhas e atrasos na rede.
- Desempenho adequado com aumento controlado de latência.

---

## Conclusão
A implementação adaptada do protocolo Streamlet demonstrou robustez e eficiência ao enfrentar desafios práticos, consolidando conhecimentos teóricos e competências em sistemas distribuídos.

---

## Referências
1. Alysson Bessani (2024). Documentação sobre Tolerância a Faltas Distribuída no Moodle.
2. Benjamin Y. Chan e Elaine Shi. Streamlet: Textbook Streamlined Blockchains. ACM AFT ’20. 2020.
"""

