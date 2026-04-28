import sys
from src.cli.commands import delete_user

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.cli <command>")
        return
    command = sys.argv[1]
    if command == "delete-user":
        delete_user.run()
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
