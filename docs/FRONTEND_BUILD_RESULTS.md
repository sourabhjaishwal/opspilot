# Frontend build results

**Validation date:** October 12, 2026  
**Toolchain:** Node.js 20 in CI; Vite 8.3.0  
**Result:** Build and lint passed

## Production build

Command, run from `frontend/`:

```bash
npm run build
```

Observed output:

| Asset | Size | Gzip |
| --- | ---: | ---: |
| `dist/index.html` | 0.57 kB | 0.35 kB |
| `dist/assets/index-ColktRqJ.css` | 16.10 kB | 3.89 kB |
| `dist/assets/index-D7bZpJE4.js` | 243.92 kB | 74.85 kB |

Build completed in 719 ms in the local validation environment. Build hashes and timing can change with source edits and environment.

## Lint

Command:

```bash
npm run lint
```

ESLint completed successfully with no reported errors.

## Configuration reminder

The frontend reads `VITE_API_BASE_URL` when it is built. Configure the correct backend origin before creating and publishing a production build. See the [frontend README](../frontend/README.md) for local setup and API URL configuration.
