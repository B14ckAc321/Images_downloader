# concurp2-lab22

Asynchronous image scraper script. See [Lab 22 Documentation](https://concurp2-lecture.kube.isc.heia-fr.ch/labs/lab22/)

## How to Execute the Script

You can run the script using either Docker or Poetry. Follow the instructions below for your preferred method.

### Using Docker

1. **Navigate to the source directory**:
    ```sh
    cd src/
    ```

2. **Build the Docker image**:
    ```sh
    docker build -t image_scraper .
    ```

3. **Run the Docker container**:
    ```sh
    docker run --rm -v $(pwd)/../images:/usr/app/images image_scraper
    ```

4. **Run the Docker container with additional options**:
    ```sh
    docker run --rm -v $(pwd)/../images:/usr/app/images image_scraper --dest=../images/ --URLlist=urls.txt --nc
    ```

### Using Poetry

1. **Navigate to the source directory**:
    ```sh
    cd src/
    ```

2. **Install the dependencies**:
    ```sh
    poetry install
    ```

3. **Activate the virtual environment**:
    ```sh
    poetry shell
    ```

4. **Run the script**:
    ```sh
    python3 image_scraper.py
    ```

5. **Run the script with additional options**:
    ```sh
    python3 image_scraper.py --dest=../images/ --URLlist=urls.txt --nc
    ```
