# GitHub Actions CI/CD

GitHub's built-in automation. **CI** (Continuous Integration) auto-runs your linters and tests on every push so broken code can't merge; **CD** (Continuous Deployment) auto-builds and ships passing code to a server. You describe the steps in a YAML file and GitHub runs them for you. *Example:* The moment Alan pushes a commit, GitHub spins up a fresh machine, runs all the tests, and only if they pass does it copy the new code onto the live server — so Chloe gets the update without Alan ever logging into a server by hand.
