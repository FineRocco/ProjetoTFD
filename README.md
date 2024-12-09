# Distributed Fault Tolerance - Streamlet Consensus Protocol

## Team

- **Rodrigo Craveiro Rodrigues** - nº 64370
- **Denis Ungureanu** - nº 56307
- **Ana Luís** - nº 53563

## Project Overview

This project implements the Streamlet consensus algorithm, a protocol for achieving consensus in a distributed network. The protocol ensures consistency across nodes, making it suitable for distributed ledgers, blockchain, or service replication through the state machine approach. The implementation includes a node library, local transaction generation, and block ordering, all in a decentralized setup.

## Comands

Start each individual node with the node_id, port, rejoin flag and config file location:

`python3 node_script.py 1 5001 False network_info.json`

Command for crashed node with flag rejoin activated:

`python3 node_script.py 1 5001 True network_info.json`

Script to delete all Json Files:

`python3 delete_blockchain_files.py`

## How to run

1. Make sure all blockchain.json files are deleted

2. Configure the network_info.json file with the desired values (num_node [int]; total_epochs[int]; delta[int]; start_time[hh:mm]; ports[List<int>]; confusion_start[int], confusion_duration[int])

3. Open the terminals and run in each one: `python3 node_script.py [node_id] [port number] [Rejoin flag] network_info.json`
NOTE: Make sure to set start_time with a minimum 2 minutes delay from current time.

4. Wait for the epochs to complete to see the displayed blockchain or you can observe the blockchain_[i].json during the process


### Key Components

- **`transaction.py`**: Defines the structure of transactions, each containing an ID, sender, receiver, and amount.
- **`block.py`**: Represents a block in the Blockchain, storing transactions, the epoch number, and a link to the previous block through its hash.
- **`node.py`**: Represents each node in the network, handling block proposals, voting, notarization, and blockchain management.
- **`node_script.py`**: Main function for running a single node in the network.
- **`message.py`**: Defines message types for communication between nodes, including transactions, votes, proposals, and notarizations.

### Features

- **Fault Tolerance**: Handles network partitions, crash faults, and ensures blockchain persistence across nodes.
- **Leader Rotation**: Rotates leader roles each epoch, enabling fair participation in proposing blocks.
- **Consensus Mechanism**: Ensures nodes reach agreement on the blockchain state through voting and notarization.
- **Blockchain Persistence**: Nodes can save and recover the blockchain state, preserving transaction history.
- **Forks Management**: Nodes select the longest chain between the forks abd merge
- **Confusion Period**: It simulates a confusion in the network with multiple leaders in the same epoch and creates new forks for testing the robustness of the blockchain

# Code Overview

## `Node`
- **Block Proposal**: The leader node for each epoch proposes a block containing the list of pending transactions.
- **Voting and Notarization**: Nodes vote on blocks based on chain length and notarize blocks that receive a majority.
- **Finalization**: Finalizes a block if three consecutive blocks are notarized, appending it to the local blockchain.
- **Transaction Management**: Clears pending transactions across nodes after a proposal.

## `Message`
- **Serialization**: Manages serialization and deserialization of messages between nodes, including block proposals, votes, and transactions.
- **Message Types**: Defines `MessageType` constants for organized communication (`PROPOSE`, `VOTE`, `ECHO_TRANSACTION`, `QUERY_MISSING_BLOCKS`, `RESPONSE_MISSING_BLOCKS`).

## `node_script.py`
- **Node Initialization**: Initializes an individual node, loads configuration parameters
- **Message Handling**: Processes different message types received by the node.
  - **PROPOSE**: Receives and votes on proposed blocks from other nodes.
  - **VOTE**: Tracks votes for blocks, updates notarizations, and ensures no duplicate votes from the same node.
  - **ECHO_TRANSACTION**: Adds echoed transactions to ensure consistent transaction state across nodes.
  - **QUERY_MISSING_BLOCKS**: Requests the missing blocks by sending the last saved epoch when flag rejoin activated.
  - **RESPONSE_MISSING_BLOCKS**: Responds to the rejoin request by calculating the missing blocks and sending them.
- **Error Handling**: Logs and handles potential exceptions during message processing to maintain robustness.

