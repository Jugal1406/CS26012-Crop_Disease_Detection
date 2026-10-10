# Archive Directory

This directory contains historical development artifacts, obsolete prototypes, and retired experimental files preserved for reference. None of these files are required for running or deploying the production application.

## Contents

### 1. `development-artifacts/`
- **`old_repo_snapshot.zip`**: An early snapshot of root markdown files from initial GitHub repository initialization. Retained in archive rather than root project workspace to keep active source clean.

### 2. `obsolete-experiments/`
- **`firebase-auth/`**:
  - `backend/firebase_auth.py`: Early Firebase Admin SDK token verification prototype. Retired in Module 9 when the project adopted Clerk authentication (`clerk_auth.py` and `@clerk/clerk-react`).
  - `frontend/firebaseconfig.js` and `frontend/src_firebaseConfig.js`: Early Firebase client configuration files.

### 3. `old-generated-reports/`
- Directory reserved for archiving past experimental diagnostic reports or benchmark runs without polluting active user scan history.
