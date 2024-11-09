import argparse
from streamletnetwork import StreamletNetwork

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Run the Streamlet Protocol with customizable parameters.")
    parser.add_argument("--num_nodes", type=int, default=3, help="The number of nodes in the network.")
    parser.add_argument("--total_epochs", type=int, default=8, help="The total number of epochs to run.")
    parser.add_argument("--delta", type=int, default=2, help="The network delay parameter (∆).")

    args = parser.parse_args()

    num_nodes = args.num_nodes
    total_epochs = args.total_epochs
    delta = args.delta

    print(f"Starting Streamlet Protocol with {num_nodes} nodes and {total_epochs} epochs.")

    # Create a new Streamlet Network 
    network = StreamletNetwork(num_nodes,delta, 8000)
    
    # Start the nodes in the network
    network.start_network()
    
    # Run the consensus protocol for the specified number of epochs
    network.run(total_epochs)

    # # After completion, stop the network and join the threads
    # network.stop_network()

    print("Streamlet Protocol finished.")

if __name__ == "__main__":
    main()
