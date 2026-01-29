# GitHub Pages Activation Guide

## Important: Manual Step Required

GitHub Pages **cannot** be activated automatically through code. You must enable it manually in your repository settings.

## Steps to Activate GitHub Pages:

1. Go to your repository: https://github.com/ali-m07/vocab-learner
2. Click on **Settings** (top menu)
3. Scroll down to **Pages** in the left sidebar
4. Under **Source**, select **"GitHub Actions"** (NOT "Deploy from a branch")
5. Click **Save**

## After Enabling:

- The GitHub Actions workflow will automatically deploy on every push to `main`
- Your site will be available at: `https://ali-m07.github.io/vocab-learner/`
- Check the **Actions** tab to see deployment progress

## Troubleshooting:

If Pages still doesn't work:
1. Check the **Actions** tab - ensure the workflow completed successfully
2. Wait 1-2 minutes after enabling Pages in settings
3. Check if the `deploy` job completed (not just `build`)
