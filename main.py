from streamletnetwork import StreamletNetwork

def main():
    # Initialize the network with 5 nodes
    num_nodes = 3
    total_epochs = 10
    delta = 5

    print(f"Starting Streamlet Protocol with {num_nodes} nodes and {total_epochs} epochs.")

    # Create a new Streamlet Network 
    network = StreamletNetwork(num_nodes,delta, 5000)
    
    # Start the nodes in the network
    network.start_network()
    
    # Run the consensus protocol for the specified number of epochs
    network.run(total_epochs)

    # # Display the final blockchain for each node
    # print("\n=== Final Blockchain for each node ===")
    # for node_process in network.processes:
    #     # Assuming we can call display_blockchain on each node's network reference
    #     node_process.display_blockchain()

    # After completion, stop the network and join the threads
    network.stop_network()

    print("Streamlet Protocol finished.")

if __name__ == "__main__":
    main()
