#!/usr/bin/env python3
import os
import platform

def main():
    print(f"Sistema Operacional: {platform.system()}")
    print(f"Diretório Atual: {os.getcwd()}")

if __name__ == "__main__":
    main()
