# Tolerância a Faltas Distribuída 2024/25

## Team

Rodrigo Craveiro Rodrigues nº 64370;
Denis Ungureanu nº 56307;
Ana Luís nº 53563

## Project

The project consists in the implementation of the Streamlet consensus algorithm that can be used to
implement a distributed ledger. Such abstraction is sufficient for implementing blockchain or for replicating
services using the state machine approach.
The project requires the implementation of a local transaction generation module and a node library capable
of generating and ordering the blocks containing the transactions in a distributed way.

### Componentes do Projeto

- **blockchain.py**: Implementa a blockchain com suporte a forks e recuperação de falhas.
- **transaction.py**: Define a estrutura das transações.
- **node.py**: Define um nó da rede distribuída e as suas operações.
- **message.py**: Define os tipos de mensagens trocadas entre os nós.
- **main.py**: Entrada principal para simulação do sistema.

### Como Executar

1. Clone o repositório.
2. Execute `main.py` para simular a interação entre dois nós e a geração de blocos.
3. Verifique a saída para observar como os nós adicionam transações, votam em blocos e alcançam consenso.

### Funcionalidades da Fase 2

- **Recuperação de Falhas**: Cada nó pode salvar e carregar o estado da blockchain.
- **Convergência de Forks**: Implementação de lógica de votação e eco para garantir consenso.
- **Persistência**: A blockchain é salva em ficheiros para permitir a recuperação do estado em caso de falha.
