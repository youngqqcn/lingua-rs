#!/bin/bash
#
# Publish lingua-slim to PyPI (multi-version wheels)
#
# Usage: ./publish.sh <version>
# Example: ./publish.sh 2.6.0
#

set -e

# Ensure we're in the lingua-rs directory
cd "$(dirname "$0")"

VERSION="${1:-}"

if [[ -z "$VERSION" ]]; then
    echo "Error: Version required"
    echo "Usage: $0 <version>"
    echo "Example: $0 2.6.0"
    exit 1
fi

echo "=== Publishing lingua-slim ${VERSION} to PyPI ==="

# 1. Update version in Cargo.toml
echo "[1/6] Updating version in Cargo.toml..."
# Only replace the [package] section version, not [workspace.package]
sed -i '/^\[package\]/,/^\[/ s/^version = ".*"/version = "'"${VERSION}"'"/' Cargo.toml

# 2. Update version in pyproject.toml
echo "[2/6] Updating version in pyproject.toml..."
sed -i "s/^version = \".*\"/version = \"${VERSION}\"/" pyproject.toml

# 3. Commit changes
echo "[3/6] Committing changes..."
git add Cargo.toml Cargo.lock pyproject.toml
git commit -m "feat: bump version to ${VERSION}"

# 4. Build wheels for all Python versions
echo "[4/6] Building wheels..."
mkdir -p target/wheels

for py in 3.10 3.11 3.12 3.13 3.14; do
    INTERP=$(uv python list --only-installed | grep "cpython-${py}" | head -1 | awk '{print $2}')
    if [[ -n "$INTERP" ]]; then
        echo "  Building for Python ${py}..."
        maturin build --interpreter "$INTERP" --release --features python --out target/wheels
    else
        echo "  Python ${py} not found, skipping..."
    fi
done

# 5. Upload to PyPI
echo "[5/6] Uploading to PyPI..."
WHEELS=$(ls target/wheels/lingua_slim-${VERSION}-*.whl 2>/dev/null || true)
if [[ -z "$WHEELS" ]]; then
    echo "Error: No wheels found for version ${VERSION}"
    exit 1
fi
pipx run twine upload target/wheels/lingua_slim-${VERSION}-*.whl

# 6. Verify
echo "[6/6] Verifying on PyPI..."
curl -s "https://pypi.org/pypi/lingua-slim/${VERSION}/json" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Available wheels:')
for w in d['urls']:
    print(' ', w['filename'])
"

echo ""
echo "=== Done! lingua-slim ${VERSION} published ==="
echo "View at: https://pypi.org/project/lingua-slim/${VERSION}/"
