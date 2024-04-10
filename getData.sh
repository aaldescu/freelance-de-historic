#!/bin/bash

# Define the scripts to run
scripts=("getData_freelance.de.py" "getData_freelancermap.de.py")

# Iterate over the scripts and execute them
for script in "${scripts[@]}"; do
  echo "Running $script..."
  python "$script"
  if [ $? -eq 0 ]; then
    echo "$script completed successfully."
  else
    echo "Error: $script encountered an issue."
  fi
  echo "-----------------------------------"
done

# Git operations
echo "Starting Git operations..."

# Optional: add specific files you want to commit, or use . to add all changed files
git add .

# Commit the changes with a message
git commit -m "Updated data"

# Push the changes to the master branch
git push origin master

echo "Git operations completed."
