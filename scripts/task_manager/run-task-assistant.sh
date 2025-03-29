#!/bin/bash
# Run the Task Assistant with Dagger integration enabled

# Set default values
DATA_DIR="$PWD/.task-manager"
DAGGER_CONFIG="$PWD/config/dagger.yaml"
AUTO_START=false
NO_BROWSER=false

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --data-dir=*)
      DATA_DIR="${1#*=}"
      shift
      ;;
    --dagger-config=*)
      DAGGER_CONFIG="${1#*=}"
      shift
      ;;
    --no-browser)
      NO_BROWSER=true
      shift
      ;;
    --auto-start)
      AUTO_START=true
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --data-dir=DIR       Directory to store task data (default: ./.task-manager)"
      echo "  --dagger-config=FILE Path to Dagger configuration file (default: ./config/dagger.yaml)"
      echo "  --no-browser         Don't open browser automatically"
      echo "  --auto-start         Automatically start the server and dashboard"
      echo "  --help               Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR"

# Build the command
CMD="./task-assistant.py --enable-dagger --dagger-config=\"$DAGGER_CONFIG\" --data-dir=\"$DATA_DIR\""

# Add optional flags
if [ "$NO_BROWSER" = true ]; then
  CMD="$CMD --no-browser"
fi

if [ "$AUTO_START" = true ]; then
  CMD="$CMD --auto-start"
fi

# Print the command
echo "Running: $CMD"

# Execute the command
eval "$CMD"
