#!/bin/bash

# Function to display usage
usage() {
  echo "Usage: $0 <log_file> [-re <search_string>] [-c] [-ic]"
  echo "  -re <search_string>   Search for specific string in JSON log."
  echo "  -ic                   Perform a case-insensitive search."
  echo "  -c                    Count the occurrences of the search string."
  exit 1
}

# init flag
count=false
search_string=""
case_insensitive=false

# Check if the log file is provided
if [ -z "$1" ]; then
  usage
fi

log_file="$1"
shift 

# Check if the log file is empty
if [ ! -s "$log_file" ]; then
  echo "[+] The log file '$log_file' is empty."
  exit 1
fi

# Parse remaining command-line options
while [[ $# -gt 0 ]]; do
  case "$1" in
    -re)
      search_string="$2"
      shift 2
      ;;
    -c)
      count=true
      shift
      ;;
    -ic)
      case_insensitive=true
      shift
      ;;
    *)
      usage
      ;;
  esac
done

# Read the log file and process each JSON line
grep_options=""
if [ "$case_insensitive" = true ]; then
  grep_options="-i"
fi

if [ -n "$search_string" ]; then
  if [ "$count" = true ]; then
    grep $grep_options -o "$search_string" "$log_file" | wc -l
  else
    # jq
    grep $grep_options "$search_string" "$log_file" | while IFS= read -r line; do
      echo "$line" | jq .
    done
  fi
else
  # prettify the entire file if no regex is given
  while IFS= read -r line; do
    echo "$line" | jq .
  done < "$log_file"
fi
