#!/bin/bash

# Simple script to display project progress in the terminal
# Usage: ./show-progress.sh

# Set up colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Progress bar function
function progress_bar {
    local percent=$1
    local width=50
    local num_chars=$(($width * $percent / 100))
    local bar=""
    
    for ((i=0; i<$num_chars; i++)); do
        bar="${bar}█"
    done
    
    for ((i=$num_chars; i<$width; i++)); do
        bar="${bar}░"
    done
    
    echo -e "[${GREEN}${bar}${NC}] ${percent}%"
}

# Project data file
PROJECT_DATA="docs/project_progress.json"

if [ ! -f "$PROJECT_DATA" ]; then
    echo -e "${RED}Error: Project data file not found at $PROJECT_DATA${NC}"
    exit 1
fi

# Extract data using grep and sed (simple approach without jq dependency)
PROJECT_NAME=$(grep -o '"project_name": "[^"]*"' "$PROJECT_DATA" | cut -d'"' -f4)
CURRENT_PHASE=$(grep -o '"current_phase": "[^"]*"' "$PROJECT_DATA" | cut -d'"' -f4)
START_DATE=$(grep -o '"start_date": "[^"]*"' "$PROJECT_DATA" | cut -d'"' -f4)
TARGET_DATE=$(grep -o '"target_completion_date": "[^"]*"' "$PROJECT_DATA" | cut -d'"' -f4)
OVERALL_PROGRESS=$(grep -o '"overall_progress": [0-9]*' "$PROJECT_DATA" | awk '{print $2}')

# Display project header
echo -e "${BOLD}${CYAN}================================================${NC}"
echo -e "${BOLD}${CYAN}  Project: ${NC}${BOLD}$PROJECT_NAME${NC}"
echo -e "${BOLD}${CYAN}================================================${NC}"
echo -e "${BLUE}Current Phase:${NC} $CURRENT_PHASE"
echo -e "${BLUE}Timeline:${NC} $START_DATE to $TARGET_DATE"
echo -e ""
echo -e "${BLUE}Overall Progress:${NC}"
progress_bar $OVERALL_PROGRESS
echo -e ""

# Extract phase data
echo -e "${BOLD}${PURPLE}Phase Progress:${NC}"
grep -A 1 '"name": "[^"]*",' "$PROJECT_DATA" | grep -v "\--" | sed 'N;s/\n/ /' | grep "name\|progress" | while read -r line; do
    PHASE_NAME=$(echo "$line" | grep -o '"name": "[^"]*"' | cut -d'"' -f4)
    PHASE_PROGRESS=$(echo "$line" | grep -o '"progress": [0-9]*' | awk '{print $2}')
    
    if [ ! -z "$PHASE_NAME" ] && [ ! -z "$PHASE_PROGRESS" ]; then
        echo -e "${YELLOW}$PHASE_NAME:${NC}"
        progress_bar $PHASE_PROGRESS
        echo -e ""
    fi
done

# Extract recent updates
echo -e "${BOLD}${PURPLE}Recent Updates:${NC}"
grep -A 2 '"date": "202[0-9]-[0-9][0-9]-[0-9][0-9]",' "$PROJECT_DATA" | grep -v "\--" | sed 'N;s/\n/ /' | grep "date\|message" | while read -r line; do
    UPDATE_DATE=$(echo "$line" | grep -o '"date": "[^"]*"' | cut -d'"' -f4)
    UPDATE_MESSAGE=$(echo "$line" | grep -o '"message": "[^"]*"' | cut -d'"' -f4)
    
    if [ ! -z "$UPDATE_DATE" ] && [ ! -z "$UPDATE_MESSAGE" ]; then
        echo -e "${YELLOW}[$UPDATE_DATE]${NC} $UPDATE_MESSAGE"
    fi
done

echo -e ""
echo -e "${BOLD}${PURPLE}Upcoming Milestones:${NC}"
grep -A 2 '"date": "202[0-9]-[0-9][0-9]-[0-9][0-9]",' "$PROJECT_DATA" | grep -v "\--" | sed 'N;s/\n/ /' | grep "date\|name" | grep "upcoming_milestones" -A 10 | while read -r line; do
    MILESTONE_DATE=$(echo "$line" | grep -o '"date": "[^"]*"' | cut -d'"' -f4)
    MILESTONE_NAME=$(echo "$line" | grep -o '"name": "[^"]*"' | cut -d'"' -f4)
    
    if [ ! -z "$MILESTONE_DATE" ] && [ ! -z "$MILESTONE_NAME" ]; then
        echo -e "${YELLOW}[$MILESTONE_DATE]${NC} $MILESTONE_NAME"
    fi
done

echo -e ""
echo -e "${BOLD}${CYAN}================================================${NC}"
echo -e "${BLUE}Run './task status' for current task details${NC}"
echo -e "${BOLD}${CYAN}================================================${NC}"
