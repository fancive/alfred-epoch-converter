# Makefile to build and install an Alfred Workflow

# Workflow name
WORKFLOW_NAME = epoch-converter

# Source directory where your workflow files are located
SRC_DIR = .

# Destination directory for the built .alfredworkflow file
DIST_DIR = dist

# Path to the .alfredworkflow file
WORKFLOW_FILE = $(DIST_DIR)/$(WORKFLOW_NAME).alfredworkflow

# Default target
all: build

# Build the .alfredworkflow file
build:
	@echo "Building the Alfred Workflow..."
	mkdir -p $(DIST_DIR)
	cd $(SRC_DIR) && zip -r ./$(WORKFLOW_FILE) *

# Install the workflow using AppleScript (optional)
install:
	@echo "Installing the Workflow..."
	osascript -e 'tell application "Finder" to open file "$(shell pwd)/$(WORKFLOW_FILE)"'

# Clean up the built files
clean:
	@echo "Cleaning up..."
	rm -rf $(DIST_DIR)

.PHONY: all build install clean
