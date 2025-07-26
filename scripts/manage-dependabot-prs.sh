#!/bin/bash
# Script to manage Dependabot PRs with AI agent workflow

set -e

echo "🤖 AI-Discover Dependabot PR Manager"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to categorize PRs
categorize_prs() {
    echo -e "\n${BLUE}📊 Categorizing PRs...${NC}"

    # Get all Dependabot PRs
    MAJOR_UPDATES=()
    MINOR_UPDATES=()
    PATCH_UPDATES=()
    SECURITY_UPDATES=()

    while IFS= read -r pr; do
        PR_NUM=$(echo "$pr" | cut -f1)
        PR_TITLE=$(echo "$pr" | cut -f2)

        if [[ "$PR_TITLE" == *"security"* ]] || [[ "$PR_TITLE" == *"vulnerability"* ]]; then
            SECURITY_UPDATES+=("$PR_NUM: $PR_TITLE")
        elif [[ "$PR_TITLE" == *"major"* ]] || [[ "$PR_TITLE" =~ [0-9]+\.[0-9]+\.[0-9]+\ to\ [0-9]+\. ]]; then
            MAJOR_UPDATES+=("$PR_NUM: $PR_TITLE")
        elif [[ "$PR_TITLE" =~ [0-9]+\.[0-9]+\.[0-9]+\ to\ [0-9]+\.[0-9]+\. ]]; then
            MINOR_UPDATES+=("$PR_NUM: $PR_TITLE")
        else
            PATCH_UPDATES+=("$PR_NUM: $PR_TITLE")
        fi
    done < <(gh pr list --repo CryptoYogiLLC/AI-Discover --author "app/dependabot" --limit 50 --json number,title --jq '.[] | "\(.number)\t\(.title)"')

    echo -e "\n${RED}🚨 Security Updates (${#SECURITY_UPDATES[@]}):${NC}"
    printf '%s\n' "${SECURITY_UPDATES[@]}"

    echo -e "\n${YELLOW}⚠️  Major Updates (${#MAJOR_UPDATES[@]}):${NC}"
    printf '%s\n' "${MAJOR_UPDATES[@]}"

    echo -e "\n${BLUE}ℹ️  Minor Updates (${#MINOR_UPDATES[@]}):${NC}"
    printf '%s\n' "${MINOR_UPDATES[@]}"

    echo -e "\n${GREEN}✓ Patch Updates (${#PATCH_UPDATES[@]}):${NC}"
    printf '%s\n' "${PATCH_UPDATES[@]}"
}

# Function to review a specific PR
review_pr() {
    local pr_num=$1
    echo -e "\n${BLUE}🔍 Reviewing PR #$pr_num...${NC}"

    # Get PR details
    PR_INFO=$(gh pr view "$pr_num" --repo CryptoYogiLLC/AI-Discover --json title,body,files)

    # Check CI status
    echo "Checking CI status..."
    gh pr checks "$pr_num" --repo CryptoYogiLLC/AI-Discover

    # Prompt for action
    echo -e "\n${YELLOW}What would you like to do?${NC}"
    echo "1) Approve and merge"
    echo "2) Approve only"
    echo "3) Request changes"
    echo "4) Skip"
    read -p "Enter choice (1-4): " choice

    case $choice in
        1)
            gh pr review "$pr_num" --repo CryptoYogiLLC/AI-Discover --approve
            gh pr merge "$pr_num" --repo CryptoYogiLLC/AI-Discover --merge
            echo -e "${GREEN}✅ PR #$pr_num approved and merged${NC}"
            ;;
        2)
            gh pr review "$pr_num" --repo CryptoYogiLLC/AI-Discover --approve
            echo -e "${GREEN}✅ PR #$pr_num approved${NC}"
            ;;
        3)
            read -p "Enter review comment: " comment
            gh pr review "$pr_num" --repo CryptoYogiLLC/AI-Discover --request-changes --body "$comment"
            echo -e "${YELLOW}✏️  Changes requested for PR #$pr_num${NC}"
            ;;
        4)
            echo -e "${BLUE}⏭️  Skipping PR #$pr_num${NC}"
            ;;
    esac
}

# Function to batch approve safe updates
batch_approve_safe() {
    echo -e "\n${GREEN}🚀 Batch approving safe updates...${NC}"

    # Get all patch updates
    while IFS= read -r pr; do
        PR_NUM=$(echo "$pr" | cut -f1)
        echo "Approving PR #$PR_NUM..."
        gh pr review "$PR_NUM" --repo CryptoYogiLLC/AI-Discover --approve || true
    done < <(gh pr list --repo CryptoYogiLLC/AI-Discover --author "app/dependabot" --limit 50 --json number,title --jq '.[] | select(.title | test("patch|Bump.*from.*to.*\\.[0-9]+$")) | "\(.number)\t\(.title)"')

    echo -e "${GREEN}✅ Batch approval complete${NC}"
}

# Main menu
main_menu() {
    while true; do
        echo -e "\n${BLUE}🤖 AI Agent Workflow for Dependabot PRs${NC}"
        echo "========================================"
        echo "1) View categorized PRs"
        echo "2) Review PRs individually"
        echo "3) Batch approve patch updates"
        echo "4) Run security audit on all PRs"
        echo "5) Generate PR summary report"
        echo "6) Exit"

        read -p "Enter choice (1-6): " choice

        case $choice in
            1)
                categorize_prs
                ;;
            2)
                read -p "Enter PR number to review: " pr_num
                review_pr "$pr_num"
                ;;
            3)
                batch_approve_safe
                ;;
            4)
                echo "🔒 Running security audit..."
                # This would invoke the Security Engineer Agent
                echo "Security audit would be performed by AI agent"
                ;;
            5)
                echo "📊 Generating summary report..."
                categorize_prs > dependabot-report.txt
                echo -e "${GREEN}Report saved to dependabot-report.txt${NC}"
                ;;
            6)
                echo "👋 Goodbye!"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice${NC}"
                ;;
        esac
    done
}

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) is required but not installed.${NC}"
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not authenticated with GitHub CLI${NC}"
    echo "Run: gh auth login"
    exit 1
fi

# Start the main menu
main_menu
