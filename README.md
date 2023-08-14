# huckleberry_app
This code is a pyshiny application that takes as input a CSV file of baby travking data from the Huckleberry app.

# Dependencies
```
conda env create -f environment.yml
conda activate huckleberry
```

# Launching app

## Local hosting
``` 
shiny run --reload app.py
```

View in browser:
http://127.0.0.1:8000/

## Cloud 
https://jzou.shinyapps.io/huckleberry/

# Deploying on shinyapps.io
rsconnect deploy shiny . --name jzou --title huckleberry