#!/bin/bash

cd /home/aaldescu/freelance-de-historic/

#update current forlder with a pull first
git pull origin main

# Define the scripts to run
scripts=("getData_freelance.de.py" "getData_freelancermap.de.py")

# Iterate over the scripts and execute them
for script in "${scripts[@]}"; do
  echo "Running $script..."
  python3 "$script"
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

# Push the changes to the main branch
git push origin main

echo "Git operations completed."
