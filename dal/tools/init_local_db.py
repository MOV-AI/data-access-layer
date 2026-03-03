"""Copyright (C) Mov.ai  - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential

Developers:
- Tiago Paulino (tiago@mov.ai) - 2020

Initialize redis local storage with:
    System:PortsData
"""
from dal.models.message import Message
from dal.movaidb import MovaiDB


def main():
    """Initialize redis local db"""

    # Connect to DBs
    MovaiDB(db="global")
    MovaiDB(db="local")

    # Load data
    Message.export_portdata(db="local")


if __name__ == "__main__":
    main()
