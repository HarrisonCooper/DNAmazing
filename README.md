# DNAmazing
This is our Hack Med project, developed by: Gemma Rate, Matt Parker, Harry Cooper and Amber Barton.

## DNAmazing ARAlert
ARAlert is a tool for diagnosing Antibiotic Resistance (AR) rapidly using nanopore long read technology and the Comprehensive Antibiotic Resistance Database (CARD).

ONT reads are aligned to known AR genes in CARD using Burrows Wheeler Alignment (BWA) and the corresponding antibiotics are identified from the Antibiotic Resistance Ontology (ARO).

Discovering antibiotic resistance is a time sensitive matter. To fully utilise the speed of ONT sequencing, and to speed up time from sample to diagnosis, ARAlert includes automated text messaging and email reports using Nexmo API, to alert doctors as soon as results are available.

* data from this [paper](https://gigascience.biomedcentral.com/articles/10.1186/s13742-016-0137-2)
* downloaded data from [ENA](https://www.ebi.ac.uk/ena/data/view/PRJEB14532)
* Aligned using BWA-MEM to [CARD database](https://card.mcmaster.ca/download)

## How to Install:
```
conda config --append channels bioconda
conda create -n hackmed python=3.5 bwa click pandas
source activate hackmed
pip install nexmo
pip install pronto
```

## Requirements:
* BWA MEM
* Click
* pandas
* Nexmo Python API
* Pronto OBO parser
* CARD database

## To Run:
```
 -i, --fastq TEXT           ONT reads to map  [required]
 -j, --aro-dir TEXT         Path to directory containing aro.json, etc
                            [required]
 -o, --output TEXT          Path to output csv  [required]
 -t, --to-number TEXT       Number to send to  [required]
 -f, --from-number TEXT     Nexmo number to send from  [required]
 -k, --key TEXT             Nexmo API key  [required]
 -s, --secret TEXT          Nexmo API secret  [required]
 -e, --email-from TEXT      email address to send from  [required]
 -p, --email-password TEXT  email address password  [required]
 -r, --email-to TEXT        email address to send to  [required]
 --help                     Show this message and exit.
```
