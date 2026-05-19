import argparse

def main():
    parser =argparse.ArgumentParser(
        description="OSINT Multi-Function Tool"
    )
    parser.add_argument("-i","--ip",help="Search information by IP address")
    parser.add_argument("-u","--username", help="Search information by username")
    parser.add_argument("-d","--domain",help="Enumerate domain information")
    parser.add_argument("-o","--output",help="Output file name")
    args=parser.parse_args()
    print(args)


if __name__ == "__main__":
    main()