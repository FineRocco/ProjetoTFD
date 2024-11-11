# Distributed Fault Tolerance - Streamlet Consensus Protocol

## Team

- **Rodrigo Craveiro Rodrigues** - nº 64370
- **Denis Ungureanu** - nº 56307
- **Ana Luís** - nº 53563

## Project Overview

This project implements the Streamlet consensus algorithm, a protocol for achieving consensus in a distributed network. The protocol ensures consistency across nodes, making it suitable for distributed ledgers, blockchain, or service replication through the state machine approach. The implementation includes a node library, local transaction generation, and block ordering, all in a decentralized setup.

### Key Components

- **`streamletnetwork.py`**: Manages the network of nodes, leader rotation, and transaction distribution.
- **`transaction.py`**: Defines the structure of transactions, each containing an ID, sender, receiver, and amount.
- **`block.py`**: Represents a block in the Blockchain, storing transactions, the epoch number, and a link to the previous block through its hash.
- **`node.py`**: Represents each node in the network, handling block proposals, voting, notarization, and blockchain management.
- **`node_script.py`**: Main function for running a single node in the network.
- **`message.py`**: Defines message types for communication between nodes, including transactions, votes, proposals, and notarizations.
- **`main.py`**: Entry point for configuring and running the Streamlet protocol simulation.

### Features

- **Fault Tolerance**: Handles network partitions, crash faults, and ensures blockchain persistence across nodes.
- **Leader Rotation**: Rotates leader roles each epoch, enabling fair participation in proposing blocks.
- **Consensus Mechanism**: Ensures nodes reach agreement on the blockchain state through voting and notarization.
- **Blockchain Persistence**: Nodes can save and recover the blockchain state, preserving transaction history.

### Running the Simulation

To run the simulation, follow these steps:

1. **Clone the Repository**: Clone the project repository to your local machine.

2. **Execute `main.py`**:
    Run the following command with deafult parameters: 5 nodes, 10 epochs, 2 seconds delta.
    ```bash
    python main.py
    ```
    OR
    Run the following command in the terminal with customizable parameters for nodes, epochs, and network delay:
    ```bash
    python main.py --num_nodes <NUMBER_OF_NODES> --total_epochs <TOTAL_EPOCHS> --delta <NETWORK_DELAY>
    ```

3. **Observe Outputs**:
 - The protocol will output each node's actions, including transaction generation, block proposals, voting, and finalization.
 - The simulation will also show the finalized blockchain at each node upon completion.

# Code Overview

## `main.py`
- **Argument Parsing**: Allows customization of the number of nodes, epochs, and network delay for the Streamlet protocol.
- **Network Initialization**: Creates and starts the `StreamletNetwork` with specified parameters.
- **Epoch Execution**: Runs the protocol for a given number of epochs, rotating leaders and generating transactions.
- **Network Termination**: Stops the network after all epochs are completed and finalizes the blockchain display.

## `StreamletNetwork`
- **Network Setup**: Initializes multiple nodes, assigns leader roles, and starts a transaction generation thread.
- **Epoch Management**: Handles leader rotation and initiates block proposals each epoch.
- **Transaction Broadcasting**: Ensures transactions are evenly distributed across nodes in the network.

## `Node`
- **Block Proposal**: The leader node for each epoch proposes a block containing the list of pending transactions.
- **Voting and Notarization**: Nodes vote on blocks based on chain length and notarize blocks that receive a majority.
- **Finalization**: Finalizes a block if three consecutive blocks are notarized, appending it to the local blockchain.
- **Transaction Management**: Clears pending transactions across nodes after a proposal.

## `Message`
- **Serialization**: Manages serialization and deserialization of messages between nodes, including block proposals, votes, and transactions.
- **Message Types**: Defines `MessageType` constants for organized communication (`START_PORPOSAL`,`PROPOSE`, `VOTE`, `TRANSACTION`, `ECHO_TRANSACTION`, `ECHO_NOTARIZE`, `DISPLAY_BLOCKCHAIN`).

## `node_script.py`
- **Node Initialization**: Initializes an individual node, loads configuration parameters, and signals readiness to the Streamlet Network.
- **Message Handling**: Processes different message types received by the node.
  - **START_PROPOSAL**: Initiates a block proposal if the node is the designated leader for the current epoch.
  - **PROPOSE**: Receives and votes on proposed blocks from other nodes.
  - **VOTE**: Tracks votes for blocks, updates notarizations, and ensures no duplicate votes from the same node.
  - **ECHO_NOTARIZE**: Processes echoed notarizations to update the node’s view of the blockchain.
  - **TRANSACTION**: Adds new transactions to pending transactions and broadcasts them.
  - **ECHO_TRANSACTION**: Adds echoed transactions to ensure consistent transaction state across nodes.
  - **DISPLAY_BLOCKCHAIN**: Outputs the current blockchain state to the console.
- **Error Handling**: Logs and handles potential exceptions during message processing to maintain robustness.

## `Professor`

Retirar prints, so interesaa a blockchain

20 epocas, so pode ter 19 blocos finalizados

fazer testes com 2 nos a crashar

O terminal main do streamlet network devia desaparecer depois de iniciar a blockhcain. 

Os nós deviam gerar as transactions

A network tem de definjr uma seed para o random e passa a seed para todos os nós, e cada nó usa a seed para gerar um numero random para definir o lider entre eles. O prof disse

A network server para iniciar a blockchain e depois fechar

Deviamos usar os mesmos sockets, sem abrir e fechar sockets para cada broadcast que fazemos. O prof disse

Começar com um tempo definido para arrancar  & uma lista de ip, ports e node_id & configurações (nu_nodes, num_epocas, delta)

Quando um broadcast é feito e um nó crashou, os outros nó definem esse socket como null e o próximo broadcast os tentam connectar de novo a esse

O genesis block é o block 0

Seriam 21 blocos no total para 20 época, mas 19 blocos finalizados na blockchain

