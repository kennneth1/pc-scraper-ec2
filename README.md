**What**:
- Scrapes https://www.pricecharting.com for price data on the top 50 most expensive products in a set, for all set names stored in a `config.json` (S3 bucket: configs-pc-psa), then dumps as CSV to another S3 bucket (price-charting-scraper-output)
   - Data available: Since January 2021, monthly average prices - if scraping a card, the scraper gets these data points for its near mint, PSA7, PSA8, PSA9, BGS9.5, and PSA10 versions
   - Table is denormalized and meant conveniently serve visualizations or queries to an analytics frontend like Streamlit or some Shinylive/React/Flask/Dask stack
   - example url: https://www.pricecharting.com/game/pokemon-fusion-strike/espeon-vmax-270
- Once deployed, runs 1x/month and writes to RDS table: `psa_data`
- Runs on EC2 via chron job (16th of each month), a day after the PSA collector (See Diagram below)


![ alt text for screen readers](/images/schema.png "Text to show on mouseover")






---
**Running with docker**:
- Download Docker for MacOS, or Docker Desktop for Windows
- pull repo and create a `.venv file` to store and pass in ACCESS KEYS and secret name (for RDS queries) at docker run time (see 5th step)
-  start up Docker at root
- `docker build -t pc-scraper .`
- `docker run --env-file .env pc-scraper`

---
**Deploy to ECR**
- `aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 808544085525.dkr.ecr.us-east-1.amazonaws.com`
- `docker tag pc-scraper:latest 808544085525.dkr.ecr.us-east-1.amazonaws.com/pc-scraper:latest`
- `docker push 808544085525.dkr.ecr.us-east-1.amazonaws.com/pc-scraper:latest`

**Run on EC2**:
- launch a t2.medium	 EC2 instance (AMI2) or larger (4GB+ mem recommended), set up installation of docker, log locations, and cloudwatch agent in EC2 user script
- ssh into the EC2 instance to pull ECR and run app:
   - `ssh -i "C:\Users\YourName\Downloads\pc-keys.pem" ec2-user@ec2-public-ip-this-changes-every-restart.compute-1.amazonaws.com`
   - `aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 808544085525.dkr.ecr.us-east-1.amazonaws.com`
   - Pull latest version: `docker pull 808544085525.dkr.ecr.us-east-1.amazonaws.com/pc-scraper:latest`
   - Start docker if user script did not: `sudo systemctl start docker`
   - `docker run -d --name your-container-name 808544085525.dkr.ecr.us-east-1.amazonaws.com/pc-scraper:latest`
   - look at live logs via: `docker logs -f your-container-name`, or Cloudwatch log groups


---
**Libs**:
- requests and bs4: get list of product names/id's for each set
- selenium: for scraping and parsing each product's historical data (hidden behind a chart element)
- pandas
- boto3: get `config.json` from S3, dump final CSV

