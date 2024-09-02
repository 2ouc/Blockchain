from pathlib import Path
import re

path = Path(__file__).parent.absolute()
file1 = open(str(path) + "\\transactions.txt", 'r')
line_number = 0
lines = []
while True:
        
    line = file1.readline()

    if not line:
        break

    if line.strip() == str(1):        
        item = {"dateTime": file1.readline(), "description": file1.readline(), "amount": file1.readline(), "balance": file1.readline()}
        
  
file1.close()