"""CLI interface for GitHub Profiler"""

import argparse
import os

from dotenv import load_dotenv
from github import Auth, Github

from github_profiler.pipeline import CollectionPipeline


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="GitHub Developer Intelligence System")
    parser.add_argument("--username", required=True, help="GitHub username")
    parser.add_argument("--since", default="2023-01-01", help="Scan from date")
    parser.add_argument("--output", default="profile.json", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    return parser.parse_args()


def main() -> None:
    """Main entry point"""
    load_dotenv()
    args = parse_args()

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN missing in .env")
        print("   Please create .env file with: GITHUB_TOKEN=your_token_here")
        return

    print("🚀 GitHub Developer Intelligence System")
    print(f"📊 Target: {args.username}")
    print(f"📅 Since: {args.since}")
    print(f"💾 Output: {args.output}")
    print()

    auth = Auth.Token(token)
    g = Github(auth=auth)

    pipeline = CollectionPipeline(g)
    results = pipeline.collect_user(args.username, args.since)

    print(f"\n✅ Collection complete: {len(results)} repos processed")

    # TODO: Phase 2-5: Normalization and aggregation
    # For now, save raw results
    import json

    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    print(f"💾 Raw data saved to {args.output}")


if __name__ == "__main__":
    main()
