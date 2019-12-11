# pCoAP: A Lightweight, Parallelized Protocol for IoT Devices
## Akshitha Ramachandran and Josh Seides

### Note
Please see [GitHub repo](https://github.com/joshseides/pCoAP) for commit history of changes made to original CoAP implementation.

### Files Worked With
The client-server system communicating via pCoAP is defined in `server_knn_parallelism_directory.py`, `server_knn_parallelism_entity.py`, and `client_knn_parallelism.py`. Changes made to the CoAP protocol specifications can be found in `aiocoap/resource.py` (parallelism directory code found here), `aiocoap/numbers/codes.py`, `aiocoap/numbers/optionnumbers.py`, and `aiocoap/options.py`. The Jupyter notebook for the kNN recommendation algorithm used in the client-server system can be found in `recommendation/kNN_implementation.ipynb`.

### Other Files
Other important files to note are the `aiocoap` directory in general (implementation of CoAP and pCoAP changes) and the `data` directory (contains subset versions of the original MovieLens data set for testing).

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
