from streamletnetwork import StreamletNetwork

def main():
    # Initialize the network with 5 nodes
    num_nodes = 5
    total_epochs = 10

    print(f"Starting Streamlet Protocol with {num_nodes} nodes and {total_epochs} epochs.")

    # Create a new Streamlet Network
    network = StreamletNetwork(num_nodes,1)
    
    # Start the nodes in the network
    network.start_network()
    
    # Run the consensus protocol for the specified number of epochs
    network.run(total_epochs)

    # After completion, stop the network and join the threads
    network.stop_network()

    print("Streamlet Protocol finished.")

if __name__ == "__main__":
    main()
