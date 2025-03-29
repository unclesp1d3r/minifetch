# Justfile for managing the development workflow of the minifetch project
# Define the default shell for commands
set shell := ["bash", "-cu"]

# Lint the codebase using ruff
lint:
    @echo "Running ruff for linting..."
    ruff check src/ tests/ --show-source

# Format the codebase using ruff
format:
    @echo "Running ruff for formatting..."
    ruff check src/ tests/ --fix

# Create a release and upload to PyPI
release version:
    @echo "Creating release version {{version}}..."
    uv build --sdist --wheel
    @echo "Generating CHANGELOG.md..."
    git-cliff --tag "v{{version}}" > CHANGELOG.md
    @echo "Tagging the release..."
    git add CHANGELOG.md
    git commit -m "Update CHANGELOG for version {{version}}"
    git tag -a "v{{version}}" -m "Release version {{version}}"
    git push origin "v{{version}}"
    @echo "Uploading to PyPI..."
    twine upload dist/*
    @echo "Release version {{version}} completed successfully."

# Clean up build artifacts
clean:
    @echo "Cleaning up build artifacts..."
    rm -rf dist/ build/ src/minifetch.egg-info/