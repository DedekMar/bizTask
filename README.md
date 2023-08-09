
# bizTask

Includes the solution to the Python Charmer task for web scraping in scraper.py and also to the (not so efficient) solution to the coding test in arr_pair_count.py

scraper.py can either by ran by itself directly from python or it can be run inside docker.
To run the script directly:
  ```bash
  python scraper.py
  ```
Try to use any additional setup of the optional parameters if the script fails when loading websites on your connection
- `--max-retries` `    :  Maximum number of retries on request failure
- `--retry-time`    :  Time (in seconds) to wait between retries
- `--wait-time`    :  Time (in seconds) to wait between page loads
  
For docker there is a volume set up, so it needs to be specified when running the container to get the resulting .csv file
 ```bash
docker run -v "$(pwd)/data:/app/data" imagename
 ```
Replace "imagename" with the actual name of your Docker image after running "docker build"
