# ServiceOS — Almailam Engineering Consultants

A web-based practice management platform for an engineering consultancy — projects, documents, government submissions, contracts, quotations, reporting, and AI-assisted review, all in one workspace.

Built with Vue 3, TypeScript, Vite, Pinia, Vue Router and Tailwind CSS.

## Prerequisites (Windows)

Install these before you start:

1. **Node.js 20 or later (22 recommended)**
   Download the LTS installer from [nodejs.org](https://nodejs.org) and run it. This also installs `npm`.
   Verify the install by opening **PowerShell** and running:
   ```powershell
   node -v
   npm -v
   ```

2. **Git for Windows**
   Download from [git-scm.com](https://git-scm.com/download/win) and install with the default options.
   Verify with:
   ```powershell
   git --version
   ```

3. **A code editor** (optional but recommended)
   [Visual Studio Code](https://code.visualstudio.com/) with the **Vue - Official (Volar)** extension gives the best TypeScript/Vue experience.

## Getting the code

Open **PowerShell** (or **Git Bash**, or **Windows Terminal**) and run:

```powershell
git clone https://github.com/BT-Rajan/almailam-roadmap-ui.git
cd almailam-roadmap-ui
```

## Install dependencies

```powershell
npm install
```

This downloads all packages listed in `package.json` into a local `node_modules` folder. It only needs to be run again when dependencies change.

## Run the app locally

```powershell
npm run dev
```

This starts the Vite dev server (with hot-reload) and prints a local URL, typically:

```
http://localhost:5173
```

Open that URL in your browser. Leave the terminal window running while you work — press `Ctrl + C` in the terminal to stop the server.

## Build for production

```powershell
npm run build
```

This runs a full TypeScript type-check (`vue-tsc`) followed by the Vite production build. Output is written to a `dist` folder in the project root, ready to be deployed to any static file host.

To preview the production build locally before deploying:

```powershell
npm run preview
```

## Lint the code

```powershell
npm run lint
```

Runs ESLint across all `.vue` and `.ts` files and auto-fixes what it can.

## Common Windows issues

- **`npm : File cannot be loaded because running scripts is disabled on this system`**
  PowerShell's execution policy is blocking npm's shim scripts. Run PowerShell **as Administrator** and execute:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
  Then reopen a normal PowerShell window and try again.

- **Port `5173` already in use**
  Another process is using the port. Either stop it, or run `npm run dev -- --port 5174` to use a different port.

- **Long path / filename errors during `npm install`**
  Enable long path support (Windows 10/11):
  ```powershell
  git config --system core.longpaths true
  ```
  Run this in an Administrator PowerShell window, then retry `npm install`.

- **Slow installs or file-watching issues**
  Avoid placing the project inside a cloud-synced folder (OneDrive, Dropbox, etc.) — file locking from the sync client can slow down `npm install` and the dev server's hot-reload. Clone into a local folder such as `C:\dev\almailam-roadmap-ui` instead.

## Project structure

```
src/
├── components/   Reusable UI components, grouped by feature area
├── pages/        Route-level page components
├── layouts/       Shell layouts (dashboard, auth, customer portal)
├── stores/       Pinia state stores
├── services/     Mock data access layer (stands in for a future API)
├── mock/         Mock/demo data
├── types/        Shared TypeScript types
├── router/       Route definitions
└── utils/        Formatting, validation and helper functions
docs/             Product and engineering specification documents
```

This project currently runs entirely on mock/demo data (no backend required) — everything above is enough to run, build, and explore the full application.
