#!/bin/bash
# Script to generate freelance market analysis reports

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Navigate to the script directory
cd "$SCRIPT_DIR" || exit 1

# Activate the virtual environment
echo "Activating virtual environment..."
source "$SCRIPT_DIR/.venv/bin/activate"
if [ $? -ne 0 ]; then
  echo "Failed to activate virtual environment."
  exit 1
fi

# Run the report generation script
echo "Generating freelance market analysis reports..."
python "$SCRIPT_DIR/generate_reports.py"
if [ $? -eq 0 ]; then
  echo "Reports generated successfully."
else
  echo "Error: Failed to generate reports."
  exit 1
fi

# Deactivate the virtual environment
deactivate

echo "Report generation completed."
echo "Reports are available in the 'reports' directory."
echo "Open 'reports/index.html' to view the reports."

exit 0
