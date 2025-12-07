# Release Process for ED-RadioProgram

This document describes how to create a new release of the ED-RadioProgram plugin.

## Automated Release Process

The project uses GitHub Actions to automatically create releases with ZIP files when you push a version tag.

## Creating a New Release

### 1. Update Version Information

Before creating a release, update the version in relevant files:

**In `README.md`:**
- Update the Changelog section with the new version
- Add release notes describing what's new/changed/fixed

### 2. Commit Your Changes

```bash
git add .
git commit -m "Prepare for release v1.1.0"
git push origin main
```

### 3. Create and Push a Version Tag

```bash
# Create an annotated tag (replace v1.1.0 with your version)
git tag -a v1.1.0 -m "Release v1.1.0 - Configurable overlay positions"

# Push the tag to GitHub
git push origin v1.1.0
```

### 4. Automatic Build Process

Once the tag is pushed, GitHub Actions will automatically:

1. ✅ Checkout the code
2. ✅ Create a clean directory structure
3. ✅ Copy only the necessary plugin files:
   - `load.py`
   - `README.md`
   - `LICENSE`
   - `parsers/` directory
4. ✅ Create a ZIP file: `ED-RadioProgram-v1.1.0.zip`
5. ✅ Create a GitHub Release with:
   - Release title: "ED-RadioProgram v1.1.0"
   - Installation instructions
   - Requirements
   - Link to README
6. ✅ Attach the ZIP file to the release

### 5. Verify the Release

1. Go to your GitHub repository
2. Click on "Releases" in the right sidebar
3. Verify the new release appears with:
   - Correct version number
   - ZIP file attachment
   - Proper release notes

## Version Numbering

Follow Semantic Versioning (SemVer):
- **Major version (X.0.0)**: Breaking changes
- **Minor version (1.X.0)**: New features, backwards compatible
- **Patch version (1.1.X)**: Bug fixes, backwards compatible

Examples:
- `v1.0.0` - Initial release
- `v1.1.0` - Added configurable overlay positions
- `v1.1.1` - Fixed bug in overlay positioning
- `v2.0.0` - Complete rewrite or breaking changes

## What Gets Included in the ZIP

**Included Files:**
- `load.py` - Main plugin file
- `README.md` - Documentation
- `LICENSE` - License file
- `parsers/__init__.py` - Parser package
- `parsers/base_parser.py` - Base parser class
- `parsers/orf_parser.py` - ORF parser implementation

**Excluded Files:**
- Test files (`test_*.py`, `find_api.py`)
- Debug files (`debug_*.py`, `debug_output.html`)
- Cache directory
- Git files (`.git`, `.gitignore`, `.github`)
- IDE configuration

## Troubleshooting

### Tag already exists
```bash
# Delete local tag
git tag -d v1.1.0

# Delete remote tag
git push origin :refs/tags/v1.1.0

# Create the tag again
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0
```

### Release failed to create
1. Check GitHub Actions tab for error messages
2. Verify your repository has Actions enabled
3. Check that you have proper permissions
4. Review the workflow file (`.github/workflows/release.yml`)

### ZIP file is missing files
1. Review the workflow's "Copy plugin files" step
2. Add any new essential files to the copy commands
3. Test locally by creating a ZIP manually

## Testing Before Release

Before pushing a version tag:

1. **Test the plugin locally** in EDMC
2. **Verify all features work** as expected
3. **Update documentation** (README, changelog)
4. **Check for Python syntax errors**: `python -m py_compile load.py`
5. **Review git status**: `git status` (ensure no uncommitted changes)

## Post-Release

After a successful release:

1. **Announce** the release (forums, Discord, etc.)
2. **Monitor** for bug reports
3. **Update project board** or issues as needed
4. **Consider documentation updates** if needed

## Quick Reference

```bash
# Complete release workflow
git add .
git commit -m "Prepare for release v1.1.0"
git push origin main
git tag -a v1.1.0 -m "Release v1.1.0 - Description"
git push origin v1.1.0

# Watch the automatic build
# Go to: https://github.com/YOUR_USERNAME/ED-RadioProgram/actions
```

## Support

If you encounter issues with the release process:
- Check GitHub Actions logs
- Review this document
- Check GitHub's documentation on Actions and Releases
