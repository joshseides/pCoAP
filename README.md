# pCoAP: A Lightweight, Parallelized Protocol for IoT Devices
## Akshitha Ramachandran and Josh Seides

### Installation Instructions
1. Make sure `pip3` is installed
1. Follow the installation instructions for aiocoap [here](https://aiocoap.readthedocs.io/en/latest/installation.html)
1. `pip3 install numpy pandas scikit`
1. Depending on the execution environment, other Python 3 libraries may need to be installed, but this will be clear from the error messages when trying to run the kNN system

### Running the kNN System (Communicating with pCoAP)
1. `cd` into the `pCoAP/` directory
1. `./server_parallelism_directory.py`
1. In a separate terminal window, run `./server_knn_parallelism_worker.py 5001` to run a worker at `127.0.0.1:5001`
1. If more than 1 worker is desired, run `./server_knn_parallelism_worker.py [PORT]` in separate termainl windows for different values of `[PORT]` (go up from `5001` by 1 for each worker)
1. In a separate terminal window, run `./client_knn_parallelism.py` to initiate the kNN recommendation request (the results and time of computation will print to this termainl)
