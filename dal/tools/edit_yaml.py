#!/usr/bin/env python3
import sys

def main():
	if len(sys.argv) == 4:	
		print("Editing File",str(sys.argv[1]))
		f = open(str(sys.argv[1]), "rt")
		data = f.read()
		data = data.replace(sys.argv[2], sys.argv[3])
		f.close()
		f = open(sys.argv[1], "wt")
		f.write(data)
		f.close()
		print("File Edited")


if __name__ == "__main__":
    main()