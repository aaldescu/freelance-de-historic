#!/bin/bash
# Initialize error flag
HAS_ERROR=0
ERROR_MESSAGE=""

# Initialize success message
SUCCESS_MESSAGE="Job Summary:\n"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Navigate to the  directory for better context.
cd "$SCRIPT_DIR" || exit 1

# Activate the virtual environment
echo "Activating virtual environment..."
source "$SCRIPT_DIR/.venv/bin/activate"
if [ $? -ne 0 ]; then
  HAS_ERROR=1
  ERROR_MESSAGE+="Failed to activate virtual environment.\n"
  curl -H "Title: ❌ ERROR - Cannot activate Python venv" -H "Priority: high" -H "Tags: error,pipeline,automation,job-scraper" -d "Failed to activate the Python virtual environment." ntfy.sh/FKsIl4udhZFOd0Aq
  exit 1
fi


# Define the scripts to run
scripts=("getData_freelance.de.py" "getData_freelancermap.de.py")

# Iterate over the scripts and execute them
for script in "${scripts[@]}"; do
  echo "Running $script..."
  python "$SCRIPT_DIR/$script"
  if [ $? -eq 0 ]; then
    echo "$script completed successfully."
    SUCCESS_MESSAGE+="- $script: SUCCESS\n"
  else
    echo "Error: $script encountered an issue."
    HAS_ERROR=1
    ERROR_MESSAGE+="- $script failed to execute properly.\n"
    SUCCESS_MESSAGE+="- $script: FAILED\n"
  fi
  echo "-----------------------------------"
done

# Git operations
echo "Starting Git operations..."
# Optional: add specific files you want to commit, or use . to add all changed files
git add .

# Check if there are changes to commit
if git diff-index --quiet HEAD --; then
  echo "No changes to commit"
  SUCCESS_MESSAGE+="Git: No changes detected to commit.\n"
else
  # Commit the changes with a message
  git commit -m "Updated data"
  if [ $? -ne 0 ]; then
    HAS_ERROR=1
    ERROR_MESSAGE+="Failed to commit changes.\n"
  else
    SUCCESS_MESSAGE+="Git: Changes committed successfully.\n"
  fi

  # Push the changes to the main branch
  git push origin main
  if [ $? -ne 0 ]; then
    HAS_ERROR=1
    ERROR_MESSAGE+="Failed to push changes to repository.\n"
  else
    SUCCESS_MESSAGE+="Git: Changes pushed to repository.\n"
  fi
fi

echo "Git operations completed."

# Deactivate the virtual environment
deactivate

# Send email based on status
if [ $HAS_ERROR -eq 1 ]; then
  SUBJECT="ERROR - Freelance data collection script"
  BODY="Errors occurred during the data collection process:\n\n$ERROR_MESSAGE\n\nFull Job Summary:\n$SUCCESS_MESSAGE"
else
  SUBJECT="SUCCESS - Freelance data collection complete"
  BODY="The data collection process completed successfully:\n\n$SUCCESS_MESSAGE"
fi

# Send notification via ntfy
if [ $HAS_ERROR -eq 1 ]; then
  curl -H "Title: ❌ $SUBJECT" -H "Priority: high" -H "Tags: error,pipeline,automation,job-scraper" -d "$BODY" ntfy.sh/FKsIl4udhZFOd0Aq
else
  curl -H "Title: ✅ $SUBJECT" -H "Priority: low" -H "Tags: success,pipeline,automation,job-scraper" -d "$BODY" ntfy.sh/FKsIl4udhZFOd0Aq
fi

exit $HAS_ERROR
