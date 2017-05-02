# FPyL
Fantasy Premier League module for data scraping

## Prerequisites
Use pip to install the required modules 
```
pip install -r requirements.txt
```

## Module
To get a list of available functions in the module run the following commands:
```
import FPyL
help(FPyL)
```
This will bring up the list of relative URLs and the docstring for each function.

## Scripts
### MyFixtures.py
MyFixtures.py will print a table of your players and their upcoming fixtures color-coded for difficulty.



Example:
```
MyFixtures.py --email FPLemail@email.com --password FPLpassword
````
or
```
MyFixtures.py -e FPLemail@email.com -p FPLpassword
```

Example output:

![alt text](http://i.imgur.com/kQmXcIO.png "MyFixtures.py output")
